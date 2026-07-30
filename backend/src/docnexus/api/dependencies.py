"""Reusable FastAPI authentication and authorization dependencies."""

import hashlib
from datetime import datetime

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from docnexus.core.security import AuthService
from docnexus.db import ApiCredential, User, get_db

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = credentials.credentials if credentials is not None else request.cookies.get("huiwen_session")
    if not token:
        raise credentials_exception
    payload = AuthService.decode_access_token(token)
    if payload is None or not (user_id := payload.get("sub")):
        if not token.startswith("qn_"):
            raise credentials_exception
        credential = db.query(ApiCredential).filter_by(key_hash=hashlib.sha256(token.encode()).hexdigest()).first()
        if (
            credential is None
            or credential.revoked_at is not None
            or (credential.expires_at and credential.expires_at < datetime.now())
        ):
            raise credentials_exception
        required_scope = "workspace:read" if request.method == "GET" else "workspace:write"
        if request.url.path.startswith("/api/enterprise"):
            required_scope = "enterprise:read" if request.method == "GET" else "enterprise:write"
        if required_scope not in (credential.scopes or []) and "*" not in (credential.scopes or []):
            raise HTTPException(status_code=403, detail="API 密钥缺少所需权限范围")
        credential.last_used_at = datetime.now()
        db.commit()
        user_id = credential.user_id

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    if payload is not None and int(payload.get("ver", -1)) != int(user.token_version or 0):
        raise credentials_exception
    if user.account_status != "正常":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被禁用")
    return user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "管理员":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问")
    return current_user
