"""Database bootstrap and compatibility migrations.

The SQL migration body is retained for existing SQLite installations. New
schema evolution should use versioned migration files rather than extending
this compatibility module.
"""

import logging
import uuid

from sqlalchemy import text

from docnexus.core.settings import get_settings
from docnexus.db.models import User
from docnexus.db.session import Base, SessionLocal, engine

logger = logging.getLogger(__name__)

def init_db():
    """初始化数据库（创建表）"""
    Base.metadata.create_all(bind=engine)
    print("[OK] 数据库初始化成功")

    # 执行数据库迁移
    migrate_db()
    # 创建初始管理员账号
    create_initial_user()


def create_initial_user():
    """Optionally create an administrator from explicit environment settings."""
    from docnexus.core.security import AuthService

    settings = get_settings()
    if not settings.has_bootstrap_admin:
        logger.info("Administrator bootstrap is disabled.")
        return

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == settings.bootstrap_admin_email).first()
        if existing:
            logger.info("Bootstrap administrator already exists; skipping creation.")
            return

        admin = User(
            id=str(uuid.uuid4())[:8],
            username=settings.bootstrap_admin_username,
            email=settings.bootstrap_admin_email,
            hashed_password=AuthService.get_password_hash(settings.bootstrap_admin_password),
            role="管理员",
        )
        db.add(admin)
        db.commit()
        logger.info("Bootstrap administrator created for %s.", settings.bootstrap_admin_email)
    finally:
        db.close()


def migrate_db():
    """执行数据库迁移"""

    db = SessionLocal()
    try:
        # 检查是否已存在这些字段
        result = db.execute(text("PRAGMA table_info(users)"))
        columns = [column[1] for column in result.fetchall()]

        # 处理 accountStatus 字段
        if "accountStatus" in columns:
            # 检查是否需要从布尔值转换为字符串
            # 获取字段类型
            result = db.execute(text("PRAGMA table_info(users)"))
            field_info = result.fetchall()
            accountStatus_type = None
            for field in field_info:
                if field[1] == "accountStatus":
                    accountStatus_type = field[2]
                    break

            if accountStatus_type and "BOOLEAN" in accountStatus_type:
                print("开始将 accountStatus 字段从布尔值转换为字符串...")
                try:
                    # 1. 创建临时表
                    db.execute(text("""
                        CREATE TABLE users_temp (
                            id VARCHAR NOT NULL,
                            username VARCHAR NOT NULL,
                            email VARCHAR,
                            hashed_password VARCHAR NOT NULL,
                            nickname TEXT,
                            gender TEXT,
                            phone TEXT,
                            accountStatus TEXT DEFAULT '正常',
                            created_at DATETIME,
                            role TEXT DEFAULT '普通用户',
                            last_login_time DATETIME,
                            last_login_ip TEXT,
                            login_status TEXT DEFAULT '离线',
                            last_activity_time DATETIME,
                            remark TEXT,
                            PRIMARY KEY (id)
                        )
                    """))

                    # 2. 复制数据，将布尔值转换为字符串
                    db.execute(text("""
                        INSERT INTO users_temp
                        SELECT id, username, email, hashed_password, nickname, gender, phone,
                               CASE WHEN accountStatus = 1 THEN '正常' ELSE '异常' END,
                               created_at, role, last_login_time, last_login_ip,
                               login_status, last_activity_time, remark
                        FROM users
                    """))

                    # 3. 删除旧表
                    db.execute(text("DROP TABLE users"))

                    # 4. 重命名临时表
                    db.execute(text("ALTER TABLE users_temp RENAME TO users"))

                    # 5. 重建索引
                    db.execute(text("CREATE INDEX ix_users_id ON users (id)"))
                    db.execute(text("CREATE UNIQUE INDEX ix_users_username ON users (username)"))
                    db.execute(text("CREATE UNIQUE INDEX ix_users_email ON users (email)"))

                    print("[OK] 成功将 accountStatus 字段从布尔值转换为字符串")

                    # 更新 columns 列表
                    result = db.execute(text("PRAGMA table_info(users)"))
                    columns = [column[1] for column in result.fetchall()]
                except Exception as e:
                    print(f"[ERR] 转换 accountStatus 字段失败：{str(e)}")
                    db.rollback()
                    raise
        elif "is_active" in columns:
            # 重命名 is_active 列为 accountStatus（SQLite 不支持直接重命名，需要重建表）
            print("开始迁移 is_active 列为 accountStatus...")
            try:
                # 1. 创建临时表
                db.execute(text("""
                    CREATE TABLE users_temp (
                        id VARCHAR NOT NULL,
                        username VARCHAR NOT NULL,
                        email VARCHAR,
                        hashed_password VARCHAR NOT NULL,
                        nickname TEXT,
                        gender TEXT,
                        phone TEXT,
                        accountStatus TEXT DEFAULT '正常',
                        created_at DATETIME,
                        role TEXT DEFAULT '普通用户',
                        last_login_time DATETIME,
                        last_login_ip TEXT,
                        login_status TEXT DEFAULT '离线',
                        last_activity_time DATETIME,
                        remark TEXT,
                        PRIMARY KEY (id)
                    )
                """))

                # 2. 复制数据，将布尔值转换为字符串
                db.execute(text("""
                    INSERT INTO users_temp
                    SELECT id, username, email, hashed_password, nickname, gender, phone,
                           CASE WHEN is_active = 1 THEN '正常' ELSE '异常' END,
                           created_at, role, last_login_time, last_login_ip,
                           login_status, last_activity_time, remark
                    FROM users
                """))

                # 3. 删除旧表
                db.execute(text("DROP TABLE users"))

                # 4. 重命名临时表
                db.execute(text("ALTER TABLE users_temp RENAME TO users"))

                # 5. 重建索引
                db.execute(text("CREATE INDEX ix_users_id ON users (id)"))
                db.execute(text("CREATE UNIQUE INDEX ix_users_username ON users (username)"))
                db.execute(text("CREATE UNIQUE INDEX ix_users_email ON users (email)"))

                print("[OK] 成功将 is_active 列重命名为 accountStatus")

                # 更新 columns 列表
                result = db.execute(text("PRAGMA table_info(users)"))
                columns = [column[1] for column in result.fetchall()]
            except Exception as e:
                print(f"[ERR] 迁移 is_active 列失败：{str(e)}")
                db.rollback()
                raise

        # 如果字段不存在，添加它们
        if "nickname" not in columns:
            db.execute(text("ALTER TABLE users ADD COLUMN nickname TEXT"))
            print("[OK] 添加 nickname 字段成功")

        if "gender" not in columns:
            db.execute(text("ALTER TABLE users ADD COLUMN gender TEXT"))
            print("[OK] 添加 gender 字段成功")

        if "phone" not in columns:
            db.execute(text("ALTER TABLE users ADD COLUMN phone TEXT"))
            print("[OK] 添加 phone 字段成功")

        # 新增字段
        if "role" not in columns:
            db.execute(text("ALTER TABLE users ADD COLUMN role TEXT DEFAULT '普通用户'"))
            print("[OK] 添加 role 字段成功")

        if "last_login_time" not in columns:
            db.execute(text("ALTER TABLE users ADD COLUMN last_login_time DATETIME"))
            print("[OK] 添加 last_login_time 字段成功")

        if "last_login_ip" not in columns:
            db.execute(text("ALTER TABLE users ADD COLUMN last_login_ip TEXT"))
            print("[OK] 添加 last_login_ip 字段成功")

        if "login_status" not in columns:
            db.execute(text("ALTER TABLE users ADD COLUMN login_status TEXT DEFAULT '离线'"))
            print("[OK] 添加 login_status 字段成功")

        if "remark" not in columns:
            db.execute(text("ALTER TABLE users ADD COLUMN remark TEXT"))
            print("[OK] 添加 remark 字段成功")

        if "last_activity_time" not in columns:
            db.execute(text("ALTER TABLE users ADD COLUMN last_activity_time DATETIME"))
            print("[OK] 添加 last_activity_time 字段成功")

        db.commit()
        print("[OK] 数据库迁移完成")
    except Exception as e:
        print(f"[ERR] 迁移失败：{str(e)}")
        db.rollback()
    finally:
        db.close()
