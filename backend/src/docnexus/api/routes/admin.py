"""Administration HTTP endpoints."""

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy.orm import Session

from docnexus.api.dependencies import require_admin
from docnexus.core.settings import get_settings
from docnexus.db import User, get_db

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter()

@router.get("/admin/user/page")
async def get_user_page(
    page: int = 1,
    page_size: int = 10,
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    account_status: Optional[str] = None,
    login_status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    【管理员】用户列表分页接口

    - page: 页码，默认1
    - page_size: 每页数量，默认10
    - keyword: 搜索关键词（用户名/邮箱）
    - status: 状态筛选（active/inactive）
    """
    # 清理长时间未活动的在线用户（超过15分钟没有心跳）
    timeout = datetime.now() - timedelta(minutes=15)
    inactive_users = db.query(User).filter(
        User.login_status == "在线",
        User.last_activity_time < timeout
    ).all()

    for user in inactive_users:
        user.login_status = "离线"

    if inactive_users:
        db.commit()

    # 构建查询
    query = db.query(User)

    # 关键词搜索
    if keyword:
        query = query.filter(
            (User.username.ilike(f"%{keyword}%") |
             User.email.ilike(f"%{keyword}%") |
             User.nickname.ilike(f"%{keyword}%")
            )
        )

    # 状态筛选
    requested_status = account_status or status
    if requested_status in {"active", "正常"}:
        query = query.filter(User.accountStatus == "正常")
    elif requested_status in {"inactive", "异常", "禁用"}:
        query = query.filter(User.accountStatus == "异常")

    if login_status in {"在线", "离线"}:
        query = query.filter(User.login_status == login_status)

    # 计算总数
    total = query.count()

    # 分页
    offset = (page - 1) * page_size
    users = query.offset(offset).limit(page_size).all()

    # 构建响应
    user_list = []
    for user in users:
        user_list.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "nickname": user.nickname,
            "gender": user.gender,
            "phone": user.phone,
            "role": user.role,
            "accountStatus": user.accountStatus,
            "login_status": user.login_status,
            "last_login_time": user.last_login_time.isoformat() if user.last_login_time else None,
            "last_activity_time": user.last_activity_time.isoformat() if user.last_activity_time else None,
            "last_login_ip": user.last_login_ip,
            "created_at": user.created_at.isoformat()
        })

    return {
        "code": 200,
        "message": "操作成功",
        "data": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "list": user_list
        }
    }


@router.get("/admin/user/{user_id}")
async def get_user_detail(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    【管理员】用户详情接口
    """
    # 查找用户
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 构建响应
    user_info = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "nickname": user.nickname,
        "gender": user.gender,
        "phone": user.phone,
        "role": user.role,
        "accountStatus": user.accountStatus,
        "login_status": user.login_status,
        "last_login_time": user.last_login_time.isoformat() if user.last_login_time else None,
        "last_activity_time": user.last_activity_time.isoformat() if user.last_activity_time else None,
        "last_login_ip": user.last_login_ip,
        "remark": user.remark,
        "created_at": user.created_at.isoformat()
    }

    return {
        "code": 200,
        "message": "操作成功",
        "data": user_info
    }


@router.put("/admin/user/{user_id}/status")
async def update_user_status(
    user_id: str,
    accountStatus: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    【管理员】启用/禁用用户接口
    """
    # 验证状态值
    if accountStatus not in ["正常", "异常"]:
        raise HTTPException(status_code=400, detail="状态值必须是'正常'或'异常'")

    # 查找用户
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 不允许禁用自己
    if user.id == current_user.id and accountStatus == "异常":
        raise HTTPException(status_code=400, detail="不能禁用自己的账号")

    # 更新状态
    user.accountStatus = accountStatus
    db.commit()
    db.refresh(user)

    return {
        "code": 200,
        "message": "操作成功",
        "data": {
            "user_id": user.id,
            "accountStatus": user.accountStatus
        }
    }


@router.put("/admin/user/{user_id}/role")
async def update_user_role(
    user_id: str,
    is_admin: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    【管理员】设置或取消用户管理员权限接口
    """
    # 查找用户
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 不允许修改自己的权限
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能修改自己的管理员权限")

    # 更新角色
    user.role = "管理员" if is_admin else "普通用户"
    db.commit()
    db.refresh(user)

    return {
        "code": 200,
        "message": "操作成功",
        "data": {
            "user_id": user.id,
            "role": user.role
        }
    }


@router.delete("/admin/user/{user_id}")
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    【管理员】删除用户接口
    """
    # 查找用户
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 不允许删除自己
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能删除自己的账号")

    # 删除用户
    db.delete(user)
    db.commit()

    return {
        "code": 200,
        "message": "操作成功",
        "data": {
            "user_id": user_id
        }
    }


@router.get("/admin/statistics")
async def get_admin_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    【管理员】获取后台统计数据接口
    会自动清理超过15分钟没有心跳的在线用户
    """
    # 清理长时间未活动的在线用户（超过15分钟没有心跳）
    timeout = datetime.now() - timedelta(minutes=15)
    inactive_users = db.query(User).filter(
        User.login_status == "在线",
        User.last_activity_time < timeout
    ).all()

    for user in inactive_users:
        user.login_status = "离线"

    if inactive_users:
        db.commit()
        logger.info("Marked %s inactive user(s) offline", len(inactive_users))

    # 统计总用户数
    total_users = db.query(User).count()

    # 统计在线用户数（15分钟内有活动的用户）
    online_users = db.query(User).filter(
        User.login_status == "在线",
        User.last_activity_time >= timeout
    ).count()

    # 统计正常用户数（活跃状态）
    normal_users = db.query(User).filter(User.accountStatus == "正常").count()

    # 构建响应
    statistics = {
        "total_users": total_users,
        "online_users": online_users,
        "normal_users": normal_users
    }

    return {
        "code": 200,
        "message": "操作成功",
        "data": statistics
    }
