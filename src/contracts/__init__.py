"""팀 공용 계약. 다른 모듈은 항상 여기서 import 한다.

    from src.contracts import Chunk, GuardResult, Category, Action
"""
from .categories import EVAL_SETS, Action, Category, Intent, Level, Mode, Status
from .interfaces import (
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
from .schemas import (
    Chunk,
    Claim,
    GuardResult,
    LearnerAnalysis,
    LearnerState,
    StageRecord,
    TutorDraft,
    TutorResponse,
    Turn,
)

CONTRACT_VERSION = "0.1.1"   # 계약을 바꿀 때마다 올리고, 단체방에 공지한다

__all__ = [
    "EVAL_SETS", "Action", "Category", "Intent", "Level", "Mode", "Status",
    "InputGuard", "LearnerAnalyzer", "OutputGuard", "Pipeline", "RefusalComposer",
    "RetrievalGuard", "Retriever", "TutorGenerator", "assert_matches",
    "Chunk", "Claim", "GuardResult", "LearnerAnalysis", "LearnerState",
    "StageRecord", "TutorDraft", "TutorResponse", "Turn", "CONTRACT_VERSION",
]
