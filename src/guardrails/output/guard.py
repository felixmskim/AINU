"""[P1 담당] 출력 가드레일 조립: 싼 코드 검사부터 순서대로 실행하고, 처음 실패한 결과를 돌려준다.

순서: 인용 형식(citations, 코드) -> 안전성(safety, P2) -> 주장-근거 일치(grounding, P1, 가장 비쌈)
이 파일은 얇게 유지한다. 각 검사의 내용은 같은 폴더의 개별 파일을 고친다 (파일이 달라야 충돌이 없다).
"""
from __future__ import annotations

from src.contracts import Action, Category, Chunk, GuardResult, TutorDraft

from .citations import check_citations
from .grounding import check_grounding
from .safety import check_safety


def output_guard(draft: TutorDraft, chunks: list[Chunk]) -> GuardResult:
    for result in (
        check_citations(draft, chunks),
        check_safety(draft),
        check_grounding(draft, chunks),
    ):
        if not result.allowed:
            return result
    return GuardResult(action=Action.PASS, category=Category.NORMAL, reason="all output checks passed")
