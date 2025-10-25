# app.py — Buffett & Quant Copilot (API key handling + image fallback hardened)
import os, re, urllib.request
from typing import List, Dict
import streamlit as st
from openai import OpenAI

st.set_page_config(
    page_title="가치 투자의 정석 — Buffett & Quant Copilot",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------- IMAGES & FALLBACK --------------------
HERO_IMG_PATH = "/mnt/data/32d37cf6-cb03-4500-ab21-08ee05047b34.png"
HERO_IMG_FALLBACK = "https://images.unsplash.com/photo-1559526324-593bc073d938?q=80&w=1600"
SIDEBAR_LOGO_CANDIDATES = [
    "/mnt/data/7caadb76-f6de-44ce-875f-b736fa88f0a6.png",
    "/mnt/data/32d37cf6-cb03-4500-ab21-08ee05047b34.png",
    "https://images.unsplash.com/photo-1542228262-3d663b306035?q=80&w=400",
    "https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=400",
]

def url_exists(url: str, timeout: float = 4.0) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return 200 <= getattr(r, "status", 200) < 300
    except Exception:
        return False

def show_sidebar_image():
    # 0) 사용자가 업로드한 로고가 있으면 최우선
    if "sidebar_logo_bytes" in st.session_state:
        st.image(st.session_state["sidebar_logo_bytes"], use_container_width=True)
        return
    # 1) 로컬
    for src in SIDEBAR_LOGO_CANDIDATES:
        if not src.startswith("http") and os.path.exists(src):
            st.image(src, use_container_width=True)
            return
    # 2) URL (가능한 경우에만)
    for src in SIDEBAR_LOGO_CANDIDATES:
        if src.startswith("http") and url_exists(src):
            st.image(src, use_container_width=True)
            return
    # 3) 최종 폴백: 이모지(깨진 아이콘 방지)
    st.markdown("<div style='text-align:center;font-size:44px;'>📈</div>", unsafe_allow_html=True)

# -------------------- STATE --------------------
if "buffett_messages" not in st.session_state:
    st.session_state.buffett_messages: List[Dict[str, str]] = []
if "quant_messages" not in st.session_state:
    st.session_state.quant_messages: List[Dict[str, str]] = []

BUFFETT_SYSTEM = (
    "너는 한국어로 답하는 '워렌 버핏 스타일' 가치투자 비서다.\n"
    "원칙: 안전마진, 해자, 역량의 범위, 오너이익, 장기보유, 합리적 가격, 단순·예측 가능한 사업, 현금흐름의 질.\n"
    "구성: 5줄 요약 → 핵심 근거 bullet → 체크리스트 표 → 밸류(보수/기준/공격) → 리스크/추가확인.\n"
    "수치 단위 명확히, 과도한 확신 금지, 불명확시 '추정' 표기 및 원자료 확인 권고.\n"
)
QUANT_SYSTEM = (
    "너는 한국어로 답하는 '퀀트 투자' 비서다.\n"
    "원칙: 규칙 기반, 데이터 청결, 학습/검증 분리, 거래비용·슬리피지 반영, 리스크 관리.\n"
    "구성: 4줄 요약 → 전략 정의(신호/리밸런스/포지션) → 백테스트 체크리스트 → 성과지표 → 리스크/주의점(+의사코드).\n"
)

# -------------------- HEADER --------------------
left, right = st.columns([1, 2])
with left:
    st.title("가치 투자의 정석 — Buffett & Quant Copilot")
    st.caption("두 개의 렌즈로 시장을 본다: 🧭 가치 · 📊 정량")
with right:
    if os.path.exists(HERO_IMG_PATH):
        st.image(HERO_IMG_PATH, use_container_width=True, caption="Clarity first, price second.")
    else:
        st.image(HERO_IMG_FALLBACK, use_container_width=True, caption="Clarity first, price second.")
st.divider()

# -------------------- API KEY (보안/검증/테스트) --------------------
def redact_api_key(text: str) -> str:
    # sk-xxxx, sk-proj-xxxx 형태를 마스킹
    return re.sub(r"sk-[a-zA-Z0-9_-]{8,}", "sk-•••(redacted)", text)

def looks_like_key(k: str) -> bool:
    # 너-무 엄격하게 막지 않고 기본적인 오타만 잡습니다.
    return k.startswith("sk-") and len(k) > 20

openai_api_key = st.secrets.get("OPENAI_API_KEY", "")
if not openai_api_key:
    openai_api_key = st.text_input("🔑 OpenAI API Key", type="password", key="api_key_input",
                                   help="`secrets.toml`에 OPENAI_API_KEY를 저장하면 입력창이 숨겨져요.")
if not openai_api_key:
    st.info("API 키를 입력하면 챗봇을 시작할 수 있습니다.", icon="🔒")
    st.stop()

col_key1, col_key2 = st.columns([1,1])
with col_key1:
    test_now = st.button("🔍 연결 테스트", help="모델 목록/간단 호출로 키 유효성을 확인합니다.")
with col_key2:
    remember_logo = st.file_uploader("사이드바 로고(선택)", type=["png","jpg","jpeg"], key="sidebar_logo_uploader")
    if remember_logo is not None:
        st.session_state["sidebar_logo_bytes"] = remember_logo.read()

client = None
if looks_like_key(openai_api_key):
    try:
        client = OpenAI(api_key=openai_api_key)
        if test_now:
            # 가벼운 호출로 유효성 확인 (예외는 아래 except에서 잡아서 친절 메시지로 표시)
            _ = client.models.list()
            st.success("✅ 연결 성공! 키가 유효합니다.")
    except Exception as e:
        msg = str(e)
        # 401/invalid_api_key 친절 메시지
        if "invalid_api_key" in msg or "Incorrect API key" in msg or "401" in msg:
            st.error(
                "❌ API 키가 유효하지 않습니다. 다음을 확인하세요.\n"
                "1) 키를 다시 복사/붙여넣기 (공백 제거)\n"
                "2) 올바른 **프로젝트 키** 사용 (`sk-...` / `sk-proj-...`)\n"
                "3) 조직/프로젝트 권한 확인\n"
                "4) 모델 접근 권한(gpt-4o-mini 등) 활성화\n"
                "오류 원문: " + redact_api_key(msg)
            )
            st.stop()
        else:
            st.error("요청 중 오류가 발생했습니다: " + redact_api_key(msg))
            st.stop()
else:
    st.warning("입력한 값이 OpenAI API 키 형식처럼 보이지 않습니다. `sk-`로 시작하는 키를 입력해 주세요.")
    st.stop()

# -------------------- SIDEBAR --------------------
with st.sidebar:
    show_sidebar_image()
    st.markdown(
        "<h4 style='text-align:center; color:#F2D06B; font-weight:800; letter-spacing:0.2px; margin:0.4rem 0;'>Value · Moat · Cash Flow</h4>",
        unsafe_allow_html=True
    )

    st.header("⚙️ 설정")
    model = st.selectbox("모델", ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"], index=0, key="model_sel")
    temperature = st.slider("창의성(temperature)", 0.0, 1.0, 0.2, 0.1, key="temp_slider")
    max_tokens = st.slider("최대 생성 토큰", 256, 4096, 1400, 128, key="max_tokens_slider")

    st.subheader("🎯 공통 프로필")
    risk_profile = st.radio("리스크 성향", ["보수적", "중립", "공격적"], index=1, horizontal=True, key="risk_radio")
    horizon = st.selectbox("보유기간", ["1~2년", "3~5년", "5~10년+"], index=1, key="horizon_sel")
    region = st.multiselect("지역", ["KR","US","JP","EU","EM"], default=["US","KR"], key="region_ms")
    sectors = st.multiselect(
        "섹터", ["Technology","Financials","Industrials","Energy","Healthcare","Consumer","Utilities","Materials"],
        default=["Technology","Consumer"], key="sectors_ms"
    )

    if st.button("🧹 대화 초기화", key="reset_all"):
        st.session_state.buffett_messages = []
        st.session_state.quant_messages = []
        st.success("두 탭의 대화를 모두 초기화했습니다.")
        st.rerun()

# -------------------- HELPERS --------------------
def trim_messages(messages: List[Dict[str, str]], max_pairs: int = 18) -> List[Dict[str, str]]:
    ua = [m for m in messages if m["role"] in ("user", "assistant")]
    return messages if len(ua) <= 2 * max_pairs else ua[-2 * max_pairs:]

def build_messages(tab: str) -> List[Dict[str, str]]:
    profile = f"투자 성향: {risk_profile}, 보유기간: {horizon}, 지역: {', '.join(region)}, 섹터: {', '.join(sectors)}"
    if tab == "buffett":
        system = BUFFETT_SYSTEM + "\n" + profile
        history = trim_messages(st.session_state.buffett_messages, 18)
    else:
        system = QUANT_SYSTEM + "\n" + profile
        history = trim_messages(st.session_state.quant_messages, 18)
    return [{"role": "system", "content": system}] + history

def stream_chat(messages: List[Dict[str, str]]):
    with st.chat_message("assistant"):
        placeholder = st.empty()
        try:
            stream = client.chat.completions.create(
                model=model,
                messages=[{"role": m["role"], "content": m["content"]} for m in messages],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            return st.write_stream(stream)
        except Exception as e:
            msg = str(e)
            # 401/키 문제는 친절 메시지로
            if "invalid_api_key" in msg or "Incorrect API key" in msg or "401" in msg:
                placeholder.error(
                    "❌ API 키 인증에 실패했습니다. 키를 다시 입력하거나 권한을 확인하세요.\n"
                    "오류: " + redact_api_key(msg)
                )
            else:
                placeholder.error("요청 중 오류가 발생했습니다: " + redact_api_key(msg))
            return ""

# -------------------- TABS --------------------
tabGuide, tabBuffett, tabQuant = st.tabs(["📘 사용설명서", "🧭 워렌 버핏 투자", "📊 퀀트 투자"])

with tabGuide:
    st.subheader("📘 ‘가치 투자의 정석’ 사용설명서")
    st.markdown("""
- **🧭 워렌 버핏 투자**: 해자·현금흐름·안전마진 중심 점검/메모/밸류 스냅샷  
- **📊 퀀트 투자**: 규칙 기반 전략 정의, 백테스트 가정, 성과·리스크 지표 해석  
모든 답변은 **일반 정보 제공**이며, 투자 자문/권유가 아닙니다.
""")

# Buffett
with tabBuffett:
    st.subheader("🧭 워렌 버핏 투자 — 가치 중심 점검")
    c1, c2 = st.columns([1.2, 1])
    with c1:
        ticker = st.text_input("티커/기업명", placeholder="예: KO, AAPL, 삼성전자", key="buffett_ticker")
        notes = st.text_area("선택: 참고 메모/최근 실적 요점", height=120, key="buffett_notes")
    with c2:
        st.info("프로필\n- 성향: {rp}\n- 보유: {hz}\n- 지역: {rg}\n- 섹터: {sc}".format(
            rp=risk_profile, hz=horizon, rg=", ".join(region), sc=", ".join(sectors)
        ))

    c3, c4, c5 = st.columns(3)
    with c3:
        if st.button("📋 버핏 스크리너 실행", key="buffett_screen_btn"):
            prompt = f"""
다음 기업을 버핏 스크리너로 점검해줘.
기업: {ticker}
참고메모: {notes}
출력: 5줄 요약 / 핵심 근거 bullet / 체크리스트 표 / 밸류 스냅샷(보수·기준·공격) / 리스크·추가확인
"""
            st.session_state.buffett_messages.append({"role": "user", "content": prompt})
    with c4:
        if st.button("📝 Investment Memo 생성", key="buffett_memo_btn"):
            prompt = f"""
'{ticker or '임의 기업'}'에 대한 버핏 스타일 투자 메모 작성.
Thesis → Business & Moat → Owner Earnings → Capital Allocation → Valuation(보수/기준/공격) → Risks → Catalysts → Monitoring → Verdict
"""
            st.session_state.buffett_messages.append({"role": "user", "content": prompt})
    with c5:
        if st.button("💬 질의하기(예시)", key="buffett_example_btn"):
            st.session_state.buffett_messages.append({"role": "user", "content": "장기 보유에 적합한 소비재 사업의 해자 유형과 리스크를 정리해줘."})

    for msg in st.session_state.buffett_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    b_prompt = st.chat_input("버핏 스타일로 무엇을 도와드릴까요?", key="buffett_input")
    if b_prompt:
        st.session_state.buffett_messages.append({"role": "user", "content": b_prompt})
    if st.session_state.buffett_messages and st.session_state.buffett_messages[-1]["role"] == "user":
        text = stream_chat(build_messages("buffett"))
        st.session_state.buffett_messages.append({"role": "assistant", "content": text})

# Quant
with tabQuant:
    st.subheader("📊 퀀트 투자 — 규칙 기반 전략 상담")
    st.markdown("전략 예시: **모멘텀 / 평균회귀 / 저변동성 / 가치·품질 믹스**")

    colq1, colq2 = st.columns(2)
    with colq1:
        strategy = st.selectbox("전략", ["모멘텀(12-1)", "평균회귀(단기 RSI/반전)", "저변동성", "가치·품질 팩터 믹스"], index=0, key="quant_strategy")
        rebalance = st.selectbox("리밸런싱 주기", ["월간", "분기", "연간"], index=0, key="quant_rebal")
        universe = st.selectbox("유니버스", ["KOSPI200", "S&P500", "NASDAQ100", "KR/US 혼합"], index=1, key="quant_universe")
    with colq2:
        fee = st.number_input("거래비용(왕복, bps)", min_value=0.0, value=10.0, step=5.0, key="quant_fee")
        slip = st.number_input("슬리피지(bps)", min_value=0.0, value=5.0, step=5.0, key="quant_slip")
        max_weight = st.slider("종목 최대 비중(%)", 1, 25, 10, 1, key="quant_maxw")

    q_cols = st.columns(3)
    with q_cols[0]:
        if st.button("🧠 전략 정의 요청", key="quant_define_btn"):
            prompt = f"""
아래 조건으로 퀀트 전략을 정의해줘.
전략: {strategy}, 리밸런싱: {rebalance}, 유니버스: {universe}
거래비용: {fee}bps, 슬리피지: {slip}bps, 종목 최대 비중: {max_weight}%
출력: 요약 / 전략 정의 / 백테스트 체크리스트 / 성과지표 해석 / 리스크 / 파이썬 의사코드
"""
            st.session_state.quant_messages.append({"role": "user", "content": prompt})
    with q_cols[1]:
        if st.button("📋 팩터 리서치 플랜", key="quant_research_btn"):
            st.session_state.quant_messages.append({"role": "user", "content": "밸류·퀄리티·모멘텀 3팩터 혼합 전략의 리서치 플랜을 단계별로 작성해줘(데이터 소스/정제/신호/검증/리스크/리포트 구조)."})
    with q_cols[2]:
        if st.button("💬 질의하기(예시)", key="quant_example_btn"):
            st.session_state.quant_messages.append({"role": "user", "content": "과최적화를 피하기 위한 검증 절차와 현실적인 거래비용 가정 범위를 정리해줘."})

    for msg in st.session_state.quant_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    q_prompt = st.chat_input("퀀트 관점으로 무엇을 도와드릴까요?", key="quant_input")
    if q_prompt:
        st.session_state.quant_messages.append({"role": "user", "content": q_prompt})
    if st.session_state.quant_messages and st.session_state.quant_messages[-1]["role"] == "user":
        text = stream_chat(build_messages("quant"))
        st.session_state.quant_messages.append({"role": "assistant", "content": text})

# -------------------- FOOTER --------------------
st.divider()
st.caption(
    "※ 본 앱의 답변은 일반 정보 제공 목적이며, 투자 자문 또는 권유가 아닙니다. "
    "모든 투자 결정과 책임은 사용자 본인에게 있습니다. 세무/법률/회계 사항은 전문기관과 상의하세요."
)
