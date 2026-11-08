"""[P3 담당, 11/9 이후 P1이 이어받아 다듬기] 데모 화면 (Streamlit).

실행:  streamlit run app/streamlit_app.py
  - 사이드바에서 모드(4단계)와 학습자 수준(수동)을 고를 수 있다.
  - 답변 아래 '처리 과정'을 펼치면 단계별 결과(trace)가 보인다. 발표 때 가드 동작을 보여주기 좋다.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from src import config
from src.contracts import LearnerState, Level, Mode
from src.pipeline import ask, remember

st.set_page_config(page_title="안전벨트를 채운 AI 튜터", layout="centered")
st.title("안전벨트를 채운 AI 튜터")

if "state" not in st.session_state:
    st.session_state.state = LearnerState()
    st.session_state.history = []     # list[Turn]
    st.session_state.messages = []    # (role, text, response 또는 None)

with st.sidebar:
    modes = [m.value for m in Mode]
    mode_name = st.selectbox("모드", modes, index=modes.index(config.default_mode().value))
    level_choice = st.radio("학습자 수준 (수동)", [Level.BEGINNER.value, Level.INTERMEDIATE.value], key="level_choice")
    if st.session_state.get("_applied_level") != level_choice:   # 사용자가 버튼을 바꿨을 때만 덮어쓴다
        st.session_state.state.level = Level(level_choice)
        st.session_state["_applied_level"] = level_choice
    st.caption(f"현재 추정 수준: {st.session_state.state.level.value}")
    if st.button("대화 초기화"):
        st.session_state.state = LearnerState()
        st.session_state.history = []
        st.session_state.messages = []
        st.session_state.pop("_applied_level", None)
        st.rerun()

prompt = st.chat_input("질문을 입력하세요")
if prompt:
    response = ask(prompt, mode=Mode(mode_name), state=st.session_state.state, history=st.session_state.history)
    remember(st.session_state.history, response)   # 원문이 아니라 마스킹된 질문만 기록
    st.session_state.messages.append(("user", prompt, None))
    st.session_state.messages.append(("assistant", response.text, response))

for role, text, response in st.session_state.messages:
    with st.chat_message(role):
        st.write(text)
        if response is not None:
            with st.expander(f"처리 과정 (status={response.status.value}, {response.latency_ms:.0f}ms)"):
                for record in response.trace:
                    verdict = f"{record.result.action.value} / {record.result.category.value}" if record.result else ""
                    st.text(f"{record.stage:<16} {record.latency_ms:6.1f}ms  {verdict}")
