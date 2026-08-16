"""Shared LLM configuration for DocNexus AI modules."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL") or "https://dashscope.aliyuncs.com/compatible-mode/v1"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "qwen3.8-max")
LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "45"))
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "0"))
LLM_CONCURRENCY = int(os.getenv("LLM_CONCURRENCY", "3"))
LLM_CACHE_SIZE = int(os.getenv("LLM_CACHE_SIZE", "128"))
LLM_MAX_CALLS_PER_RUN = int(os.getenv("LLM_MAX_CALLS_PER_RUN", "40"))
LLM_MAX_TOTAL_TOKENS_PER_RUN = int(os.getenv("LLM_MAX_TOTAL_TOKENS_PER_RUN", "120000"))
TABLE_REPAIR_MAX_ATTEMPTS = int(os.getenv("TABLE_REPAIR_MAX_ATTEMPTS", "1"))

_llm_instance = None


def get_chat_llm():
    global _llm_instance
    if _llm_instance is None:
        if OPENAI_API_KEY:
            try:
                from langchain_openai import ChatOpenAI
            except ImportError as exc:
                raise ImportError("使用 OpenAI 需要安装 langchain-openai: pip install langchain-openai") from exc
            _llm_instance = ChatOpenAI(
                model=OPENAI_MODEL,
                temperature=0,
                api_key=OPENAI_API_KEY,
                base_url=OPENAI_BASE_URL or None,
                timeout=LLM_TIMEOUT_SECONDS,
                max_retries=LLM_MAX_RETRIES,
            )
        else:
            raise ValueError("请在 .env 文件中配置 OPENAI_API_KEY")
    return _llm_instance
