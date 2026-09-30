"""Send verification codes using the infrastructure HTML templates."""

from src.backend.infra.manage import email_files, sender
from src.backend.logs.log import log_operation


class Sender:
    @log_operation
    async def create_account(self, email: str, code: str) -> dict[str, bool]:
        if not isinstance(code, str) or len(code) != 6 or not code.isascii() or not code.isdigit():
            raise ValueError("Verification code must contain six ASCII digits")
        contents = email_files.read()["create_account"].replace("{{code}}", code)
        return await sender.send(
            email, "Código de verificação para criação de conta", contents, html=True,
        )

    @log_operation
    async def change_password(self, email: str, code: str) -> dict[str, bool]:
        if not isinstance(code, str) or len(code) != 6 or not code.isascii() or not code.isdigit():
            raise ValueError("Verification code must contain six ASCII digits")
        contents = email_files.read()["change_password"].replace("{{code}}", code)
        return await sender.send(
            email, "Código de verificação para alterar senha", contents, html=True,
        )
