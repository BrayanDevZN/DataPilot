"""Run: python tests/integration/sender.py."""

import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.backend.service.sender import Sender


class SenderTests(unittest.IsolatedAsyncioTestCase):
    async def test_create_account_html(self) -> None:
        transport = AsyncMock(return_value={"sent": True})

        with patch(
            "src.backend.service.sender.sender.send",
            transport,
        ):
            result = await Sender().create_account(
                "test@example.com",
                "123456",
            )

        self.assertEqual(result, {"sent": True})
        args = transport.await_args.args
        self.assertEqual(args[0], "test@example.com")
        self.assertIn("123456", args[2])

    async def test_change_password_and_auth2_html(self) -> None:
        transport = AsyncMock(return_value={"sent": True})

        with patch(
            "src.backend.service.sender.sender.send",
            transport,
        ):
            change = await Sender().change_password(
                "test@example.com",
                "654321",
            )
            auth2 = await Sender().auth2(
                "test@example.com",
                "111222",
            )

        self.assertEqual(change, {"sent": True})
        self.assertEqual(auth2, {"sent": True})
        self.assertEqual(transport.await_count, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
