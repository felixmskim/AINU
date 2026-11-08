"""[P3 담당] 최종 답변 문자열 조립. 권장 형식: 핵심 답변 -> 쉬운 설명(비유) -> 근거 문서 -> 이해도 확인."""
from __future__ import annotations

from src.contracts import Chunk, TutorDraft


def _format_sources(citations: list[str], chunks: list[Chunk]) -> str:
    by_id = {c.chunk_id: c for c in chunks}
    lines = []
    for cid in dict.fromkeys(citations):   # 중복 제거, 순서 유지
        chunk = by_id.get(cid)
        if chunk is None:
            continue
        location = " · ".join(
            str(x) for x in (chunk.section, f"p.{chunk.page}" if chunk.page is not None else None) if x
        )
        line = f"- {chunk.doc}" + (f" ({location})" if location else "")
        if line not in lines:   # 같은 문서·같은 위치의 다른 조각은 한 줄로 표시
            lines.append(line)
    return "\n".join(lines)


def render_answer(draft: TutorDraft, chunks: list[Chunk]) -> str:
    parts = [draft.grounded_explanation.strip()]
    if draft.analogy:
        parts.append(f"쉬운 설명(비유): {draft.analogy.strip()}")
    sources = _format_sources(draft.citations, chunks)
    if sources:
        parts.append("근거 자료:\n" + sources)
    if draft.check_question:
        parts.append(f"이해 확인: {draft.check_question.strip()}")
    return "\n\n".join(parts)
