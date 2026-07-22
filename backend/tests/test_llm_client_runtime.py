from collections import OrderedDict
from threading import Lock
from types import SimpleNamespace

from docnexus.ai.table_engine.llm.client import OpenAiLlmClient


class _FakeCompletions:
    def __init__(self) -> None:
        self.call_count = 0

    def create(self, **kwargs):
        self.call_count += 1
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content='{"ok": true}'))],
            usage=SimpleNamespace(prompt_tokens=10, completion_tokens=2, total_tokens=12),
            model="fake-model",
            model_dump=lambda: {"model": "fake-model"},
        )


def test_llm_client_reuses_identical_prompt_from_memory_cache() -> None:
    completions = _FakeCompletions()
    client = OpenAiLlmClient.__new__(OpenAiLlmClient)
    client.provider = "openai"
    client.model = "fake-model"
    client.base_url = None
    client.last_metrics = {}
    client.is_available = True
    client._client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    client._cache_size = 2
    client._cache = OrderedDict()
    client._cache_lock = Lock()

    first = client.invoke_json(system_prompt="system", user_prompt="same")
    second = client.invoke_json(system_prompt="system", user_prompt="same")

    assert first.content == second.content
    assert completions.call_count == 1
    assert first.metrics["cache_hit"] is False
    assert second.metrics["cache_hit"] is True
