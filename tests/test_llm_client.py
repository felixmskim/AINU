import pytest

from src import config, llm_client


def test_fake_provider_returns_text_and_counts_calls():
    llm_client.reset_stats()
    text = llm_client.chat("안녕", role="judge")
    assert text.startswith("[FAKE-LLM:judge]")
    assert llm_client.stats.calls == 1
    assert llm_client.stats.by_role == {"judge": 1}


def test_extract_json_handles_plain_fenced_and_surrounded_text():
    assert llm_client.extract_json('{"a": 1}') == {"a": 1}
    assert llm_client.extract_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert llm_client.extract_json('결과는 다음과 같다: {"a": 1} 이상') == {"a": 1}


def test_extract_json_rejects_garbage():
    with pytest.raises(llm_client.LLMError):
        llm_client.extract_json("JSON 이 아닌 문장")


def test_unknown_provider_raises():
    config.override("llm.provider", "bogus")
    try:
        with pytest.raises(llm_client.LLMError):
            llm_client.chat("x")
    finally:
        config.override("llm.provider", "fake")


def test_http_provider_without_credentials_fails_clearly(monkeypatch):
    monkeypatch.delenv("ELICE_ML_API_BASE_URL", raising=False)
    monkeypatch.delenv("ELICE_ML_API_KEY", raising=False)
    config.override("llm.provider", "http")
    config.override("llm.cache", False)
    try:
        with pytest.raises(llm_client.LLMError, match=".env"):
            llm_client.chat("x")
    finally:
        config.override("llm.provider", "fake")
        config.override("llm.cache", True)
