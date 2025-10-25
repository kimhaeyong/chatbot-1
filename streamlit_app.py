import streamlit as st

# ---------------------------- PAGE CONFIG ----------------------------
st.set_page_config(
    page_title="가치 투자의 정석",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------- COLOR THEME ----------------------------
COLOR_BG = "#FFFFFF"        # 전체 배경: 화이트
COLOR_TEXT = "#2B2B2B"      # 본문: 짙은 브라운
COLOR_ACCENT = "#A67C52"    # 포인트 브라운
COLOR_BORDER = "#EAE2D8"    # 옅은 베이지
COLOR_SUBTEXT = "#7A6E63"   # 서브 브라운톤

# 업로드된 주식 관련 이미지
HERO_IMG_PATH = "/mnt/data/6a74d4d3-1b27-4490-a69a-1d458689e170.png"

# ---------------------------- STYLING ----------------------------
st.markdown(f"""
<style>
/* 전체 배경 및 텍스트 */
html, body, [class*="css"] {{
  background-color: {COLOR_BG};
  color: {COLOR_TEXT};
  font-family: 'Pretendard', 'Noto Sans KR', sans-serif;
}}

/* 사이드바 */
section[data-testid="stSidebar"] > div {{
  background: linear-gradient(180deg, #FFFFFF 0%, #FFF6EB 100%);
  border-right: 1px solid {COLOR_BORDER};
}}

/* 버튼 */
.stButton > button {{
  background-color: {COLOR_ACCENT};
  color: #FFF;
  border: none;
  border-radius: 12px;
  padding: 0.55em 1.2em;
  font-weight: 600;
  box-shadow: 0 4px 10px {COLOR_ACCENT}33;
}}
.stButton > button:hover {{
  background-color: #8C633A;
  color: #FFF;
}}

/* 제목 스타일 */
.title-container {{
  background: rgba(255, 255, 255, 0.85);
  padding: 2rem 3rem;
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  backdrop-filter: blur(6px);
  width: fit-content;
}}
h1.title-text {{
  font-size: 2.6rem;
  color: {COLOR_TEXT};
  text-shadow: 1px 1px 4px rgba(0,0,0,0.1);
  margin-bottom: 0.4rem;
}}
p.subtitle {{
  color: {COLOR_SUBTEXT};
  font-size: 1rem;
  margin-top: 0.1rem;
}}

/* 이미지와 텍스트를 같은 줄에 배치 */
.image-container {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 40px;
}}
</style>
""", unsafe_allow_html=True)

# ---------------------------- HEADER ----------------------------
with st.container():
    st.markdown('<div class="image-container">', unsafe_allow_html=True)

    # 왼쪽 텍스트 영역
    st.markdown("""
    <div class="title-container">
        <h1 class="title-text">가치 투자의 정석</h1>
        <p class="subtitle">화이트 배경 · 브라운 포인트 · 워렌 버핏 원칙 기반 가치투자 비서</p>
    </div>
    """, unsafe_allow_html=True)

    # 오른쪽 이미지
    st.image(HERO_IMG_PATH, use_container_width=True, caption="Long-term mindset meets rational investing.")
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# ---------------------------- BODY ----------------------------
st.write("### 📘 소개")
st.write(
    """
    **‘가치 투자의 정석’**은 워렌 버핏의 투자 철학을 바탕으로 한 인공지능 투자 비서입니다.  
    이 앱은 기업의 내재가치 분석, 재무제표 요약, DCF 계산, 리스크 요약 등  
    **가치 중심의 투자 판단**을 돕는 다양한 도구를 제공합니다. 💹  
    """
)

st.info("👉 왼쪽 사이드바에서 모델과 투자 성향을 설정하세요.", icon="🎯")

# ---------------------------- SIDEBAR ----------------------------
with st.sidebar:
    st.image(HERO_IMG_PATH, caption="Value • Moat • Cash Flow", use_container_width=True)

    st.header("⚙️ 설정")
    st.selectbox("모델 선택", ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"], index=0)
    st.slider("창의성 (temperature)", 0.0, 1.0, 0.2, 0.1)
    st.slider("최대 생성 토큰", 256, 4096, 1024, 128)

    st.subheader("🎯 투자 성향")
    st.radio("리스크 성향", ["보수적", "중립", "공격적"], horizontal=True)
    st.selectbox("보유 기간", ["1~2년", "3~5년", "5~10년 이상"], index=1)
    st.multiselect("관심 지역", ["KR", "US", "JP", "EU"], default=["KR", "US"])

    st.divider()
    st.caption("Made with ❤️ for long-term investors")
