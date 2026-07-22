"""Authentication and user profile HTTP endpoints."""

import logging
import uuid
from datetime import datetime, timedelta

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)
from sqlalchemy.orm import Session

from docnexus.api.dependencies import get_current_user
from docnexus.core.security import AuthService
from docnexus.core.settings import get_settings
from docnexus.db import User, get_db
from docnexus.schemas.auth import LoginRequest, Token, UserCreate, UserProfileUpdate

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter()

@router.post("/auth/register", response_model=dict)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户是否存在
    existing = (
        db.query(User)
        .filter((User.username == user_data.username) | (User.email == user_data.email))
        .first()
    )

    if existing:
        raise HTTPException(400, "用户名或邮箱已存在")

    # 创建用户
    user = User(
        id=str(uuid.uuid4())[:8],
        username=user_data.username,
        email=user_data.email,
        hashed_password=AuthService.get_password_hash(user_data.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "注册成功", "user_id": user.id, "username": user.username}


@router.post("/auth/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
    request: Request = None
):
    """用户登录"""
    # 根据邮箱查找用户
    user = db.query(User).filter(User.email == login_data.email).first()

    if not user or not AuthService.verify_password(
        login_data.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.accountStatus != "正常":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被禁用")

    # 更新登录信息
    from datetime import datetime
    user.last_login_time = datetime.now()
    user.last_activity_time = datetime.now()  # 初始化最后活动时间
    if request:
        user.last_login_ip = request.client.host
    user.login_status = "在线"
    db.commit()
    db.refresh(user)

    # 创建 Token (使用用户ID作为sub，过期时间为3小时)
    access_token = AuthService.create_access_token(
        data={"sub": user.id}, expires_delta=timedelta(hours=3)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_info": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "accountStatus": user.accountStatus,
        },
    }


@router.post("/auth/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """用户登出"""
    # 更新登录状态为离线
    current_user.login_status = "离线"
    db.commit()
    db.refresh(current_user)

    return {
        "code": 200,
        "message": "登出成功",
        "data": {}
    }


@router.post("/auth/heartbeat")
async def heartbeat(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    用户心跳接口，用于保持在线状态
    前端需要定期调用（建议每5分钟一次）
    """
    # 更新最后活动时间（不更新 last_login_time）
    current_user.last_activity_time = datetime.now()
    # 确保状态为在线
    if current_user.login_status != "在线":
        current_user.login_status = "在线"
    db.commit()
    db.refresh(current_user)

    return {
        "code": 200,
        "message": "心跳成功",
        "data": {
            "user_id": current_user.id,
            "login_status": current_user.login_status
        }
    }


@router.get("/user/profile", response_model=dict)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """获取个人信息"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "nickname": current_user.nickname,
        "gender": current_user.gender,
        "phone": current_user.phone,
        "accountStatus": current_user.accountStatus,
        "role": current_user.role,
    }


@router.put("/user/profile", response_model=dict)
async def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """修改个人资料"""
    # 检查邮箱是否已被其他用户使用
    if profile_data.email and profile_data.email != current_user.email:
        existing_user = db.query(User).filter(User.email == profile_data.email).first()
        if existing_user:
            raise HTTPException(400, "邮箱已被其他用户使用")

    # 验证性别字段
    if profile_data.gender and profile_data.gender not in ["男", "女"]:
        raise HTTPException(400, "性别只能是'男'或'女'")

    # 验证手机号格式（简单验证）
    if profile_data.phone:
        import re
        phone_regex = r'^1[3-9]\d{9}$'
        if not re.match(phone_regex, profile_data.phone):
            raise HTTPException(400, "手机号格式不正确")

    # 更新用户信息
    if profile_data.nickname is not None:
        current_user.nickname = profile_data.nickname
    if profile_data.gender is not None:
        current_user.gender = profile_data.gender
    if profile_data.email is not None:
        current_user.email = profile_data.email
    if profile_data.phone is not None:
        current_user.phone = profile_data.phone

    db.commit()
    db.refresh(current_user)

    return {
        "message": "个人资料更新成功",
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "nickname": current_user.nickname,
            "gender": current_user.gender,
            "phone": current_user.phone,
        }
    }
