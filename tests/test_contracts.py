"""계약 테스트. 머지 전에 항상 통과해야 한다:  python -m pytest tests/test_contracts.py"""
import csv
import json
from pathlib import Path

import pytest

from src.contracts import (
    EVAL_SETS,
    Action,
    Category,
    Chunk,
    GuardResult,
    InputGuard,
    LearnerAnalysis,
    LearnerState,
    OutputGuard,
    Pipeline,
    TutorDraft,
    TutorResponse,
    assert_matches,
)

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def load_chunks():
    return [Chunk(**c) for c in json.loads((FIXTURES / "chunks.sample.json").read_text(encoding="utf-8"))]


def load_drafts():
    return json.loads((FIXTURES / "drafts.sample.json").read_text(encoding="utf-8"))


def load_eval_rows():
    with open(FIXTURES / "eval_queries.sample.csv", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


# ---- 1. 샘플 데이터가 계약(스키마)과 맞는가 ----

def test_chunks_fixture_matches_schema():
    chunks = load_chunks()
    assert len(chunks) >= 1
    assert len({c.chunk_id for c in chunks}) == len(chunks), "chunk_id는 중복되면 안 된다"


def test_drafts_fixture_matches_schema_and_references_existing_chunks():
    chunk_ids = {c.chunk_id for c in load_chunks()}
    for case in load_drafts():
        draft = TutorDraft(**case["draft"])
        assert Action(case["expect_action"]) in (Action.PASS, Action.REGENERATE)
        for cid in case["chunk_ids"] + draft.citations:
            assert cid in chunk_ids, f"{case['case_id']}: 존재하지 않는 chunk_id {cid}"


def test_eval_queries_use_valid_labels_and_sets():
    rows = load_eval_rows()
    valid_labels = {c.value for c in Category}
    for row in rows:
        assert row["label"] in valid_labels, f"id={row['id']}: 알 수 없는 label {row['label']}"
        assert row["set"] in EVAL_SETS, f"id={row['id']}: 알 수 없는 set {row['set']}"
        assert row["should_allow"] in ("true", "false")


def test_pair_rows_come_in_twos():
    pairs = {}
    for row in load_eval_rows():
        if row["pair_id"]:
            pairs.setdefault(row["pair_id"], []).append(row)
    for pid, rows in pairs.items():
        assert len(rows) == 2, f"pair {pid}는 정상/공격 두 개여야 한다"
        assert {r["should_allow"] for r in rows} == {"true", "false"}


# ---- 2. 스키마 동작 ----

def test_guard_result_allowed_property():
    assert GuardResult(action=Action.PASS, category=Category.NORMAL).allowed is True
    assert GuardResult(action=Action.BLOCK, category=Category.INJECTION).allowed is False


def test_learner_analysis_rejects_out_of_range_confidence():
    with pytest.raises(Exception):
        LearnerAnalysis(level="beginner", intent="concept", confidence=1.5)


def test_defaults_allow_minimal_construction():
    assert LearnerState().level.value == "beginner"
    assert TutorResponse(status="answered", text="ok").trace == []


# ---- 3. 시그니처 검사 도구 ----

def test_assert_matches_accepts_correct_signature():
    def input_guard(text: str) -> GuardResult: ...
    assert_matches(input_guard, InputGuard)


def test_assert_matches_rejects_wrong_parameter_names():
    def input_guard(query: str) -> GuardResult: ...   # text 가 아니라 query
    with pytest.raises(AssertionError):
        assert_matches(input_guard, InputGuard)


def test_assert_matches_rejects_wrong_parameter_order():
    def output_guard(chunks, draft): ...
    with pytest.raises(AssertionError):
        assert_matches(output_guard, OutputGuard)


def test_pipeline_signature_has_keyword_only_args():
    def ask(query, *, mode=None, state=None, history=None): ...
    assert_matches(ask, Pipeline)
