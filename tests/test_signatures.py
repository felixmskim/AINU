"""각 담당자의 함수가 계약(시그니처)을 지키는지 한 번에 검사한다. 스텁을 진짜 구현으로 바꿔도 계속 통과해야 한다."""
from src.contracts import (
    InputGuard,
    LearnerAnalyzer,
    OutputGuard,
    Pipeline,
    RefusalComposer,
    RetrievalGuard,
    Retriever,
    TutorGenerator,
    assert_matches,
)
from src.guardrails.input import input_guard
from src.guardrails.output import output_guard
from src.guardrails.retrieval import retrieval_guard
from src.pipeline import ask
from src.rag import retrieve
from src.tutor.analyze import analyze_learner
from src.tutor.generate import generate
from src.tutor.refusal import compose_refusal


def test_every_module_function_matches_its_contract():
    assert_matches(input_guard, InputGuard)               # P2
    assert_matches(retrieve, Retriever)                   # P1
    assert_matches(retrieval_guard, RetrievalGuard)       # P1
    assert_matches(output_guard, OutputGuard)             # P1 + P2
    assert_matches(analyze_learner, LearnerAnalyzer)      # P3
    assert_matches(generate, TutorGenerator)              # P3
    assert_matches(compose_refusal, RefusalComposer)      # P3
    assert_matches(ask, Pipeline)                         # P3
