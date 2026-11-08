import pytest

from src import config


@pytest.fixture(autouse=True, scope="session")
def _force_fake_llm():
    """테스트는 어떤 경우에도 실제 API 를 부르지 않는다 (settings.yaml 이 http 여도 fake 로 강제)."""
    config.load_settings()
    config.override("llm.provider", "fake")
    yield
