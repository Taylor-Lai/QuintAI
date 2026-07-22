"""Password hashing and JWT token primitives."""

from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from docnexus.core.settings import get_settings

ALGORITHM = "HS256"
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Stateless authentication primitives used by the HTTP layer."""

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return password_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        return password_context.hash(password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        settings = get_settings()
        expire = datetime.utcnow() + (
            expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
        )
        payload = {**data, "exp": expire}
        return jwt.encode(payload, settings.require_secret_key(), algorithm=ALGORITHM)

    @staticmethod
    def decode_access_token(token: str) -> Optional[dict]:
        try:
            return jwt.decode(
                token,
                get_settings().require_secret_key(),
                algorithms=[ALGORITHM],
            )
        except (JWTError, RuntimeError):
            return None
