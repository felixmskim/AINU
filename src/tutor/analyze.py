"""[P3 담당] 학습자 분석: 질문과 대화 기록으로 수준(level)과 목적(intent)을 추정한다.

지금은 STUB: 수준은 '현재 메모장 값(= 데모 화면의 수동 버튼)', 목적은 concept, 확신도 1.0 을 돌려준다.

구현 순서 (docs/MODULES.md 참고)
  1) (지금) 수동 버튼으로 수준을 정한다 -> strategy/generate 를 먼저 완성
  2) llm_client.chat_json(role="judge") 으로 {level, intent, confidence} 를 JSON 으로 받는다
     - 판단 단서: 이번 질문의 말투/용어, 대화 기록(같은 걸 두 번 묻기, "모르겠어요"), 확인 질문에 대한 답
     - confidence 가 낮으면 수준을 바꾸지 않는다 (state.update_state 가 처리)
  3) state.pending_check 가 있으면 이번 메시지가 확인 질문의 답인지(intent=answer) 먼저 본다
"""
from __future__ import annotations

from src.contracts import Intent, LearnerAnalysis, LearnerState, Turn


def analyze_learner(query: str, history: list[Turn], state: LearnerState) -> LearnerAnalysis:
    return LearnerAnalysis(level=state.level, intent=Intent.CONCEPT, confidence=1.0)
