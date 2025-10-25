# app.py
# ─────────────────────────────────────────────────────────────
# Two-Track Investing Copilot: Warren Buffett vs. Quant
# - 📘 사용설명서 탭
# - 🧭 워렌 버핏 투자 탭 (가치투자 내장 프롬프트/샘플)
# - 📊 퀀트 투자 탭 (정량/팩터/전략 내장 프롬프트/샘플)
# - 사이드바 이미지 3단 폴백(로컬→URL→이모지), 대화 초기화
# ─────────────────────────────────────────────────────────────
import os
from typing import List, Dict
import streamlit as st
from openai import OpenAI

# 기본 페이지 설정
st.set_page_config(
    page_title="가치 투자의 정석 — Buffett & Quant Copilot",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 이미지 경로/URL & 폴백 유틸
HERO_IMG_PATH = "/mnt/data/32d37cf6-cb03-4500-ab21-08ee05047b34.png"  # 차트 이미지(있으면 사용)
HERO_IMG_FALLBACK = "https://images.unsplash.com/photo-1559526324-593bc073d938?q=80&w=1600"

SIDEBAR_LOGO_CANDIDATES = [
    "/mnt/data/7caadb76-f6de-44ce-875f-b736fa88f0a6.png",  # 로컬 후보1
    "/mnt/data/32d37cf6-cb03-4500-ab21-08ee05047b34.png",  # 로컬 후보2
    "https://images.unsplash.com/photo-1542228262-3d663b306035?q=80&w=400",  # URL 후보1
    "https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=400",  # URL 후보2
]

def show_sidebar_image():
    """사이드바 이미지: 로컬 → URL → 이모지 폴백"""
    for src in SIDEBAR_LOGO_CANDIDATES:
        try:
            if src.startswith("http"):
                st.image(src, use_container_width=True)
                return
            elif os.path.exists(src):
                st.image(src, use_container_width=True)
                return
        except Exception:
            continue
    st.markdown("<div style='text-align:center;font-size:44px;'>📈</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# Session State
# ─────────────────────────────────────────────────────────────
if "buffett_messages" not in st.session_state:
    st.session_state.buffett_messages: List[Dict[str, str]] = []
if "quant_messages" not in st.session_state:
    st.session_state.quant_messages: List[Dict[str, str]] = []

# 시스템 프롬프트 (탭별)
BUFFETT_SYSTEM = (
    "너는 한국어로 답하는 '워렌 버핏 스타일' 가치투자 비서다.\n"
    "원칙: 안전마진, 해자, 역량의 범위, 오너이익, 장기보유, 합리적 가격, 단순·예측 가능한 사업, 현금흐름의 질.\n"
    "구성(항상 유지): 5줄 요약 → 핵심 근거 bullet → 체크리스트 표(해자/현금흐름/부채/ROIC/자본배분/경영진/규제/환율·금리/사이클/거버넌스/희석) "
    "→ 밸류(보수/기준/공격) 가정과 결과 → 리스크/추가확인.\n"
    "수치 단위(%, KRW, USD) 명확히. 과도한 확신 금지. 최신 데이터가 불명확하면 '추정'으로 표기하고 원자료 확인 권고.\n"
)

QUANT_SYSTEM = (
    "너는 한국어로 답하는 '퀀트 투자' 비서다.\n"
    "원칙: 재현가능한 규칙, 데이터 청결, 학습/검증 분리, 거래비용/슬리피지 고려, 리스크 관리(DD, 변동성, 포트 리밸런스 규칙) 명시.\n"
    "구성(항상 유지): 4줄 요약 → 전략 정의(신호/리밸런싱/우선순위/포지션 크기) → 백테스트 체크리스트(기간/유니버스/수수료/슬리피지/거래규칙/리밸런스/위험지표) "
    "→ 성과지표(연복리/변동성/샤프/최대낙폭, AUM/현실성 코멘트) → 리스크/주의점.\n"
    "가능하면 의사코드(또는 파이썬 의사코드)로 규칙을 제시하고, 데이터 과최적화 경고를 명시하라.\n"
)

# ─────────────────────────────────────────────────────────────
# 헤더
# ─────────────────────────────────────────────────────────────
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

# ─────────────────────────────────────────────────────────────
# 온보딩(간략): API Key 입력 없으면 중단
# ─────────────────────────────────────────────────────────────
openai_api_key = st.secrets.get("OPENAI_API_KEY", "")
if not openai_api_key:
    openai_api_key = st.text_input("🔑 OpenAI API Key", type="password", help="secrets.toml에 OPENAI_API_KEY로 저장하면 입력창이 숨겨져요.")
if not openai_api_key:
    st.info("API 키를 입력하면 챗봇을 시작할 수 있습니다.", icon="🔒")
    st.stop()

client = OpenAI(api_key=openai_api_key)

# ─────────────────────────────────────────────────────────────
# 사이드바
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    show_sidebar_image()
    st.markdown("<h4 style='text-align:center; color:#F2D06B; font-weight:800; letter-spacing:0.2px; margin:0.4rem 0;'>Value · Moat · Cash Flow</h4>", unsafe_allow_html=True)

    st.header("⚙️ 설정")
    model = st.selectbox("모델", ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"], index=0)
    temperature = st.slider("창의성(temperature)", 0.0, 1.0, 0.2, 0.1)
    max_tokens = st.slider("최대 생성 토큰", 256, 4096, 1400, 128)

    st.subheader("🎯 공통 프로필")
    risk_profile = st.radio("리스크 성향", ["보수적", "중립", "공격적"], index=1, horizontal=True)
    horizon = st.selectbox("보유기간", ["1~2년","3~5년","5~10년+"], index=1)
    region = st.multiselect("지역", ["KR","US","JP","EU","EM"], default=["US","KR"])
    sectors = st.multiselect("섹터", ["Technology","Financials","Industrials","Energy","Healthcare","Consumer","Utilities","Materials"], default=["Technology","Consumer"])

    if st.button("🧹 대화 초기화"):
        st.session_state.buffett_messages = []
        st.session_state.quant_messages = []
        st.success("두 탭의 대화를 모두 초기화했습니다.")
        st.rerun()

# ─────────────────────────────────────────────────────────────
# 헬퍼
# ─────────────────────────────────────────────────────────────
def trim_messages(messages: List[Dict[str, str]], max_pairs: int = 18) -> List[Dict[str, str]]:
    ua = [m for m in messages if m["role"] in ("user", "assistant")]
    if len(ua) <= 2 * max_pairs:
        return messages
    return ua[-2 * max_pairs:]

def build_messages(tab: str) -> List[Dict[str, str]]:
    if tab == "buffett":
        system = BUFFETT_SYSTEM + f"\n투자 성향: {risk_profile}, 보유기간: {horizon}, 지역: {', '.join(region)}, 섹터: {', '.join(sectors)}"
        history = trim_messages(st.session_state.buffett_messages, 18)
    else:
        system = QUANT_SYSTEM + f"\n투자 성향: {risk_profile}, 보유기간: {horizon}, 지역: {', '.join(region)}, 섹터: {', '.join(sectors)}"
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
            placeholder.error(f"요청 중 오류가 발생했습니다: {e}")
            return ""

# ─────────────────────────────────────────────────────────────
# 탭 구성: 사용설명서 / 버핏 / 퀀트
# ─────────────────────────────────────────────────────────────
tabGuide, tabBuffett, tabQuant = st.tabs(["📘 사용설명서", "🧭 워렌 버핏 투자", "📊 퀀트 투자"])

# 0) 사용설명서
with tabGuide:
    st.subheader("📘 ‘가치 투자의 정석’ 사용설명서")
    st.markdown("""
두 개의 철학으로 시장을 봅니다.

- **🧭 워렌 버핏 투자**: 해자·현금흐름·안전마진 중심의 질적/정량 체크리스트와 밸류 스냅샷.  
- **📊 퀀트 투자**: 규칙 기반 전략 정의, 백테스트 가정 체크리스트, 성과·위험지표 해석.

**시작 방법**
1) 왼쪽에서 API Key와 모델/temperature를 설정  
2) 원하는 탭에서 질문하거나, 아래 샘플 버튼으로 시작

**주의**: 모든 답변은 일반 정보 제공입니다. 투자 자문·권유가 아니며 책임은 사용자에게 있습니다.
""")

# 1) 워렌 버핏 투자 탭
with tabBuffett:
    st.subheader("🧭 워렌 버핏 투자 — 가치 중심 점검")
    c1, c2 = st.columns([1.2, 1])
    with c1:
        ticker = st.text_input("티커/기업명", placeholder="예: KO, AAPL, 삼성전자")
        notes = st.text_area("선택: 참고 메모/최근 실적 요점", height=120)
    with c2:
        st.info("프로필\n- 성향: {rp}\n- 보유: {hz}\n- 지역: {rg}\n- 섹터: {sc}".format(
            rp=risk_profile, hz=horizon, rg=", ".join(region), sc=", ".join(sectors)
        ))

    c3, c4, c5 = st.columns(3)
    with c3:
        if st.button("📋 버핏 스크리너 실행"):
            prompt = f"""
다음 기업을 버핏 스크리너로 점검해줘.
기업: {ticker}
참고메모: {notes}

출력 형식:
1) 5줄 요약
2) 핵심 근거 bullet(해자/현금흐름/부채/ROIC/오너이익/경영진/규제/환율·금리·사이클)
3) 체크리스트 표(항목/평가/간단이유)
4) 밸류 스냅샷(보수/기준/공격) — 사용 가정 명시
5) 리스크/추가확인
"""
            st.session_state.buffett_messages.append({"role": "user", "content": prompt})
    with c4:
        if st.button("📝 Investment Memo 생성"):
            prompt = f"""
'{ticker or '임의 기업'}'에 대한 버핏 스타일 투자 메모를 작성해줘.
Thesis → Business & Moat → Owner Earnings → Capital Allocation → Valuation(보수/기준/공격) → Risks → Catalysts → Monitoring → Verdict
"""
            st.session_state.buffett_messages.append({"role": "user", "content": prompt})
    with c5:
        if st.button("💬 질의하기(예시)"):
            st.session_state.buffett_messages.append({"role": "user", "content": "장기 보유에 적합한 소비재 사업의 해자 유형과 리스크를 정리해줘."})

    # 히스토리 출력
    for msg in st.session_state.buffett_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 사용자 입력
    b_prompt = st.chat_input("버핏 스타일로 무엇을 도와드릴까요?", key="buffett_input")
    if b_prompt:
        st.session_state.buffett_messages.append({"role": "user", "content": b_prompt})

    # 모델 호출
    if st.session_state.buffett_messages and st.session_state.buffett_messages[-1]["role"] == "user":
        text = stream_chat(build_messages("buffett"))
        st.session_state.buffett_messages.append({"role": "assistant", "content": text})

# 2) 퀀트 투자 탭
with tabQuant:
    st.subheader("📊 퀀트 투자 — 규칙 기반 전략 상담")
    st.markdown("전략 예시: **모멘텀 / 평균회귀 / 저변동성 / 품질·가치 팩터 믹스**")

    colq1, colq2 = st.columns(2)
    with colq1:
        strategy = st.selectbox("전략", ["모멘텀(12-1)", "평균회귀(단기 RSI/반전)", "저변동성", "가치·품질 팩터 믹스"], index=0)
        rebalance = st.selectbox("리밸런싱 주기", ["월간", "분기", "연간"], index=0)
        universe = st.selectbox("유니버스", ["KOSPI200", "S&P500", "NASDAQ100", "KR/US 혼합"], index=1)
    with colq2:
        fee = st.number_input("거래비용(왕복, bps)", min_value=0.0, value=10.0, step=5.0)
        slip = st.number_input("슬리피지(bps)", min_value=0.0, value=5.0, step=5.0)
        max_weight = st.slider("종목 최대 비중(%)", 1, 25, 10, 1)

    q_cols = st.columns(3)
    with q_cols[0]:
        if st.button("🧠 전략 정의 요청"):
            prompt = f"""
아래 조건으로 퀀트 전략을 정의해줘.
전략: {strategy}, 리밸런싱: {rebalance}, 유니버스: {universe}
거래비용: {fee}bps, 슬리피지: {slip}bps, 종목 최대 비중: {max_weight}%

출력:
- 4줄 요약
- 전략 정의(신호/선정 규칙/리밸런싱 규칙/포지션 크기/현금 처리)
- 백테스트 체크리스트(기간/유니버스/수수료/슬리피지/거래규칙/리밸런스/위험지표)
- 성과지표 해석 가이드(연복리/변동성/샤프/최대낙폭)
- 리스크/주의점(과최적화, 거래비용 민감도 등)
- 파이썬 의사코드
"""
            st.session_state.quant_messages.append({"role": "user", "content": prompt})
    with q_cols[1]:
        if st.button("📋 팩터 리서치 플랜"):
            st.session_state.quant_messages.append({"role": "user", "content": "밸류·퀄리티·모멘텀 3팩터 혼합 전략의 리서치 플랜을 단계별로 작성해줘(데이터 소스/정제/신호/검증/리스크/리포트 구조)."})
    with q_cols[2]:
        if st.button("💬 질의하기(예시)"):
            st.session_state.quant_messages.append({"role": "user", "content": "과최적화를 피하기 위한 검증 절차와 현실적인 거래비용 가정 범위를 정리해줘."})

    # 히스토리 출력
    for msg in st.session_state.quant_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 사용자 입력
    q_prompt = st.chat_input("퀀트 관점으로 무엇을 도와드릴까요?", key="quant_input")
    if q_prompt:
        st.session_state.quant_messages.append({"role": "user", "content": q_prompt})

    # 모델 호출
    if st.session_state.quant_messages and st.session_state.quant_messages[-1]["role"] == "user":
        text = stream_chat(build_messages("quant"))
        st.session_state.quant_messages.append({"role": "assistant", "content": text})

# ─────────────────────────────────────────────────────────────
# 하단 고지
# ─────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "※ 본 앱의 답변은 일반 정보 제공 목적이며, 투자 자문 또는 권유가 아닙니다. "
    "모든 투자 결정과 책임은 사용자 본인에게 있습니다. 세무/법률/회계 사항은 전문기관과 상의하세요."
)
