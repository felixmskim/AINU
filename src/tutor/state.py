"""[P3 담당] 학습자 메모장(LearnerState)을 고치는 규칙. 이미 구현되어 있다.

- update_state : 답변을 만들기 '전'에, 분석 결과로 수준과 헷갈림 횟수를 갱신
- after_answer : 답변을 만든 '후'에, 힌트 횟수와 확인 질문(pending_check)을 갱신
"""
from __future__ import annotations

from src import config
from src.contracts import Intent, LearnerAnalysis, LearnerState, Level, TutorDraft


def update_state(state: LearnerState, analysis: LearnerAnalysis) -> LearnerState:
    threshold = config.get("tutor.level_confidence_threshold", 0.7)
    if analysis.confidence >= threshold:
        state.level = analysis.level
    if analysis.intent == Intent.CONFUSED:
        state.confused_count += 1
        state.level = Level.BEGINNER
    return state


def after_answer(state: LearnerState, analysis: LearnerAnalysis, draft: TutorDraft) -> LearnerState:
    if analysis.intent == Intent.HOMEWORK:
        state.hint_count += 1
    else:
        state.hint_count = 0
    state.pending_check = (
        {"question": draft.check_question, "chunk_ids": list(draft.citations)} if draft.check_question else None
    )
    return state
