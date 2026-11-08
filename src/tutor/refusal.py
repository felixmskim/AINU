"""[P3 담당] 거절/보류 안내문: 가드 결과(GuardResult)를 사용자에게 보여줄 문장으로 바꾼다.

원칙
  - 단순 거절이 아니라 '안전한 학습 경로로 되돌려 주는' 문장으로 쓴다.
  - 정책 전문, 내부 지시, 탐지 규칙(reason)은 절대 노출하지 않는다. (reason 은 내부 로그용)
  - 그래서 이 함수는 result.reason 을 사용하지 않고 category 별 문구만 사용한다.
"""
from __future__ import annotations

from src.contracts import Category, GuardResult

_GENERIC = "지금은 답변을 드리기 어려워요. 질문을 조금 바꿔서 다시 시도해 주세요."

_TEMPLATES: dict[Category, str] = {
    Category.OUT_OF_SCOPE: (
        "그 질문은 이 튜터가 다루는 학습 범위를 벗어나 있어요. "
        "대신 교육자료에 있는 개념이나 문제에 대해 질문해 주시면 도와드릴게요."
    ),
    Category.HARMFUL: "그 요청은 도와드릴 수 없어요. 안전하게 학습할 수 있는 다른 주제라면 기꺼이 도울게요.",
    Category.INJECTION: "설정을 바꾸거나 규칙을 우회하는 요청은 처리할 수 없어요. 학습하고 싶은 내용을 알려 주세요.",
    Category.SYSTEM_LEAK: (
        "내부 설정이나 비밀 정보는 알려드릴 수 없어요. "
        "대신 관련된 개념이 궁금하시다면 일반적인 원리부터 설명해 드릴게요."
    ),
    Category.PII: "개인정보나 비밀 정보는 입력하지 않는 게 안전해요. 해당 정보를 빼고 다시 질문해 주세요.",
    Category.NO_EVIDENCE: (
        "제공된 교육자료에서는 이 질문의 근거를 찾지 못했어요. "
        "어떤 단원이나 개념에 대한 질문인지 조금 더 구체적으로 알려 주시겠어요?"
    ),
    Category.UNGROUNDED: "자료로 확인되는 범위에서 정확한 답을 만들지 못했어요. 질문을 조금 바꿔서 다시 물어봐 주시겠어요?",
}


def compose_refusal(result: GuardResult, query: str) -> str:
    return _TEMPLATES.get(result.category, _GENERIC)
