"""[P1 담당] 출력 검사 2: 주장-근거 일치 검증 (환각 방어의 핵심, 심사 40점과 직결).

지금은 STUB: 모두 통과시킨다.

v1 구현 방법
  - draft.claims 의 주장을 하나씩, 인용한 청크 텍스트와 비교한다.
  - "이 주장이 이 청크에 실제로 들어 있는가?"를 LLM 으로 판정한다 (llm_client.chat_json, role="judge").
  - 하나라도 근거가 없으면 action=REGENERATE, category=UNGROUNDED.
  - draft.analogy(비유)는 '근거 설명의 의미를 바꾸지 않는가'만 완화해서 검사한다.
  - config.flag("llm_judges") 가 꺼진 모드(code_guard)에서는 LLM 을 부르지 않는다.
"""
from __future__ import annotations

from src.contracts import Action, Category, Chunk, GuardResult, TutorDraft


def check_grounding(draft: TutorDraft, chunks: list[Chunk]) -> GuardResult:
    return GuardResult(action=Action.PASS, category=Category.NORMAL, reason="stub: 모두 통과")
