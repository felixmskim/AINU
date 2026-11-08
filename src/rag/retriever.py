"""[P1 담당] 검색: 질문과 가장 비슷한 교육자료 조각 k개를 돌려준다.

지금은 STUB: fixtures 의 샘플 청크를 '글자 2개 단위 겹침 비율'로 대충 정렬해서 돌려준다.
실제 교육자료 인덱스(임베딩 + 벡터 저장소)를 만들면 이 함수 안을 교체한다.
함수 이름과 시그니처(retrieve(query, k=5) -> list[Chunk])는 바꾸지 않는다.
"""
from __future__ import annotations

import json
from functools import lru_cache

from src import config
from src.contracts import Chunk


@lru_cache(maxsize=1)
def _fixture_chunks() -> tuple[Chunk, ...]:
    path = config.ROOT / config.get("paths.chunks_fixture", "fixtures/chunks.sample.json")
    rows = json.loads(path.read_text(encoding="utf-8"))
    return tuple(Chunk(**row) for row in rows)


def _bigrams(text: str) -> set[str]:
    compact = "".join(text.split())
    return {compact[i : i + 2] for i in range(len(compact) - 1)}


def retrieve(query: str, k: int = 5) -> list[Chunk]:
    query_grams = _bigrams(query)
    scored = []
    for chunk in _fixture_chunks():
        overlap = len(query_grams & _bigrams(chunk.text)) / max(len(query_grams), 1)
        scored.append(chunk.model_copy(update={"score": round(overlap, 3)}))
    scored.sort(key=lambda c: c.score, reverse=True)
    return scored[:k]
