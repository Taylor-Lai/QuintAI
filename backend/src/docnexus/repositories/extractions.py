import logging
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import String
from sqlalchemy.orm import Session

from docnexus.db import ExtractionRecord

logger = logging.getLogger(__name__)


class ExtractionRepository:
    """数据库服务层"""

    @staticmethod
    def save_extraction(
        db: Session,
        filename: str,
        file_type: str,
        fields_requested: list[str],
        extracted_data: dict[str, Any],
        user_id: str,
        task_id: str | None = None,
        content_preview: str = "",
        status: str = "success",
    ) -> ExtractionRecord:
        """保存提取记录"""
        record_id = uuid.uuid4().hex

        record = ExtractionRecord(
            id=record_id,
            user_id=user_id,
            task_id=task_id,
            filename=filename,
            file_type=file_type,
            fields_requested=fields_requested,
            extracted_data=extracted_data,
            content_preview=content_preview[:1000] if content_preview else "",
            status=status,
            created_at=datetime.now(),
        )

        try:
            db.add(record)
            db.commit()
            db.refresh(record)
            logger.info("Saved extraction record: %s", record_id)
            return record
        except Exception:
            db.rollback()  # 出错时回滚事务
            logger.exception("Failed to save extraction record")
            raise

    @staticmethod
    def get_extraction(db: Session, record_id: str, user_id: str) -> ExtractionRecord | None:
        """查询提取记录"""
        return (
            db.query(ExtractionRecord)
            .filter(ExtractionRecord.id == record_id, ExtractionRecord.user_id == user_id)
            .first()
        )

    @staticmethod
    def list_extractions(
        db: Session, user_id: str, limit: int = 20, offset: int = 0
    ) -> list[ExtractionRecord]:
        """获取提取记录列表"""
        return (
            db.query(ExtractionRecord)
            .filter(ExtractionRecord.user_id == user_id)
            .order_by(ExtractionRecord.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    @staticmethod
    def delete_extraction(db: Session, record_id: str, user_id: str) -> bool:
        """删除提取记录"""
        try:
            record = (
                db.query(ExtractionRecord)
                .filter(ExtractionRecord.id == record_id, ExtractionRecord.user_id == user_id)
                .first()
            )
            if record:
                db.delete(record)
                db.commit()
                return True
            return False
        except Exception:
            db.rollback()
            logger.exception("Failed to delete extraction record")
            raise

    @staticmethod
    def search_extractions(db: Session, keyword: str, user_id: str) -> list[ExtractionRecord]:
        """搜索提取记录（支持多字段搜索）"""
        from sqlalchemy import or_

        # 搜索：文件名、提取的数据、内容预览
        return (
            db.query(ExtractionRecord)
            .filter(
                ExtractionRecord.user_id == user_id,
                or_(
                    ExtractionRecord.filename.contains(keyword),
                    ExtractionRecord.content_preview.contains(keyword),
                    # 新增：在 extracted_data 的 JSON 中搜索
                    ExtractionRecord.extracted_data.cast(String).contains(keyword),
                )
            )
            .order_by(ExtractionRecord.created_at.desc())
            .limit(20)
            .all()
        )
