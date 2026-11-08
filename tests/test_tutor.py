"""[P3] 튜터 모듈 테스트: 전략표, 메모장 규칙, 프롬프트 조립, 거절 문구, 답변 조립."""
from src.contracts import (
    Action, Category, Chunk, GuardResult, Intent, LearnerAnalysis, LearnerState, Level, TutorDraft,
)
from src.tutor.generate import build_prompt
from src.tutor.refusal import compose_refusal
from src.tutor.render import render_answer
from src.tutor.state import after_answer, update_state
from src.tutor.strategy import HINTS, pick_strategy


def analysis(intent=Intent.CONCEPT, level=Level.BEGINNER, confidence=0.9):
    return LearnerAnalysis(level=level, intent=intent, confidence=confidence)


# ---- 전략
def test_strategy_differs_by_level():
    beginner = pick_strategy(analysis(level=Level.BEGINNER), LearnerState(level=Level.BEGINNER))
    intermediate = pick_strategy(analysis(level=Level.INTERMEDIATE), LearnerState(level=Level.INTERMEDIATE))
    assert beginner != intermediate


def test_homework_hints_escalate_with_attempts():
    texts = [pick_strategy(analysis(Intent.HOMEWORK), LearnerState(hint_count=n)) for n in range(len(HINTS) + 2)]
    assert HINTS[0] in texts[0] and HINTS[1] in texts[1]
    assert HINTS[-1] in texts[-1]           # 마지막 단계를 넘어서도 마지막 힌트에 머문다
    assert "정답을 바로 알려주지 말고" in texts[0]


def test_repeated_confusion_switches_to_new_analogy():
    state = LearnerState(confused_count=2)
    assert "다른 비유" in pick_strategy(analysis(Intent.CONFUSED), state)


def test_every_intent_has_a_strategy():
    for intent in Intent:
        for level in Level:
            assert pick_strategy(analysis(intent, level), LearnerState(level=level))


# ---- 메모장
def test_low_confidence_does_not_change_level():
    state = LearnerState(level=Level.BEGINNER)
    update_state(state, analysis(level=Level.INTERMEDIATE, confidence=0.4))
    assert state.level == Level.BEGINNER


def test_high_confidence_changes_level():
    state = LearnerState(level=Level.BEGINNER)
    update_state(state, analysis(level=Level.INTERMEDIATE, confidence=0.9))
    assert state.level == Level.INTERMEDIATE


def test_confusion_resets_to_beginner_and_counts():
    state = LearnerState(level=Level.INTERMEDIATE)
    update_state(state, analysis(Intent.CONFUSED, Level.INTERMEDIATE, 0.9))
    assert state.level == Level.BEGINNER and state.confused_count == 1


def test_after_answer_tracks_hints_and_pending_check():
    state = LearnerState()
    draft = TutorDraft(grounded_explanation="x", citations=["c1"], check_question="질문?")
    after_answer(state, analysis(Intent.HOMEWORK), draft)
    assert state.hint_count == 1 and state.pending_check["question"] == "질문?"
    after_answer(state, analysis(Intent.CONCEPT), TutorDraft(grounded_explanation="x", citations=["c1"]))
    assert state.hint_count == 0 and state.pending_check is None


# ---- 프롬프트
def test_build_prompt_contains_strategy_sources_and_question():
    chunk = Chunk(chunk_id="c42", doc="교재", text="오버랩 설명")
    prompt = build_prompt("오버랩이 뭐야?", [chunk], analysis(), LearnerState(), [])
    assert "[c42]" in prompt and "오버랩이 뭐야?" in prompt
    assert pick_strategy(analysis(), LearnerState()) in prompt


# ---- 거절 문구
def test_refusals_exist_for_every_blocking_category_and_never_leak_reason():
    for category in (Category.OUT_OF_SCOPE, Category.HARMFUL, Category.INJECTION, Category.SYSTEM_LEAK,
                     Category.PII, Category.NO_EVIDENCE, Category.UNGROUNDED):
        result = GuardResult(action=Action.BLOCK, category=category, reason="내부 규칙 R-17 에 걸림")
        message = compose_refusal(result, "질문")
        assert message and "R-17" not in message


# ---- 답변 조립
def test_render_lists_sources_once_and_includes_check_question():
    chunks = [
        Chunk(chunk_id="a", doc="교재", section="1장", page=1, text="t"),
        Chunk(chunk_id="b", doc="교재", section="1장", page=1, text="t"),
    ]
    draft = TutorDraft(grounded_explanation="본문", analogy="비유", citations=["a", "b"], check_question="이해했나요?")
    text = render_answer(draft, chunks)
    assert text.count("- 교재 (1장 · p.1)") == 1
    assert "쉬운 설명(비유): 비유" in text and "이해 확인: 이해했나요?" in text
