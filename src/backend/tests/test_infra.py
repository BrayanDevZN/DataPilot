import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests

from src.backend.infra.connection.ai import AIConnection
from src.backend.infra.connection.database import PostgreSQLConnection, SQLConnection
from src.backend.infra.connection.email import ResendConnection
from src.backend.infra.connection.http import HTTPConnection
from src.backend.infra.core.config import Settings, load_environment
from src.backend.infra.manage import Infrastructure


class ConfigurationTests(unittest.TestCase):
    def test_local_env_has_priority_and_selection_ignores_cwd(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            root = Path(directory)
            local = root / "src/backend/infra/core/.env"
            local.parent.mkdir(parents=True)
            local.write_text("DB_NAME=local\n", encoding="utf-8")
            (root / ".env").write_text("DB_NAME=root\nDB_HOST=root-only\n", encoding="utf-8")
            self.assertEqual(load_environment(root), local)
            self.assertEqual(os.getenv("DB_NAME"), "local")
            self.assertIsNone(os.getenv("DB_HOST"))

    def test_root_fallback_and_process_priority(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"DB_NAME": "process"}, clear=True):
            root = Path(directory)
            (root / ".env").write_text("DB_NAME=root\nDB_HOST=localhost\n", encoding="utf-8")
            settings = Settings.from_env(root)
            self.assertEqual(settings.db_name, "process")
            self.assertEqual(settings.db_host, "localhost")

    def test_process_only_and_secret_repr(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {
            "DB_NAME": "process", "DB_PASSWORD": "db-sensitive",
            "KEY_EMAIL": "email-sensitive", "SECRET": "jwt-sensitive",
            "DATABASE_URL": "postgresql://u:url-sensitive@localhost/db",
        }, clear=True):
            settings = Settings.from_env(Path(directory))
            self.assertEqual(settings.db_name, "process")
            for secret in ("db-sensitive", "email-sensitive", "jwt-sensitive", "url-sensitive"):
                self.assertNotIn(secret, repr(settings))

    def test_invalid_port_is_rejected(self):
        for value in ("bad", "0", "-1"):
            with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"DB_PORT": value}, clear=True):
                with self.assertRaisesRegex(ValueError, "DB_PORT"):
                    Settings.from_env(Path(directory))


class DatabaseTests(unittest.TestCase):
    def test_sql_connection_real_sqlite_probe_and_engine_reuse(self):
        connection = SQLConnection("sqlite://")
        self.assertNotIn("engine", connection.__dict__)
        self.assertTrue(connection.test_connection())
        self.assertIs(connection.engine, connection.engine)
        connection.close()

    def test_postgresql_url_preserves_special_password_and_pool_options(self):
        connection = PostgreSQLConnection(database="db", host="localhost", username="user",
                                          password="p@ss:/?#", connect_timeout=7)
        with patch("src.backend.infra.connection.database.create_engine") as create:
            connection.engine
            self.assertEqual(create.call_args.args[0].password, "p@ss:/?#")
            self.assertEqual(create.call_args.kwargs["connect_args"], {"connect_timeout": 7})
            self.assertTrue(create.call_args.kwargs["pool_pre_ping"])

    def test_database_url_uses_psycopg_and_keeps_ssl(self):
        connection = PostgreSQLConnection(database_url="postgres://u:p@localhost/db?sslmode=require")
        with patch("src.backend.infra.connection.database.create_engine") as create:
            connection.engine
            url = create.call_args.args[0]
            self.assertEqual(url.drivername, "postgresql+psycopg")
            self.assertEqual(url.query["sslmode"], "require")

    def test_missing_credentials_are_deferred_until_use(self):
        infrastructure = Infrastructure(Settings())
        infrastructure.close()
        self.assertNotIn("engine", infrastructure.database.__dict__)
        with self.assertRaisesRegex(ValueError, "Missing PostgreSQL settings"):
            infrastructure.database.engine

    def test_failed_database_probe_propagates(self):
        connection = SQLConnection("sqlite://")
        with patch.object(connection, "connect", side_effect=RuntimeError("offline")):
            with self.assertRaisesRegex(RuntimeError, "offline"):
                connection.test_connection()


class HTTPTests(unittest.TestCase):
    def test_ai_probe_uses_health_path_timeout_and_get(self):
        with patch("src.backend.infra.connection.http.requests.Session") as session:
            client = session.return_value.__enter__.return_value
            self.assertTrue(AIConnection("https://ai.example", timeout=8, health_path="/health").test_connection())
            client.request.assert_called_once_with("GET", "https://ai.example/health", headers={}, timeout=8)
            client.request.return_value.raise_for_status.assert_called_once()

    def test_resend_probe_is_authenticated_and_read_only(self):
        with patch("src.backend.infra.connection.http.requests.Session") as session:
            client = session.return_value.__enter__.return_value
            self.assertTrue(ResendConnection("test-key").test_connection())
            client.request.assert_called_once_with(
                "GET", "https://api.resend.com/domains",
                headers={"Authorization": "Bearer test-key"}, timeout=30,
            )

    def test_resend_missing_key_does_not_make_network_call(self):
        with patch("src.backend.infra.connection.http.requests.Session") as session:
            with self.assertRaisesRegex(ValueError, "KEY_EMAIL"):
                ResendConnection(None).test_connection()
            session.assert_not_called()

    def test_http_error_and_timeout_propagate(self):
        with patch("src.backend.infra.connection.http.requests.Session") as session:
            client = session.return_value.__enter__.return_value
            client.request.return_value.raise_for_status.side_effect = requests.HTTPError("503")
            with self.assertRaises(requests.HTTPError):
                HTTPConnection().test_connection("https://example.com")
            client.request.side_effect = requests.Timeout("offline")
            with self.assertRaises(requests.Timeout):
                HTTPConnection().test_connection("https://example.com")

    def test_invalid_protocol_is_rejected(self):
        with self.assertRaises(ValueError):
            HTTPConnection().test_connection("file:///etc/hosts")


if __name__ == "__main__":
    unittest.main()
