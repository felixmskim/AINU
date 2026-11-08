"""공용 용어(열거형) 모음.

이 파일의 값은 '코드(가드레일 결과)'와 '테스트셋 라벨'이 함께 쓴다.
값을 추가/삭제/이름 변경하려면 팀 전체 합의 후 P3가 반영한다.
"""
from enum import Enum


class Category(str, Enum):
    """질문 또는 검사 결과의 종류. 테스트셋의 label 컬럼도 이 값을 그대로 쓴다."""

    NORMAL = "normal"              # 정상 학습 질문 (과제 정답 요구도 여기 포함: 차단이 아니라 힌트로 전환)
    OUT_OF_SCOPE = "out_of_scope"  # 교육과 무관한 요청 (주식, 맛집 등)
    HARMFUL = "harmful"            # 범죄, 폭력, 개인정보 악용 등
    INJECTION = "injection"        # 탈옥, 직접/간접 프롬프트 인젝션
    SYSTEM_LEAK = "system_leak"    # 시스템 프롬프트, API 키 등 내부 정보 요구
    PII = "pii"                    # 입력에 개인정보/비밀정보가 들어 있음 (차단이 아니라 마스킹 대상)
    NO_EVIDENCE = "no_evidence"    # 검색 결과가 질문의 근거로 부족함
    UNGROUNDED = "ungrounded"      # 답변이 근거와 일치하지 않음 (환각)


class Action(str, Enum):
    """가드가 내리는 결정."""

    PASS = "pass"              # 통과
    BLOCK = "block"            # 차단하고 안내문 제공
    HOLD = "hold"              # 답변 보류 (근거 부족, 질문 구체화 유도)
    REGENERATE = "regenerate"  # 출력 검사 실패: 다시 생성


class Level(str, Enum):
    """추정한 학습자 수준."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"


class Intent(str, Enum):
    """학습자의 질문 목적."""

    CONCEPT = "concept"    # 개념 이해
    HOMEWORK = "homework"  # 문제 풀이, 정답 요구
    DEBUG = "debug"        # 오류 해결
    CONFUSED = "confused"  # 앞 설명이 이해 안 됨
    ANSWER = "answer"      # 내가 낸 확인 질문에 대한 학습자의 답


class Status(str, Enum):
    """최종 응답의 상태."""

    ANSWERED = "answered"  # 검증을 통과한 정상 답변
    BLOCKED = "blocked"    # 입력 단계에서 차단
    HELD = "held"          # 근거 부족으로 보류
    FALLBACK = "fallback"  # 재생성 후에도 실패해 안전 응답으로 대체


class Mode(str, Enum):
    """4단계 비교 실험용 모드. settings.yaml의 mode 값과 같다."""

    BASELINE = "baseline"          # 가드 없음
    PROMPT_ONLY = "prompt_only"    # 시스템 프롬프트만
    CODE_GUARD = "code_guard"      # 입력/출력 코드 검사
    FULL = "full"                  # 다층 가드레일 + 근거 검증


# 테스트셋의 set 컬럼에 허용되는 값
EVAL_SETS = ("dev", "pair", "holdout_a", "holdout_b")
