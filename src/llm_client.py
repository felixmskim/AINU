"""AI(LLM) 호출 창구. 모든 모듈은 반드시 이 파일의 chat()/chat_json() 만 통해 모델을 부른다.

이렇게 한 곳으로 모으는 이유
  1) 호출 횟수와 걸린 시간이 자동으로 기록된다 -> 비용/지연 지표가 공짜로 나온다.
  2) 같은 요청의 응답을 저장(캐시)해서 평가를 여러 번 돌려도 크레딧이 줄지 않는다.
  3) provider 를 fake 로 두면 API 키 없이도 전체 파이프라인이 돌아간다.

주의 (P3가 첫날 확인할 것)
  - provider=http 는 'OpenAI 호환 chat/completions' 형식이라고 *가정*하고 만든 어댑터다.
    엘리스 ML API 의 실제 주소/요청 형식/모델 이름을 문서로 확인하고 _http_chat 을 맞춰야 한다.
    (아직 실제 API 로 시험하지 않았다.)
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Optional

from src import config


class LLMError(RuntimeError):
    """AI 호출/응답 처리 실패."""


@dataclass
class Stats:
    calls: int = 0            # 실제로 모델을 부른 횟수 (캐시 적중은 제외)
    cache_hits: int = 0
    total_ms: float = 0.0
    by_role: dict[str, int] = field(default_factory=dict)


stats = Stats()


def reset_stats() -> None:
    stats.calls = 0
    stats.cache_hits = 0
    stats.total_ms = 0.0
    stats.by_role = {}


# ---------------------------------------------------------------- 캐시
_cache: dict[str, str] | None = None


def _cache_path():
    return config.ROOT / config.get("llm.cache_path", ".cache/llm_cache.json")


def _cache_load() -> dict[str, str]:
    global _cache
    if _cache is None:
        path = _cache_path()
        _cache = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    return _cache


def _cache_key(model: str, system: Optional[str], prompt: str, temperature: float) -> str:
    raw = json.dumps([model, system, prompt, temperature], ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _cache_put(key: str, value: str) -> None:
    cache = _cache_load()
    cache[key] = value
    path = _cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------- provider
def _fake_chat(prompt: str, role: str) -> str:
    snippet = " ".join(prompt.split())[:80]
    return f"[FAKE-LLM:{role}] {snippet}"


def _http_chat(prompt: str, system: Optional[str], model: str, temperature: float) -> str:
    base_url = os.environ.get(config.get("llm.base_url_env", "ELICE_ML_API_BASE_URL"))
    api_key = os.environ.get(config.get("llm.api_key_env", "ELICE_ML_API_KEY"))
    if not base_url or not api_key:
        raise LLMError(".env 에 ELICE_ML_API_BASE_URL / ELICE_ML_API_KEY 를 채우세요")
    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    payload = json.dumps({"model": model, "messages": messages, "temperature": temperature}).encode("utf-8")
    request = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=config.get("llm.timeout_s", 60)) as response:
            body: Any = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError) as exc:
        raise LLMError(f"ML API 호출 실패: {exc}") from exc
    try:
        return body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMError(f"예상과 다른 응답 형식입니다: {str(body)[:200]}") from exc


# ---------------------------------------------------------------- 공개 함수
def chat(prompt: str, *, system: Optional[str] = None, role: str = "generate", temperature: float = 0.0) -> str:
    """모델에게 프롬프트를 보내고 텍스트 응답을 받는다.

    role: "generate"(답변 생성용 큰 모델) 또는 "judge"(분류/판정용 작은 모델). settings.yaml 의 llm.models 참고.
    """
    provider = config.get("llm.provider", "fake")
    model = config.get(f"llm.models.{role}", "unknown")

    cache_key = None
    if provider == "http" and config.get("llm.cache", True):
        cache_key = _cache_key(model, system, prompt, temperature)
        cached = _cache_load().get(cache_key)
        if cached is not None:
            stats.cache_hits += 1
            return cached

    started = time.perf_counter()
    if provider == "fake":
        text = _fake_chat(prompt, role)
    elif provider == "http":
        text = _http_chat(prompt, system, model, temperature)
    else:
        raise LLMError(f"알 수 없는 llm.provider: {provider!r} (fake 또는 http)")

    stats.calls += 1
    stats.total_ms += (time.perf_counter() - started) * 1000
    stats.by_role[role] = stats.by_role.get(role, 0) + 1
    if cache_key:
        _cache_put(cache_key, text)
    return text


def extract_json(text: str) -> dict[str, Any]:
    """모델 응답에서 JSON 객체를 꺼낸다 (```json 코드블록이나 앞뒤 설명이 붙어도 처리)."""
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.S)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    raise LLMError(f"JSON 으로 해석할 수 없는 응답입니다: {text[:200]!r}")


def chat_json(prompt: str, *, system: Optional[str] = None, role: str = "judge", temperature: float = 0.0) -> dict[str, Any]:
    """chat() 결과를 JSON 으로 파싱해서 돌려준다. 분류기/판정기가 주로 사용."""
    return extract_json(chat(prompt, system=system, role=role, temperature=temperature))
