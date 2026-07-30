"""企业平台请求模型。"""

import ipaddress
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator


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

    @field_validator("url")
    @classmethod
    def validate_webhook_url(cls, value: HttpUrl) -> HttpUrl:
        host = (value.host or "").lower().rstrip(".")
        if value.scheme != "https":
            raise ValueError("Webhook 地址必须使用 HTTPS")
        if value.username or value.password:
            raise ValueError("Webhook 地址不得包含用户凭据")
        if host == "localhost" or host.endswith((".localhost", ".local", ".internal")):
            raise ValueError("Webhook 地址不得指向本地或内部网络")
        try:
            address = ipaddress.ip_address(host.strip("[]"))
        except ValueError:
            address = None
        if address is not None and not address.is_global:
            raise ValueError("Webhook 地址不得指向本地、保留或内部网络地址")
        return value


class KnowledgeCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(default="", max_length=1000)
    retrieval_mode: Literal["keyword", "vector", "hybrid"] = "hybrid"


class KnowledgeItemCreate(BaseModel):
    document_id: str = Field(min_length=32, max_length=32)


class KnowledgeEntityReview(BaseModel):
    review_status: Literal["unreviewed", "confirmed", "questioned"]


class ScheduleCreate(BaseModel):
    workflow_id: str = Field(min_length=32, max_length=32)
    document_id: str = Field(min_length=32, max_length=32)
    name: str = Field(min_length=2, max_length=120)
    cron_expression: str = Field(min_length=5, max_length=80)
    timezone: str = Field(default="Asia/Shanghai", max_length=50)
    retry_limit: int = Field(default=2, ge=0, le=10)


class PlanUpdate(BaseModel):
    organization_id: str = Field(min_length=32, max_length=32)
    plan: Literal["starter", "team", "enterprise"]


class TemplateUpsert(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    category: str = Field(min_length=1, max_length=80)
    scene: str = Field(default="", max_length=120)
    description: str = Field(default="", max_length=2000)
    format: str = Field(default="Excel / 在线表单", max_length=80)
    tags: list[str] = Field(default_factory=list, max_length=20)
    fields: list[dict[str, object] | str] = Field(min_length=1, max_length=100)
