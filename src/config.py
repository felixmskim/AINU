"""설정 로더. settings.yaml 을 읽고, 모드(baseline/prompt_only/code_guard/full)별 스위치를 제공한다.

- 다른 모듈은 설정값을 직접 파일에서 읽지 말고 config.get("a.b.c", 기본값) 으로 읽는다.
- 파이프라인이 config.use_mode(mode) 안에서 실행되므로, 가드 내부에서는 config.flag("llm_judges")
  처럼 '지금 모드에서 켜져 있는가'를 물어볼 수 있다.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Any, Iterator

import yaml

from src.contracts import Mode

ROOT = Path(__file__).resolve().parent.parent
SETTINGS_PATH = ROOT / "settings.yaml"

_settings: dict[str, Any] | None = None
_mode_var: ContextVar[Mode] = ContextVar("current_mode", default=Mode.FULL)


def _load_dotenv(path: Path) -> None:
    """의존성 없이 .env 의 KEY=VALUE 를 환경변수로 읽는다 (이미 있는 환경변수는 덮어쓰지 않음)."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv(ROOT / ".env")


def load_settings(*, reload: bool = False) -> dict[str, Any]:
    global _settings
    if _settings is None or reload:
        with open(SETTINGS_PATH, encoding="utf-8") as f:
            _settings = yaml.safe_load(f) or {}
    return _settings


def get(key: str, default: Any = None) -> Any:
    """점(.)으로 구분한 경로로 설정값을 읽는다. 예: get("retrieval.k", 5)"""
    node: Any = load_settings()
    for part in key.split("."):
        if not isinstance(node, dict) or part not in node:
            return default
        node = node[part]
    return node


def override(key: str, value: Any) -> None:
    """메모리상의 설정을 임시로 바꾼다 (테스트/실험용. 파일은 바뀌지 않음)."""
    node = load_settings()
    parts = key.split(".")
    for part in parts[:-1]:
        node = node.setdefault(part, {})
    node[parts[-1]] = value


def default_mode() -> Mode:
    return Mode(get("mode", "full"))


def mode_flags(mode: Mode | str) -> dict[str, bool]:
    name = Mode(mode).value
    flags = get(f"modes.{name}")
    if flags is None:
        raise KeyError(f"settings.yaml 의 modes.{name} 가 없습니다")
    return dict(flags)


def current_mode() -> Mode:
    return _mode_var.get()


@contextmanager
def use_mode(mode: Mode | str) -> Iterator[None]:
    token = _mode_var.set(Mode(mode))
    try:
        yield
    finally:
        _mode_var.reset(token)


def flag(name: str) -> bool:
    """지금 실행 중인 모드에서 스위치 name 이 켜져 있는가."""
    return bool(mode_flags(current_mode()).get(name, False))
