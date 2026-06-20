import json
from typing import Annotated
from fastapi.params import Depends
import jwt
from datetime import datetime, timedelta, timezone
import secrets
from sqlalchemy import select

from apps.auth.models import AdminAccessTokens
from core.database.sqlalchamey.core import SessionDep
from core.exception.request import InvalidRequestException
from core.fastapi.dependency.service_dependency import AbstractService
from apps.settings import settings


class AuthService(AbstractService):
    DEPENDENCIES = {
        "session": SessionDep,
    }

    def __init__(self, session: SessionDep, **kwargs):
        super().__init__(**kwargs)
        self.session = session

    def password_authenticate(self, username: str, password: str):
        with open("credentials.json") as f:
            credentials = json.load(f)
        if username in credentials and credentials[username] == password:
            return True
        return False

    async def authenticate_and_create_jwt(self, username: str, password: str):
        if not self.password_authenticate(username, password):
            raise InvalidRequestException("unauthorized")

        access_token = secrets.token_urlsafe(32)
        token = AdminAccessTokens(
            token=access_token,
        )
        self.session.add(token)
        await self.session.commit()
        return access_token

    async def invalidate_jwt(self, token: str):
        query = await self.session.execute(
            select(AdminAccessTokens).where(AdminAccessTokens.token == token)
        )
        token_entry = query.scalars().first()
        if token_entry:
            await self.session.delete(token_entry)
            await self.session.commit()
            return True
        return False


AuthServiceDependency = Annotated[AuthService, AuthService.get_dependency()]
