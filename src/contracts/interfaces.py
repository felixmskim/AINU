"""각 모듈이 반드시 지켜야 하는 '함수 시그니처'.

| 함수              | 담당 | 위치(제안)                          |
|-------------------|------|-------------------------------------|
| input_guard       | P2   | src/guardrails/input/               |
| retrieve          | P1   | src/rag/                            |
| retrieval_guard   | P1   | src/guardrails/retrieval/           |
| analyze_learner   | P3   | src/tutor/analyze.py                |
| generate          | P3   | src/tutor/generate.py               |
| output_guard      | P1+P2| src/guardrails/output/              |
| compose_refusal   | P3   | src/tutor/refusal.py                |
| ask (pipeline)    | P3   | src/pipeline.py                     |

각 담당자는 자기 함수가 이 시그니처와 같은지 테스트로 확인한다:
    from src.contracts import assert_matches, InputGuard
    assert_matches(input_guard, InputGuard)
"""
from __future__ import annotations

import inspect
from typing import Callable, Optional, Protocol

from .categories import Mode
from .schemas import (
    Chunk,
    GuardResult,
    LearnerAnalysis,
    LearnerState,
    TutorDraft,
    TutorResponse,
    Turn,
)


class InputGuard(Protocol):
    def __call__(self, text: str) -> GuardResult:
        """질문을 정규화/마스킹하고 종류를 판별한다. 통과면 sanitized_text에 정리된 질문을 담는다."""
        ...


class Retriever(Protocol):
    def __call__(self, query: str, k: int = 5) -> list[Chunk]:
        """질문과 가장 비슷한 교육자료 조각 k개를 점수순으로 돌려준다."""
        ...


class RetrievalGuard(Protocol):
    def __call__(self, query: str, chunks: list[Chunk]) -> GuardResult:
        """조각이 질문의 근거로 충분한지 판단한다. 부족하면 action=HOLD, category=NO_EVIDENCE."""
        ...


class LearnerAnalyzer(Protocol):
    def __call__(self, query: str, history: list[Turn], state: LearnerState) -> LearnerAnalysis:
        """질문과 대화 기록으로 학습자 수준과 목적을 추정한다."""
        ...


class TutorGenerator(Protocol):
    def __call__(
        self,
        query: str,
        chunks: list[Chunk],
        analysis: LearnerAnalysis,
        state: LearnerState,
        history: list[Turn],
    ) -> TutorDraft:
        """근거 조각만 사용해 학습자 수준에 맞는 답변 초안을 만든다."""
        ...


class OutputGuard(Protocol):
    def __call__(self, draft: TutorDraft, chunks: list[Chunk]) -> GuardResult:
        """답변-근거 일치, 인용 형식, 안전성을 검사한다. 실패면 action=REGENERATE."""
        ...


class RefusalComposer(Protocol):
    def __call__(self, result: GuardResult, query: str) -> str:
        """차단/보류 결과를 사용자에게 보여줄 안내문으로 바꾼다 (정책 전문과 내부 정보는 노출 금지)."""
        ...


class Pipeline(Protocol):
    def __call__(
        self,
        query: str,
        *,
        mode: Mode = Mode.FULL,
        state: Optional[LearnerState] = None,
        history: Optional[list[Turn]] = None,
    ) -> TutorResponse:
        """질문 하나를 처음부터 끝까지 처리한다. 평가 러너와 데모 화면이 호출하는 유일한 진입점."""
        ...


def assert_matches(func: Callable, protocol: type) -> None:
    """func의 매개변수 이름과 순서가 protocol과 같은지 확인한다. 다르면 AssertionError."""
    expected = [p for p in inspect.signature(protocol.__call__).parameters if p != "self"]
    actual = list(inspect.signature(func).parameters)
    if expected != actual:
        raise AssertionError(
            f"{getattr(func, '__name__', func)} 의 매개변수 {actual} 가 "
            f"계약 {protocol.__name__} 의 {expected} 와 다릅니다."
        )
