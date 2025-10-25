# app.py
# ------------------------------------------------------------
# Cozy Winter Brown Theme — Buffett-Style AI Investment Copilot
# - 온보딩(사용방법) 첫 화면
# - 겨울/브라운 계열 감성 UI (커스텀 CSS)
# - 버핏 원칙 내장 시스템 프롬프트
# - 4 탭: Buffett Screener / Investment Memo / General Chat / DCF & Upload
# - 업로드(PDF/TXT) 요약·리스크 구조화(JSON) → 표 렌더링 + 다운로드
# - 간이 DCF 계산기(보수/기준/공격) + CSV 다운로드
# - 워치리스트 + 샘플 프롬프트 + 대화 초기화
# ------------------------------------------------------------
import os
import re
import io
import json
import time
from typing import List, Dict, Any, Optional

import streamlit as st
import pandas as pd

# PDF 텍스트 추출
try:
    from pypdf import PdfReader
    PDF_AVAILABLE = True
except Exception:
    PDF_AVAILABLE = False

from openai import OpenAI

# ========================== THEME SETTINGS ==========================
# (따뜻한 겨울 브라운 톤 팔레트)
COLOR_BG        = "#F7F1EA"  # 배경 아이보리-베이지
COLOR_BG_ALT    = "#EFE6DC"  # 사이드바/카드 배경
COLOR_TEXT      = "#3B2D26"  # 짙은 브라운 텍스트
COLOR_SUBTEXT   = "#5E4B3C"  # 서브 텍스트
COLOR_ACCENT    = "#A67C52"  # 메인 브라운 포인트
COLOR_ACCENT_2  = "#D9C3A3"  # 연한 브라운
COLOR_ACCENT_3  = "#8C633A"  # 버튼 hover/강조
COLOR_SUCCESS   = "#769E6F"  # 따뜻한 그린
COLOR_WARNING   = "#B2704E"  # 코퍼톤 경고

# 겨울 분위기의 따뜻한 이미지 (Unsplash 등)
HERO_IMG_URL     = "https://images.unsplash.com/photo-1517686469429-8bdb88b9f907?q=80&w=1600"  # 코지 겨울 무드(머그+니트)
SIDEBAR_LOGO_PATH = "/mnt/data/7caadb76-f6de-44ce-875f-b736fa88f0a6.png"  # 로컬 이미지가 있으면 사용
SIDEBAR_FALLBACK  = "https://images.unsplash.com/photo-1519681393784-d120267933ba?q=80&w=800"  # 코지 머그/책 이미지

# =========================== PAGE CONFIG ===========================
st.set_page_config(
    page_title="☕ Cozy Value Copilot (Winter Edition)",
    page_icon="🧣",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================= GLOBAL CSS ===========================
st.markdown(f"""
<style>
/* 배경 & 텍스트 */
html, body, [class*="css"] {{
  background-color: {COLOR_BG};
  color: {COLOR_TEXT};
  font-family: 'Noto Sans KR', 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Helvetica Neue', Arial, 'Apple Color Emoji','Segoe UI Emoji','Segoe UI Symbol', sans-serif;
}}

/* 사이드바 */
section[data-testid="stSidebar"] > div {{
  background: linear-gradient(180deg, {COLOR_BG_ALT} 0%, {COLOR_BG} 100%);
  border-right: 1px solid {COLOR_ACCENT_2}22;
}}

/* 헤더/캡션 */
h1, h2, h3, h4, h5 {{
  color: {COLOR_TEXT};
}}
p, span, label {{
  color: {COLOR_TEXT};
}}
small, .stCaption, .st-emotion-cache-1dp5vir p {{
  color: {COLOR_SUBTEXT} !important;
}}

/* 버튼 스타일 */
.stButton > button {{
  background-color: {COLOR_ACCENT};
  color: {COLOR_BG};
  border: none;
  border-radius: 12px;
  padding: 0.55em 1.0em;
  font-weight: 700;
  box-shadow: 0 4px 10px {COLOR_ACCENT}22;
}}
.stButton > button:hover {{
  background-color: {COLOR_ACCENT_3};
  color: #FFF;
  transform: translateY(-1px);
}}

/* 입력/셀렉트/슬라이더 */
.stTextInput > div > div > input,
.stTextArea textarea,
.stSelectbox > div > div > select,
.stRadio > div, .stMultiSelect > div > div {{
  background-color: #FFFFFF;
  color: {COLOR_TEXT};
  border-radius: 10px;
  border: 1px solid {COLOR_ACCENT_2}AA;
}}
.stSlider > div > div > div {{
  color: {COLOR_ACCENT};
}}
/* 카드 스타일 컨테이너 */
.block-container {{
  padding-top: 1.6rem;
}}
div[data-testid="stVerticalBlock"] > div[style*="border"] {{
  border: 1px solid {COLOR_ACCENT_2}77 !important;
  border-radius: 16px !important;
  background: {COLOR_BG_ALT} !important;
}}

/* 채팅 말풍선 */
.stChatMessage {{
  border-radius: 14px;
  padding: 0.8em 0.9em;
  background: #FFFFFF;
  border: 1px solid {COLOR_ACCENT_2}66;
  box-shadow: 0 2px 8px {COLOR_ACCENT}14;
}}
/* 구분선 */
hr, .stDivider {{
  border-color: {COLOR_ACCENT_2}66 !important;
}}
/* 알림 */
.stAlert > div {{
  background: #FFFFFF;
  border: 1px solid {COLOR_ACCENT_2}AA;
  border-radius: 12px;
}}

/* 데이터프레임 테이블 */
.stDataFrame, .stTable {{
  background: #FFFFFF;
  border-radius: 12px;
  border: 1px solid {COLOR_ACCENT_2}88;
}}

</style>
""", unsafe_allow_html=True)

# ========================= SESSION STATE ============================
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
        "8) 가능한 경우 JSON 구조(summary, bullets[], checklist[], valuation{{bear,base,bull}}, risks[])도 함께 반환하라.\n"
        "9) 어조는 겨울 시즌의 따뜻하고 차분한 톤으로 유지하라."
    )

if "onboarding_open" not in st.session_state:
    st.session_state.onboarding_open = True  # 첫 진입 시 사용방법 노출

if "profile" not in st.session_state:
    st.session_state.profile = {
        "risk": "보수적",
        "horizon": "3~5년",
        "region": ["US", "KR"],
        "sectors": ["Technology", "Consumer"],
        "watchlist": ["AAPL", "NVDA"]
    }

# ============================ HEADER AREA ============================
left, right = st.columns([1, 2])
with left:
    st.title("☕ Cozy Value Copilot — Winter Edition")
    st.caption("브라운 계열의 따뜻한 감성으로 함께하는 가치투자 비서")
with right:
    st.image(HERO_IMG_URL, use_container_width=True, caption="Warm thoughts, careful valuations.")

st.divider()

# ============================ ONBOARDING =============================
def onboarding_panel():
    with st.container(border=True):
        st.subheader("🧣 시작하기: 따뜻한 겨울 비서 사용 안내")
        st.markdown(f"""
**이 앱은 버핏의 가치투자 원칙**을 바탕으로, 겨울에 어울리는 **따뜻한 브라운 톤**으로 디자인된 투자 비서입니다.

**1) API 키 입력**  
좌측 사이드바 또는 `.streamlit/secrets.toml`에 `OPENAI_API_KEY`를 저장하세요.

**2) 설정**  
- 모델: `gpt-4o-mini` 권장 (빠르고 경제적)  
- temperature: 0.1~0.3 (보수적 분석에 유리)  
- 성향/보유기간/지역/섹터/톤 → 답변에 반영

**3) 주요 기능**  
- **🧰 Buffett Screener**: 티커 점검 + 체크리스트 + 간단 밸류 스냅샷  
- **📝 Investment Memo**: 투자 메모 템플릿 자동 생성  
- **💬 General Chat**: 자유 질의응답  
- **🧮 DCF & Upload**: PDF/TXT 업로드 요약 + 간이 DCF 계산기

**4) 대화 관리**  
- 좌측 **🧹 대화 초기화**로 기록을 정리하세요.  
- 워치리스트로 관심 종목을 모아둘 수 있어요.

> ⚠️ 이 앱의 답변은 일반 정보 제공이며, 투자 자문/권유가 아닙니다.  
> 최종 판단과 책임은 사용자에게 있으며, 세무/법률/회계는 전문가와 상의하세요.
        """)
        cols = st.columns([1, 1, 2, 1])
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

# ============================= OPENAI KEY ============================
openai_api_key = st.secrets.get("OPENAI_API_KEY", "")
if not openai_api_key:
    openai_api_key = st.text_input("🔑 OpenAI API Key", type="password", help="secrets.toml에 OPENAI_API_KEY로 저장하면 입력창이 숨겨져요.")
if not openai_api_key:
    st.info("API 키를 입력하면 챗봇을 시작할 수 있습니다.", icon="🔒")
    st.stop()
client = OpenAI(api_key=openai_api_key)

# =============================== SIDEBAR =============================
with st.sidebar:
    if os.path.exists(SIDEBAR_LOGO_PATH):
        st.image(SIDEBAR_LOGO_PATH, use_container_width=True)
    else:
        st.image(SIDEBAR_FALLBACK, use_container_width=True)

    st.markdown(
        f"<h4 style='text-align:center; color:{COLOR_ACCENT}; margin-top:0.5rem;'>Cozy · Careful · Compounding</h4>",
        unsafe_allow_html=True
    )

    st.header("⚙️ 설정")
    model = st.selectbox("모델 선택", ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"], index=0)
    temperature = st.slider("창의성(temperature)", 0.0, 1.0, 0.2, 0.1)
    max_tokens = st.slider("최대 생성 토큰", 256, 4096, 1400, 128)

    st.subheader("🎯 프로필")
    st.session_state.profile["risk"] = st.radio("리스크 성향", ["보수적", "중립", "공격적"],
                                                index=["보수적","중립","공격적"].index(st.session_state.profile["risk"]), horizontal=True)
    st.session_state.profile["horizon"] = st.selectbox("보유기간", ["1~2년","3~5년","5~10년+"],
                                                       index=["1~2년","3~5년","5~10년+"].index(st.session_state.profile["horizon"]))
    st.session_state.profile["region"] = st.multiselect("지역", ["KR","US","JP","EU","EM"], default=st.session_state.profile["region"])
    st.session_state.profile["sectors"] = st.multiselect(
        "섹터", ["Technology","Financials","Industrials","Energy","Healthcare","Consumer","Utilities","Materials"],
        default=st.session_state.profile["sectors"]
    )

    st.subheader("🧠 어시스턴트 톤")
    tone = st.radio("톤", ["중립/보수", "중립/균형", "기회발굴"], index=1, horizontal=True)
    tone_line = {
        "중립/보수": "안전마진을 최우선으로 삼고, 리스크를 먼저 식별/서술하라.",
        "중립/균형": "긍/부정 요인을 균형있게 제시하되, 핵심 변수를 강조하라.",
        "기회발굴": "저평가 구간/카탈리스트를 적극 탐색하되, 리스크 경고를 명시하라."
    }[tone]

    st.subheader("👀 워치리스트")
    wl_new = st.text_input("티커 추가", placeholder="예: AAPL")
    c1, c2 = st.columns([1,1])
    with c1:
        if st.button("추가"):
            if wl_new and wl_new.upper() not in st.session_state.profile["watchlist"]:
                st.session_state.profile["watchlist"].append(wl_new.upper())
                st.experimental_rerun()
    with c2:
        if st.button("초기화"):
            st.session_state.profile["watchlist"] = []

    st.write("📝", ", ".join(st.session_state.profile["watchlist"]) or "(비어있음)")

    if st.button("🧹 대화 초기화"):
        st.session_state.messages = []
        st.success("대화를 초기화했습니다.")
        st.rerun()

    st.subheader("💡 샘플 프롬프트")
    if st.button("• 버핏 스크리너로 KO 점검"):
        st.session_state.messages.append({"role": "user", "content": "KO를 버핏 스크리너 체크리스트로 점검해줘."})
        st.rerun()
    if st.button("• 겨울 시즌 소비재 시나리오"):
        st.session_state.messages.append({"role":"user", "content":"겨울 시즌 소비재(의류/식음료) 섹터를 보수/기준/공격 3가지 시나리오로 정리해줘."})
        st.rerun()

# ============================= HELPERS ===============================
def trim_messages(messages: List[Dict[str, str]], max_pairs: int = 18) -> List[Dict[str, str]]:
    ua = [m for m in messages if m["role"] in ("user", "assistant")]
    if len(ua) <= 2 * max_pairs:
        return messages
    return ua[-2 * max_pairs:]

def parse_json_block(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    fence = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    raw = fence.group(1) if fence else None
    if not raw:
        brace = re.search(r"(\{.*\})", text, flags=re.DOTALL)
        raw = brace.group(1) if brace else None
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None

def extract_text_from_pdf(file) -> str:
    if not PDF_AVAILABLE:
        return ""
    try:
        reader = PdfReader(file)
        texts = []
        for page in reader.pages:
            texts.append(page.extract_text() or "")
        return "\n".join(texts)
    except Exception:
        return ""

def simple_dcf_scenarios(
    revenue: float, op_margin: float, tax_rate: float, reinvest_rate: float, shares_out: float,
    wacc_bear: float, wacc_base: float, wacc_bull: float,
    g_bear: float, g_base: float, g_bull: float,
    horizon_years: int = 5
) -> pd.DataFrame:
    def scenario_calc(name, wacc, g):
        ebit = revenue * op_margin
        nopat = ebit * (1 - tax_rate)
        fcf = nopat * (1 - reinvest_rate)    # 단순화된 FCF
        if wacc <= g:
            tv = float('nan')
        else:
            tv = fcf * (1 + g) / (wacc - g)  # 터미널 가치
        pv_fcf = fcf / (1 + wacc)            # 1년 뒤 FCF 할인
        pv_tv = tv / ((1 + wacc) ** horizon_years) if tv == tv else float('nan')
        ev = pv_fcf + pv_tv
        price_per_share = ev / max(shares_out, 1e-6)
        return {"scenario": name, "WACC": wacc, "g": g, "FCF(yr1)": fcf, "EV(PV)": ev, "Price/Share": price_per_share}
    rows = [
        scenario_calc("보수", wacc_bear, g_bear),
        scenario_calc("기준", wacc_base, g_base),
        scenario_calc("공격", wacc_bull, g_bull),
    ]
    return pd.DataFrame(rows)

def build_messages(tone_line_: str) -> List[Dict[str, str]]:
    system_full = st.session_state.system_prompt + "\n" + f"추가 톤 지시: {tone_line_}"
    history = trim_messages(st.session_state.messages, max_pairs=18)
    return [{"role": "system", "content": system_full}] + history

def call_chat(messages: List[Dict[str, str]], stream: bool = True) -> str:
    with st.chat_message("assistant"):
        placeholder = st.empty()
        try:
            if stream:
                rstream = client.chat.completions.create(
                    model=model,
                    messages=[{"role": m["role"], "content": m["content"]} for m in messages],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True,
                )
                response_text = st.write_stream(rstream)
            else:
                resp = client.chat.completions.create(
                    model=model,
                    messages=[{"role": m["role"], "content": m["content"]} for m in messages],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                response_text = resp.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            return response_text
        except Exception as e:
            placeholder.error(f"요청 중 오류가 발생했습니다: {e}")
            return ""

# =============================== TABS ================================
tab1, tab2, tab3, tab4 = st.tabs([
    "🧰 Buffett Screener", "📝 Investment Memo", "💬 General Chat", "🧮 DCF & Upload"
])

# 1) Screener
with tab1:
    st.subheader("🧰 버핏 스크리너 체크리스트")
    c1, c2 = st.columns([1.2, 1])
    with c1:
        ticker = st.text_input("티커/기업명", placeholder="예: KO, AAPL, 삼성전자, 현대모비스")
        notes = st.text_area("선택: 참고 메모/최근 실적 요점(있으면 붙여넣기)", height=140,
                             placeholder="최근 분기 하이라이트, 매출/영업이익/FCF 추세, 가격레벨, 이슈 등")
    with c2:
        st.info("프로필 요약\n- 성향: {risk}\n- 보유: {hz}\n- 지역: {rg}\n- 섹터: {sc}".format(
            risk=st.session_state.profile["risk"],
            hz=st.session_state.profile["horizon"],
            rg=", ".join(st.session_state.profile["region"]),
            sc=", ".join(st.session_state.profile["sectors"])
        ))

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
6) JSON도 함께 반환: keys = summary, bullets[], checklist[], valuation{{bear,base,bull}}, risks[]

투자 성향: {st.session_state.profile["risk"]}, 보유기간: {st.session_state.profile["horizon"]}, 지역: {', '.join(st.session_state.profile["region"])}, 섹터 선호: {', '.join(st.session_state.profile["sectors"])}
톤 가이드: {tone_line}
"""
        st.session_state.messages.append({"role":"user","content":user_prompt})
        text = call_chat(build_messages(tone_line_=tone_line), stream=True)
        data = parse_json_block(text)
        if data:
            st.write("### 📦 구조화 결과(JSON)")
            if "summary" in data:
                st.markdown("**요약**: " + str(data["summary"]))
            if "bullets" in data and isinstance(data["bullets"], list):
                st.markdown("**핵심 근거:**")
                for b in data["bullets"]:
                    st.markdown(f"- {b}")
            if "checklist" in data and isinstance(data["checklist"], list):
                st.dataframe(pd.DataFrame(data["checklist"]), use_container_width=True)
            if "valuation" in data and isinstance(data["valuation"], dict):
                val_df = pd.DataFrame.from_dict(data["valuation"], orient="index").reset_index().rename(columns={"index":"Scenario"})
                st.dataframe(val_df, use_container_width=True)
            if "risks" in data and isinstance(data["risks"], list):
                st.markdown("**리스크**")
                for r in data["risks"]:
                    st.markdown(f"- {r}")
            raw_md = io.StringIO()
            raw_md.write("# Buffett Screener 결과\n\n")
            raw_md.write(text)
            st.download_button("⬇️ 원문 저장(.md)", data=raw_md.getvalue(), file_name=f"screener_{ticker}.md", mime="text/markdown")
            st.download_button("⬇️ JSON 저장(.json)", data=json.dumps(data, ensure_ascii=False, indent=2), file_name=f"screener_{ticker}.json", mime="application/json")

# 2) Memo
with tab2:
    st.subheader("📝 버핏 스타일 Investment Memo 템플릿")
    company = st.text_input("기업/티커", placeholder="예: BRK.B, AAPL, MSFT, NVDA")
    memo_hints = st.text_area("선택: 추가 힌트(제품/해자/가격대/이벤트 등)", height=120)
    if st.button("메모 생성"):
        user_prompt = f"""
'{company}'에 대한 '버핏 스타일 Investment Memo'를 작성해줘.
템플릿 요구사항:
- 1. Thesis(핵심 논지) — 4~6줄
- 2. Business & Moat — 제품/브랜드/네트워크/규모/규제/전환비용 등
- 3. Unit Economics & Owner Earnings — 매출/마진/CAPEX/FCF/오너이익 개념
- 4. Capital Allocation — 배당/자사주/인수/R&D, ROIC 추세
- 5. Valuation — 보수/기준/공격 3가지(멀티플 또는 간이 DCF) + 가정치 명시
- 6. Risks — 금리/환율/규제/사이클/경쟁/기술/희석/지배구조
- 7. Catalysts — 리프라이싱 트리거(신제품/정책/가격인상/점유율 등)
- 8. Monitoring — 분기별 체크 포인트
- 9. Verdict — 요약 코멘트(가치 대비 가격, 안전마진 관점)
- 10) JSON도 함께 반환: keys = thesis, moat, unit, capital, valuation{{bear,base,bull}}, risks[], catalysts[], monitoring[], verdict

추가 힌트: {memo_hints}
투자 성향: {st.session_state.profile["risk"]}, 보유기간: {st.session_state.profile["horizon"]}, 지역: {', '.join(st.session_state.profile["region"])}, 섹터 선호: {', '.join(st.session_state.profile["sectors"])}
톤 가이드: {tone_line}
"""
        st.session_state.messages.append({"role":"user","content":user_prompt})
        text = call_chat(build_messages(tone_line_=tone_line), stream=True)
        data = parse_json_block(text)
        if data:
            st.write("### 📦 구조화 결과(JSON)")
            if "valuation" in data:
                st.dataframe(pd.DataFrame.from_dict(data["valuation"], orient="index").reset_index().rename(columns={"index":"Scenario"}), use_container_width=True)
            for key in ["thesis","moat","unit","capital","verdict"]:
                if key in data:
                    st.markdown(f"**{key.capitalize()}**")
                    st.write(data[key])
            if "risks" in data:
                st.markdown("**Risks**"); [st.markdown(f"- {r}") for r in data["risks"]]
            if "catalysts" in data:
                st.markdown("**Catalysts**"); [st.markdown(f"- {c}") for c in data["catalysts"]]
            if "monitoring" in data:
                st.markdown("**Monitoring**"); [st.markdown(f"- {m}") for m in data["monitoring"]]
            raw_md = io.StringIO(); raw_md.write("# Investment Memo\n\n"); raw_md.write(text)
            st.download_button("⬇️ 원문 저장(.md)", data=raw_md.getvalue(), file_name=f"memo_{company}.md", mime="text/markdown")
            st.download_button("⬇️ JSON 저장(.json)", data=json.dumps(data, ensure_ascii=False, indent=2), file_name=f"memo_{company}.json", mime="application/json")

# 3) General Chat
with tab3:
    st.subheader("💬 일반 대화")
    if len(st.session_state.messages) == 0:
        st.info("겨울의 차분한 톤으로 가치투자 질문을 시작해보세요. 예) '배당 성장주 3가지 시나리오로 안전마진 관점 정리'")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    prompt = st.chat_input("무엇을 도와드릴까요?")
    if prompt:
        st.session_state.messages.append({"role":"user","content":prompt})
        call_chat(build_messages(tone_line_=tone_line), stream=True)

# 4) DCF & Upload
with tab4:
    st.subheader("🧮 간이 DCF & 📎 업로드 분석")
    lcol, rcol = st.columns([1,1])

    # 업로드 분석
    with lcol:
        st.markdown("### 📎 10-K/IR 자료 업로드 요약")
        uploaded = st.file_uploader("PDF 또는 텍스트 업로드", type=["pdf","txt"])
        extract_btn = st.button("업로드 요약/리스크 추출")
        if uploaded and extract_btn:
            if uploaded.type == "application/pdf":
                if not PDF_AVAILABLE:
                    st.warning("pypdf가 설치되어 있지 않아 PDF를 읽을 수 없습니다. `pip install pypdf` 후 재시도하세요.")
                    extracted = ""
                else:
                    extracted = extract_text_from_pdf(uploaded)
            else:
                extracted = uploaded.read().decode("utf-8", errors="ignore")
            short = extracted[:8000] if extracted else ""
            if not short:
                st.warning("추출된 텍스트가 없습니다.")
            else:
                user_prompt = f"""
아래 업로드 텍스트의 핵심을 버핏 원칙 관점에서 요약하고, 리스크/체크포인트/추정 표시를 구조화해줘.
텍스트(일부): ```{short}```

JSON도 함께 반환: keys = summary, bullets[], risks[], checkpoints[], redflags[]
"""
                st.session_state.messages.append({"role":"user","content":user_prompt})
                text = call_chat(build_messages(tone_line_=tone_line), stream=True)
                data = parse_json_block(text)
                if data:
                    if "bullets" in data:
                        st.markdown("**핵심 요약**"); [st.markdown(f"- {b}") for b in data["bullets"]]
                    if "risks" in data:
                        st.markdown("**리스크**"); [st.markdown(f"- {r}") for r in data["risks"]]
                    if "checkpoints" in data:
                        st.markdown("**체크포인트**"); [st.markdown(f"- {c}") for c in data["checkpoints"]]

    # 간이 DCF 계산기
    with rcol:
        st.markdown("### 🧮 DCF 스냅샷 계산기 (단순화)")
        with st.form("dcf_form"):
            revenue = st.number_input("현재 매출", min_value=0.0, value=10000.0, step=100.0)
            op_margin = st.number_input("영업이익률(0~1)", min_value=0.0, max_value=1.0, value=0.25, step=0.01)
            tax_rate = st.number_input("세율(0~1)", min_value=0.0, max_value=1.0, value=0.21, step=0.01)
            reinvest_rate = st.number_input("재투자 비율(0~1)", min_value=0.0, max_value=1.0, value=0.30, step=0.01)
            shares_out = st.number_input("주식수 (분모 단위에 맞게)", min_value=0.0, value=1000.0, step=10.0)

            st.markdown("**시나리오별 가정**")
            wacc_bear = st.number_input("보수 WACC", min_value=0.01, max_value=0.5, value=0.12, step=0.005)
            g_bear    = st.number_input("보수 g",    min_value=-0.1, max_value=0.2, value=0.01, step=0.005)
            wacc_base = st.number_input("기준 WACC", min_value=0.01, max_value=0.5, value=0.10, step=0.005)
            g_base    = st.number_input("기준 g",    min_value=-0.1, max_value=0.2, value=0.02, step=0.005)
            wacc_bull = st.number_input("공격 WACC", min_value=0.01, max_value=0.5, value=0.09, step=0.005)
            g_bull    = st.number_input("공격 g",    min_value=-0.1, max_value=0.2, value=0.03, step=0.005)
            horizon   = st.slider("명목상 TV 할인연수", 3, 10, 5)

            run = st.form_submit_button("DCF 계산")
        if run:
            df = simple_dcf_scenarios(
                revenue, op_margin, tax_rate, reinvest_rate, shares_out,
                wacc_bear, wacc_base, wacc_bull, g_bear, g_base, g_bull, horizon_years=horizon
            )
            st.dataframe(df, use_container_width=True)
            st.download_button("⬇️ DCF 결과 CSV", data=df.to_csv(index=False).encode("utf-8-sig"),
                               file_name="dcf_snapshot.csv", mime="text/csv")

# ============================ FOOTER NOTE ============================
st.divider()
st.caption(
    "※ 본 앱의 답변은 일반 정보 제공 목적이며, 투자 자문 또는 권유가 아닙니다. "
    "모든 투자 결정과 책임은 사용자 본인에게 있습니다. 세무/법률/회계 사항은 전문기관과 상의하세요."
)
