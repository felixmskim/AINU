"""모듈 사이를 오가는 데이터의 '모양'.

규칙
- 필드를 추가할 때는 반드시 기본값(Optional 또는 default)을 준다. 그러면 기존 코드가 깨지지 않는다.
- 필드 삭제와 이름 변경은 금지(필요하면 팀 합의 후 전원이 동시에 수정).
"""
from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from .categories import Action, Category, Intent, Level, Status


class Chunk(BaseModel):
    """교육자료 조각 하나. 검색(P1)이 만들고 모든 단계가 읽는다."""

    chunk_id: str                      # 예: "ragbook_p12_c3". 인용 검사의 기준이 되는 ID
    doc: str                           # 문서명
    section: Optional[str] = None      # 단원/절 제목
    page: Optional[int] = None
    text: str
    score: float = 0.0                 # 검색 유사도 (검색 단계에서만 채움)
    difficulty: Optional[Level] = None                       # 선택: 사전 준비 때 태깅
    prerequisites: list[str] = Field(default_factory=list)   # 선택: 선수 개념


class Turn(BaseModel):
    """대화 한 줄."""

    role: Literal["user", "tutor"]
    content: str


class GuardResult(BaseModel):
    """모든 가드(입력/검색/출력)가 돌려주는 공통 결과."""

    action: Action
    category: Category
    reason: str = ""                       # 사람이 읽는 이유 (내부 로그용, 정책 전문 노출 금지)
    sanitized_text: Optional[str] = None   # 입력 가드가 마스킹/정규화한 질문. 이후 단계는 이것을 사용
    score: Optional[float] = None          # 판정 확신도 등 (선택)

    @property
    def allowed(self) -> bool:
        return self.action == Action.PASS


class Claim(BaseModel):
    """답변 속 주장 하나와 그 근거. 출력 가드가 주장별로 검증한다."""

    text: str
    citations: list[str] = Field(default_factory=list)   # chunk_id 목록


class TutorDraft(BaseModel):
    """튜터가 만든 답변 초안 (출력 가드 통과 전)."""

    grounded_explanation: str                              # 교재 내용에 근거한 설명 (출처 필수, 엄격 검사)
    claims: list[Claim] = Field(default_factory=list)
    analogy: Optional[str] = None                          # 비유/쉬운 예시 (비유임을 표시, 완화 검사)
    citations: list[str] = Field(default_factory=list)     # 답변 전체의 chunk_id 목록
    check_question: Optional[str] = None                   # 이해도 확인 질문


class LearnerAnalysis(BaseModel):
    """질문 하나에 대한 학습자 분석 결과."""

    level: Level
    intent: Intent
    confidence: float = Field(ge=0.0, le=1.0)


class LearnerState(BaseModel):
    """대화(세션) 동안만 기억하는 학습자 메모장."""

    level: Level = Level.BEGINNER
    confused_count: int = 0
    hint_count: int = 0
    pending_check: Optional[dict[str, Any]] = None   # 낸 확인 질문 (아직 답을 못 받음)


class StageRecord(BaseModel):
    """파이프라인 한 단계의 기록. 평가 러너가 단계별 통계를 낼 때 쓴다."""

    stage: str                             # "input_guard" | "retrieval_guard" | "output_guard" 등
    result: Optional[GuardResult] = None
    latency_ms: float = 0.0


class TutorResponse(BaseModel):
    """pipeline이 사용자에게 돌려주는 최종 응답. 평가 러너도 이것을 입력으로 받는다."""

    status: Status
    text: str                              # 사용자에게 보여줄 최종 텍스트
    citations: list[str] = Field(default_factory=list)
    category: Category = Category.NORMAL   # 입력 가드가 판별한 종류
    sanitized_query: Optional[str] = None  # 가드가 마스킹한 질문. 대화 기록에는 원문 대신 이것을 저장한다
    trace: list[StageRecord] = Field(default_factory=list)
    llm_calls: int = 0                     # 비용 지표용
    latency_ms: float = 0.0                # 지연 지표용
