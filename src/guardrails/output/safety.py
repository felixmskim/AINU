"""[P2 담당] 출력 검사 3: 안전성 검사.

지금은 STUB: 모두 통과시킨다.

v0 (규칙): 시스템 프롬프트/내부 설정 문구, API 키 패턴, 개인정보 패턴이 답변에 섞였는지 검사
v1 (llm_judges 켜진 모드): 유해 내용 여부를 LLM 으로 판정

실패 시 action=BLOCK (유출/유해는 다시 생성하지 않고 안전 응답으로 대체)
"""
from __future__ import annotations

from src.contracts import Action, Category, GuardResult, TutorDraft


def check_safety(draft: TutorDraft) -> GuardResult:
    return GuardResult(action=Action.PASS, category=Category.NORMAL, reason="stub: 모두 통과")
