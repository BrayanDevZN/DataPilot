"""Run from the root: python tests/unit/domain.py."""

import ast
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import jwt as pyjwt

from src.backend.domain.module import ExpiredTokenError, InvalidTokenError, JWT, PasswordHash


class JWTTests(unittest.TestCase):
    def setUp(self):
        self.sign = "unit-test-signing-secret-32-bytes-long"
        self.jwt = JWT(sign=self.sign)

    def test_roundtrip_does_not_modify_input(self):
        payload = {"user_id": 7, "role": "user"}
        token = self.jwt.write(payload)
        claims = self.jwt.read(token)
        self.assertEqual(claims["user_id"], 7)
        self.assertIn("exp", claims)
        self.assertIn("iat", claims)
        self.assertNotIn("exp", payload)

    def test_wrong_signature_and_unsigned_tokens_are_rejected(self):
        token = self.jwt.write({"user_id": 7})
        with self.assertRaises(InvalidTokenError):
            JWT(sign="another-unit-test-secret-32-bytes-long").read(token)
        unsigned = pyjwt.encode({"user_id": 7}, key="", algorithm="none")
        with self.assertRaises(InvalidTokenError):
            self.jwt.read(unsigned)

    def test_expired_missing_expiration_and_malformed_tokens_are_rejected(self):
        now = datetime.now(timezone.utc)
        expired = pyjwt.encode({"iat": now - timedelta(minutes=2), "exp": now - timedelta(minutes=1)}, self.sign, algorithm="HS256")
        with self.assertRaises(ExpiredTokenError):
            self.jwt.read(expired)
        for token in ("invalid", "", pyjwt.encode({"iat": now}, self.sign, algorithm="HS256")):
            with self.assertRaises(InvalidTokenError):
                self.jwt.read(token)

    def test_invalid_configuration(self):
        with self.assertRaises(ValueError):
            JWT(sign="short")
        with self.assertRaises(ValueError):
            JWT(sign=self.sign, expires_in=timedelta(0))


class PasswordTests(unittest.TestCase):
    def test_salt_and_comparison(self):
        passwords = PasswordHash(rounds=4)  # Lower cost only for unit tests.
        first = passwords.generate("SenhaSegura123!")
        second = passwords.generate("SenhaSegura123!")
        self.assertNotEqual(first, second)
        self.assertTrue(passwords.compare("SenhaSegura123!", first))
        self.assertFalse(passwords.compare("OutraSenha", first))
        self.assertFalse(passwords.compare("SenhaSegura123!", "invalid hash"))

    def test_utf8_limit_and_empty_password(self):
        passwords = PasswordHash(rounds=4)
        boundary = "é" * 36
        self.assertTrue(passwords.compare(boundary, passwords.generate(boundary)))
        for password in ("", "é" * 37, "a" * 73):
            with self.assertRaises(ValueError):
                passwords.generate(password)


class LayerTests(unittest.TestCase):
    def test_domain_does_not_import_other_backend_layers(self):
        root = Path(__file__).resolve().parents[2] / "src/backend/domain"
        for path in root.glob("*.py"):
            for node in ast.walk(ast.parse(path.read_text())):
                if isinstance(node, ast.ImportFrom):
                    self.assertFalse(node.level > 1)
                    if (node.module or "").startswith("src.backend"):
                        self.assertEqual(node.module, "src.backend.logs.log")
                elif isinstance(node, ast.Import):
                    self.assertFalse(any(alias.name.startswith("src.backend") for alias in node.names))

    def test_authentication_logs_do_not_include_secrets(self):
        from src.backend.logs.log import logger

        sign = "sensitive-signature-that-must-not-be-logged"
        password = "sensitive-password"
        with self.assertLogs(logger, level="INFO") as captured:
            tokens = JWT(sign=sign)
            token = tokens.write({"user_id": 7})
            tokens.read(token)
            passwords = PasswordHash(rounds=4)
            password_hash = passwords.generate(password)
            passwords.compare(password, password_hash)
        output = "\n".join(captured.output)
        self.assertIn("JWT.write", output)
        self.assertIn("PasswordHash.compare", output)
        for value in (sign, password, token, password_hash):
            self.assertNotIn(value, output)


if __name__ == "__main__":
    unittest.main(verbosity=2)
