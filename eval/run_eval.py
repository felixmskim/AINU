"""[P4 담당] 평가 러너: 테스트 질문 CSV 를 읽어 모드별로 ask() 를 돌리고, 결과 CSV 와 비교표를 만든다.

실행:  python -m eval.run_eval                       # dev,pair 세트를 4개 모드로
       python -m eval.run_eval --modes baseline,full --sets dev
       python -m eval.run_eval --sets holdout_a      # 홀드아웃은 체크포인트에서만 실행 (개발 중 열어보지 않기!)

질문 CSV 형식 (data/eval/queries.csv): id, query, label, should_allow, set, pair_id
  - label 은 src/contracts 의 Category 값, set 은 dev / pair / holdout_a / holdout_b
결과: eval/results/{시각}_{모드}.csv  (git 에 올리지 않음)
"""
from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path
from typing import Optional

from eval.metrics import format_table, summarize
from src import config
from src.contracts import Mode
from src.pipeline import ask

DEFAULT_QUERIES = config.ROOT / "data" / "eval" / "queries.csv"
RESULTS_DIR = config.ROOT / "eval" / "results"


def load_rows(path: Path, sets: Optional[list[str]] = None) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    return [r for r in rows if not sets or r["set"] in sets]


def evaluate(rows: list[dict], modes: list[Mode]) -> dict[str, list[dict]]:
    """모드별 결과 기록 목록을 돌려준다. 질문마다 새 학습자 메모장으로 독립 실행."""
    results: dict[str, list[dict]] = {}
    for mode in modes:
        records = []
        for row in rows:
            response = ask(row["query"], mode=mode)
            records.append(
                {
                    "id": row["id"],
                    "mode": mode.value,
                    "set": row["set"],
                    "label": row["label"],
                    "should_allow": row["should_allow"].strip().lower() == "true",
                    "query": row["query"],
                    "status": response.status.value,
                    "refused": response.status.value != "answered",
                    "predicted_category": response.category.value,
                    "llm_calls": response.llm_calls,
                    "latency_ms": round(response.latency_ms, 1),
                }
            )
        results[mode.value] = records
    return results


def write_csv(records: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not records:
        return
    with open(path, "w", encoding="utf-8-sig", newline="") as f:   # utf-8-sig: 엑셀에서 한글이 안 깨짐
        writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="4단계 비교 평가")
    parser.add_argument("--queries", type=Path, default=DEFAULT_QUERIES)
    parser.add_argument("--sets", default="dev,pair", help="쉼표로 구분 (dev,pair,holdout_a,holdout_b)")
    parser.add_argument("--modes", default=",".join(m.value for m in Mode))
    parser.add_argument("--limit", type=int, default=0, help="질문 수 제한 (크레딧 절약용, 0=전체)")
    args = parser.parse_args(argv)

    rows = load_rows(args.queries, [s for s in args.sets.split(",") if s])
    if args.limit:
        rows = rows[: args.limit]
    modes = [Mode(m) for m in args.modes.split(",") if m]
    results = evaluate(rows, modes)

    stamp = time.strftime("%Y%m%d_%H%M%S")
    for mode_name, records in results.items():
        write_csv(records, RESULTS_DIR / f"{stamp}_{mode_name}.csv")
    print(f"질문 {len(rows)}개 x 모드 {len(modes)}개   (결과: eval/results/{stamp}_*.csv)\n")
    print(format_table({name: summarize(records) for name, records in results.items()}))


if __name__ == "__main__":
    main()
