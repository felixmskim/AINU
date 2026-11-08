"""[P3 담당] 파이프라인: 질문 하나를 처음부터 끝까지 처리하는 유일한 진입점 ask().

흐름 (모드에 따라 일부 단계는 건너뛴다. settings.yaml 의 modes 참고)

  질문
   -> 입력 가드레일 ----(차단)----> 안내문 (status=blocked)
   -> 학습자 분석 + 메모장 갱신   (tutor 모드만)
   -> 교육자료 검색
   -> 검색 가드레일 ----(근거 부족)--> 안내문 (status=held)
   -> 답변 생성 -> 출력 가드레일 --(실패)--> 1회 재생성 -> 그래도 실패하면 안전 응답 (status=fallback)
   -> 검증된 답변 (status=answered)

이 파일은 '연결'만 한다. 각 단계의 실제 로직은 담당자의 모듈 파일을 고친다.
함수들을 이 파일 맨 위에서 import 하므로, 테스트에서는 pipeline.input_guard 처럼 바꿔 끼울 수 있다.

실행:  python -m src.pipeline "chunk overlap이 왜 필요해?" --mode full
"""
from __future__ import annotations

import argparse
import time
from typing import Callable, Optional, TypeVar

from src import config, llm_client
from src.contracts import (
    Action,
    Category,
    GuardResult,
    LearnerState,
    Mode,
    StageRecord,
    Status,
    TutorDraft,
    TutorResponse,
    Turn,
)
from src.guardrails.input import input_guard
from src.guardrails.output import output_guard
from src.guardrails.retrieval import retrieval_guard
from src.rag import retrieve
from src.tutor.analyze import analyze_learner
from src.tutor.baseline import baseline_generate
from src.tutor.generate import generate
from src.tutor.refusal import compose_refusal
from src.tutor.render import render_answer
from src.tutor.state import after_answer, update_state

T = TypeVar("T")


def _timed(trace: list[StageRecord], stage: str, fn: Callable[[], T]) -> T:
    """fn 을 실행하고, 걸린 시간과 (가드라면) 결과를 trace 에 기록한다."""
    started = time.perf_counter()
    value = fn()
    trace.append(
        StageRecord(
            stage=stage,
            result=value if isinstance(value, GuardResult) else None,
            latency_ms=(time.perf_counter() - started) * 1000,
        )
    )
    return value


def ask(
    query: str,
    *,
    mode: Mode = Mode.FULL,
    state: Optional[LearnerState] = None,
    history: Optional[list[Turn]] = None,
) -> TutorResponse:
    """질문 하나를 처리해 TutorResponse 를 돌려준다.

    state 는 대화(세션) 동안 호출자가 들고 있다가 계속 넘겨주면 이 함수가 고쳐서 돌려준다(제자리 갱신).
    history 는 호출자가 관리한다 (이 함수는 수정하지 않는다). 턴이 끝나면 remember(history, response) 로 기록한다.
    """
    mode = Mode(mode)
    state = state if state is not None else LearnerState()
    history = history if history is not None else []
    started = time.perf_counter()
    calls_before = llm_client.stats.calls
    trace: list[StageRecord] = []
    ctx: dict[str, Optional[str]] = {"sanitized": None}   # 가드가 마스킹한 질문 (대화 기록용)

    def finish(status: Status, text: str, category: Category, citations: Optional[list[str]] = None) -> TutorResponse:
        return TutorResponse(
            status=status,
            text=text,
            citations=citations or [],
            category=category,
            sanitized_query=ctx["sanitized"],
            trace=trace,
            llm_calls=llm_client.stats.calls - calls_before,
            latency_ms=(time.perf_counter() - started) * 1000,
        )

    with config.use_mode(mode):
        flags = config.mode_flags(mode)
        category = Category.NORMAL
        working_query = query

        # 1) 입력 가드레일
        ctx["sanitized"] = query          # 가드를 쓰지 않는 모드(baseline 등)는 원문 그대로
        if flags["input_guard"]:
            guard = _timed(trace, "input_guard", lambda: input_guard(query))
            category = guard.category
            ctx["sanitized"] = guard.sanitized_text
            if not guard.allowed:
                return finish(Status.BLOCKED, compose_refusal(guard, query), category)
            working_query = guard.sanitized_text or query   # 이후 단계는 마스킹된 질문만 사용
            ctx["sanitized"] = working_query

        # 2) 학습자 분석 (튜터 모드만)
        analysis = None
        if flags["tutor"]:
            analysis = _timed(trace, "analyze_learner", lambda: analyze_learner(working_query, history, state))
            update_state(state, analysis)

        # 3) 검색
        chunks = _timed(trace, "retrieve", lambda: retrieve(working_query, k=config.get("retrieval.k", 5)))

        # 4) 검색 가드레일
        if flags["retrieval_guard"]:
            rguard = _timed(trace, "retrieval_guard", lambda: retrieval_guard(working_query, chunks))
            if not rguard.allowed:
                return finish(Status.HELD, compose_refusal(rguard, query), category)

        # 5) 생성 + 6) 출력 가드레일 (실패하면 정해진 횟수만큼 다시 생성)
        max_regenerations = int(config.get("pipeline.max_regenerations", 1))
        draft: TutorDraft
        for attempt in range(max_regenerations + 1):
            draft = _timed(
                trace, "generate", lambda: _generate(flags, working_query, chunks, analysis, state, history)
            )
            if not flags["output_guard"]:
                break
            oguard = _timed(trace, "output_guard", lambda: output_guard(draft, chunks))
            if oguard.allowed:
                break
            if oguard.action == Action.BLOCK or attempt == max_regenerations:
                return finish(Status.FALLBACK, compose_refusal(oguard, query), category)

        # 7) 전달
        if analysis is not None:
            after_answer(state, analysis, draft)
        return finish(Status.ANSWERED, render_answer(draft, chunks), category, citations=draft.citations)


OMITTED_TURN = "[차단되었거나 기록하지 않은 요청]"


def remember(history: list[Turn], response: TutorResponse) -> None:
    """대화 기록(history)에 이번 턴을 추가한다. 기록에는 반드시 이 함수를 쓴다.

    - 사용자 발화는 원문이 아니라 '가드가 마스킹한 질문'만 저장한다 (개인정보가 다음 턴 프롬프트로 새는 것 방지).
    - 차단된 요청은 내용을 저장하지 않는다 (공격 문장이 다음 턴 프롬프트에 남아 영향을 주는 것 방지).
    """
    if response.status == Status.BLOCKED or not response.sanitized_query:
        user_text = OMITTED_TURN
    else:
        user_text = response.sanitized_query
    history.append(Turn(role="user", content=user_text))
    history.append(Turn(role="tutor", content=response.text))


def _generate(flags, query, chunks, analysis, state, history) -> TutorDraft:
    if flags["tutor"]:
        return generate(query, chunks, analysis, state, history)
    return baseline_generate(query, chunks, policy_prompt=flags["policy_prompt"])


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="질문 하나를 파이프라인에 넣어 본다")
    parser.add_argument("query")
    parser.add_argument("--mode", default=config.default_mode().value, choices=[m.value for m in Mode])
    parser.add_argument("--json", action="store_true", help="결과 전체(trace 포함)를 JSON 으로 출력")
    args = parser.parse_args(argv)

    response = ask(args.query, mode=Mode(args.mode))
    if args.json:
        print(response.model_dump_json(indent=2))
        return
    print(response.text)
    print("\n--- 처리 기록 ---")
    print(f"status={response.status.value}  category={response.category.value}  "
          f"llm_calls={response.llm_calls}  latency={response.latency_ms:.1f}ms")
    for record in response.trace:
        verdict = f"{record.result.action.value}/{record.result.category.value}" if record.result else ""
        print(f"  {record.stage:<16} {record.latency_ms:7.1f}ms  {verdict}")


if __name__ == "__main__":
    main()
