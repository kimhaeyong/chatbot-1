import streamlit as st
from openai import OpenAI

# 제목 표시
st.title("💬 나만의 챗봇12")

# 🔑 OpenAI API Key 입력 (또는 secrets.toml에 저장 가능)
openai_api_key = st.secrets.get("OPENAI_API_KEY", "")
if not openai_api_key:
    openai_api_key = st.text_input("OpenAI API Key 입력", type="password")

# 키가 없으면 안내 메시지 표시 후 중단
if not openai_api_key:
    st.info("API 키를 입력해야 챗봇을 사용할 수 있습니다.", icon="🔒")
    st.stop()

# OpenAI 클라이언트 생성
client = OpenAI(api_key=openai_api_key)

# --- 세션 상태 초기화 (대화 기록 저장용)
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 🎛️ 사이드바 설정 (모델 선택 / 온도 설정)
st.sidebar.header("⚙️ 설정")
model = st.sidebar.selectbox("모델 선택", ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"])
temperature = st.sidebar.slider("창의성 (temperature)", 0.0, 1.5, 0.7)

# --- 🧹 대화 초기화 버튼 추가
if st.sidebar.button("🧹 대화 초기화"):
    st.session_state.messages = []
    st.success("대화가 초기화되었습니다.")
    st.rerun()

# --- 이전 대화 내용 표시
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 사용자 입력창
if prompt := st.chat_input("메시지를 입력하세요 ✏️"):

    # 사용자의 입력 저장 및 표시
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- GPT 모델로부터 응답 생성
    with st.chat_message("assistant"):
        try:
            stream = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                temperature=temperature,
                stream=True,  # 실시간 출력
            )
            response = st.write_stream(stream)
            # GPT 응답 저장
            st.session_state.messages.append({"role": "assistant", "content": response})
        except Exception as e:
            st.error(f"⚠️ 오류 발생: {e}")
