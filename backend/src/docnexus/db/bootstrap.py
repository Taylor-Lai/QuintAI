"""Database bootstrap operations executed after migrations."""

import logging
import uuid

from docnexus.core.security import AuthService
from docnexus.core.settings import get_settings
from docnexus.db.models import User
from docnexus.db.session import SessionLocal

logger = logging.getLogger(__name__)


def create_initial_admin() -> None:
    settings = get_settings()
    if not settings.has_bootstrap_admin:
        logger.info("Administrator bootstrap is disabled")
        return
    assert settings.bootstrap_admin_username is not None
    assert settings.bootstrap_admin_email is not None
    assert settings.bootstrap_admin_password is not None
    with SessionLocal() as db:
        if db.query(User).filter(User.email == settings.bootstrap_admin_email).first():
            return
        db.add(
            User(
                id=uuid.uuid4().hex,
                username=settings.bootstrap_admin_username,
                email=settings.bootstrap_admin_email,
                password_hash=AuthService.get_password_hash(settings.bootstrap_admin_password),
                role="管理员",
            )
        )
        db.commit()
        logger.info("Bootstrap administrator created")
