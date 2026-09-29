"""Run from the project root: python tests/unit/infra.py.

Install first: pip install -r tests/requirements.txt.
Uses in-memory SQLite and mocked Resend, without production access.
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
            (root / ".env").write_text("DB_NAME=root_database\n", encoding="utf-8")
            with patch.dict(os.environ, {}, clear=True):
                self.assertEqual(Settings.from_env(root).db_name, "root_database")

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

    def test_resend(self):
        infrastructure = Infrastructure(Settings(key_email="unit-test-key"))
        with patch("src.backend.infra.connection.email.requests.Session") as mocked:
            client = mocked.return_value.__enter__.return_value
            client.request.return_value.status_code = 200
            self.assertIs(infrastructure.email(), infrastructure.email)
            client.request.assert_called_once_with(
                "GET", "https://api.resend.com/domains",
                headers={"Authorization": "Bearer unit-test-key"}, timeout=30,
            )
            client.request.return_value.raise_for_status.assert_called_once()

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
