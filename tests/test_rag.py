"""[P1] 검색 모듈의 계약 수준 테스트. 실제 인덱스로 교체해도 통과해야 하는 성질만 검사한다."""
from src.contracts import Chunk
from src.rag import retrieve


def test_retrieve_returns_chunks_sorted_by_score_and_respects_k():
    results = retrieve("오버랩이 왜 필요해?", k=2)
    assert 1 <= len(results) <= 2
    assert all(isinstance(c, Chunk) for c in results)
    scores = [c.score for c in results]
    assert scores == sorted(scores, reverse=True)


def test_every_chunk_has_citation_metadata():
    for chunk in retrieve("청킹이 뭐야?", k=5):
        assert chunk.chunk_id and chunk.doc and chunk.text
