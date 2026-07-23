"""Administration HTTP endpoints."""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from docnexus.api.dependencies import require_admin
from docnexus.db import User, get_db

router = APIRouter(prefix="/admin", tags=["管理员"])
ONLINE_WINDOW = timedelta(minutes=15)


def _is_online(user: User) -> bool:
    return bool(user.last_activity_at and user.last_activity_at >= datetime.now() - ONLINE_WINDOW)


def _serialize_user(user: User) -> dict[str, object]:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "nickname": user.nickname,
        "gender": user.gender,
        "phone": user.phone,
        "role": user.role,
        "account_status": user.account_status,
        "login_status": "在线" if _is_online(user) else "离线",
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        "last_activity_at": user.last_activity_at.isoformat() if user.last_activity_at else None,
        "last_login_ip": user.last_login_ip,
        "remark": user.remark,
        "created_at": user.created_at.isoformat(),
    }


@router.get("/users")
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str | None = Query(None, max_length=100),
    account_status: str | None = None,
    login_status: str | None = None,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    query = db.query(User)
    if keyword:
        query = query.filter(
            or_(User.username.ilike(f"%{keyword}%"), User.email.ilike(f"%{keyword}%"), User.nickname.ilike(f"%{keyword}%"))
        )
    if account_status in {"正常", "异常"}:
        query = query.filter(User.account_status == account_status)
    cutoff = datetime.now() - ONLINE_WINDOW
    if login_status == "在线":
        query = query.filter(User.last_activity_at >= cutoff)
    elif login_status == "离线":
        query = query.filter(or_(User.last_activity_at.is_(None), User.last_activity_at < cutoff))
    total = query.count()
    users = query.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"page": page, "page_size": page_size, "total": total, "items": [_serialize_user(user) for user in users]}


@router.get("/users/{user_id}")
def get_user(user_id: str, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, "用户不存在")
    return _serialize_user(user)


@router.put("/users/{user_id}/status")
def update_user_status(
    user_id: str,
    account_status: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if account_status not in {"正常", "异常"}:
        raise HTTPException(400, "状态必须是“正常”或“异常”")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, "用户不存在")
    if user.id == admin.id and account_status == "异常":
        raise HTTPException(400, "不能禁用自己的账号")
    user.account_status = account_status
    if account_status == "异常":
        user.token_version += 1
    db.commit()
    return {"id": user.id, "account_status": user.account_status}


@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: str,
    is_admin: bool,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, "用户不存在")
    if user.id == admin.id:
        raise HTTPException(400, "不能修改自己的管理员权限")
    user.role = "管理员" if is_admin else "普通用户"
    user.token_version += 1
    db.commit()
    return {"id": user.id, "role": user.role}


@router.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: str, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, "用户不存在")
    if user.id == admin.id:
        raise HTTPException(400, "不能删除自己的账号")
    db.delete(user)
    db.commit()


@router.get("/statistics")
def statistics(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    cutoff = datetime.now() - ONLINE_WINDOW
    return {
        "total_users": db.query(User).count(),
        "online_users": db.query(User).filter(User.last_activity_at >= cutoff).count(),
        "normal_users": db.query(User).filter(User.account_status == "正常").count(),
    }
