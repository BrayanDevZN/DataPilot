"""Run: python tests/integration/sender.py.

Sends two real HTML emails to EMAIL_USER using EMAIL_PASSWORD from the infra
configuration. Codes are test data and are not saved as account validations.
"""

import secrets
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.backend.infra.manage import settings
from src.backend.service.sender import Sender


class SenderTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not settings.email_user or not settings.email_password:
            raise RuntimeError(
                "Configure EMAIL_USER and EMAIL_PASSWORD in the infra .env "
                "or project root .env before running the real email tests"
            )

    async def test_create_account_html(self) -> None:
        code = f"{secrets.randbelow(1_000_000):06d}"
        result = await Sender().create_account(settings.email_user, code)
        self.assertEqual(result, {"sent": True})

    async def test_change_password_html(self) -> None:
        code = f"{secrets.randbelow(1_000_000):06d}"
        result = await Sender().change_password(settings.email_user, code)
        self.assertEqual(result, {"sent": True})


if __name__ == "__main__":
    unittest.main(verbosity=2)
