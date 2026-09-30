"""Send verification codes using the infrastructure HTML templates."""

from src.backend.infra.manage import email_files, sender, settings
from src.backend.logs.log import log_operation


class Sender:
    def _validate_code(self, code: str) -> None:
        if not isinstance(code, str) or len(code) != 6 or not code.isascii() or not code.isdigit():
            raise ValueError("Verification code must contain six ASCII digits")

    @log_operation
    async def create_account(self, email: str, code: str) -> dict[str, bool]:
        self._validate_code(code)
        if settings.enviroiment == "test":
            return {"sent": True}
        contents = email_files.read()["create_account"].replace("{{code}}", code)
        return await sender.send(
            email, "Código de verificação para criação de conta", contents, html=True,
        )

    @log_operation
    async def change_password(self, email: str, code: str) -> dict[str, bool]:
        self._validate_code(code)
        if settings.enviroiment == "test":
            return {"sent": True}
        contents = email_files.read()["change_password"].replace("{{code}}", code)
        return await sender.send(
            email, "Código de verificação para alterar senha", contents, html=True,
        )

    @log_operation
    async def auth2(self, email: str, code: str) -> dict[str, bool]:
        self._validate_code(code)
        if settings.enviroiment == "test":
            return {"sent": True}
        contents = email_files.read()["auth2"].replace("{{code}}", code)
        return await sender.send(
            email, "Código de autenticação em duas etapas", contents, html=True,
        )
