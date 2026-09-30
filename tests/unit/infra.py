"""Run from project root: python tests/unit/infra.py."""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from src.backend.infra.core.config.settings import Settings
from src.backend.infra.manage import Infrastructure
from src.backend.logs.log import LOG_FILE, logger


class InfraTests(unittest.IsolatedAsyncioTestCase):
    def test_configuration_test_defaults_and_prod_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            with patch.dict(
                os.environ,
                {"ENVIROIMENT": "test"},
                clear=True,
            ):
                settings = Settings.from_env(root)
                self.assertEqual(settings.enviroiment, "test")
                self.assertTrue(
                    settings.database_url.startswith(
                        "sqlite+aiosqlite:///"
                    )
                )
                self.assertIsNone(settings.openai_api_key)
                self.assertGreaterEqual(len(settings.sing.encode()), 32)

            with patch.dict(
                os.environ,
                {
                    "ENVIROIMENT": "test",
                    "DATABASE_URL": "postgresql://user:pass@host/db",
                },
                clear=True,
            ):
                with self.assertRaises(ValueError):
                    Settings.from_env(root)

            with patch.dict(
                os.environ,
                {"ENVIROIMENT": "prod"},
                clear=True,
            ):
                with self.assertRaises(ValueError):
                    Settings.from_env(root)

    async def test_database(self):
        settings = Settings(
            enviroiment="test",
            database_url="sqlite+aiosqlite://",
            sing="unit-test-signing-key-32-bytes-long",
        )
        infrastructure = Infrastructure(settings)
        connection = infrastructure.external_database(
            "sqlite+aiosqlite://"
        )
        try:
            engine, sessions = await connection()
            self.assertIsInstance(engine, AsyncEngine)
            self.assertIsInstance(sessions, async_sessionmaker)
            self.assertTrue(await connection.test())
            async with sessions() as session:
                self.assertIsInstance(session, AsyncSession)
                result = await session.execute(text("SELECT 42"))
                self.assertEqual(result.scalar_one(), 42)
        finally:
            await connection.close()
            await infrastructure.close()

    async def test_redis(self):
        from src.backend.infra.connection.redis import RedisConnection

        with patch(
            "src.backend.infra.connection.redis.Redis"
        ) as mocked:
            client = mocked.return_value
            client.ping = AsyncMock(return_value=True)
            client.aclose = AsyncMock()

            connection = RedisConnection()
            self.assertIs(await connection(), client)
            self.assertTrue(await connection.test_connection())

            await connection.close()
            client.aclose.assert_awaited_once()

    async def test_sender_http_transport(self):
        settings = Settings(
            enviroiment="test",
            database_url="sqlite+aiosqlite://",
            url_sender="http://sender.test",
            sing="unit-test-signing-key-32-bytes-long",
        )
        infrastructure = Infrastructure(settings)

        response = unittest.mock.Mock()
        response.raise_for_status.return_value = None

        with patch(
            "src.backend.infra.sender.requests.post",
            return_value=response,
        ) as post:
            result = await infrastructure.sender.send(
                "to@example.com",
                "Subject",
                "Body",
                html=True,
            )

        self.assertEqual(result, {"sent": True})
        post.assert_called_once_with(
            "http://sender.test/sender/",
            json={
                "email": "to@example.com",
                "subject": "Subject",
                "body": "Body",
            },
        )

    async def test_openai_test_mode(self):
        settings = Settings(
            enviroiment="test",
            database_url="sqlite+aiosqlite://",
            openai_api_key=None,
            sing="unit-test-signing-key-32-bytes-long",
        )
        infrastructure = Infrastructure(settings)

        response = await infrastructure.openai.send("hello")
        self.assertIn("Resposta de teste", response.output_text)
        self.assertEqual(response.output, [])

    def test_logger(self):
        from logging import StreamHandler
        from logging.handlers import RotatingFileHandler

        marker = "Teste unitário da infraestrutura: logger funcionando"
        logger.info(marker)
        for handler in logger.handlers:
            handler.flush()

        self.assertTrue(
            any(type(handler) is StreamHandler for handler in logger.handlers)
        )
        self.assertTrue(
            any(
                isinstance(handler, RotatingFileHandler)
                for handler in logger.handlers
            )
        )
        self.assertIn(marker, LOG_FILE.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
