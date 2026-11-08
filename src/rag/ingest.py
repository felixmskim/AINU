"""[P1 담당] 사전 준비: 교육자료 -> 파싱 -> 청킹 -> 임베딩 -> 인덱스 저장.

질문이 오기 전에 한 번만 실행하는 스크립트다. 아직 구현되지 않았다.

실행(구현 후):  python -m src.rag.ingest
입력: data/raw/ (교육자료 원본, git 에 올리지 않음)   출력: data/index/ (인덱스, git 에 올리지 않음)

구현할 것 (docs/MODULES.md 의 P1 항목 참고)
  - 문서 구조를 보존하는 파싱, 의미 단위(단원/문단) 청킹, 적절한 크기와 overlap
  - 청크마다 chunk_id, doc, section, page 메타데이터 유지
  - 임베딩 후 벡터 저장소에 적재
"""


def main() -> None:
    raise NotImplementedError("P1: ingest 를 구현하세요 (docs/MODULES.md 참고)")


if __name__ == "__main__":
    main()
