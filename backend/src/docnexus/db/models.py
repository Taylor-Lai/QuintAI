"""SQLAlchemy persistence models."""

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text

from docnexus.db.session import Base


class ExtractionRecord(Base):
    """提取记录表"""

    __tablename__ = "extraction_records"

    id = Column(String, primary_key=True, index=True)  # UUID
    filename = Column(String, index=True)
    file_type = Column(String)
    fields_requested = Column(JSON)  # 请求的字段列表
    extracted_data = Column(JSON)  # 提取结果
    content_preview = Column(Text)  # 文档内容预览
    status = Column(String, default="success")  # success/failed
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class FileRecord(Base):
    """文件记录表"""

    __tablename__ = "file_records"

    id = Column(String, primary_key=True, index=True)
    original_filename = Column(String)
    stored_path = Column(String)  # 文件存储路径
    file_size = Column(Integer)
    file_type = Column(String)
    parsed_content = Column(Text)
    created_at = Column(DateTime, default=datetime.now)


class User(Base):
    """用户表"""

    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    nickname = Column(String, nullable=True)  # 昵称
    gender = Column(String, nullable=True)  # 性别：男/女
    phone = Column(String, nullable=True)  # 手机号
    accountStatus = Column(String, default="正常")  # 账户状态：正常/异常
    created_at = Column(DateTime, default=datetime.now)
    # 新增字段
    role = Column(String, default="普通用户")  # 用户角色：管理员、普通用户
    last_login_time = Column(DateTime, nullable=True)  # 最后登录时间
    last_login_ip = Column(String, nullable=True)  # 最后登录IP
    login_status = Column(String, default="离线")  # 登录状态：在线、离线
    last_activity_time = Column(DateTime, nullable=True)  # 最后活动时间（用于心跳检测）
    remark = Column(Text, nullable=True)
