# 계약 변경 제안 v0.2 (CONTRACT_VERSION 0.1.1 → 0.2.0)

> 상태: 제안 (2026-11-06). 반영은 P3가 팀 합의 후 한다 (`src/contracts/README.md` 절차).
> 모든 변경은 '추가'이고 기본값이 있어 기존 코드·픽스처·테스트를 깨지 않는다. 이름 변경·삭제는 없다.
> 배경: `docs/SPEC.md` §4.2–4.5

## 1. `categories.py`

```python
class ElementStatus(str, Enum):
    """요소별 이해 판정 (docs/design/학습수준_판별로직.md §7). 처리 실패는 여기에 넣지 않는다."""

    E = "E"    # 충족 증거 있음
    X = "X"    # 충돌 증거 있음
    U = "U"    # 확인 필요
    NA = "NA"  # 이번 판정 대상 아님


class ArtifactKind(str, Enum):
    """학습 출력물 종류 (docs/SPEC.md §4.5)."""

    NOTE_TXT = "note_txt"
    CARD_NEWS = "card_news"
    CONCEPT_MAP = "concept_map"
```

## 2. `schemas.py`

새 모델. `ElementDecision` 은 `LearnerState` 보다 위에 둔다 (`LearnerState` 가 참조).

```python
class ElementDecision(BaseModel):
    """확인 질문 답 하나에 대한 요소별 판정. 학습자 원문 인용이 코드로 확인된 경우에만 E/X."""

    element_id: str
    status: ElementStatus
    reason_code: Optional[str] = None    # MISSING_SUBJECT | MISSING_RELATION | CONDITION_UNOBSERVED
                                         # | EXPLICIT_ERROR | INTERNAL_CONFLICT | NO_EVIDENCE
    learner_quotes: list[str] = Field(default_factory=list)   # 검증된 학습자 원문 인용
    chunk_ids: list[str] = Field(default_factory=list)        # 기준이 된 교육자료 조각
    stage: str = "probe_response"        # initial | probe_response | after_hint
    approved_rubric: bool = False        # 질문 은행(팀 검토) 기준이면 True


class ArtifactItem(BaseModel):
    text: str
    kind: Literal["fact", "analogy", "question"] = "fact"
    citations: list[str] = Field(default_factory=list)       # fact 는 1개 이상 필수 (빌더가 검사)


class ArtifactSpec(BaseModel):
    kind: ArtifactKind
    title: str
    items: list[ArtifactItem] = Field(default_factory=list)
    edges: list[tuple[str, str, str]] = Field(default_factory=list)   # 개념도: (출발, 관계, 도착)
```

기존 모델에 필드 추가:

| 모델 | 필드 | 타입 · 기본값 | 용도 |
|---|---|---|---|
| `TutorDraft` | `check_points` | `list[str] = []` | 확인 질문의 필수 요소 (인용 범위 안) |
| `TutorDraft` | `check_element_id` | `Optional[str] = None` | 판정 요소 ID |
| `LearnerState` | `interests` | `list[str] = []` | 관심사 (최대 `tutor.max_interests`) |
| `LearnerState` | `element_decisions` | `dict[str, ElementDecision] = {}` | 세션 한정 판정 기록 |
| `LearnerState` | `last_chunks` | `list[Chunk] = []` | 직전 답의 근거 (후속 질문·판정용) |
| `TutorResponse` | `draft` | `Optional[TutorDraft] = None` | 검증 통과한 초안 (출력물 입력) |
| `TutorResponse` | `check_result` | `Optional[ElementDecision] = None` | 이번 턴 판정 |

`LearnerState.pending_check`(dict) 키: 기존 `question`, `chunk_ids` + 신규(선택) `element_id`, `check_points`, `approved`.

## 3. `interfaces.py`

import 변경:

```python
from typing import Any, Callable, Optional, Protocol

from .categories import ArtifactKind, Mode
from .schemas import (
    ArtifactSpec,
    Chunk,
    ElementDecision,
    GuardResult,
    LearnerAnalysis,
    LearnerState,
    StageRecord,
    TutorDraft,
    TutorResponse,
    Turn,
)
```

새 Protocol (`assert_matches` 위에 추가):

```python
class QueryRewriter(Protocol):
    def __call__(self, query: str, history: list[Turn], state: LearnerState) -> str:
        """후속 질문을 직전 맥락을 담은 독립 질문으로 바꾼다."""
        ...


class AnswerChecker(Protocol):
    def __call__(self, answer: str, pending_check: dict[str, Any], chunks: list[Chunk]) -> Optional[ElementDecision]:
        """확인 질문 답을 판정한다. None = 처리 실패(학습 상태 미발행)."""
        ...


class ArtifactBuilder(Protocol):
    def __call__(self, kind: ArtifactKind, responses: list[TutorResponse], state: LearnerState) -> ArtifactSpec:
        """검증 통과한 답변(responses[i].draft)으로 출력물 스펙을 만든다. 인용 없는 fact 항목은 버린다."""
        ...


class ArtifactRenderer(Protocol):
    def __call__(self, spec: ArtifactSpec) -> list[tuple[str, bytes]]:
        """(파일명, 내용) 목록을 돌려준다. LLM 호출 금지."""
        ...
```

| 함수 | 담당 | 위치 |
|---|---|---|
| `rewrite_query` | P3 | `src/tutor/rewrite.py` |
| `check_answer` | P3 | `src/tutor/check.py` |
| `build_artifact` | 배정 필요 | `src/artifacts/build.py` |
| `render_txt`, `render_cards`, `render_map` | 배정 필요 | `src/artifacts/` |

### 3.1 선택 항목: `Pipeline` 에 `on_stage` (검사 단계 실시간 표시, K6·I26)

넣지 않아도 다른 항목과 독립적이다. 넣지 않으면 화면은 대기 중 고정 문구만 보여 주고, 끝난 뒤 `response.trace` 로 단계를 표시한다.

```python
class Pipeline(Protocol):
    def __call__(
        self,
        query: str,
        *,
        mode: Mode = Mode.FULL,
        state: Optional[LearnerState] = None,
        history: Optional[list[Turn]] = None,
        on_stage: Optional[Callable[[StageRecord], None]] = None,   # 신규: 단계가 끝날 때마다 호출. 평가 러너는 None
    ) -> TutorResponse:
        ...
```

- `src/pipeline.py`: `ask()` 에 같은 매개변수 추가. `_timed()` 가 `trace` 에 기록한 직후 `on_stage(record)` 를 부른다 (None이면 생략).
- `tests/test_contracts.py::test_pipeline_signature_has_keyword_only_args` 의 더미 `ask` 에도 `on_stage=None` 을 추가해야 통과한다.
- 화면 사용 예 (P3, `app/streamlit_app.py`). 단계 이름만 보여 주고 `result.reason` 은 표시하지 않는다 (AGENTS 규칙 11). 답 본문은 검사가 끝난 뒤에만 표시한다 (규칙 10).

```python
STAGE_LABELS = {"input_guard": "질문 확인", "analyze_learner": "학습 상태 파악", "retrieve": "자료 찾기",
                "retrieval_guard": "근거 확인", "generate": "답변 작성", "output_guard": "근거 대조"}
with st.status("확인 중…") as box:
    response = ask(prompt, mode=Mode(mode_name), state=st.session_state.state, history=st.session_state.history,
                   on_stage=lambda record: st.write(f"✓ {STAGE_LABELS.get(record.stage, record.stage)}"))
    box.update(label="확인 완료", state="complete", expanded=False)
```

## 4. 반영 체크리스트

1. 1–3절 코드 추가 (`interfaces.py` import 변경 포함), `__init__.py` 의 import·`__all__` 에 새 이름 9개 추가 (`ElementStatus`, `ArtifactKind`, `ElementDecision`, `ArtifactItem`, `ArtifactSpec`, `QueryRewriter`, `AnswerChecker`, `ArtifactBuilder`, `ArtifactRenderer`), `CONTRACT_VERSION = "0.2.0"`.
2. `tests/test_contracts.py`: 새 모델 최소 생성, 기존 픽스처가 그대로 통과하는지. 3.1을 넣으면 더미 `ask` 시그니처 수정.
3. `tests/test_signatures.py`: 새 함수가 생기면 `assert_matches` 추가 (`rewrite_query` ↔ `QueryRewriter`, `check_answer` ↔ `AnswerChecker` 등).
4. `python -m pytest` 전체 통과 후 머지, 단체방 공지.

- 사전 확인 (2026-11-06, 스크래치 사본): 1–3절과 3.1을 모두 반영 → 49 passed, 1 skipped(Streamlit 미설치), 1 xfailed. 3.1을 넣고 더미 `ask` 를 고치지 않으면 `test_pipeline_signature_has_keyword_only_args` 1개 실패. `ask(on_stage=…)` 로 받은 단계 순서 = `response.trace` 순서, 콜백 없는 호출(평가 러너 경로) 정상. 새 모델 생성·JSON 왕복 정상.
