import os
import time
from typing import List, Dict
import streamlit as st
from openai import OpenAI

# ─────────────────────────────────────────────────────────────
# 기본 페이지 설정
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="📈 Buffett-Style AI Investment Copilot",
    page_icon="🦫",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ───────────────── 이미지 경로/URL & 폴백 유틸 ─────────────────
HERO_IMG_PATH = "/mnt/data/32d37cf6-cb03-4500-ab21-08ee05047b34.png"  # 주식/차트 로컬 이미지(있으면 사용)
HERO_IMG_FALLBACK = "https://images.unsplash.com/photo-1559526324-593bc073d938?q=80&w=1600"

SIDEBAR_LOGO_CANDIDATES = [
    "/mnt/data/7caadb76-f6de-44ce-875f-b736fa88f0a6.png",             # 로컬 1
    "/mnt/data/32d37cf6-cb03-4500-ab21-08ee05047b34.png",             # 로컬 2
    "https://images.unsplash.com/photo-1542228262-3d663b306035?q=80&w=400",  # URL 1
    "https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=400",  # URL 2
]

def show_sidebar_image():
    """사이드바 이미지: 로컬 → URL → 이모지 3단 폴백"""
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
# Session State 초기화
# ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages: List[Dict[str, str]] = []
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = (
        "너는 한국어로 답하는 '워렌 버핏 스타일의 가치투자' 금융투자 비서다. 다음 원칙을 반드시 지켜라.\n"
        "1) 면책: 너의 답변은 일반 정보 제공이며 투자 자문/권유가 아니다. 최종 판단과 책임은 사용자에게 있음을 명확히 하라.\n"
        "2) 핵심 철학: 안전마진(margin of safety), 해자(moat), 역량의 범위(circle of competence), 오너이익(owner earnings), "
        "장기보유(long-term), 합리적 가격, 단순·예측 가능한 사업, 현금흐름의 질을 중시하라.\n"
        "3) 분석 구조(항상 유지): (요약 4~6줄) → (핵심 근거 불릿) → (체크리스트 표) → (리스크/가정/추가확인) 순서로 제시하라.\n"
        "4) 체크리스트: 해자/현금흐름/부채/ROIC/자본배분/경영진 정합성/규제/환율/금리 민감도/사이클/거버넌스/희석 리스크.\n"
        "5) 수치 표현: 단위를 명확히(%, KRW, USD 등). 계산·평가모형 가정은 간단히 공개하라.\n"
        "6) 과도한 확신 금지: 보수/기준/공격 3가지 시나리오로 가정 값을 나누어 제시하라.\n"
        "7) 최신 데이터 필요 시 '추정'임을 표시하고, 원자료/재무제표/10-K 확인을 권고하라.\n"
    )
if "onboarding_open" not in st.session_state:
    st.session_state.onboarding_open = True

# ─────────────────────────────────────────────────────────────
# 상단 타이틀 & 배너
# ─────────────────────────────────────────────────────────────
left, right = st.columns([1, 2])
with left:
    st.title("📈 Buffett-Style AI Investment Copilot")
    st.caption("AI 에이전시용 가치투자 비서 · 저평가/현금흐름 중심 · 해자 점검 · 리스크 우선")
with right:
    if os.path.exists(HERO_IMG_PATH):
        st.image(HERO_IMG_PATH, use_container_width=True, caption="Clarity first, price second.")
    else:
        st.image(HERO_IMG_FALLBACK, use_container_width=True, caption="Clarity first, price second.")

st.divider()

# ─────────────────────────────────────────────────────────────
# 온보딩 패널
# ─────────────────────────────────────────────────────────────
def onboarding_panel():
    with st.container(border=True):
        st.subheader("🚀 시작하기: 챗봇 사용 방법")
        st.markdown(
            """
**버핏의 가치투자 원칙**(안전마진·해자·오너이익 등)을 내장한 금융투자 비서입니다.  

**1) API 키 입력**: 사이드바 또는 `secrets.toml`  
**2) 설정**: 모델 `gpt-4o-mini` 권장, temperature 0.1~0.3  
**3) 주요 기능**  
- 🧰 Buffett Screener: 체크리스트 + 간단 밸류  
- 📝 Investment Memo: 메모 템플릿 자동 생성  
- 💬 General Chat: 자유 질의응답

> ⚠️ 본 챗봇 답변은 일반 정보 제공이며 투자 자문/권유가 아닙니다.
"""
        )
        cols = st.columns([1,1,2,1])
        with cols[1]:
            if st.button("✅ 시작하기", use_container_width=True):
                st.session_state.onboarding_open = False
                st.rerun()
        with cols[2]:
            if st.button("ℹ️ 다음에도 보기", use_container_width=True):
                pass

if st.session_state.onboarding_open:
    onboarding_panel()
    st.stop()

# ─────────────────────────────────────────────────────────────
# OpenAI Key
# ─────────────────────────────────────────────────────────────
openai_api_key = st.secrets.get("OPENAI_API_KEY", "")
if not openai_api_key:
    openai_api_key = st.text_input("🔑 OpenAI API Key", type="password", help="secrets.toml에 OPENAI_API_KEY로 저장하면 입력창이 숨겨져요.")
if not openai_api_key:
    st.info("API 키를 입력하면 챗봇을 시작할 수 있습니다.", icon="🔒")
    st.stop()
client = OpenAI(api_key=openai_api_key)

# ─────────────────────────────────────────────────────────────
# 사이드바: 로고/설정/샘플/초기화
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    show_sidebar_image()  # ← 깨짐 방지 폴백 적용
    st.markdown("<h4 style='text-align:center; color:#F2D06B; font-weight:800; letter-spacing:0.2px; margin:0.4rem 0;'>Value · Moat · Cash Flow</h4>", unsafe_allow_html=True)

    st.header("⚙️ 설정")
    model = st.selectbox("모델 선택", ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"], index=0)
    temperature = st.slider("창의성(temperature)", 0.0, 1.0, 0.2, 0.1)
    max_tokens = st.slider("최대 생성 토큰", 256, 4096, 1400, 128)

    st.subheader("🎯 투자 성향 & 조건")
    risk_profile = st.radio("리스크 성향", ["보수적", "중립", "공격적"], index=0, horizontal=True)
    horizon = st.selectbox("투자 보유기간", ["1~2년", "3~5년", "5~10년+"], index=1)
    region = st.multiselect("지역", ["KR", "US", "JP", "EU", "EM"], default=["US", "KR"])
    sectors = st.multiselect("섹터", ["Technology", "Financials", "Industrials", "Energy", "Healthcare", "Consumer", "Utilities", "Materials"], default=["Technology","Consumer"])

    st.subheader("🧠 어시스턴트 톤")
    tone = st.radio("톤", ["중립/보수", "중립/균형", "기회발굴"], index=1, horizontal=True)
    tone_line = {
        "중립/보수": "안전마진을 최우선으로 삼고, 리스크를 먼저 식별/서술하라.",
        "중립/균형": "긍·부정 요인을 균형 있게 제시하되 핵심 변수를 강조하라.",
        "기회발굴": "저평가 구간/카탈리스트를 적극 탐색하되 리스크 경고를 명시하라."
    }[tone]

    st.subheader("✍️ 시스템 프롬프트(선택)")
    with st.expander("편집/커스터마이즈", expanded=False):
        edited = st.text_area("시스템 프롬프트", value=st.session_state.system_prompt, height=220)
        if st.button("적용"):
            st.session_state.system_prompt = edited
            st.success("시스템 프롬프트 적용 완료")

    if st.button("🧹 대화 초기화"):
        st.session_state.messages = []
        st.success("대화를 초기화했습니다.")
        st.rerun()

    st.subheader("💡 샘플 프롬프트")
    if st.button("• 버핏 스크리너(AAPL)"):
        st.session_state.messages.append({"role": "user", "content": "AAPL을 버핏 스크리너 체크리스트로 점검해줘."})
        st.rerun()
    if st.button("• 소비재 기업 메모 템플릿"):
        st.session_state.messages.append({"role": "user", "content": "소비재 기업 하나를 가정하고, 버핏 스타일 인베스트먼트 메모 템플릿을 채워줘."})
        st.rerun()

# ─────────────────────────────────────────────────────────────
# 도우미
# ─────────────────────────────────────────────────────────────
def trim_messages(messages: List[Dict[str, str]], max_pairs: int = 18) -> List[Dict[str, str]]:
    ua = [m for m in messages if m["role"] in ("user", "assistant")]
    if len(ua) <= 2 * max_pairs:
        return messages
    return ua[-2 * max_pairs :]

def build_messages() -> List[Dict[str, str]]:
    system_full = st.session_state.system_prompt + "\n" + f"추가 톤 지시: {tone_line}"
    history = trim_messages(st.session_state.messages, max_pairs=18)
    return [{"role": "system", "content": system_full}] + history

# ─────────────────────────────────────────────────────────────
# 탭: 📘 사용설명서 + 기존 3탭
# ─────────────────────────────────────────────────────────────
tabGuide, tab1, tab2, tab3 = st.tabs(["📘 사용설명서", "🧰 Buffett Screener", "📝 Investment Memo", "💬 General Chat"])

# 0) 사용설명서
with tabGuide:
    st.subheader("📘 ‘가치 투자의 정석’ 사용설명서")
    st.markdown("""
**이 앱은 버핏의 가치투자 원칙**을 기반으로 한 AI 투자 비서입니다.  

### 1) 시작 준비
- **OpenAI API Key**: 사이드바 또는 `secrets.toml`에 `OPENAI_API_KEY` 저장
- **권장 모델**: `gpt-4o-mini`
- **온보딩**: 처음 접속 시 ‘시작하기’ 버튼으로 안내를 마치면 본 화면으로 이동

### 2) 주요 기능
- **🧰 Buffett Screener**: 해자/현금흐름/ROIC/부채/자본배분 체크리스트 + 간단 밸류(보수·기준·공격)
- **📝 Investment Memo**: Thesis → Moat → Owner Earnings → Valuation → Risks → Catalysts → Monitoring → Verdict
- **💬 General Chat**: 자유 질의응답

### 3) 설정 팁
- **temperature** 0.1~0.3(보수적 분석 유리)  
- 리스크 성향/보유기간/지역/섹터는 답변에 반영됩니다.  
- **시스템 프롬프트**는 사이드바에서 수정 가능

### 4) 샘플 프롬프트
- “AAPL을 버핏 스크리너 체크리스트로 점검해줘.”
- “소비재 기업 하나 가정하고 버핏 스타일 메모 작성.”
- “배당 성장주를 안전마진 관점에서 보수·기준·공격 시나리오로 요약.”

### 5) 문제 해결(FAQ)
- **사이드바 로고가 깨짐** → 로컬→URL→이모지 **3단 폴백**으로 자동 대체됩니다. 로컬 이미지를 쓰려면 `/mnt/data/*.png`에 올려 주세요.  
- **API 오류/빈 응답** → API Key 확인, 모델 전환, 토큰 한도 조정, 프롬프트 길이 축소.  

### 6) 컴플라이언스
이 앱의 답변은 **일반 정보 제공**이며 **투자 자문/권유가 아닙니다.**  
최종 판단과 책임은 사용자에게 있으며, 세무/법률/회계는 전문가와 상담하세요.
""")

# 1) Screener
with tab1:
    st.subheader("🧰 버핏 스크리너 체크리스트")
    ticker = st.text_input("티커/기업명", placeholder="예: KO, AAPL, 삼성전자, 현대모비스")
    notes = st.text_area("선택: 참고 메모/최근 실적 요점(있으면 붙여넣기)", height=120)
    if st.button("스크리너 실행"):
        user_prompt = f"""
다음 기업을 '버핏 스크리너'로 점검해줘.
기업: {ticker}
참고메모: {notes}

출력 형식:
1) 5줄 요약
2) 핵심 근거 bullet (해자/현금흐름/부채/ROIC/오너이익/경영진/규제/환율·금리·사이클)
3) 체크리스트 표(항목/평가/간단이유) — 해자, 현금흐름의 질, 부채·이자보상, 자본배분, 규제·정책, 환율·금리 민감도, 거버넌스, 희석리스크
4) 간단 밸류에이션 스냅샷(보수/기준/공격) — 사용 가정(멀티플/DCF 단순 가정)과 결과 범위(가격 또는 EV/EBIT 수준)
5) 리스크/추가확인 목록

투자 성향: {risk_profile}, 보유기간: {horizon}, 지역: {', '.join(region)}, 섹터 선호: {', '.join(sectors)}
톤 가이드: {tone_line}
"""
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        st.rerun()

# 2) Memo
with tab2:
    st.subheader("📝 버핏 스타일 Investment Memo 템플릿")
    company = st.text_input("기업/티커", placeholder="예: BRK.B, AAPL, MSFT, NVDA")
    memo_hints = st.text_area("선택: 추가 힌트(제품/해자/가격대/이벤트 등)", height=120)
    if st.button("메모 생성"):
        user_prompt = f"""
'{company}'에 대한 '버핏 스타일 Investment Memo'를 작성해줘.
템플릿 요구사항:
- Thesis(핵심 논지) 4~6줄
- Business & Moat
- Unit Economics & Owner Earnings
- Capital Allocation
- Valuation(보수/기준/공격)
- Risks / Catalysts / Monitoring / Verdict

추가 힌트: {memo_hints}
투자 성향: {risk_profile}, 보유기간: {horizon}, 지역: {', '.join(region)}, 섹터 선호: {', '.join(sectors)}
톤 가이드: {tone_line}
"""
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        st.rerun()

# 3) General Chat
with tab3:
    st.subheader("💬 일반 대화")
    if len(st.session_state.messages) == 0:
        st.info("예) '배당 성장주 3가지 시나리오로 안전마진 관점 정리'")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    prompt = st.chat_input("무엇을 도와드릴까요? (예: ETF 리밸런싱 규칙 초안)")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})

# ─────────────────────────────────────────────────────────────
# 모델 호출 (스트리밍)
# ─────────────────────────────────────────────────────────────
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant"):
        placeholder = st.empty()
        try:
            stream = client.chat.completions.create(
                model=model,
                messages=[{"role": m["role"], "content": m["content"]} for m in build_messages()],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            response_text = st.write_stream(stream)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
        except Exception as e:
            placeholder.error(f"요청 중 오류가 발생했습니다: {e}")

# ─────────────────────────────────────────────────────────────
# 하단 주의 문구
# ─────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "※ 본 챗봇의 답변은 일반 정보 제공 목적이며, 투자 자문 또는 권유가 아닙니다. "
    "모든 투자 결정과 책임은 사용자 본인에게 있습니다. 세무/법률/회계 사항은 전문기관과 상의하세요."
)
