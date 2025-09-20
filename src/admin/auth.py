from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
import bcrypt
from src.settings import settings
import base64


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username, password = form["username"], form["password"]

        request.session.update({
            "token": bcrypt.hashpw(
                f"{username}:{password}".encode(),
                bcrypt.gensalt()
            ).decode()
        })

        return self.authenticate(request)

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")

        if not token:
            return False

        return bcrypt.checkpw(
            f"{settings.ADMIN_USERNAME}:{settings.ADMIN_PASSSWORD}".encode(),
            str(token).encode()
        )
