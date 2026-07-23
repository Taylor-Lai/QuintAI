"""Reusable FastAPI authentication and authorization dependencies."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from docnexus.core.security import AuthService
from docnexus.db import User, get_db

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = AuthService.decode_access_token(credentials.credentials)
    if payload is None or not (user_id := payload.get("sub")):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    if int(payload.get("ver", -1)) != int(user.token_version or 0):
        raise credentials_exception
    if user.account_status != "正常":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被禁用")
    return user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "管理员":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问")
    return current_user
