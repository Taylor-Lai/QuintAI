"""文档工作台 API 请求模型。"""

from typing import Any, Literal

from pydantic import BaseModel, Field


class DocumentUpdate(BaseModel):
    category: str | None = Field(default=None, max_length=80)
    tags: list[str] | None = Field(default=None, max_length=20)
    status: Literal["ready", "processing", "needs_review", "completed", "archived"] | None = None


class ReviewField(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    value: Any = None
    original_value: Any = None
    confidence: float = Field(default=0.5, ge=0, le=1)
    evidence: str = Field(default="", max_length=2000)
    source_page: int | None = Field(default=None, ge=1)
    corrected: bool = False
    auto_fixed: bool = False


class ReviewUpdate(BaseModel):
    fields: list[ReviewField] = Field(default_factory=list, max_length=200)
    note: str | None = Field(default=None, max_length=2000)
    action: Literal["save", "approve", "reject", "reopen"] = "save"


class BulkReviewUpdate(BaseModel):
    review_ids: list[str] = Field(min_length=1, max_length=100)
    action: Literal["approve", "reject", "reopen"]
    note: str | None = Field(default=None, max_length=2000)


class WorkflowCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(default="", max_length=1000)
    nodes: list[dict[str, Any]] = Field(default_factory=list, max_length=50)
    rules: list[dict[str, Any]] = Field(default_factory=list, max_length=100)


class WorkflowUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    nodes: list[dict[str, Any]] | None = Field(default=None, max_length=50)
    rules: list[dict[str, Any]] | None = Field(default=None, max_length=100)
    status: Literal["draft", "active", "paused"] | None = None


class WorkflowRunCreate(BaseModel):
    document_id: str = Field(min_length=32, max_length=32)
