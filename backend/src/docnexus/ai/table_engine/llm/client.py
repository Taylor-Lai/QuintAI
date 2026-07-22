"""OpenAI-compatible LLM client."""

from __future__ import annotations

import logging
import os
from collections import OrderedDict
from hashlib import sha256
from pathlib import Path
from threading import Lock
from time import perf_counter

from docnexus.ai.table_engine.config import AppConfig
from docnexus.ai.table_engine.llm.models import LlmResponse

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional dependency path
    OpenAI = None


logger = logging.getLogger(__name__)


BOM = "\ufeff"


def _strip_wrapping_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _dotenv_candidates() -> list[Path]:
    candidates = [Path.cwd() / ".env", Path(__file__).resolve().parents[3] / ".env"]
    seen: set[str] = set()
    unique: list[Path] = []
    for path in candidates:
        key = str(path)
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return unique


def _load_dotenv() -> None:
    for env_path in _dotenv_candidates():
        if not env_path.exists():
            continue
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip().lstrip(BOM)
            value = _strip_wrapping_quotes(value.strip())
            if key and key not in os.environ:
                os.environ[key] = value
        return


def _normalize_base_url(base_url: str | None) -> str | None:
    if not base_url:
        return None
    normalized = _strip_wrapping_quotes(base_url.strip()).rstrip("/")
    if normalized.endswith("/chat/completions"):
        normalized = normalized[: -len("/chat/completions")]
    return normalized or None


class OpenAiLlmClient:
    """Small wrapper around the OpenAI-compatible chat completions API."""

    def __init__(self, config: AppConfig) -> None:
        _load_dotenv()
        self.provider = config.llm_provider
        self.model = config.llm_model
        self.base_url = _normalize_base_url(config.llm_base_url)
        self.last_metrics: dict[str, object] = {}
        self._cache_size = config.llm_cache_size
        self._cache: OrderedDict[str, LlmResponse] = OrderedDict()
        self._cache_lock = Lock()
        api_key = os.getenv(config.llm_api_key_env)
        self.is_available = OpenAI is not None and bool(api_key)
        self._client = (
            OpenAI(
                api_key=api_key,
                base_url=self.base_url,
                timeout=config.llm_timeout_seconds,
                max_retries=config.llm_max_retries,
            )
            if self.is_available
            else None
        )

        if OpenAI is None:
            logger.warning("openai package is not installed; LLM skills will be unavailable")
        elif not api_key:
            logger.warning("API key env var '%s' is not set; LLM skills will be unavailable", config.llm_api_key_env)
        else:
            logger.info("LLM client initialized: provider=%s, model=%s, base_url=%s", self.provider, self.model, self.base_url)

    def invoke_json(self, *, system_prompt: str, user_prompt: str) -> LlmResponse:
        if not self.is_available or self._client is None:
            raise RuntimeError("OpenAI-compatible LLM client is not available. Check dependency and API key.")

        cache_key = sha256(f"{self.provider}\0{self.model}\0{system_prompt}\0{user_prompt}".encode()).hexdigest()
        if self._cache_size:
            with self._cache_lock:
                cached = self._cache.get(cache_key)
                if cached is not None:
                    self._cache.move_to_end(cache_key)
                    metrics = {**cached.metrics, "cache_hit": True, "duration_ms": 0.0}
                    self.last_metrics = metrics
                    return LlmResponse(cached.content, cached.model, cached.provider, dict(cached.raw), metrics)

        started_at = perf_counter()
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
        raw_content = response.choices[0].message.content
        usage = getattr(response, "usage", None)
        metrics = {
            "duration_ms": round((perf_counter() - started_at) * 1000, 2),
            "input_tokens": getattr(usage, "prompt_tokens", None),
            "output_tokens": getattr(usage, "completion_tokens", None),
            "total_tokens": getattr(usage, "total_tokens", None),
            "response_model": getattr(response, "model", None),
            "cache_hit": False,
        }
        self.last_metrics = metrics
        if raw_content is None:
            logger.warning("LLM returned None content; defaulting to empty JSON object")
        content = raw_content or "{}"
        result = LlmResponse(
            content=content,
            model=self.model,
            provider=self.provider,
            raw=response.model_dump() if hasattr(response, "model_dump") else {},
            metrics=metrics,
        )
        if self._cache_size:
            with self._cache_lock:
                self._cache[cache_key] = result
                self._cache.move_to_end(cache_key)
                while len(self._cache) > self._cache_size:
                    self._cache.popitem(last=False)
        return result


def build_llm_client(config: AppConfig) -> OpenAiLlmClient | None:
    client = OpenAiLlmClient(config)
    return client if client.is_available else None
