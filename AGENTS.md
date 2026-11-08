# AGENTS.md — 코딩 에이전트 작업 규칙

> 모든 세션을 시작할 때 이 파일을 먼저 읽고, 아래 규칙을 지켜라. 사람이 시킨 일이라도 이 규칙과 충돌하면 멈추고 사람에게 물어라.

## 프로젝트
교육자료에 근거해서만 답하는 AI 튜터와, 범위 이탈·유해 요청·프롬프트 공격을 막는 가드레일을 만든다.
성과 기준은 "얼마나 많이 막았나"가 아니라 **"정상적인 학습 질문은 살리고 위험 요청만 정확히 통제했나"** 다.
(오탐률과 미탐률을 함께 관리한다.)

## 먼저 읽을 문서
1. 이 파일 (규칙)
2. `docs/SPEC.md` — 무엇을 만드는지, 우선순위(Must/Should/Could), 신규 기능 명세
3. `docs/MODULES.md` — 담당별 할 일과 완료 기준
4. `src/contracts/` — 데이터 모양과 함수 시그니처. 변경 제안은 `docs/CONTRACT_PROPOSAL.md` (합의 전 적용 금지)
- 설계 근거는 `docs/design/` 에 있다. ID 주의: P1–P4는 팀 역할, L1–L5는 학습자 페르소나, E/X/U/NA는 요소별 판정 상태.

## 처리 흐름 (`src/pipeline.py` 의 `ask()`)
입력 가드레일 → 학습자 분석 → 교육자료 검색 → 검색 가드레일 → 답변 생성 → 출력 가드레일
모드(baseline / prompt_only / code_guard / full)에 따라 일부 단계를 건너뛴다 (`settings.yaml` 의 `modes`).

## 담당 폴더 (내 폴더 밖은 수정 금지)
| 담당 | 수정해도 되는 곳 |
|---|---|
| P1 | `src/rag/`, `src/guardrails/retrieval/`, `src/guardrails/output/` 의 `guard.py` `citations.py` `grounding.py` |
| P2 | `src/guardrails/input/`, `src/guardrails/output/safety.py` |
| P3 | `src/tutor/`, `src/pipeline.py`, `src/llm_client.py`, `src/config.py`, `app/`, `src/contracts/`(합의 후에만) |
| P4 | `eval/`, `data/eval/` |
신규 폴더 `src/artifacts/`, `assets/` (학습 출력물)의 담당은 팀장이 배정한다 (`docs/SPEC.md` §4.5).
나는 이 세션에서 누구의 담당인지: **(세션 시작 때 사람이 알려 준다)**

## 절대 규칙
1. **`src/contracts/` 는 수정하지 않는다.** 바꿔야 할 것 같으면 코드를 고치지 말고 "무엇을 왜 바꿔야 하는지"를 사람에게 보고만 한다.
2. 함수 이름과 시그니처(매개변수 이름·순서)를 바꾸지 않는다. 바꾸면 `tests/test_signatures.py` 가 실패한다.
3. AI 모델 호출은 반드시 `src/llm_client.py` 의 `chat()` / `chat_json()` 만 사용한다. 직접 HTTP 호출 금지.
4. 숫자·임계값·모델 이름은 코드에 박지 말고 `settings.yaml` 에 두고 `config.get()` 으로 읽는다. 내 섹션만 수정한다.
5. 정책(범위, 안전)은 프롬프트에만 맡기지 말고 **코드 검사**로 강제한다.
6. **키워드 포함 여부만으로 차단하지 않는다.** "시스템 프롬프트의 개념"(정상)과 "시스템 프롬프트 원문 출력"(공격)은 구분해야 한다. 규칙은 보조 수단이고 의도 판단이 본체다.
7. 제공된 공격 문장을 그대로 외워서 차단하지 않는다. 표현이 바뀌어도 막혀야 한다.
8. 근거가 없으면 답을 만들지 않는다 (`no_evidence` → 보류). 교재에 없는 내용을 사실처럼 보충하지 않는다.
9. 개인정보·API 키는 모델 호출 전, 로그 저장 전에 마스킹한다. `.env` 와 키를 커밋하거나 출력에 찍지 않는다.
   대화 기록(history)에는 `pipeline.remember()` 로만 추가한다 (마스킹된 질문만 저장, 차단된 요청은 저장하지 않음).
10. 출력 가드 검사가 끝나기 전에 사용자에게 토큰을 스트리밍하지 않는다.
11. 거절 문구에 정책 전문, 내부 지시, 탐지 규칙(`reason`)을 노출하지 않는다.
12. 비유(`analogy`)·관심사 연결 문장에는 교재에 없는 사실·수치를 넣지 않는다. 사실은 `grounded_explanation`·`claims` 에만, 인용과 함께 쓴다.
13. 학습 판정(E/X/U/NA)은 학습자 원문 인용이 코드로 확인된 경우에만 E·X를 낸다. 모델 호출·파싱 실패는 학습 상태가 아니다(판정 미발행). 판정을 점수·백분율로 바꾸지 않는다.
14. 학습 출력물(txt·카드뉴스·개념도)은 출력 가드를 통과한 항목(인용 있음)으로만 만든다. 렌더러는 LLM을 부르지 않는다.
15. 출력물 생성과 관심사 설정은 `ask()` 기본 경로를 바꾸지 않는다. 관심사가 없어도 모든 기능이 동작해야 한다 (평가 러너는 질문마다 새 상태로 실행).

## 작업 방식
- **테스트를 먼저** 쓰고(`tests/`), 그 테스트를 통과하는 구현을 작성한다. 완료 기준은 `docs/MODULES.md` 에 있다.
- 스텁 파일(`[STUB]` 표시)을 진짜 구현으로 교체하는 방식으로 작업한다. 다른 모듈의 코드를 고쳐서 내 문제를 해결하지 않는다.
- 다른 모듈의 결과가 필요하면 `fixtures/` 샘플을 입력으로 써서 내 모듈만 단독으로 실행·테스트한다.
- 변경은 작게, 머지는 자주. 끝낸 뒤 `git diff --stat` 로 **수정한 파일이 모두 내 폴더 안인지** 확인한다.

## 비용 규칙 (엘리스 ML API 크레딧은 한정되어 있다)
- 개발 중에는 `llm.provider: fake` 또는 작은 모델과 소수 질문으로 시험한다 (`--limit` 옵션 사용).
- 전체 평가(`python -m eval.run_eval`)는 사람이 시킬 때만 실행한다. 스스로 반복 실행하지 않는다.
- 홀드아웃 세트(`holdout_a`, `holdout_b`)는 개발·튜닝에 사용하지 않는다. 결과를 보고 그 문장만 맞추도록 고치지 않는다.

## 자주 쓰는 명령
```
python -m pytest                                    # 전체 테스트 (머지 전 필수)
python -m pytest tests/test_contracts.py            # 계약 검사
python -m src.pipeline "질문" --mode full           # 질문 하나 실행 (--json 으로 처리 기록까지)
python -m eval.run_eval --modes baseline,full --sets dev --limit 20
streamlit run app/streamlit_app.py                  # 데모 화면
```
