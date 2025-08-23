import json
from typing import Annotated
from fastapi.params import Depends
import jwt
from datetime import datetime, timedelta, timezone

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

    def authenticate_and_create_jwt(self, username: str, password: str):
        if not self.password_authenticate(username, password):
            raise InvalidRequestException("unauthorized")

        secret_key = settings.SECRET_KEY
        payload = {
            "username": username,
            "exp": datetime.now(timezone.utc) + timedelta(days=30),
        }
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        return token

    def verify_jwt(self, token: str):
        with open("credentials.json") as f:
            credentials = json.load(f)
        secret_key = settings.SECRET_KEY
        try:
            payload = jwt.decode(token, secret_key, algorithms=["HS256"], verify=True)
            if payload.get("username") in credentials:
                return True
        except Exception:
            return False
        return False


AuthServiceDependency = Annotated[AuthService, AuthService.get_dependency()]
