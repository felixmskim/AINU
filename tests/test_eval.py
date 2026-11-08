"""[P4] 평가 러너와 지표 계산 테스트."""
from eval.metrics import format_table, summarize
from eval.run_eval import DEFAULT_QUERIES, evaluate, load_rows
from src.contracts import Mode


def rec(should_allow, refused, latency=10.0, calls=1):
    return {"should_allow": should_allow, "refused": refused, "latency_ms": latency, "llm_calls": calls}


def test_summarize_computes_block_miss_and_false_positive_rates():
    records = [
        rec(False, True), rec(False, True), rec(False, False), rec(False, True),   # 위험 4개 중 3개 차단
        rec(True, False), rec(True, False), rec(True, False), rec(True, True),     # 정상 4개 중 1개 오탐
    ]
    summary = summarize(records)
    assert summary["block_rate"] == 0.75
    assert summary["miss_rate"] == 0.25
    assert summary["false_positive_rate"] == 0.25
    assert summary["n"] == 8 and summary["n_harmful"] == 4 and summary["n_normal"] == 4


def test_summarize_handles_missing_groups():
    summary = summarize([rec(True, False)])
    assert summary["block_rate"] is None and summary["miss_rate"] is None
    assert summarize([])["avg_latency_ms"] is None


def test_evaluate_runs_every_mode_on_the_sample_queries():
    rows = load_rows(DEFAULT_QUERIES, ["dev", "pair"])
    assert rows, "data/eval/queries.csv 에 dev/pair 질문이 있어야 한다"
    results = evaluate(rows, list(Mode))
    assert set(results) == {m.value for m in Mode}
    for records in results.values():
        assert len(records) == len(rows)
        assert {"id", "mode", "status", "refused", "latency_ms", "llm_calls"} <= set(records[0])
    table = format_table({name: summarize(r) for name, r in results.items()})
    assert "baseline" in table and "full" in table
