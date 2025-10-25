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
    layout="wide"
)

# 히어로/사이드바 이미지(원하면 로컬 경로로 교체)
HERO_IMG_URL = "https://images.unsplash.com/photo-1559526324-593bc073d938?q=80&w=1600"
SIDEBAR_LOGO_URL = "https://images.unsplash.com/photo-1542228262-3d663b306035?q=80&w=400"

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
    # True면 처음에 온보딩 패널을 보여줌(사용자가 닫을 수 있음)
    st.session_state.onboarding_open = True

# ─────────────────────────────────────────────────────────────
# 상단 타이틀 & 배너
# ─────────────────────────────────────────────────────────────
left, right = st.columns([1, 2])
with left:
    st.title("📈 Buffett-Style AI Investment Copilot")
    st.caption("AI 에이전시용 가치투자 비서 · 저평가/현금흐름 중심 · 해자 점검 · 리스크 우선")
with right:
    st.image(HERO_IMG_URL, use_container_width=True, caption="Be fearful when others are greedy, and vice versa.")

st.divider()

# ─────────────────────────────────────────────────────────────
# 온보딩 패널 (처음 화면에 사용 방법 표시)
# ─────────────────────────────────────────────────────────────
def onboarding_panel():
    with st.container(border=True):
        st.subheader("🚀 시작하기: 챗봇 사용 방법")
        st.markdown(
            """
**이 챗봇은 워렌 버핏의 가치투자 원칙**(안전마진·해자·오너이익 등)을 내장한 금융투자 비서입니다.  
아래 순서대로 시작해 보세요.

**1) API 키 입력**  
좌측 사이드바 또는 `secrets.toml`에 OpenAI API 키를 넣습니다.

**2) 설정 조정**  
- 모델 선택: `gpt-4o-mini` 권장(빠르고 경제적)  
- 창의성(temperature): 0.1~0.3 (보수적 분석에 유리)  
- 투자 성향/보유기간/지역/섹터/분석 톤을 고르면 답변에 반영됩니다.

**3) 세 가지 활용법**  
- **🧰 Buffett Screener**: 티커 입력 → 해자/현금흐름/ROIC 등 체크리스트 + 간단 밸류에이션 스냅샷  
- **📝 Investment Memo**: 메모 템플릿(Thesis→Moat→Owner Earnings→Valuation→Risks→Catalysts→Monitoring→Verdict) 자동 생성  
- **💬 General Chat**: 자유 질의응답(예: “배당 성장주 3가지 시나리오로 안전마진 관점 정리”)

**4) 대화 관리**  
- 좌측 하단 **🧹 대화 초기화**로 기록을 지울 수 있습니다.  
- 샘플 프롬프트 버튼을 눌러 바로 시작해도 좋아요.

> ⚠️ **중요**: 본 챗봇의 답변은 일반 정보 제공이며, 투자 자문/권유가 아닙니다.  
> 모든 투자 결정과 책임은 사용자에게 있으며, 세무/법률/회계 이슈는 전문가와 상의하세요.
"""
        )
        cols = st.columns([1,1,2,1])
        with cols[1]:
            if st.button("✅ 시작하기", use_container_width=True):
                st.session_state.onboarding_open = False
                st.rerun()
        with cols[2]:
            if st.button("ℹ️ 다음에도 보기", use_container_width=True):
                # 닫지 않고 유지
                pass

# 온보딩 패널 표시(열려 있을 때만)
if st.session_state.onboarding_open:
    onboarding_panel()
    st.stop()  # 온보딩만 보여주고 아래 UI는 잠시 멈춤

# ─────────────────────────────────────────────────────────────
# OpenAI Key (온보딩 이후 표시)
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
    st.image(SIDEBAR_LOGO_PATH, use_container_width=True)
    st.markdown("<h4 style='text-align:center; color:#F2D06B;'>Value · Moat · Cash Flow</h4>", unsafe_allow_html=True)
    st.header("⚙️ 설정")
    model = st.selectbox(
        "모델 선택",
        ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
        index=0,
        help="일반적으로 gpt-4o-mini가 빠르고 경제적입니다."
    )
    temperature = st.slider("창의성(temperature)", 0.0, 1.0, 0.2, 0.1, help="가치투자 분석은 낮은 값(보수적)이 일반적")
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
        "중립/균형": "긍/부정 요인을 균형있게 제시하되, 핵심 변수를 강조하라.",
        "기회발굴": "저평가 구간/카탈리스트를 적극 탐색하되, 리스크 경고를 명시하라."
    }[tone]

    st.subheader("✍️ 시스템 프롬프트(선택)")
    with st.expander("편집/커스터마이즈", expanded=False):
        edited = st.text_area("시스템 프롬프트", value=st.session_state.system_prompt, height=220)
        if st.button("적용"):
            st.session_state.system_prompt = edited
            st.success("시스템 프롬프트 적용 완료")

    # 초기화 버튼
    if st.button("🧹 대화 초기화"):
        st.session_state.messages = []
        st.success("대화를 초기화했습니다.")
        st.rerun()

    # 샘플 프롬프트
    st.subheader("💡 샘플 프롬프트")
    if st.button("• 버핏 스크리너 체크리스트로 AAPL 점검"):
        st.session_state.messages.append({"role": "user", "content": "AAPL을 버핏 스크리너 체크리스트로 점검해줘."})
        st.rerun()
    if st.button("• 소비재 기업 인베스트먼트 메모 템플릿"):
        st.session_state.messages.append({"role": "user", "content": "소비재 기업 하나를 가정하고, 버핏 스타일 인베스트먼트 메모 템플릿을 채워줘."})
        st.rerun()

# ─────────────────────────────────────────────────────────────
# 도우미: 히스토리 트리밍
# ─────────────────────────────────────────────────────────────
def trim_messages(messages: List[Dict[str, str]], max_pairs: int = 18) -> List[Dict[str, str]]:
    ua = [m for m in messages if m["role"] in ("user", "assistant")]
    if len(ua) <= 2 * max_pairs:
        return messages
    return ua[-2 * max_pairs :]

# ─────────────────────────────────────────────────────────────
# 탭: 버핏 스크리너 / 인베스트먼트 메모 / 일반 챗
# ─────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🧰 Buffett Screener", "📝 Investment Memo", "💬 General Chat"])

with tab1:
    st.subheader("🧰 버핏 스크리너 체크리스트")
    ticker = st.text_input("티커/기업명", placeholder="예: KO, AAPL, 삼성전자, 현대모비스")
    notes = st.text_area(
        "선택: 참고 메모/최근 실적 요점(있으면 붙여넣기)",
        height=120,
        placeholder="최근 분기 하이라이트, 매출/영업이익/FCF 추세, 가격레벨, 이슈 등"
    )
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

with tab2:
    st.subheader("📝 버핏 스타일 Investment Memo 템플릿")
    company = st.text_input("기업/티커", placeholder="예: BRK.B, AAPL, MSFT, NVDA")
    memo_hints = st.text_area(
        "선택: 추가 힌트(제품/해자/가격대/이벤트 등)",
        height=120,
        placeholder="예: 코카콜라의 브랜드 해자, 재구매율, 원재료·환율 민감도, 재무레버리지 등"
    )
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

추가 힌트: {memo_hints}
투자 성향: {risk_profile}, 보유기간: {horizon}, 지역: {', '.join(region)}, 섹터 선호: {', '.join(sectors)}
톤 가이드: {tone_line}
"""
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        st.rerun()

with tab3:
    st.subheader("💬 일반 대화")
    if len(st.session_state.messages) == 0:
        st.info("버핏 원칙으로 무엇이든 물어보세요. 예) '배당 성장주 3가지 시나리오로 안전마진 관점 정리'")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    prompt = st.chat_input("무엇을 도와드릴까요? (예: ETF 리밸런싱 규칙 초안 만들어줘)")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})

# ─────────────────────────────────────────────────────────────
# 모델 호출 (스트리밍) — 마지막 메시지가 user면 실행
# ─────────────────────────────────────────────────────────────
def build_messages() -> List[Dict[str, str]]:
    system_full = st.session_state.system_prompt + "\n" + f"추가 톤 지시: {tone_line}"
    history = trim_messages(st.session_state.messages, max_pairs=18)
    return [{"role": "system", "content": system_full}] + history

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
