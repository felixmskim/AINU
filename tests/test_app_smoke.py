"""데모 화면이 에러 없이 뜨고, 질문 하나를 처리하는지 확인한다 (streamlit 이 없으면 건너뜀)."""
import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest

from src import config


def test_app_loads_and_answers_one_question():
    app = AppTest.from_file(str(config.ROOT / "app" / "streamlit_app.py"), default_timeout=30).run()
    assert not app.exception
    app.chat_input[0].set_value("오버랩이 왜 필요해?").run()
    assert not app.exception
    assert len(app.chat_message) == 2    # 사용자 질문 1개 + 튜터 답변 1개
