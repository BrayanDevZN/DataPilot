"""Run: pip install -r tests/integration/requirements.txt && python tests/integration/repository.py.

Starts an isolated local PostgreSQL and creates a private schema per test.
No production configuration or credentials are used.
"""

import asyncio
import sys
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path
from uuid import UUID, uuid4
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pgserver
from sqlalchemy import func, text, update
from fakeredis.aioredis import FakeRedis
from unittest.mock import AsyncMock, patch
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.backend.logs.log import logger
from src.backend.repository.manage import ControlDb, Migration
from src.backend.repository.db.control_base import RecordNotFoundError, TransactionRequiredError
from src.backend.repository.db.models import ValidationAccount


class RepositoryTests(unittest.IsolatedAsyncioTestCase):
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
        self.redis = FakeRedis(decode_responses=True)
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
        await self.redis.aclose()

    def database_controls(self, session):
        """Exercise the SQL controls through the cached manager's db attributes."""
        manager = ControlDb(self.redis, session)
        return SimpleNamespace(**{name: control.db for name, control in vars(manager).items()})

    async def test_manager_instantiates_cached_controls(self):
        async with self.sessions() as session:
            manager = ControlDb(self.redis, session)
            self.assertEqual(len(vars(manager)), 11)
            for name, control in vars(manager).items():
                self.assertTrue(type(control).__name__.startswith('Control'))
                self.assertIs(control.session, session)
                self.assertIs(control.cache.redis, self.redis)
                self.assertEqual(control.table.name, name)
            with self.assertRaises(TypeError):
                ControlDb(None, session)

    async def user(self, suffix='owner'):
        async with self.sessions() as session, session.begin():
            return (await self.database_controls(session).users.create({
                'name': suffix, 'username': suffix, 'email': suffix + '@example.com',
                'password': 'stored-hash', 'age': 18, 'gender': 'other', 'auth2': False,
            }))['item']

    async def dashboard(self, owner_id):
        async with self.sessions() as session, session.begin():
            return (await self.database_controls(session).dashboards.create({'user_id': owner_id, 'title': 'Test'}))['item']

    async def test_crud_filters_and_context_transactions(self):
        async with self.sessions() as session:
            control = self.database_controls(session).users
            automatic = await control.create({'name': 'Auto', 'username': 'auto',
                'email': 'auto@example.com', 'password': 'hash', 'age': 18, 'gender': 'other'})
            self.assertFalse(session.in_transaction())
            self.assertTrue((await control.get(automatic['item']['user_id']))['found'])
            await control.delete(automatic['item']['user_id'])
            self.assertFalse(session.in_transaction())
            await session.execute(text('SELECT 1'))
            with self.assertRaises(TransactionRequiredError):
                await control.list()
            await session.rollback()
            with self.assertRaises(ValueError):
                await control.create({'unknown_column': 'invalid'})
            self.assertFalse(session.in_transaction())
            self.assertEqual((await control.list())['count'], 0)
        owner = await self.user()
        async with self.sessions() as session, session.begin():
            control = self.database_controls(session).users
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
                await self.database_controls(session).conversations.create({'user_id': owner['user_id'], 'title': 'Rollback'})
                await self.database_controls(session).dashboards.create({'user_id': owner['user_id'], 'title': 'Rollback'})
                raise RuntimeError('abort transaction')
        except RuntimeError:
            pass
        async with self.sessions() as session:
            self.assertEqual((await self.database_controls(session).conversations.list())['count'], 0)
            self.assertEqual((await self.database_controls(session).dashboards.list())['count'], 0)

    async def test_concurrent_duplicate_email_is_rejected_by_database(self):
        async def insert_user(username):
            try:
                async with self.sessions() as session, session.begin():
                    await self.database_controls(session).users.create({'name': 'Test', 'username': username,
                        'email': 'duplicate@example.com', 'password': 'hash', 'age': 18, 'gender': 'other'})
                return True
            except IntegrityError:
                return False
        results = await asyncio.gather(insert_user('first'), insert_user('second'))
        self.assertEqual(sum(results), 1)

    async def test_concurrent_account_code_consumption_and_expiration(self):
        async with self.sessions() as session, session.begin():
            await self.database_controls(session).validation_account.issue('test@example.com', '012345')
        async def consume():
            async with self.sessions() as session, session.begin():
                return (await self.database_controls(session).validation_account.consume('test@example.com', '012345'))['consumed']
        self.assertEqual(sum(await asyncio.gather(consume(), consume())), 1)
        async with self.sessions() as session, session.begin():
            code = (await self.database_controls(session).validation_account.issue('test@example.com', '654321'))['item']
            await session.execute(update(ValidationAccount).where(ValidationAccount.validation_id == code['validation_id']).values(created_at=func.now() - timedelta(hours=1)))
            self.assertFalse((await self.database_controls(session).validation_account.consume('test@example.com', '654321'))['consumed'])

    async def test_concurrent_password_code_consumption(self):
        owner = await self.user()
        async with self.sessions() as session, session.begin():
            await self.database_controls(session).validation.issue(owner['user_id'], '012345')
        async def consume():
            async with self.sessions() as session, session.begin():
                return (await self.database_controls(session).validation.consume(owner['user_id'], '012345'))['consumed']
        self.assertEqual(sum(await asyncio.gather(consume(), consume())), 1)

    async def test_conversation_scope_and_message_atomicity(self):
        owner, other = await self.user(), await self.user('other')
        async with self.sessions() as session, session.begin():
            conversation = (await self.database_controls(session).conversations.create({'user_id': owner['user_id'], 'title': 'Test'}))['item']
            with self.assertRaises(RecordNotFoundError):
                await self.database_controls(session).messages.append(conversation['id'], other['user_id'], 'user', 'Forbidden')
            await self.database_controls(session).messages.append(conversation['id'], owner['user_id'], 'user', 'Test')
            self.assertEqual((await self.database_controls(session).messages.list_by_conversation(conversation['id'], owner['user_id']))['count'], 1)
            self.assertEqual((await self.database_controls(session).messages.list_by_conversation(conversation['id'], other['user_id']))['count'], 0)
            self.assertFalse((await self.database_controls(session).conversations.delete_owned(conversation['id'], other['user_id']))['deleted'])
            await self.database_controls(session).conversations.delete_owned(conversation['id'], owner['user_id'])
            self.assertEqual((await self.database_controls(session).messages.list())['count'], 0)

    async def test_concurrent_settings_saves_produce_one_row(self):
        owner = await self.user()
        dashboard = await self.dashboard(owner['user_id'])
        async def save(color):
            async with self.sessions() as session, session.begin():
                return await self.database_controls(session).dashboard_chart_settings.save(dashboard['id'], {'chart_color': color})
        await asyncio.gather(save('red'), save('blue'))
        async with self.sessions() as session:
            rows = await self.database_controls(session).dashboard_chart_settings.list(filters={'dashboard_id': dashboard['id']})
            self.assertEqual(rows['count'], 1)

    async def test_concurrent_invitation_response_has_one_winner(self):
        owner, other = await self.user(), await self.user('other')
        dashboard = await self.dashboard(owner['user_id'])
        async with self.sessions() as session, session.begin():
            collaboration = (await self.database_controls(session).dashboard_collaborations.invite(dashboard['id'], owner['user_id'], other['user_id'], 'read'))['item']
        async def respond(value):
            async with self.sessions() as session, session.begin():
                return (await self.database_controls(session).dashboard_collaborations.respond(collaboration['id'], other['user_id'], value))['updated']
        self.assertEqual(sum(await asyncio.gather(respond('accepted'), respond('declined'))), 1)

    async def test_refresh_version_and_failed_replacement(self):
        owner = await self.user()
        dashboard = await self.dashboard(owner['user_id'])
        charts = [{'chart_type': 'bar', 'title': 'Original', 'chart_data': []}]
        async with self.sessions() as session, session.begin():
            await self.database_controls(session).dashboard_charts.replace_all(dashboard['id'], charts)
            with self.assertRaises(IntegrityError):
                await self.database_controls(session).dashboard_charts.replace_all(dashboard['id'], [{'chart_type': 'bar', 'title': None, 'chart_data': []}])
            self.assertEqual((await self.database_controls(session).dashboard_charts.list_by_dashboard(dashboard['id']))['items'][0]['title'], 'Original')
        async def refresh(title):
            async with self.sessions() as session, session.begin():
                return (await self.database_controls(session).dashboards.finish_refresh(
                    dashboard['id'], owner['user_id'], dashboard['updated_at'],
                    [{'chart_type': 'bar', 'title': title, 'chart_data': []}], 'Analysis',
                ))['updated']
        self.assertEqual(sum(await asyncio.gather(refresh('First'), refresh('Second'))), 1)

    async def test_concurrent_source_claims_and_stale_lease(self):
        owner = await self.user()
        async with self.sessions() as session, session.begin():
            source = (await self.database_controls(session).data_sources.create({'user_id': owner['user_id'], 'name': 'Source',
                'file_name': 'api', 'file_data': [], 'row_count': 0, 'column_count': 0,
                'source_type': 'web', 'refresh_interval_days': 1, 'next_sync_at': func.now() - timedelta(days=1)}))['item']
        async def claim():
            async with self.sessions() as session, session.begin():
                return await self.database_controls(session).data_sources.claim_due(owner['user_id'])
        claims = await asyncio.gather(claim(), claim())
        self.assertEqual(sum(result['count'] for result in claims), 1)
        claimed = next(result['items'][0] for result in claims if result['count'])
        async with self.sessions() as session, session.begin():
            control = self.database_controls(session).data_sources
            data = {'file_data': [{'a': 1}], 'row_count': 1, 'column_count': 1}
            self.assertFalse((await control.finish_sync(source['id'], owner['user_id'], data, source['next_sync_at']))['updated'])
            self.assertTrue((await control.finish_sync(source['id'], owner['user_id'], data, claimed['next_sync_at']))['updated'])
            self.assertFalse((await control.finish_sync(source['id'], owner['user_id'], data, claimed['next_sync_at']))['updated'])

    async def test_notification_scope(self):
        owner, other = await self.user(), await self.user('other')
        async with self.sessions() as session, session.begin():
            control = self.database_controls(session).collaboration_notifications
            notification = (await control.create({'user_id': owner['user_id'], 'message': 'Test', 'notification_type': 'invitation'}))['item']
            self.assertFalse((await control.mark_read(notification['id'], other['user_id']))['updated'])
            self.assertEqual((await control.mark_all_read(owner['user_id']))['count'], 1)
            self.assertEqual((await control.mark_all_read(owner['user_id']))['count'], 0)

    async def test_manager_and_crud_for_every_table(self):
        owner, other = await self.user(), await self.user('other')
        dashboard = await self.dashboard(owner['user_id'])
        async with self.sessions() as session:
            db = self.database_controls(session)
            self.assertEqual(len(vars(db)), 11)
            self.assertTrue(all(control.session is session for control in vars(db).values()))
            self.assertFalse(session.in_transaction())
            conversation = (await db.conversations.create({'user_id': owner['user_id'], 'title': 'Parent'}))['item']
            cases = {
                'users': ({'name': 'CRUD', 'username': 'crud', 'email': 'crud@example.com',
                           'password': 'hash', 'age': 18, 'gender': 'other', 'auth2': False},
                          {'name': 'Changed', 'auth2': True}),
                'validation': ({'user_id': owner['user_id'], 'number': '123456'}, {'number': '654321'}),
                'validation_account': ({'email': 'crud@example.com', 'number': '123456'}, {'used': True}),
                'conversations': ({'user_id': owner['user_id'], 'title': 'CRUD'}, {'title': 'Changed'}),
                'messages': ({'conversation_id': conversation['id'], 'role': 'user', 'content': 'CRUD'}, {'content': 'Changed'}),
                'data_sources': ({'user_id': owner['user_id'], 'name': 'CRUD', 'file_name': 'file',
                                  'file_data': [], 'row_count': 0, 'column_count': 0}, {'name': 'Changed'}),
                'dashboards': ({'user_id': owner['user_id'], 'title': 'CRUD'}, {'title': 'Changed'}),
                'dashboard_charts': ({'dashboard_id': dashboard['id'], 'chart_type': 'bar',
                                      'title': 'CRUD', 'chart_data': []}, {'title': 'Changed'}),
                'dashboard_chart_settings': ({'dashboard_id': dashboard['id']}, {'chart_color': 'red'}),
                'dashboard_collaborations': ({'dashboard_id': dashboard['id'], 'owner_user_id': owner['user_id'],
                                             'collaborator_user_id': other['user_id'], 'permission': 'read'}, {'permission': 'edit'}),
                'collaboration_notifications': ({'user_id': owner['user_id'], 'message': 'CRUD',
                                                 'notification_type': 'invitation'}, {'message': 'Changed'}),
            }
            for name, (values, change) in cases.items():
                with self.subTest(table=name):
                    control = getattr(db, name)
                    created = await control.create(values)
                    self.assertIsInstance(created, dict)
                    record_id = created['item'][control.primary_key.name]
                    filters = {control.primary_key.name: record_id}
                    fetched = await control.get(record_id, for_update=True)
                    self.assertEqual(fetched['item'], created['item'])
                    listed = await control.list(filters=filters, limit=1)
                    self.assertEqual(listed, {'items': [created['item']], 'count': 1})
                    self.assertEqual((await control.list(filters=filters, offset=1))['count'], 0)
                    self.assertFalse((await control.update(record_id, change, expected={control.primary_key.name: -1}))['updated'])
                    changed = await control.update(record_id, change)
                    self.assertTrue(changed['updated'])
                    for key, value in change.items():
                        self.assertEqual(changed['item'][key], value)
                    self.assertFalse((await control.delete(record_id, expected={control.primary_key.name: -1}))['deleted'])
                    self.assertEqual(await control.delete(record_id), {'deleted': True, 'id': record_id})
                    self.assertEqual(await control.get(record_id), {'found': False, 'item': None})
                    self.assertFalse((await control.update(record_id, change))['updated'])
                    self.assertFalse((await control.delete(record_id))['deleted'])
                    self.assertFalse(session.in_transaction())
                    redis = FakeRedis(decode_responses=True)
                    try:
                        cached = getattr(ControlDb(redis, session), name)
                        inserted = await cached.insert(values)
                        identity = inserted[control.primary_key.name]
                        cache_key = f'{name}:{control.primary_key.name}:{identity}'
                        self.assertGreater(await redis.ttl(cache_key), 0)
                        self.assertLessEqual(await redis.ttl(cache_key), 60)
                        with patch.object(cached.db, 'list', new_callable=AsyncMock) as query:
                            self.assertEqual(await cached.select(control.primary_key.name, identity), inserted)
                            query.assert_not_awaited()
                        await redis.delete(cache_key)
                        self.assertEqual(await cached.select(control.primary_key.name, identity), inserted)
                        self.assertIsNotNone(await redis.get(cache_key))
                        updated = await cached.update(control.primary_key.name, identity, change)
                        for key, value in change.items():
                            self.assertEqual(updated[key], value)
                        self.assertIsNone(await redis.get(cache_key))
                        self.assertEqual(await cached.select(control.primary_key.name, identity), updated)
                        self.assertTrue((await cached.delete(control.primary_key.name, identity))['deleted'])
                        self.assertIsNone(await redis.get(cache_key))
                        self.assertIsNone(await cached.select(control.primary_key.name, identity))
                    finally:
                        await redis.aclose()
        with self.assertRaises(TypeError):
            ControlDb(self.redis, None)

    async def test_scoped_queries_and_dashboard_aggregation(self):
        owner, other = await self.user(), await self.user('other')
        async with self.sessions() as session:
            db = self.database_controls(session)
            user_id = owner['user_id']
            self.assertEqual((await db.users.get_by_username(' OWNER '))['item']['user_id'], user_id)
            self.assertFalse((await db.users.get_by_username('missing'))['found'])
            self.assertFalse((await db.users.get_by_email('missing@example.com'))['found'])
            changed = await db.users.update(user_id, {'username': ' RENAMED ', 'email': ' RENAMED@EXAMPLE.COM '})
            self.assertEqual(changed['item']['username'], 'renamed')
            self.assertEqual(changed['item']['email'], 'renamed@example.com')
            conversation = (await db.conversations.create({'user_id': user_id, 'title': 'Owned'}))['item']
            self.assertTrue((await db.conversations.get_owned(conversation['id'], user_id, for_update=True))['found'])
            self.assertFalse((await db.conversations.get_owned(conversation['id'], other['user_id']))['found'])
            self.assertEqual((await db.conversations.list_by_user(user_id))['count'], 1)
            self.assertEqual((await db.conversations.list_by_user(other['user_id']))['count'], 0)
            source = (await db.data_sources.create({'user_id': user_id, 'name': 'Source', 'file_name': 'file',
                'file_data': [], 'row_count': 0, 'column_count': 0}))['item']
            self.assertEqual((await db.data_sources.list_by_user(user_id))['count'], 1)
            self.assertEqual((await db.data_sources.list_by_user(other['user_id']))['count'], 0)
            dashboard = (await db.dashboards.create({'user_id': user_id, 'title': 'Dashboard', 'data_source_id': source['id']}))['item']
            self.assertEqual((await db.dashboards.list_by_user(user_id))['count'], 1)
            self.assertEqual((await db.dashboards.list_by_user(other['user_id']))['count'], 0)
            replacement = await db.dashboard_charts.replace_all(dashboard['id'], [{'chart_type': 'bar', 'title': 'Chart', 'chart_data': []}])
            chart_id = replacement['items'][0]['id']
            settings = await db.dashboard_chart_settings.save(dashboard['id'], {'chart_color': 'red'}, chart_id=chart_id)
            saved = await db.dashboard_chart_settings.save(dashboard['id'], {'chart_color': 'blue'}, chart_id=chart_id)
            self.assertEqual(saved['item']['id'], settings['item']['id'])
            self.assertEqual(saved['item']['chart_color'], 'blue')
            combined = await db.dashboards.get_with_charts(dashboard['id'], user_id)
            self.assertEqual(combined['item']['charts'], replacement['items'])
            self.assertEqual(combined['item']['chart_settings'], [saved['item']])
            with self.assertRaises(RecordNotFoundError):
                await db.dashboards.get_with_charts(dashboard['id'], other['user_id'])
            marked = await db.dashboards.mark_outdated_by_source(source['id'])
            self.assertEqual(marked['count'], 1)
            self.assertTrue(marked['items'][0]['is_outdated'])
            self.assertEqual((await db.dashboards.mark_outdated_by_source(-1))['count'], 0)
            refreshed = await db.dashboards.finish_refresh(dashboard['id'], user_id, marked['items'][0]['updated_at'], [{'chart_type': 'bar', 'title': 'Refreshed', 'chart_data': []}], 'Analysis', prompt='New prompt')
            self.assertTrue(refreshed['updated'])
            self.assertEqual(refreshed['item']['prompt'], 'New prompt')
            self.assertFalse(refreshed['item']['is_outdated'])
            self.assertEqual((await db.dashboard_charts.list_by_dashboard(dashboard['id']))['items'][0]['title'], 'Refreshed')
            note = (await db.collaboration_notifications.create({'user_id': user_id, 'message': 'Test', 'notification_type': 'invitation'}))['item']
            self.assertEqual((await db.collaboration_notifications.list_by_user(user_id))['count'], 1)
            self.assertEqual((await db.collaboration_notifications.list_by_user(other['user_id']))['count'], 0)
            self.assertTrue((await db.collaboration_notifications.mark_read(note['id'], user_id))['updated'])
            self.assertTrue((await db.collaboration_notifications.get(note['id']))['item']['is_read'])

    async def test_invalid_inputs_rollback_and_session_remains_usable(self):
        owner = await self.user()
        dashboard = await self.dashboard(owner['user_id'])
        async with self.sessions() as session:
            db = self.database_controls(session)
            calls = [
                lambda: db.users.list(limit=0),
                lambda: db.users.list(offset=-1),
                lambda: db.users.list(filters={'unknown': 1}),
                lambda: db.users.create({'unknown': 1}),
                lambda: db.users.update(owner['user_id'], {'user_id': 99}),
                lambda: db.validation.issue(owner['user_id'], 'abc'),
                lambda: db.validation.consume(owner['user_id'], '123456', max_age=timedelta(0)),
                lambda: db.validation_account.issue('test@example.com', 'abc'),
                lambda: db.validation_account.consume('test@example.com', '123456', max_age=timedelta(0)),
                lambda: db.messages.append(-1, owner['user_id'], 'invalid', 'text'),
                lambda: db.messages.list_by_conversation(-1, owner['user_id'], limit=0),
                lambda: db.dashboard_collaborations.invite(dashboard['id'], owner['user_id'], owner['user_id'], 'read'),
                lambda: db.dashboard_collaborations.respond(-1, owner['user_id'], 'invalid'),
            ]
            for call in calls:
                with self.assertRaises(ValueError):
                    await call()
                self.assertFalse(session.in_transaction())
            with self.assertRaises(RecordNotFoundError):
                await db.dashboard_chart_settings.save(dashboard['id'], {'chart_color': 'red'}, chart_id=-1)
            with self.assertRaises(RecordNotFoundError):
                await db.validation.issue(-1, '123456')
            with self.assertRaises(IntegrityError):
                await db.users.create({'name': 'Duplicate', 'username': 'duplicate', 'email': owner['email'],
                    'password': 'hash', 'age': 18, 'gender': 'other'})
            self.assertFalse(session.in_transaction())
            self.assertEqual((await db.users.list())['count'], 1)

    async def test_public_ids_generation_uniqueness_and_immutability(self):
        owner, other = await self.user(), await self.user('other')
        first, second = await self.dashboard(owner['user_id']), await self.dashboard(owner['user_id'])
        self.assertEqual(len({owner['public_id'], other['public_id'], first['public_id'], second['public_id']}), 4)
        for row in (owner, other, first, second):
            self.assertIsInstance(row['public_id'], UUID)
            self.assertEqual(row['public_id'].version, 4)
        async with self.sessions() as session:
            db = self.database_controls(session)
            for control, row, key in ((db.users, owner, 'user_id'), (db.dashboards, first, 'id')):
                with self.subTest(table=control.table.name):
                    self.assertEqual((await control.list(filters={'public_id': row['public_id']}))['items'][0][key], row[key])
                    with self.assertRaises(ValueError):
                        await control.update(row[key], {'public_id': uuid4()})
                    with self.assertRaises(IntegrityError):
                        async with session.begin():
                            await session.execute(update(control.table).where(control.primary_key != row[key]).values(public_id=row['public_id']))
                    self.assertEqual((await control.get(row[key]))['item']['public_id'], row['public_id'])

    async def test_public_ids_upgrade_existing_rows_is_idempotent(self):
        owner = await self.user()
        dashboard = await self.dashboard(owner['user_id'])
        async with self.engine.begin() as connection:
            await connection.execute(text('ALTER TABLE users DROP COLUMN public_id'))
            await connection.execute(text('ALTER TABLE users DROP COLUMN auth2'))
            await connection.execute(text('ALTER TABLE dashboards DROP COLUMN public_id'))
        await Migration(self.engine)()
        async with self.sessions() as session:
            db = self.database_controls(session)
            user_after = (await db.users.get(owner['user_id']))['item']
            dashboard_after = (await db.dashboards.get(dashboard['id']))['item']
            self.assertIsInstance(user_after['public_id'], UUID)
            self.assertFalse(user_after['auth2'])
            self.assertIsInstance(dashboard_after['public_id'], UUID)
            self.assertEqual(dashboard_after['user_id'], owner['user_id'])
        await Migration(self.engine)()
        async with self.sessions() as session:
            db = self.database_controls(session)
            self.assertEqual((await db.users.get(owner['user_id']))['item']['public_id'], user_after['public_id'])
            self.assertEqual((await db.dashboards.get(dashboard['id']))['item']['public_id'], dashboard_after['public_id'])
        new_user = await self.user('new')
        self.assertIsInstance(new_user['public_id'], UUID)
        self.assertFalse(new_user['auth2'])

    async def test_cached_public_id_aliases_rollback_and_cascades(self):
        redis = FakeRedis(decode_responses=True)
        try:
            async with self.sessions() as session:
                manager = ControlDb(redis, session)
                users = manager.users
                dashboards = manager.dashboards
                user = await users.insert({'name': 'Cache', 'username': 'cache', 'email': 'cache@example.com',
                    'password': 'hash', 'age': 18, 'gender': 'other'})
                public_key = f"users:public_id:{user['public_id']}"
                self.assertIsNotNone(await redis.get(public_key))
                self.assertEqual(await users.select('public_id', str(user['public_id'])), user)
                self.assertEqual(await users.select('email', ' CACHE@EXAMPLE.COM '), user)
                changed = await users.update('public_id', user['public_id'], {'username': 'changed'})
                self.assertIsNone(await redis.get(public_key))
                self.assertIsNone(await users.select('username', 'cache'))
                self.assertEqual(await users.select('username', 'changed'), changed)
                dashboard = await dashboards.insert({'user_id': user['user_id'], 'title': 'Cached'})
                with self.assertRaises(ValueError):
                    async with session.begin():
                        await users.insert({'name': 'Forbidden'})
                with self.assertRaises(IntegrityError):
                    await users.insert({'name': 'Duplicate', 'username': 'different', 'email': user['email'],
                        'password': 'hash', 'age': 18, 'gender': 'other'})
                self.assertIsNone(await users.select('username', 'different'))
                self.assertTrue((await users.delete('public_id', user['public_id']))['deleted'])
                self.assertIsNone(await dashboards.select('public_id', dashboard['public_id']))
                self.assertFalse((await users.delete('user_id', user['user_id']))['deleted'])
                self.assertIsNone(await users.update('user_id', user['user_id'], {'name': 'Missing'}))
        finally:
            await redis.aclose()


if __name__ == '__main__':
    unittest.main(verbosity=2)
