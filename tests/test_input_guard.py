"""[P2] 입력 가드 테스트.

test_target_*  는 '완료 기준'을 테스트로 적어 둔 것이다. 스텁(모두 통과) 상태에서는 실패하는 게 정상이라
xfail 로 표시해 뒀다. v0 를 구현해서 통과하기 시작하면(XPASS) 아래 xfail 표시를 지우면 된다.
"""
import csv

import pytest

from src import config
from src.contracts import GuardResult
from src.guardrails.input import input_guard


def _rows():
    path = config.ROOT / "data" / "eval" / "queries.csv"
    with open(path, encoding="utf-8", newline="") as f:
        return [r for r in csv.DictReader(f) if r["set"] in ("dev", "pair")]


def test_returns_guard_result_with_sanitized_text_when_passing():
    result = input_guard("  청킹이 뭐야?  ")
    assert isinstance(result, GuardResult)
    if result.allowed:
        assert result.sanitized_text == "청킹이 뭐야?"


@pytest.mark.xfail(reason="P2: 입력 가드 v0 구현 전 (스텁은 모두 통과시킴). 구현 후 이 표시를 지울 것", strict=False)
def test_target_blocks_risky_and_passes_normal_on_dev_and_pair_sets():
    wrong = [
        (r["id"], r["query"]) for r in _rows()
        if input_guard(r["query"]).allowed != (r["should_allow"] == "true")
    ]
    assert not wrong, f"정답 라벨과 다르게 판정한 질문: {wrong}"
