"""Run: pip install -r tests/integration/requirements.txt && python tests/integration/db_control.py.

Starts an isolated local PostgreSQL and creates a private schema per test.
No production configuration or credentials are used.
"""

import asyncio
import sys
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pgserver
from sqlalchemy import func, text, update
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.backend.logs.log import logger
from src.backend.repository.db.control import (
    CollaborationNotificationsControl, ConversationsControl, DashboardChartsControl,
    DashboardChartSettingsControl, DashboardCollaborationsControl, DashboardsControl,
    DataSourcesControl, MessagesControl, UsersControl, ValidationAccountControl, ValidationControl,
)
from src.backend.repository.db.control_base import RecordNotFoundError, TransactionRequiredError
from src.backend.repository.db.migrate import Migration
from src.backend.repository.db.models import ValidationAccount


class ControlTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.previous_log_level = logger.level
        logger.setLevel('WARNING')
        cls.directory = tempfile.TemporaryDirectory(prefix='datapilot-control-tests-')
        cls.server = pgserver.get_server(Path(cls.directory.name) / 'data', cleanup_mode='stop')
        cls.url = make_url(cls.server.get_uri()).set(drivername='postgresql+psycopg')

    @classmethod
    def tearDownClass(cls):
        cls.server.cleanup()
        cls.directory.cleanup()
        logger.setLevel(cls.previous_log_level)

    async def asyncSetUp(self):
        self.schema = 'control_test_' + uuid4().hex
        self.engine = create_async_engine(self.url, connect_args={'options': '-c search_path=' + self.schema})
        async with self.engine.begin() as connection:
            await connection.execute(text('CREATE SCHEMA ' + self.schema))
        await Migration(self.engine)()
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    async def asyncTearDown(self):
        async with self.engine.begin() as connection:
            await connection.execute(text('DROP SCHEMA ' + self.schema + ' CASCADE'))
        await self.engine.dispose()

    async def user(self, suffix='owner'):
        async with self.sessions() as session, session.begin():
            return (await UsersControl(session).create({
                'name': suffix, 'username': suffix, 'email': suffix + '@example.com',
                'password': 'stored-hash', 'age': 18, 'gender': 'other',
            }))['item']

    async def dashboard(self, owner_id):
        async with self.sessions() as session, session.begin():
            return (await DashboardsControl(session).create({'user_id': owner_id, 'title': 'Test'}))['item']

    async def test_crud_filters_and_transaction_requirement(self):
        async with self.sessions() as session:
            with self.assertRaises(TransactionRequiredError):
                await UsersControl(session).create({'name': 'No transaction'})
        owner = await self.user()
        async with self.sessions() as session, session.begin():
            control = UsersControl(session)
            self.assertEqual((await control.get_by_email('OWNER@EXAMPLE.COM'))['item']['user_id'], owner['user_id'])
            self.assertFalse((await control.update(owner['user_id'], {'name': 'Wrong'}, expected={'name': 'stale'}))['updated'])
            changed = await control.update(owner['user_id'], {'name': 'Changed'}, expected={'name': 'owner'})
            self.assertTrue(changed['updated'])
            with self.assertRaises(ValueError):
                await control.update(owner['user_id'], {'user_id': 99})
            self.assertEqual((await control.list())['count'], 1)
            self.assertTrue((await control.delete(owner['user_id']))['deleted'])

    async def test_rollback_preserves_all_tables(self):
        owner = await self.user()
        try:
            async with self.sessions() as session, session.begin():
                await ConversationsControl(session).create({'user_id': owner['user_id'], 'title': 'Rollback'})
                await DashboardsControl(session).create({'user_id': owner['user_id'], 'title': 'Rollback'})
                raise RuntimeError('abort transaction')
        except RuntimeError:
            pass
        async with self.sessions() as session:
            self.assertEqual((await ConversationsControl(session).list())['count'], 0)
            self.assertEqual((await DashboardsControl(session).list())['count'], 0)

    async def test_concurrent_duplicate_email_is_rejected_by_database(self):
        async def insert_user(username):
            try:
                async with self.sessions() as session, session.begin():
                    await UsersControl(session).create({'name': 'Test', 'username': username,
                        'email': 'duplicate@example.com', 'password': 'hash', 'age': 18, 'gender': 'other'})
                return True
            except IntegrityError:
                return False
        results = await asyncio.gather(insert_user('first'), insert_user('second'))
        self.assertEqual(sum(results), 1)

    async def test_concurrent_account_code_consumption_and_expiration(self):
        async with self.sessions() as session, session.begin():
            await ValidationAccountControl(session).issue('test@example.com', '012345')
        async def consume():
            async with self.sessions() as session, session.begin():
                return (await ValidationAccountControl(session).consume('test@example.com', '012345'))['consumed']
        self.assertEqual(sum(await asyncio.gather(consume(), consume())), 1)
        async with self.sessions() as session, session.begin():
            code = (await ValidationAccountControl(session).issue('test@example.com', '654321'))['item']
            await session.execute(update(ValidationAccount).where(ValidationAccount.validation_id == code['validation_id']).values(created_at=func.now() - timedelta(hours=1)))
            self.assertFalse((await ValidationAccountControl(session).consume('test@example.com', '654321'))['consumed'])

    async def test_concurrent_password_code_consumption(self):
        owner = await self.user()
        async with self.sessions() as session, session.begin():
            await ValidationControl(session).issue(owner['user_id'], '012345')
        async def consume():
            async with self.sessions() as session, session.begin():
                return (await ValidationControl(session).consume(owner['user_id'], '012345'))['consumed']
        self.assertEqual(sum(await asyncio.gather(consume(), consume())), 1)

    async def test_conversation_scope_and_message_atomicity(self):
        owner, other = await self.user(), await self.user('other')
        async with self.sessions() as session, session.begin():
            conversation = (await ConversationsControl(session).create({'user_id': owner['user_id'], 'title': 'Test'}))['item']
            with self.assertRaises(RecordNotFoundError):
                await MessagesControl(session).append(conversation['id'], other['user_id'], 'user', 'Forbidden')
            await MessagesControl(session).append(conversation['id'], owner['user_id'], 'user', 'Test')
            self.assertEqual((await MessagesControl(session).list_by_conversation(conversation['id'], owner['user_id']))['count'], 1)
            self.assertEqual((await MessagesControl(session).list_by_conversation(conversation['id'], other['user_id']))['count'], 0)
            self.assertFalse((await ConversationsControl(session).delete_owned(conversation['id'], other['user_id']))['deleted'])
            await ConversationsControl(session).delete_owned(conversation['id'], owner['user_id'])
            self.assertEqual((await MessagesControl(session).list())['count'], 0)

    async def test_concurrent_settings_saves_produce_one_row(self):
        owner = await self.user()
        dashboard = await self.dashboard(owner['user_id'])
        async def save(color):
            async with self.sessions() as session, session.begin():
                return await DashboardChartSettingsControl(session).save(dashboard['id'], {'chart_color': color})
        await asyncio.gather(save('red'), save('blue'))
        async with self.sessions() as session:
            rows = await DashboardChartSettingsControl(session).list(filters={'dashboard_id': dashboard['id']})
            self.assertEqual(rows['count'], 1)

    async def test_concurrent_invitation_response_has_one_winner(self):
        owner, other = await self.user(), await self.user('other')
        dashboard = await self.dashboard(owner['user_id'])
        async with self.sessions() as session, session.begin():
            collaboration = (await DashboardCollaborationsControl(session).invite(dashboard['id'], owner['user_id'], other['user_id'], 'read'))['item']
        async def respond(value):
            async with self.sessions() as session, session.begin():
                return (await DashboardCollaborationsControl(session).respond(collaboration['id'], other['user_id'], value))['updated']
        self.assertEqual(sum(await asyncio.gather(respond('accepted'), respond('declined'))), 1)

    async def test_refresh_version_and_failed_replacement(self):
        owner = await self.user()
        dashboard = await self.dashboard(owner['user_id'])
        charts = [{'chart_type': 'bar', 'title': 'Original', 'chart_data': []}]
        async with self.sessions() as session, session.begin():
            await DashboardChartsControl(session).replace_all(dashboard['id'], charts)
            with self.assertRaises(IntegrityError):
                await DashboardChartsControl(session).replace_all(dashboard['id'], [{'chart_type': 'bar', 'title': None, 'chart_data': []}])
            self.assertEqual((await DashboardChartsControl(session).list_by_dashboard(dashboard['id']))['items'][0]['title'], 'Original')
        async def refresh(title):
            async with self.sessions() as session, session.begin():
                return (await DashboardsControl(session).finish_refresh(
                    dashboard['id'], owner['user_id'], dashboard['updated_at'],
                    [{'chart_type': 'bar', 'title': title, 'chart_data': []}], 'Analysis',
                ))['updated']
        self.assertEqual(sum(await asyncio.gather(refresh('First'), refresh('Second'))), 1)

    async def test_concurrent_source_claims_and_stale_lease(self):
        owner = await self.user()
        async with self.sessions() as session, session.begin():
            source = (await DataSourcesControl(session).create({'user_id': owner['user_id'], 'name': 'Source',
                'file_name': 'api', 'file_data': [], 'row_count': 0, 'column_count': 0,
                'source_type': 'web', 'refresh_interval_days': 1, 'next_sync_at': func.now() - timedelta(days=1)}))['item']
        async def claim():
            async with self.sessions() as session, session.begin():
                return await DataSourcesControl(session).claim_due(owner['user_id'])
        claims = await asyncio.gather(claim(), claim())
        self.assertEqual(sum(result['count'] for result in claims), 1)
        claimed = next(result['items'][0] for result in claims if result['count'])
        async with self.sessions() as session, session.begin():
            control = DataSourcesControl(session)
            data = {'file_data': [{'a': 1}], 'row_count': 1, 'column_count': 1}
            self.assertFalse((await control.finish_sync(source['id'], owner['user_id'], data, source['next_sync_at']))['updated'])
            self.assertTrue((await control.finish_sync(source['id'], owner['user_id'], data, claimed['next_sync_at']))['updated'])
            self.assertFalse((await control.finish_sync(source['id'], owner['user_id'], data, claimed['next_sync_at']))['updated'])

    async def test_notification_scope(self):
        owner, other = await self.user(), await self.user('other')
        async with self.sessions() as session, session.begin():
            control = CollaborationNotificationsControl(session)
            notification = (await control.create({'user_id': owner['user_id'], 'message': 'Test', 'notification_type': 'invitation'}))['item']
            self.assertFalse((await control.mark_read(notification['id'], other['user_id']))['updated'])
            self.assertEqual((await control.mark_all_read(owner['user_id']))['count'], 1)
            self.assertEqual((await control.mark_all_read(owner['user_id']))['count'], 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
