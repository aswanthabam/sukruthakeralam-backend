from datetime import datetime, timezone
from typing_extensions import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from sqlalchemy import select

from apps.auth.models import AdminAccessTokens
from apps.settings import settings
from core.database.sqlalchamey.core import SessionDep

# Replace with your secret key
SECRET_KEY = settings.SECRET_KEY

security = HTTPBearer()


async def verify_jwt_token(
    session: SessionDep,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    try:
        query = select(AdminAccessTokens).where(
            AdminAccessTokens.token == credentials.credentials
        )
        result = await session.execute(query)
        token_entry = result.scalars().first()
        if not token_entry:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )
        if not token_entry.expiry or token_entry.expiry < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
            )
        return token_entry
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


AuthDependency = Annotated[AdminAccessTokens, Depends(verify_jwt_token)]
