from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from app.api.deps import DBSession
from app.core.config import get_settings
from app.models.user import User

settings = get_settings()

security = HTTPBearer()

TokenDep = Annotated[
    HTTPAuthorizationCredentials,
    Depends(security),
]


def get_current_user(
    token: TokenDep,
    db: DBSession,
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
    )

    try:
        payload = jwt.decode(
            token.credentials,
            settings.secret_key,
            algorithms=["HS256"],
        )

        user_id = int(payload.get("sub"))

    except Exception:
        raise credentials_exception

    user = db.execute(
        select(User).where(User.id == user_id)
    ).scalar_one_or_none()

    if not user:
        raise credentials_exception

    return user