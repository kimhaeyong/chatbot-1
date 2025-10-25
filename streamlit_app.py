# app.py
# ------------------------------------------------------------
# 🐶 겨울 브라운 톤 · 코지 스타일
# Buffett-Style "댕댕이 가치비서" (Warm Brown Winter Theme)
# ------------------------------------------------------------
import os
import re
import io
import json
from typing import List, Dict, Any, Optional

import streamlit as st
import pandas as pd
from openai import OpenAI

# (선택) PDF 텍스트 추출
try:
    from pypdf import PdfReader
    PDF_AVAILABLE = True
except Exception:
    PDF_AVAILABLE = False


# ======================== THEME & BRAND ========================
# 페이지 메타
st.set_page_config(
    page_title="🐾 댕댕이 가치비서 — Cozy Winter",
    page_icon="🐶",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 겨울 브라운 팔레트
COLOR_BG       = "#F7F1EA"  # 따뜻한 아이보리
COLOR_TEXT     = "#4B3A2A"  # 다크 브라운
COLOR_BRAND    = "#B9885A"  # 브라운/카라멜
COLOR_ACCENT   = "#D9BBA3"  # 누가/라떼 톤
COLOR_HOVER    = "#A77146"  # 버튼 hover 브라운
COLOR_CARD     = "#FBF6F1"  # 카드 배경
COLOR_SIDEBAR  = "#EFE3D8"  # 사이드바 배경

# 코지 겨울/강아지 이미지
HERO_IMG_URL = "https://images.unsplash.com/photo-1543466835-00a7907e9de1?q=80&w=1600"  # 코지 겨울 강아지 느낌
SIDEBAR_LOGO_PATH = "/mnt/data/your_logo.png"  # ← 여기에 로고(또는 귀여운 강아지 PNG) 파일 경로를 두세요.

# 전체 CSS (브라운 톤, 둥근 버튼, 말풍선 대화 등)
st.markdown(f"""
<style>
/* Base */
html, body, [class*="css"]  {{
  background-color: {COLOR_BG};
  color: {COLOR_TEXT};
  font-family: 'Noto Sans KR', 'Pretendard', 'Inter', sans-serif;
}}
/* Sidebar */
section[data-testid="stSidebar"] > div:first-child {{
  background-color: {COLOR_SIDEBAR};
  border-right: 1px solid {COLOR_ACCENT}33;
}}
/* Headers */
h1, h2, h3, h4 {{
  color: {COLOR_TEXT};
}}
/* Buttons */
.stButton>button {{
  background: {COLOR_BRAND};
  color: white;
  border-radius: 12px;
  border: 0;
  padding: 0.55rem 0.9rem;
  transition: 0.2s ease-in-out;
}}
.stButton>button:hover {{
  background: {COLOR_HOVER};
  color: #fff;
}}
/* Input, Select, Textarea */
div.stTextInput>div>div>input,
div.stTextArea>div>div>textarea,
div.stSelectbox>div>div>div>div,
div.stNumberInput input {{
  background: {COLOR_CARD};
  color: {COLOR_TEXT};
  border-radius: 10px;
  border: 1px solid {COLOR_ACCENT};
}}
/* Chat bubbles (best-effort) */
[data-testid="stChatMessage"] {{
  background: {COLOR_CARD};
  border: 1px solid {COLOR_ACCENT}77;
  border-radius: 16px;
  padding: 0.8rem;
}}
/* Info / Caption */
.block-container {{
  padding-top: 1.2rem;
}}
small, .stCaption, .st-emotion-cache-1y4p8pa {{
  color: {COLOR_TEXT}AA !important;
}}
/* Tabs */
.stTabs [data-baseweb="tab-list"] button[role="tab"] {{
  background: {COLOR_CARD};
  color: {COLOR_TEXT};
  border-radius: 10px 10px 0 0;
  border: 1px solid {COLOR_ACCENT}66;
  margin-right: 4px;
}}
.stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{
  background: #fff;
  border-bottom: 1px solid white;
}}
/* Cards */
.cozy-card {{
  background: {COLOR_CARD};
  border: 1px solid {COLOR_ACCENT}55;
  border-radius: 12px;
  padding: 1rem;
}}
/* Cozy badges */
.badge {{
  display: inline-block;
  padding: .25rem .6rem;
  background: {COLOR_ACCENT};
  color: {COLOR_TEXT};
  border-radius: 999px;
  font-size: .85rem;
  margin-right: .3rem;
}}
</style>
""", unsafe_allow_html=True)


# ======================== SESSION & PROMPTS ========================
if "messages" not in st.session_state:
    st.session_state.messages: List[Dict[str, str]] = []

if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = (
        "너는 한국어로 답하는 '워렌 버핏 스타일의 가치투자' 금융투자 비서다. 다음 원칙을 반드시 지켜라.\n"
        "1) 면책: 답변은 일반 정보 제공이며 투자 자문/권유가 아니다. 최종 판단과 책임은 사용자에게 있음을 명확히 하라.\n"
        "2) 철학: 안전마진, 해자, 역량의 범위, 오너이익, 장기보유, 현금흐름의 질을 중시하라.\n"
        "3) 구조: (요약 4~6줄) → (핵심 근거 bullet) → (체크리스트 표) → (리스크/가정/추가확인) 순.\n"
        "4) 체크리스트: 해자/현금흐름/부채/ROIC/자본배분/경영진/규제/환율/금리/사이클/거버넌스/희석.\n"
        "5) 수치: 단위를 명확히(%, KRW, USD 등). 가정은 간단히 공개하라.\n"
        "6) 과신 금지: 보수/기준/공격 3가지 시나리오로 제시.\n"
        "7) 최신 데이터 필요 시 '추정'임을 밝히고 원자료/10-K 확인 권고.\n"
        "8) 가능하면 JSON도 함께 반환: summary, bullets[], checklist[], valuation{{bear,base,bull}}, risks[].\n"
        "톤은 다정하고 따뜻하되, 분석은 명료하고 사실 기반으로 하라."
    )

if "onboarding_open" not in st.session_state:
    st.session_state.onboarding_open = True

if "profile" not in st.session_state:
    st.session_state.profile = {
        "risk": "보수적",
        "horizon": "3~5년",
        "region": ["US", "KR"],
        "sectors": ["Technology", "Consumer"],
        "watchlist": ["AAPL", "NVDA"]
    }


# ======================== HEADER (Winter Cozy) ========================
left, right = st.columns([1, 2])
with left:
    st.markdown("## 🐾 댕댕이 가치비서")
    st.caption("겨울엔 따뜻하게, 분석은 단단하게. 브라운 톤 코지 스타일로 함께해요.")
with right:
    st.image(HERO_IMG_URL, use_container_width=True, caption="Cozy winter vibes with a loyal partner 🐶")

st.divider()


# ======================== ONBOARDING PANEL ========================
def onboarding_panel():
    with st.container():
        st.markdown(f"""
<div class="cozy-card">
  <h3>❄️ 겨울 코지 스타트 — 사용 방법</h3>
  <p><span class="badge">버핏 원칙</span><span class="badge">해자</span><span class="badge">안전마진</span><span class="badge">현금흐름</span></p>
  <ol>
    <li><b>API 키</b>를 좌측 사이드바 또는 <code>.streamlit/secrets.toml</code>에 저장해요.</li>
    <li><b>설정</b>: 모델(4o-mini 권장), temperature(0.1~0.3), 성향·보유기간·지역·섹터·톤을 고르면 답변에 반영돼요.</li>
    <li><b>활용</b>:
      <ul>
        <li>🧰 <b>Buffett Screener</b>: 체크리스트 + 간단 밸류 범위</li>
        <li>📝 <b>Investment Memo</b>: 템플릿으로 정리</li>
        <li>💬 <b>General Chat</b>: 아무거나 물어보기</li>
        <li>🧮 <b>DCF & Upload</b>: 업로드 요약 + 간이 DCF 계산/다운로드</li>
      </ul>
    </li>
  </ol>
  <p style="opacity:.8">⚠️ 본 챗봇은 일반 정보 제공용이며 투자 자문/권유가 아닙니다.</p>
</div>
""", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("🐶 시작하기"):
                st.session_state.onboarding_open = False
                st.rerun()
        with c2:
            st.button("ℹ️ 다음에도 보기")  # 유지


if st.session_state.onboarding_open:
    onboarding_panel()
    st.stop()


# ======================== OPENAI KEY ========================
openai_api_key = st.secrets.get("OPENAI_API_KEY", "")
if not openai_api_key:
    openai_api_key = st.text_input("🔑 OpenAI API Key", type="password", help="secrets.toml에 OPENAI_API_KEY로 저장하면 입력창이 숨겨져요.")
if not openai_api_key:
    st.info("API 키를 입력하면 시작할 수 있어요. 🐕‍🦺", icon="🔒")
    st.stop()

client = OpenAI(api_key=openai_api_key)


# ======================== SIDEBAR ========================
with st.sidebar:
    # 로고/이미지
    if os.path.exists(SIDEBAR_LOGO_PATH):
        st.image(SIDEBAR_LOGO_PATH, use_container_width=True)
    else:
        st.markdown("<div style='text-align:center;font-size:48px;'>🐶</div>", unsafe_allow_html=True)

    st.markdown(
        f"<h4 style='text-align:center; color:{COLOR_BRAND}; margin-top:.3rem;'>Cozy Value • Warm Insight</h4>",
        unsafe_allow_html=True
    )

    st.header("⚙️ 설정")
    model = st.selectbox("모델 선택", ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"], index=0)
    temperature = st.slider("창의성(temperature)", 0.0, 1.0, 0.2, 0.1)
    max_tokens = st.slider("최대 생성 토큰", 256, 4096, 1400, 128)

    st.subheader("🎯 프로필")
    st.session_state.profile["risk"] = st.radio("리스크 성향", ["보수적","중립","공격적"],
                                                index=["보수적","중립","공격적"].index(st.session_state.profile["risk"]),
                                                horizontal=True)
    st.session_state.profile["horizon"] = st.selectbox("보유기간", ["1~2년","3~5년","5~10년+"],
                                                       index=["1~2년","3~5년","5~10년+"].index(st.session_state.profile["horizon"]))
    st.session_state.profile["region"] = st.multiselect("지역", ["KR","US","JP","EU","EM"],
                                                        default=st.session_state.profile["region"])
    st.session_state.profile["sectors"] = st.multiselect("섹터",
        ["Technology","Financials","Industrials","Energy","Healthcare","Consumer","Utilities","Materials"],
        default=st.session_state.profile["sectors"])

    st.subheader("🧠 어시스턴트 톤")
    tone = st.radio("톤", ["중립/보수","중립/균형","기회발굴"], index=1, horizontal=True)
    tone_line = {
        "중립/보수": "안전마진을 최우선으로 삼고, 리스크를 먼저 식별/서술하라.",
        "중립/균형": "긍/부정 요인을 균형있게 제시하되, 핵심 변수를 강조하라.",
        "기회발굴": "저평가 구간/카탈리스트를 적극 탐색하되, 리스크 경고를 명시하라."
    }[tone]

    st.subheader("✍️ 시스템 프롬프트(선택)")
    with st.expander("편집/커스터마이즈", expanded=False):
        edited = st.text_area("시스템 프롬프트", value=st.session_state.system_prompt, height=220)
        if st.button("적용"):
            st.session_state.system_prompt = edited
            st.success("시스템 프롬프트 적용 완료")

    # 워치리스트
    st.subheader("👀 워치리스트")
    wl_new = st.text_input("티커 추가", placeholder="예: AAPL")
    cw1, cw2 = st.columns([1,1])
    with cw1:
        if st.button("추가"):
            if wl_new and wl_new.upper() not in st.session_state.profile["watchlist"]:
                st.session_state.profile["watchlist"].append(wl_new.upper())
                st.experimental_rerun()
    with cw2:
        if st.button("초기화"):
            st.session_state.profile["watchlist"] = []
    st.write("📝", ", ".join(st.session_state.profile["watchlist"]) or "(비어있음)")

    # 대화 초기화
    if st.button("🧹 대화 초기화"):
        st.session_state.messages = []
        st.success("대화를 초기화했습니다.")
        st.rerun()

    # 샘플 프롬프트
    st.subheader("💡 샘플 프롬프트")
    if st.button("• 버핏 스크리너로 KO 점검"):
        st.session_state.messages.append({"role":"user","content":"KO를 버핏 스크리너 체크리스트로 점검해줘."})
        st.rerun()
    if st.button("• 겨울 성수기 소비 테마 시나리오"):
        st.session_state.messages.append({"role":"user","content":"겨울 성수기 소비 테마를 보수/기준/공격 3가지 시나리오로 정리하고 핵심 변수와 리스크를 설명해줘."})
        st.rerun()


# ======================== HELPERS ========================
def trim_messages(messages: List[Dict[str, str]], max_pairs: int = 18) -> List[Dict[str, str]]:
    ua = [m for m in messages if m["role"] in ("user", "assistant")]
    if len(ua) <= 2 * max_pairs:
        return messages
    return ua[-2 * max_pairs:]

def parse_json_block(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    fence = re.search(r"```json\s*(\{{1}.*?\}{1})\s*```", text, flags=re.DOTALL)
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
    revenue: float,
    op_margin: float,
    tax_rate: float,
    reinvest_rate: float,
    shares_out: float,
    wacc_bear: float, wacc_base: float, wacc_bull: float,
    g_bear: float, g_base: float, g_bull: float,
    horizon_years: int = 5
) -> pd.DataFrame:
    """
    매우 단순화된 DCF 스냅샷:
    FCF = EBIT*(1-T) * (1 - 재투자비율)
    TV = FCF*(1+g)/(WACC-g) (5년 뒤 가정), PV는 간단 디스카운트
    """
    def scenario_calc(name, wacc, g):
        ebit = revenue * op_margin
        nopat = ebit * (1 - tax_rate)
        fcf = nopat * (1 - reinvest_rate)
        if wacc <= g:
            tv = float('nan')
        else:
            tv = fcf * (1 + g) / (wacc - g)
        pv_fcf = fcf / (1 + wacc)
        pv_tv = tv / ((1 + wacc) ** horizon_years) if tv == tv else float('nan')
        ev = pv_fcf + pv_tv
        pps = ev / max(shares_out, 1e-6)
        return {"Scenario": name, "WACC": wacc, "g": g, "FCF(yr1)": fcf, "EV(PV)": ev, "Price/Share": pps}

    return pd.DataFrame([
        scenario_calc("보수", wacc_bear, g_bear),
        scenario_calc("기준", wacc_base, g_base),
        scenario_calc("공격", wacc_bull, g_bull),
    ])

def build_messages(tone_line_: str) -> List[Dict[str, str]]:
    system_full = st.session_state.system_prompt + "\n" + f"추가 톤 지시: {tone_line_}"
    history = trim_messages(st.session_state.messages, max_pairs=18)
    return [{"role": "system", "content": system_full}] + history

def call_chat(messages: List[Dict[str, str]], stream: bool = True) -> str:
    with st.chat_message("assistant"):
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
                    stream=False,
                )
                response_text = resp.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            return response_text
        except Exception as e:
            st.error(f"요청 중 오류가 발생했습니다: {e}")
            return ""


# ======================== TABS ========================
tab1, tab2, tab3, tab4 = st.tabs([
    "🧰 Buffett Screener",
    "📝 Investment Memo",
    "💬 General Chat",
    "🧮 DCF & Upload"
])

# 1) Screener
with tab1:
    st.markdown("### 🧰 버핏 스크리너 — 따뜻하지만 날카롭게")
    c1, c2 = st.columns([1.25, 1])
    with c1:
        ticker = st.text_input("티커/기업명", placeholder="예: KO, AAPL, 삼성전자")
        notes = st.text_area("선택: 참고 메모/최근 실적 요점", height=140,
                             placeholder="최근 분기 하이라이트, 매출/마진/FCF 추세, 가격레벨, 이슈 등")
    with c2:
        st.markdown(f"""
<div class="cozy-card">
  <b>프로필 요약</b><br/>
  성향: {st.session_state.profile["risk"]}<br/>
  보유: {st.session_state.profile["horizon"]}<br/>
  지역: {", ".join(st.session_state.profile["region"])}<br/>
  섹터: {", ".join(st.session_state.profile["sectors"])}
</div>
""", unsafe_allow_html=True)

    if st.button("스크리너 실행"):
        user_prompt = f"""
다음 기업을 '버핏 스크리너'로 점검해줘.
기업: {ticker}
참고메모: {notes}

출력 형식:
1) 5줄 요약
2) 핵심 근거 bullet (해자/현금흐름/부채/ROIC/오너이익/경영진/규제/환율·금리·사이클)
3) 체크리스트 표(항목/평가/간단이유) — 해자, 현금흐름의 질, 부채·이자보상, 자본배분, 규제·정책, 환율·금리 민감도, 거버넌스, 희석리스크
4) 간단 밸류에이션 스냅샷(보수/기준/공격) — 가정과 결과 범위
5) 리스크/추가확인 목록
6) JSON도 함께 반환: keys = summary, bullets[], checklist[], valuation{{bear,base,bull}}, risks[]

투자 성향: {st.session_state.profile["risk"]}, 보유기간: {st.session_state.profile["horizon"]},
지역: {', '.join(st.session_state.profile["region"])}, 섹터: {', '.join(st.session_state.profile["sectors"])}
톤 가이드: {tone_line}
"""
        st.session_state.messages.append({"role":"user","content":user_prompt})
        text = call_chat(build_messages(tone_line_=tone_line), stream=True)
        data = parse_json_block(text)
        if data:
            st.markdown("#### 📦 구조화 결과")
            if "summary" in data:
                st.markdown(f"**요약:** {data['summary']}")
            if "bullets" in data and isinstance(data["bullets"], list):
                st.markdown("**핵심 근거**")
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

            # 다운로드
            md = io.StringIO(); md.write("# Screener Result\n\n"); md.write(text)
            st.download_button("⬇️ 원문 저장(.md)", data=md.getvalue(), file_name=f"screener_{ticker}.md", mime="text/markdown")
            st.download_button("⬇️ JSON 저장(.json)", data=json.dumps(data, ensure_ascii=False, indent=2), file_name=f"screener_{ticker}.json", mime="application/json")

# 2) Investment Memo
with tab2:
    st.markdown("### 📝 Investment Memo — 겨울엔 따뜻하게, 결론은 명확하게")
    company = st.text_input("기업/티커", placeholder="예: BRK.B, AAPL, NVDA")
    memo_hints = st.text_area("선택: 추가 힌트(제품/해자/가격대/이벤트 등)", height=120)

    if st.button("메모 생성"):
        user_prompt = f"""
'{company}'에 대한 '버핏 스타일 Investment Memo'를 작성해줘.
- Thesis(4~6줄)
- Business & Moat
- Unit Economics & Owner Earnings
- Capital Allocation (ROIC 추세 포함)
- Valuation (보수/기준/공격) + 가정치
- Risks / Catalysts / Monitoring
- Verdict(안전마진 관점)
- JSON도 반환: keys = thesis, moat, unit, capital, valuation{{bear,base,bull}}, risks[], catalysts[], monitoring[], verdict

추가 힌트: {memo_hints}
프로필: 성향={st.session_state.profile["risk"]}, 보유={st.session_state.profile["horizon"]}, 지역={', '.join(st.session_state.profile["region"])}, 섹터={', '.join(st.session_state.profile["sectors"])}
톤: {tone_line}
"""
        st.session_state.messages.append({"role":"user","content":user_prompt})
        text = call_chat(build_messages(tone_line_=tone_line), stream=True)
        data = parse_json_block(text)
        if data:
            st.markdown("#### 📦 구조화 결과")
            if "valuation" in data:
                st.dataframe(pd.DataFrame.from_dict(data["valuation"], orient="index").reset_index().rename(columns={"index":"Scenario"}), use_container_width=True)
            for key in ["thesis","moat","unit","capital","verdict"]:
                if key in data:
                    st.markdown(f"**{key.capitalize()}**")
                    st.write(data[key])
            if "risks" in data:
                st.markdown("**Risks**")
                for r in data["risks"]:
                    st.markdown(f"- {r}")
            if "catalysts" in data:
                st.markdown("**Catalysts**")
                for c in data["catalysts"]:
                    st.markdown(f"- {c}")
            if "monitoring" in data:
                st.markdown("**Monitoring**")
                for m in data["monitoring"]:
                    st.markdown(f"- {m}")

            # 다운로드
            md = io.StringIO(); md.write("# Investment Memo\n\n"); md.write(text)
            st.download_button("⬇️ 원문 저장(.md)", data=md.getvalue(), file_name=f"memo_{company}.md", mime="text/markdown")
            st.download_button("⬇️ JSON 저장(.json)", data=json.dumps(data, ensure_ascii=False, indent=2), file_name=f"memo_{company}.json", mime="application/json")

# 3) General Chat
with tab3:
    st.markdown("### 💬 겨울 담요 같은 대화, 하지만 팩트는 단단하게")
    if len(st.session_state.messages) == 0:
        st.info("예시: “배당 성장주로 분기 현금흐름 설계안을 3가지 시나리오로 정리해줘.”")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    prompt = st.chat_input("무엇을 도와드릴까요? (예: ETF 리밸런싱 규칙 초안)")
    if prompt:
        st.session_state.messages.append({"role":"user","content":prompt})
        call_chat(build_messages(tone_line_=tone_line), stream=True)

# 4) DCF & Upload
with tab4:
    st.markdown("### 🧮 DCF & 📎 Upload — 코지한 계산과 정리")
    lc, rc = st.columns([1,1])

    # 업로드 분석
    with lc:
        st.markdown("#### 📎 10-K / IR 자료 요약")
        uploaded = st.file_uploader("PDF 또는 TXT 업로드", type=["pdf","txt"])
        if st.button("업로드 요약/리스크 추출"):
            if not uploaded:
                st.warning("파일을 먼저 업로드해주세요.")
            else:
                if uploaded.type == "application/pdf":
                    if not PDF_AVAILABLE:
                        st.warning("pypdf 미설치로 PDF 추출 불가. `pip install pypdf` 후 재시도하세요.")
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
아래 업로드 텍스트를 버핏 관점에서 요약하고 리스크/체크포인트를 구조화해줘.
텍스트 일부: ```{short}```
JSON: summary, bullets[], risks[], checkpoints[], redflags[]
"""
                    st.session_state.messages.append({"role":"user","content":user_prompt})
                    text = call_chat(build_messages(tone_line_=tone_line), stream=True)
                    data = parse_json_block(text)
                    if data:
                        if "bullets" in data:
                            st.markdown("**핵심 요약**")
                            for b in data["bullets"]:
                                st.markdown(f"- {b}")
                        if "risks" in data:
                            st.markdown("**리스크**")
                            for r in data["risks"]:
                                st.markdown(f"- {r}")
                        if "checkpoints" in data:
                            st.markdown("**체크포인트**")
                            for c in data["checkpoints"]:
                                st.markdown(f"- {c}")

    # DCF 계산기
    with rc:
        st.markdown("#### 🧮 간이 DCF 스냅샷")
        with st.form("dcf_form"):
            revenue = st.number_input("현재 매출", min_value=0.0, value=10000.0, step=100.0)
            op_margin = st.number_input("영업이익률(0~1)", min_value=0.0, max_value=1.0, value=0.25, step=0.01)
            tax_rate = st.number_input("세율(0~1)", min_value=0.0, max_value=1.0, value=0.21, step=0.01)
            reinvest_rate = st.number_input("재투자 비율(0~1)", min_value=0.0, max_value=1.0, value=0.30, step=0.01)
            shares_out = st.number_input("주식수(분모 단위에 맞게)", min_value=0.0, value=1000.0, step=10.0)

            st.markdown("**시나리오 가정**")
            wacc_bear = st.number_input("보수 WACC", min_value=0.01, max_value=0.5, value=0.12, step=0.005)
            g_bear    = st.number_input("보수 g",    min_value=-0.1, max_value=0.2, value=0.01, step=0.005)
            wacc_base = st.number_input("기준 WACC", min_value=0.01, max_value=0.5, value=0.10, step=0.005)
            g_base    = st.number_input("기준 g",    min_value=-0.1, max_value=0.2, value=0.02, step=0.005)
            wacc_bull = st.number_input("공격 WACC", min_value=0.01, max_value=0.5, value=0.09, step=0.005)
            g_bull    = st.number_input("공격 g",    min_value=-0.1, max_value=0.2, value=0.03, step=0.005)
            horizon   = st.slider("TV 할인 연수(명목)", 3, 10, 5)

            run = st.form_submit_button("DCF 계산")
        if run:
            df = simple_dcf_scenarios(
                revenue, op_margin, tax_rate, reinvest_rate, shares_out,
                wacc_bear, wacc_base, wacc_bull, g_bear, g_base, g_bull, horizon_years=horizon
            )
            st.dataframe(df, use_container_width=True)
            st.download_button("⬇️ DCF 결과 CSV", data=df.to_csv(index=False).encode("utf-8-sig"),
                               file_name="dcf_snapshot.csv", mime="text/csv")


# ======================== FOOTER ========================
st.divider()
st.caption(
    "※ 본 챗봇의 답변은 일반 정보 제공 목적이며, 투자 자문 또는 권유가 아닙니다. "
    "모든 투자 결정과 책임은 사용자 본인에게 있습니다. 세무/법률/회계 사항은 전문기관과 상의하세요."
)
