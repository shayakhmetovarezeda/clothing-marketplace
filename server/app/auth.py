from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.deps import get_session
from app.models.user import User
from sqlalchemy import select

import uuid
from app.redis_client import redis_client

# откуда брать токен в запросе
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def create_access_token(user_id: int) -> str:
    """Создаёт JWT-токен для пользователя."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "jti": str(uuid.uuid4()),  # уникальный id токена
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Достаёт пользователя из токена. Проверяет чёрный список."""
    credentials_error = HTTPException(status_code=401, detail="Неверный или истёкший токен")
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        user_id = int(payload.get("sub"))
        jti = payload.get("jti")
    except jwt.PyJWTError:
        raise credentials_error

    # проверяем чёрный список
    if jti and await redis_client.exists(f"blacklist:{jti}"):
        raise credentials_error

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_error
    return user