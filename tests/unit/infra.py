"""Run from the project root: python tests/unit/infra.py.

Install first: pip install -r tests/requirements.txt.
Uses in-memory SQLite and mocked yagmail, without production access.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Allow direct execution without installing the backend as a package.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from src.backend.infra.core.config import Settings
from src.backend.infra.manage import Infrastructure
from src.backend.logs.log import LOG_FILE, logger


class InfraTests(unittest.IsolatedAsyncioTestCase):
    def test_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".env").write_text("DB_NAME=root_database\nEMAIL_USER=sender@example.com\nEMAIL_PASSWORD=test-password\n", encoding="utf-8")
            with patch.dict(os.environ, {}, clear=True):
                settings = Settings.from_env(root)
                self.assertEqual(settings.db_name, "root_database")
                self.assertEqual(settings.email_user, "sender@example.com")
                self.assertEqual(settings.email_password, "test-password")
                self.assertNotIn("test-password", repr(settings))

            local = root / "src/backend/infra/core/.env"
            local.parent.mkdir(parents=True)
            local.write_text("DB_NAME=local_database\n", encoding="utf-8")
            with patch.dict(os.environ, {}, clear=True):
                self.assertEqual(Settings.from_env(root).db_name, "local_database")
            with patch.dict(os.environ, {"DB_NAME": "process_database"}, clear=True):
                self.assertEqual(Settings.from_env(root).db_name, "process_database")

    async def test_database(self):
        infrastructure = Infrastructure(Settings())
        connection = infrastructure.external_database("sqlite+aiosqlite://")
        try:
            engine, sessions = await connection()
            self.assertIsInstance(engine, AsyncEngine)
            self.assertIsInstance(sessions, async_sessionmaker)
            self.assertTrue(await connection.test())
            async with sessions() as session:
                self.assertIsInstance(session, AsyncSession)
                result = await session.execute(text("SELECT 42"))
                self.assertEqual(result.scalar_one(), 42)
            async with sessions() as first, sessions() as second:
                self.assertIsNot(first, second)
        finally:
            await connection.close()
            await infrastructure.close()

    async def test_sender(self):
        import threading
        infrastructure = Infrastructure(Settings(email_user="sender@example.com", email_password="test-password"))
        main_thread = threading.get_ident()
        with patch("src.backend.infra.sender.yagmail.SMTP") as mocked:
            client = mocked.return_value.__enter__.return_value
            threads = []
            client.send.side_effect = lambda **kwargs: threads.append(threading.get_ident())
            self.assertEqual(await infrastructure.sender.send("to@example.com", "Subject", "Body"), {"sent": True})
            mocked.assert_called_once_with(user="sender@example.com", password="test-password", timeout=30)
            client.send.assert_called_once_with(to="to@example.com", subject="Subject", contents="Body")
            mocked.return_value.__exit__.assert_called_once()
            self.assertNotEqual(threads[0], main_thread)
            client.send.side_effect = RuntimeError("SMTP error")
            with self.assertRaises(RuntimeError):
                await infrastructure.sender.send("to@example.com", "Subject", "Body")
            self.assertEqual(mocked.return_value.__exit__.call_count, 2)
        with self.assertRaises(ValueError):
            await Infrastructure(Settings()).sender.send("to@example.com", "Subject", "Body")

    async def test_email_files_and_html_sender(self):
        from src.backend.infra.manage import email_files
        from html.parser import HTMLParser
        templates = email_files.read()
        self.assertEqual(set(templates), {"create_account", "change_password"})
        for name, template in templates.items():
            with self.subTest(template=name):
                self.assertIn("{{code}}", template)
                self.assertIn('<html lang="pt-BR">', template)
                HTMLParser().feed(template)
        message = templates["create_account"].replace("{{code}}", "012345")
        infrastructure = Infrastructure(Settings(email_user="sender@example.com", email_password="test-password"))
        with patch("src.backend.infra.sender.yagmail.SMTP") as mocked:
            result = await infrastructure.sender.send("to@example.com", "Confirme sua conta", message, html=True)
            self.assertEqual(result, {"sent": True})
            mocked.return_value.__enter__.return_value.send.assert_called_once_with(
                to="to@example.com", subject="Confirme sua conta", contents=message,
            )
        self.assertIn("{{code}}", email_files.read()["create_account"])

    def test_logger(self):
        from logging import StreamHandler
        from logging.handlers import RotatingFileHandler

        marker = "Teste unitário da infraestrutura: logger funcionando"
        logger.info(marker)
        for handler in logger.handlers:
            handler.flush()
        self.assertTrue(any(type(handler) is StreamHandler for handler in logger.handlers))
        self.assertTrue(any(isinstance(handler, RotatingFileHandler) for handler in logger.handlers))
        self.assertIn(marker, LOG_FILE.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
