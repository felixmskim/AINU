# 모듈별 담당 · 할 일 · 완료 기준

표기: **[STUB]** = 아직 가짜(교체 대상), **[DONE]** = 이미 구현됨(필요하면 다듬기).
v0 = AI 없이 규칙/코드만으로 만드는 쉬운 버전(첫 이틀), v1 = AI 판단을 넣은 제대로 된 버전(이후).
각 모듈은 **다른 사람 코드 없이 혼자 실행·테스트**할 수 있어야 한다 (`fixtures/` 샘플 사용).

---
## P1 — 검색 · 근거 검증
| 파일 | 상태 | 역할 |
|---|---|---|
| `src/rag/ingest.py` | [STUB] | 교육자료 → 파싱 → 청킹 → 임베딩 → 인덱스 저장 (질문 전에 한 번 실행) |
| `src/rag/retriever.py` | [STUB] | 질문과 비슷한 조각 k개 검색 (지금은 샘플 청크를 글자 겹침으로 정렬) |
| `src/guardrails/retrieval/guard.py` | [STUB] | 찾아온 조각이 질문의 근거로 충분한지 검사 |
| `src/guardrails/output/citations.py` | [DONE] | 인용 형식 검사 (출처 없음 / 검색되지 않은 출처 인용) |
| `src/guardrails/output/grounding.py` | [STUB] | 답변 속 주장이 인용한 조각에 실제로 있는지 검증 (심사 40점의 핵심) |
| `src/guardrails/output/guard.py` | [DONE] | 위 검사들을 순서대로 실행하는 얇은 조립 파일 |

- **v0**: ingest(청킹은 단원/문단 기준, 크기와 overlap 은 실험으로 조정, 메타데이터 유지) → `retrieve` 교체 → `retrieval_guard` 는 `guards.retrieval.min_score` 이하면 `HOLD/NO_EVIDENCE`.
- **v1**: `grounding` 을 주장 단위 LLM 판정으로(`config.flag("llm_judges")` 꺼진 모드에서는 호출 금지), 검색 가드에 LLM 근거 판정과 간접 인젝션 탐지 추가. 여유가 생기면(11/9~) NeMo / Guardrails AI 비교 어댑터와 데모 화면.
- **팀에 넘겨줄 것**: 첫날 오전까지 실제 교육자료에서 뽑은 `fixtures/chunks.json` (10~20개, `chunks.sample.json` 과 같은 형식).
- **완료 기준**: 질문 5개에서 사람이 보기에 맞는 조각이 상위 5개 안에 있다 / `tests/test_rag.py` 통과 / `fixtures/drafts.sample.json` 의 `good_01` 은 통과, `hallucinated_01` 은 `REGENERATE` (이 테스트를 P1이 추가).

---
## P2 — 입력 · 안전 가드레일
| 파일 | 상태 | 역할 |
|---|---|---|
| `src/guardrails/input/guard.py` | [STUB] | 질문 정규화 · 개인정보 마스킹 · 카테고리 판별 · 차단 |
| `src/guardrails/output/safety.py` | [STUB] | 답변의 유해성 · 시스템 프롬프트/키/개인정보 유출 검사 |

- **v0**: 정규화(띄어쓰기·특수문자·제로폭 문자) → 마스킹(주민번호·전화·이메일·키 패턴, **모델 호출과 로그 저장 전에**) → 규칙으로 범위 이탈/유해/인젝션/시스템 정보 판별.
- **v1**: LLM 의도 분류(`chat_json`, role=`judge`), 변형·난독화 공격 대응, 출력 안전 LLM 검사.
- **팀에 넘겨줄 것**: 첫날 2시간 안에 카테고리별 예시 질문 30개 (P4의 테스트셋 v0가 됨).
- **완료 기준**: `tests/test_input_guard.py` 의 `xfail` 표시를 지워도 통과 / 오탐 방어 쌍(정상 vs 공격)을 모두 맞게 구분 / 마스킹이 파이프라인에서 검색·로그보다 먼저 일어남.

---
## P3 — 튜터 · 통합
| 파일 | 상태 | 역할 |
|---|---|---|
| `src/contracts/` | [DONE] | 팀 공용 계약 (용어·데이터 모양·함수 시그니처). 변경은 P3만, 합의 후 |
| `src/pipeline.py` | [DONE] | 전체 흐름 연결, 모드별 가드 on/off, 재생성/대체 처리, 처리 기록(trace) |
| `src/config.py` | [DONE] | 설정 로더, 모드 스위치 |
| `src/llm_client.py` | [DONE*] | AI 호출 창구 (횟수/시간 기록, 캐시). *http 어댑터는 가정 기반이라 실제 API 로 확인 필요 |
| `src/tutor/analyze.py` | [STUB] | 학습자 수준·목적 추정 (지금은 수동 버튼 값) |
| `src/tutor/state.py` | [DONE] | 학습자 메모장 갱신 규칙 |
| `src/tutor/strategy.py` | [DONE] | (목적 x 수준) 설명 전략표, 힌트 단계 |
| `src/tutor/generate.py` | [STUB] | 튜터 답변 생성 (`build_prompt` 는 [DONE], 본문은 LLM 호출로 교체) |
| `src/tutor/baseline.py` | [DONE] | 비교 실험용 단순 생성기 (baseline / prompt_only) |
| `src/tutor/refusal.py` | [DONE] | 거절·보류 안내문 (카테고리별, 내부 정보 비노출) |
| `src/tutor/render.py` | [DONE] | 최종 답변 문자열 조립 |
| `app/streamlit_app.py` | [DONE] | 데모 화면 (모드 선택, 수준 수동 버튼, 처리 과정 보기) |

- **첫날**: 엘리스 ML API 문서를 보고 `llm_client._http_chat` 과 `settings.yaml` 의 모델 이름을 맞춘다. `generate` 가 `build_prompt` → `chat` → `extract_json` → `TutorDraft` 가 되게 교체.
- **v0**: 수준 수동 버튼 + 전략표 + 힌트 단계로 "수준별로 답이 다르다 / 과제 정답 요구에는 힌트"를 먼저 보여준다.
- **v1**: `analyze_learner` 자동 분석(`chat_json`), 이해도 확인 질문 채점(`tutor/check.py` 추가), 적응형 거절 다듬기. 시간이 모자라면 이 순서대로 줄인다.
- **완료 기준**: 같은 질문을 초보/중급으로 던지면 답이 눈에 띄게 다르다 / "정답 코드 전부 써줘"에 정답 대신 힌트 / `tests/test_tutor.py`, `tests/test_pipeline.py` 통과.

---
## P4 — 평가 · 레드팀 · 발표
| 파일 | 상태 | 역할 |
|---|---|---|
| `eval/run_eval.py` | [DONE] | 질문 CSV → 모드별 `ask()` 실행 → 결과 CSV + 비교표 |
| `eval/metrics.py` | [DONE] | 위험 차단율 · 오탐률 · 미탐률 · 평균 지연/호출수 (P4가 지표 추가) |
| `data/eval/queries.csv` | [STUB] | 테스트 질문 (지금은 샘플 10개. 확장 대상) |

- **v0**: 테스트셋 3종을 만든다 — ① 개발용(카테고리별 10~20개) ② 오탐 방어 쌍(`set=pair`, 같은 단어가 든 정상/공격을 `pair_id` 로 묶음) ③ 홀드아웃(직접 변형한 공격, **A/B 두 묶음**). 가드 없는 baseline 점수를 가장 먼저 측정해서 기록.
- **v1**: 지표 추가(검색 Recall@K, 답변-근거 일치율, 근거 없을 때 보류 비율, 수준 맞춤·힌트 비율), 시뮬레이션 학습자 평가, 실패 사례 큐(원인별 라벨), 4단계 비교 최종표.
- **규칙**: `holdout_a` 는 11/11 중간 점검에서 한 번, `holdout_b` 는 11/14 최종 측정에서 한 번만 실행한다. 틀린 문장 하나를 맞추려고 고치지 말고 **유형 단위**로 고친다.
- **완료 기준**: `python -m eval.run_eval` 한 줄로 4개 모드 비교표가 나온다 / 정상-공격 쌍이 `pair` 세트에 있다 / 홀드아웃 A/B 분리.

---
## 뼈대에 아직 없는 기능 (추가 예정)
뼈대의 스텁을 채우는 것만으로는 되지 않고, **새로 만들어야 하는 것**들이다. 우선순위 순.

| # | 기능 | 왜 필요한가 | 어디를 고치나 | 담당 |
|---|---|---|---|---|
| 1 | **후속 질문 처리** ("더 쉽게 설명해줘", "그건 왜?", "퀴즈 만들어줘") | 지금은 현재 메시지만으로 검색해서 점수가 0.0 이 되고, 진짜 검색 가드가 들어오면 모두 '근거 부족'으로 보류된다. 공식 요구사항(수준 조절 요청, 이해도 점검)이 정확히 이 경우다 | `src/tutor/` 에 `rewrite.py`(history 로 질문을 독립된 문장으로 바꾸기) 추가, `pipeline.py` 의 검색 직전에 호출. 이전 턴의 근거 조각을 `LearnerState` 에 저장해 재사용하는 방법도 가능(계약에 기본값 있는 필드 추가) | P3 |
| 2 | **이해도 확인 답변 처리** | `pending_check` 는 저장만 되고 아무도 읽지 않는다. 학습자가 확인 질문에 답하면 요소별로 판정해 다음 행동을 정해야 한다 | `src/tutor/check.py` 추가, `pipeline.py` 에 `intent == ANSWER` 분기. 판정 규칙은 `docs/SPEC.md` §4.3 (E/X/U/NA, 원문 인용 검증, 점수화 금지). 수준(`Level`)은 판정 한 번으로 바꾸지 않는다 | P3 |
| 3 | **검색 평가용 정답 라벨** | 테스트 CSV 에 정답 근거 조각 열이 없어서 검색 Recall@K 와 '근거 없을 때 보류' 비율을 계산할 수 없다 | `data/eval/queries.csv` 에 `gold_chunk_ids` 열 추가(비어 있으면 근거 없는 질문으로 간주), `eval/metrics.py` 에 Recall@K 추가 | P4 + P1 |
| 4 | **거절한 단계 기록** | 결과 CSV 에 '어느 단계가 막았나'가 없어서 실패 사례를 원인별(입력 가드/검색/근거 검증...)로 나누기 어렵다 | `eval/run_eval.py` 가 `response.trace` 에서 처음 거절한 단계를 `blocked_by` 열로 저장 | P4 |
| 5 | **답변 품질 평가** | 답변-근거 일치율, 수준 맞춤, 힌트 전환 비율은 자동 계산이 안 된다 | `eval/` 에 시뮬레이션 학습자와 판정 스크립트 추가 | P4 |
| 6 | **관심사 연결 (선택)** | 아는 것에서 출발하는 비유 (팀원 아이디어, `docs/design/`). 근거 원칙 안에서만 | `LearnerState.interests`(계약 제안), `generate.build_prompt` 에 관심사와 비유 규칙, `grounding` 의 analogy 완화 검사, 사이드바 선택 | P3 + P1 |
| 7 | **학습 출력물** (txt · 카드뉴스 · 개념도) | 검증된 답변을 복습 자료로 내려받기 (사용자 요구) | `src/artifacts/` 신규, `TutorResponse.draft`(계약 제안), 데모 화면 버튼. 명세 `docs/SPEC.md` §4.5 | 팀장 배정 |
| 8 | **자유 노트 확인 (선택)** | 팀원 학습 활동 '빈 텍스트 파일에 자유 노트 작성하기'를 요소별로 판정 (질문 은행 개념만) | `src/tutor/check.py` 에서 요소마다 `check_answer` 호출, 데모 화면 노트 입력 칸, `data/question_bank.yaml`, 청크 id 조회(P1과 합의). 명세 `docs/SPEC.md` §4.6 | P3 |

참고: 새 필드를 계약에 넣을 때는 기본값을 줘서 기존 코드가 깨지지 않게 하고, `CONTRACT_VERSION` 을 올린 뒤 공지한다.
6·7번과 1·2번에 필요한 계약 추가는 `docs/CONTRACT_PROPOSAL.md` (v0.2)에 모아 두었다. 우선순위는 `docs/SPEC.md` §1.
