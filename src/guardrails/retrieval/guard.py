"""[P1 담당] 검색 가드레일: 찾아온 조각이 정말 질문의 근거가 되는지 검사한다.

지금은 STUB: 모두 통과시킨다.

v0: 유사도 점수가 settings.yaml 의 guards.retrieval.min_score 보다 낮은 결과만 있으면 근거 부족
v1: (llm_judges 켜진 모드) "이 조각들로 질문에 답할 수 있는가?"를 LLM 으로 판정 + 조각 안에 숨은
    지시문(간접 인젝션) 탐지

반환 규칙
  - 근거 충분: action=PASS
  - 근거 부족: action=HOLD, category=NO_EVIDENCE  (답변을 아예 만들지 않는다 = 환각 방어 1차선)
"""
from __future__ import annotations

from src.contracts import Action, Category, Chunk, GuardResult


def retrieval_guard(query: str, chunks: list[Chunk]) -> GuardResult:
    return GuardResult(action=Action.PASS, category=Category.NORMAL, reason="stub: 모두 통과")
