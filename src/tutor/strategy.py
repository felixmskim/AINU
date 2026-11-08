"""[P3 담당] 설명 전략: (목적 x 수준)에 따라 '설명 순서 지침'을 고른다. 이미 구현되어 있다.

수준별 설명은 AI 에게 주는 지시문의 '설명 순서'가 바뀌는 것이다. 표(STRATEGY)를 고치며 다듬는다.
"""
from __future__ import annotations

from src.contracts import Intent, LearnerAnalysis, LearnerState, Level

STRATEGY: dict[tuple[Intent, Level], str] = {
    (Intent.CONCEPT, Level.BEGINNER): (
        "① 핵심 용어를 쉬운 말로 풀어 주고 ② 교재에 있는 예시를 우선 사용하며, 비유가 필요하면 '비유'라고 "
        "표시해서 따로 적고 ③ 한 줄로 요약해라."
    ),
    (Intent.CONCEPT, Level.INTERMEDIATE): "① 원리를 설명하고 ② 비슷한 개념과 비교하고 ③ 한계와 주의점을 말해라.",
    (Intent.DEBUG, Level.BEGINNER): "어디서 틀렸는지 먼저 짚고, 고치는 방법은 한 단계씩 알려줘라.",
    (Intent.DEBUG, Level.INTERMEDIATE): "원인 가설을 제시하고, 그것을 확인하는 방법을 알려줘라.",
    (Intent.CONFUSED, Level.BEGINNER): "앞 설명보다 더 쉬운 말로, 더 작은 단계로 나눠서 다시 설명해라.",
    (Intent.CONFUSED, Level.INTERMEDIATE): "반례나 대조되는 경우를 들어 다시 설명해라.",
}

HINTS = ["방향만 알려주기", "핵심 개념만 알려주기", "풀이 뼈대 보여주기", "단계별 풀이 보여주기"]


def pick_strategy(analysis: LearnerAnalysis, state: LearnerState) -> str:
    if analysis.intent == Intent.HOMEWORK:
        step = HINTS[min(state.hint_count, len(HINTS) - 1)]
        return f"정답을 바로 알려주지 말고, 이번에는 '{step}'까지만 해라."
    if analysis.intent == Intent.CONFUSED and state.confused_count >= 2:
        return "앞에서 쓰지 않은 다른 비유와 예시로 다시 설명해라."
    default = STRATEGY[(Intent.CONCEPT, state.level)]
    return STRATEGY.get((analysis.intent, state.level), default)
