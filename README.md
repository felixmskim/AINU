# 안전벨트를 채운 AI 튜터

교육자료에 **근거해서만** 답하는 AI 튜터와, 범위 이탈·유해 요청·프롬프트 공격을 막는 **가드레일**을 만드는 프로젝트(AI 부트캠프 통합 경진대회).
성과 기준: 얼마나 많이 막았나가 아니라 **정상 학습 질문은 살리고 위험 요청만 정확히 통제했나**(오탐률·미탐률 동시 관리).

## 빠른 시작
```bash
pip install -r requirements.txt
python -m pytest                                      # 테스트 (처음엔 50 passed, 1 xfailed 가 정상. Streamlit 미설치 시 49 passed, 1 skipped, 1 xfailed)
python -m src.pipeline "chunk overlap이 왜 필요해?"      # 질문 하나 실행 (기본 모드)
python -m src.pipeline "질문" --mode baseline --json   # 모드 지정, 처리 기록까지 JSON 으로
python -m eval.run_eval                               # 4개 모드 비교표 + 결과 CSV
streamlit run app/streamlit_app.py                    # 데모 화면
```
처음에는 `settings.yaml` 의 `llm.provider: fake` 라서 API 키 없이 전체가 돈다. 실제 호출은 `.env.example` 을 `.env` 로 복사해 키를 채우고 `provider: http` 로 바꾼 뒤 사용한다 (`src/llm_client.py` 의 주의 사항 먼저 읽기).

## 요청 처리 흐름
```
질문
 → [입력 가드]  정규화 · 개인정보 마스킹 · 종류 판별 ──(위험/범위 이탈)──→ 안내문            status=blocked
 → [학습자 분석] 수준 · 목적 추정, 메모장 갱신  (튜터 모드만)
 → [검색]       교육자료에서 관련 조각 k개
 → [검색 가드]  근거로 충분한가? ──(부족)──────────────────────────────→ 답변 보류 + 질문 구체화    status=held
 → [생성]       근거 조각만으로 수준에 맞는 설명 + 힌트 + 이해 확인 질문
 → [출력 가드]  인용 형식 · 안전성 · 주장-근거 일치 ──(실패)──→ 1회 재생성 → 그래도 실패 시 안전 응답   status=fallback
 → 검증된 답변 + 출처                                                                          status=answered
```

## 4단계 비교 모드 (`settings.yaml` 의 `modes`)
같은 코드에서 스위치만 바꿔 비교 실험 조건 네 개를 만든다.
| 모드 | 입력/검색/출력 가드 | LLM 판정 | 튜터 기능 | 설명 |
|---|---|---|---|---|
| `baseline` | 모두 끔 | - | 끔 | 가드 없는 단순 RAG 챗봇 ("개선 전") |
| `prompt_only` | 모두 끔 | - | 끔 | "자료에 있는 것만 답해라" 지시문만 추가 |
| `code_guard` | 모두 켬 | 끔 | 켬 | 규칙/코드 검사만 |
| `full` | 모두 켬 | 켬 | 켬 | 다층 가드레일 + 근거 검증 + 튜터 |

## 지금 상태
| 구분 | 내용 |
|---|---|
| 구현됨 | 계약, 설정 로더, AI 호출 창구(fake 동작), 파이프라인(모드·차단·보류·재생성·대체), 전략표, 메모장 규칙, 프롬프트 조립, 거절 문구, 답변 조립, 비교용 단순 생성기, 인용 형식 검사, 평가 러너와 기본 지표, 데모 화면, 테스트 |
| 스텁(교체 대상) | 검색(샘플 기반), 자료 인제스트, 입력 가드, 검색 가드, 근거 일치 검증, 안전 검사, 학습자 분석, 튜터 생성 |
| 아직 없는 기능 | 후속 질문 처리, 이해도 확인 답변 채점, 검색 평가용 정답 라벨 등 (`docs/MODULES.md` 맨 아래 표) |
| 미검증 | `llm_client` 의 http 어댑터 (엘리스 ML API 형식을 가정해서 작성, 실제 API 로 시험하지 않음) |

스텁은 모두 "통과"시키므로 지금 비교표의 차단율이 0% 인 게 정상이다. 이게 나중에 개선 폭을 보여 줄 출발점이다.

## 프로젝트 구조
`[P1~P4]` = 담당, `스텁` = 교체 대상, `완료` = 구현됨. (`__init__.py` 는 생략)

```text
ai_tutor_skeleton/
├─ README.md                    # 프로젝트 소개 · 실행법 · 폴더 지도
├─ AGENTS.md                    # 코딩 에이전트 규칙 (세션마다 첨부)
├─ settings.yaml                # 모든 설정 + 4단계 모드 스위치
├─ requirements.txt             # 라이브러리 목록
├─ .env.example                 # API 키 양식 (복사해서 .env 로)
├─ .gitignore                   # 커밋 제외 목록
├─ .github/                     # GitHub 설정
│  └─ pull_request_template.md  # PR 체크리스트
├─ docs/                        # 팀 문서
│  ├─ SPEC.md                   # 구현 명세 (우선순위 · 신규 기능 · 출력물)
│  ├─ CONTRACT_PROPOSAL.md      # 계약 변경 제안 v0.2 (합의 전 적용 금지)
│  ├─ MODULES.md                # 모듈별 담당 · 할 일 · 완료 기준
│  ├─ TEAM_GUIDE.md             # 병렬 작업 규칙 · 일정 · 통합일 체크리스트
│  └─ design/                   # 설계 근거 (디자인 씽킹, 학습수준 판별, 학습 문서 안내, 관심사 연결)
├─ src/                         # 프로그램 본체
│  ├─ contracts/                # 팀 공용 계약 (설계도) — 수정은 P3만, 합의 후
│  │  ├─ README.md              # 계약 사용·변경 규칙
│  │  ├─ categories.py          # 공용 용어 (카테고리·결정·수준·모드)
│  │  ├─ interfaces.py          # 함수 시그니처 + assert_matches 검사 도구
│  │  └─ schemas.py             # 모듈 사이를 오가는 데이터 모양
│  ├─ guardrails/               # 가드레일 3종
│  │  ├─ input/                 # 입력 가드레일
│  │  │  └─ guard.py            # [P2·스텁] 정규화 · 마스킹 · 종류 판별 · 차단
│  │  ├─ output/                # 출력 가드레일
│  │  │  ├─ citations.py        # [P1·완료] 인용 형식 검사 (코드)
│  │  │  ├─ grounding.py        # [P1·스텁] 주장-근거 일치 검증
│  │  │  ├─ guard.py            # [P1·완료] 아래 검사들을 순서대로 실행
│  │  │  └─ safety.py           # [P2·스텁] 유해/유출 검사
│  │  └─ retrieval/             # 검색 가드레일
│  │     └─ guard.py            # [P1·스텁] 근거 충분성 검사
│  ├─ rag/                      # 검색
│  │  ├─ ingest.py              # [P1·스텁] 자료 → 청킹 → 임베딩 → 인덱스
│  │  └─ retriever.py           # [P1·스텁] 질문과 비슷한 조각 k개 검색
│  ├─ tutor/                    # 튜터
│  │  ├─ analyze.py             # [P3·스텁] 학습자 수준·목적 추정
│  │  ├─ baseline.py            # [P3·완료] 비교용 단순 생성기
│  │  ├─ generate.py            # [P3·스텁] 튜터 답변 생성 (build_prompt 는 완료)
│  │  ├─ refusal.py             # [P3·완료] 거절/보류 안내문
│  │  ├─ render.py              # [P3·완료] 최종 답변 문자열 조립
│  │  ├─ state.py               # [P3·완료] 학습자 메모장 갱신 규칙
│  │  └─ strategy.py            # [P3·완료] (목적 x 수준) 설명 전략표, 힌트 단계
│  ├─ config.py                 # [P3·완료] 설정 로더 · 모드 스위치
│  ├─ llm_client.py             # [P3·완료] AI 호출 창구 (횟수/시간 기록, 캐시)
│  └─ pipeline.py               # [P3·완료] 전체 흐름 연결 ask()
├─ app/                         # 데모 화면
│  └─ streamlit_app.py          # [P3·완료] Streamlit 데모
├─ eval/                        # 평가
│  ├─ results/                  # 평가 결과 CSV (git 제외)
│  ├─ metrics.py                # [P4·완료] 차단율 · 오탐률 · 지연 · 호출수
│  └─ run_eval.py               # [P4·완료] 질문 CSV → 모드별 실행 → 비교표
├─ data/                        # 데이터 (원본·인덱스는 git 제외)
│  ├─ eval/                     # 테스트 질문
│  │  └─ queries.csv            # [P4·스텁] 테스트 질문 (지금은 샘플 10개)
│  ├─ index/                    # 생성된 검색 인덱스
│  └─ raw/                      # 교육자료 원본을 넣는 곳
├─ fixtures/                    # 샘플 데이터 (앞 단계 없이 내 모듈 테스트용)
│  ├─ chunks.sample.json        # 샘플 교육자료 조각 (형식 예시)
│  ├─ drafts.sample.json        # 좋은 답변 / 환각 답변 샘플
│  └─ eval_queries.sample.csv   # 테스트 질문 형식 예시
└─ tests/                       # 테스트
   ├─ conftest.py               # 테스트는 항상 fake LLM 사용
   ├─ test_app_smoke.py         # 데모 화면 실행 검사
   ├─ test_contracts.py         # 계약·샘플 데이터 검사
   ├─ test_eval.py              # 평가 러너·지표 검사
   ├─ test_input_guard.py       # 입력 가드 + 완료 기준(xfail)
   ├─ test_llm_client.py        # AI 호출 창구 검사
   ├─ test_pipeline.py          # 차단/보류/재생성/대체 경로 검사
   ├─ test_rag.py               # 검색 계약 수준 검사
   ├─ test_signatures.py        # 모든 함수가 계약 시그니처를 지키는지
   └─ test_tutor.py             # 전략·메모장·프롬프트·거절 문구 검사
```

## 문서
- `AGENTS.md` — 코딩 에이전트 규칙 (모든 세션에 첨부)
- `docs/SPEC.md` — 구현 명세: 우선순위, 막힘 루프, 요소별 이해 판별, 관심사 연결, 학습 출력물(txt·카드뉴스·개념도)
- `docs/CONTRACT_PROPOSAL.md` — 계약 변경 제안 v0.2
- `docs/design/` — 설계 근거 문서
- `docs/TEAM_GUIDE.md` — 병렬 작업 규칙, 일정, 통합일 체크리스트
- `docs/MODULES.md` — 모듈별 담당, 할 일(v0/v1), 완료 기준
- `src/contracts/README.md` — 계약 사용·변경 규칙
