"""企业平台请求模型。"""

from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class OrganizationUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=120)


class MemberCreate(BaseModel):
    email: str = Field(min_length=5, max_length=320)
    role: Literal["viewer", "member", "reviewer", "admin"] = "member"


class MemberUpdate(BaseModel):
    role: Literal["viewer", "member", "reviewer", "admin"]


class CommentCreate(BaseModel):
    resource_type: Literal["document", "review", "workflow"]
    resource_id: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    mentions: list[str] = Field(default_factory=list, max_length=20)


class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    scopes: list[str] = Field(default_factory=lambda: ["workspace:read"], max_length=20)
    expires_in_days: int | None = Field(default=90, ge=1, le=3650)


class WebhookCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    url: HttpUrl
    events: list[str] = Field(default_factory=list, max_length=30)


class KnowledgeCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(default="", max_length=1000)
    retrieval_mode: Literal["keyword", "vector", "hybrid"] = "hybrid"


class KnowledgeItemCreate(BaseModel):
    document_id: str = Field(min_length=32, max_length=32)


class ScheduleCreate(BaseModel):
    workflow_id: str = Field(min_length=32, max_length=32)
    document_id: str = Field(min_length=32, max_length=32)
    name: str = Field(min_length=2, max_length=120)
    cron_expression: str = Field(min_length=5, max_length=80)
    timezone: str = Field(default="Asia/Shanghai", max_length=50)
    retry_limit: int = Field(default=2, ge=0, le=10)


class PlanUpdate(BaseModel):
    plan: Literal["starter", "team", "enterprise"]
