"""[P1 담당] 출력 검사 1: 인용 형식 검사 (순수 코드, AI 호출 없음). 이미 구현되어 있다.

규칙
  - 답변에는 출처(citations)가 하나 이상 있어야 한다.
  - 인용한 chunk_id 는 모두 '이번에 검색된 조각' 안에 실제로 존재해야 한다 (없는 출처를 지어내는 것 방지).
"""
from __future__ import annotations

from src.contracts import Action, Category, Chunk, GuardResult, TutorDraft


def check_citations(draft: TutorDraft, chunks: list[Chunk]) -> GuardResult:
    known = {c.chunk_id for c in chunks}
    cited = list(draft.citations)
    for claim in draft.claims:
        cited.extend(claim.citations)

    if not draft.citations:
        return GuardResult(action=Action.REGENERATE, category=Category.UNGROUNDED, reason="출처가 없는 답변")

    unknown = sorted({cid for cid in cited if cid not in known})
    if unknown:
        return GuardResult(
            action=Action.REGENERATE,
            category=Category.UNGROUNDED,
            reason=f"검색되지 않은 출처를 인용함: {unknown}",
        )
    return GuardResult(action=Action.PASS, category=Category.NORMAL, reason="citations ok")
