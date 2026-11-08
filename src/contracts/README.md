# contracts/ 사용 규칙

이 폴더는 팀 전체의 약속이다. 코딩 에이전트를 포함해 누구도 마음대로 수정하지 않는다.

## 구성
| 파일 | 내용 |
|---|---|
| `categories.py` | 공용 용어 (요청 카테고리, 가드 결정, 학습자 수준, 모드 등) |
| `schemas.py` | 모듈 사이를 오가는 데이터의 모양 (Chunk, GuardResult, TutorDraft ...) |
| `interfaces.py` | 각 모듈 함수의 시그니처 + `assert_matches` 검사 도구 |
| `fixtures/` | 샘플 데이터. 앞 단계 모듈이 없어도 내 모듈을 혼자 테스트하기 위한 것 |

## 쓰는 법
- 항상 `from src.contracts import ...` 로 가져온다.
- 내 함수를 만든 뒤 테스트에 `assert_matches(내함수, 계약이름)` 을 넣는다.
- 개발할 때는 `fixtures/` 의 샘플을 입력으로 쓴다.

## 바꾸는 법
1. 단체방에 "무엇을, 왜 바꾸려는지" 올린다.
2. 새 필드 추가는 반드시 기본값을 줘서 기존 코드가 깨지지 않게 한다.
3. 필드 삭제/이름 변경/카테고리 변경은 전원 동의 후 한꺼번에 수정한다.
4. P3가 반영하고 `CONTRACT_VERSION` 을 올린 뒤 공지한다.
5. `python -m pytest tests/test_contracts.py` 가 통과해야 머지한다.
