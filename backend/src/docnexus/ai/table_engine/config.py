"""Configuration defaults for Any2table."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

# Skills bundled inside the package so they are committed alongside the code.
_PACKAGE_SKILLS_ROOT = str(Path(__file__).parent / "skills" / "definitions")

logger = logging.getLogger(__name__)


@dataclass
class AppConfig:
    """Application-level configuration for local runs."""

    retrieval_backend: str = "rule"
    router_backend: str = "default"
    rag_backend: str = "hybrid"
    extractor_backend: str = "default"
    verifier_backend: str = "default"
    writer_backend: Literal["auto", "xlsx", "docx"] = "auto"
    enable_agent_runtime: bool = False
    agent_runtime_backend: str = "langgraph"
    enable_skill_runtime: bool = True
    skills_root: str = field(default_factory=lambda: _PACKAGE_SKILLS_ROOT)
    enable_llm_skill_execution: bool = False
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    llm_base_url: str | None = None
    llm_api_key_env: str = "OPENAI_API_KEY"
    llm_timeout_seconds: float = 90.0
    llm_max_retries: int = 2
    llm_concurrency: int = 3
    llm_cache_size: int = 128
    llm_max_calls_per_run: int = 40
    llm_max_total_tokens_per_run: int = 120000
    repair_max_attempts: int = 1
    output_dir: str = "outputs"
    enable_intermediate_dump: bool = False
    intermediate_root: str = "workspace/cache"
    extra: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.enable_llm_skill_execution and not self.enable_skill_runtime:
            logger.warning(
                "enable_llm_skill_execution=True has no effect when enable_skill_runtime=False; "
                "set enable_skill_runtime=True to execute skills with LLM."
            )
        if self.writer_backend not in ("auto", "xlsx", "docx"):
            raise ValueError(
                f"Invalid writer_backend '{self.writer_backend}'; must be one of: 'auto', 'xlsx', 'docx'."
            )
        if self.llm_concurrency < 1:
            raise ValueError("llm_concurrency must be at least 1.")
        if self.llm_cache_size < 0:
            raise ValueError("llm_cache_size cannot be negative.")
        if self.llm_max_calls_per_run < 1 or self.llm_max_total_tokens_per_run < 1:
            raise ValueError("LLM run budgets must be positive.")
        if self.repair_max_attempts < 0:
            raise ValueError("repair_max_attempts cannot be negative.")
