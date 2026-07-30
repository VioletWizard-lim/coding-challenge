import streamlit as st
from supabase import create_client
from datetime import datetime, timezone, timedelta
import time
import extra_streamlit_components as stx

st.set_page_config(page_title="과제 제출", page_icon="📝", layout="centered")

KST = timezone(timedelta(hours=9))

def to_kst(utc_str):
    if not utc_str:
        return ""
    try:
        dt = datetime.fromisoformat(utc_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(KST).strftime("%Y-%m-%d %H:%M")
    except:
        return utc_str[:16].replace("T", " ")

if "user" not in st.session_state or not st.session_state.user:
    st.switch_page("app.py")
if st.session_state.user["role"] != "student":
    st.switch_page("app.py")

@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["supabase"]["url"],
        st.secrets["supabase"]["key"]
    )

supabase = get_supabase()
user = st.session_state.user
cookie_manager = stx.CookieManager(key="student_cookies")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
* { font-family: 'Noto Sans KR', sans-serif; }
[data-testid="stSidebarNav"] { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }
[data-testid="stAppViewContainer"] { background: #f5f7fa; }
.block-container { max-width: 660px !important; padding-top: 60px !important; }
h3 { color: #1a1a2e !important; }
label { color: #555 !important; }
.stSelectbox > div > div { background: white !important; border-color: #dde1f0 !important; color: #1a1a2e !important; }
.stTextArea textarea { background: white !important; border-color: #dde1f0 !important; color: #1a1a2e !important; font-family: 'Courier New', monospace !important; }
.stTextInput input { background: white !important; border-color: #dde1f0 !important; color: #1a1a2e !important; }
.stButton button {
    background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
    color: white !important; border: none !important;
    border-radius: 10px !important; font-weight: 700 !important;
}
#MainMenu { visibility: hidden !important; }
header[data-testid="stHeader"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div style="display:flex; justify-content:space-between; align-items:center;
            background:white; border-radius:12px; padding:14px 20px;
            border:1px solid #e0e4f0; box-shadow:0 2px 8px rgba(0,0,0,0.05);
            margin-bottom:20px;">
    <div>
        <span style="background:#4f46e5; color:white; padding:3px 10px; border-radius:20px; font-size:0.8rem; font-weight:700;">학생</span>
        <span style="color:#1a1a2e; font-weight:700; font-size:1.1rem; margin-left:10px;">{user['name']}님 환영합니다 👋</span>
    </div>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🏆 랭킹 보기", use_container_width=True):
        st.switch_page("pages/leaderboard.py")
with col2:
    st.empty()
with col3:
    if st.button("🚪 로그아웃", use_container_width=True):
        try:
            cookie_manager.delete("session")
        except:
            pass
        st.session_state.user = None
        st.switch_page("app.py")

st.markdown("---")
st.markdown("### 📝 과제 제출")

PROBLEM_NAMES = {
    "1-1": "오늘의 급식 안내하기", "1-2": "급식 어땠어?", "1-3": "급식 도우미의 인사",
    "1-4": "내가 좋아하는 메뉴 두 가지", "1-5": "나만의 급식 조합 만들기", "1-6": "급식 추천 카드 완성",
    "2-1": "매점 가격표 만들기", "2-2": "두 개 사면 얼마일까?", "2-3": "내가 가진 용돈 확인하기",
    "2-4": "과자 여러 개 사기", "2-5": "거스름돈 계산기", "2-6": "매점 영수증 완성",
    "3-1": "합격일까 불합격일까?", "3-2": "등급을 나눠보자", "3-3": "최우수상 도전!",
    "3-4": "성적 등급 판정기(elif)", "3-5": "나의 학습 리포트 완성",
    "4-1": "응원 구호 다섯 번 외치기", "4-2": "목표 점수까지 응원하기", "4-3": "그만할래요!",
    "4-4": "줄다리기 랜덤 승부", "4-5": "우리 반 응원전 완성",
    "5-1": "입장 안내 방송 5번 틀기", "5-2": "손님 수만큼 티켓 나눠주기", "5-3": "하루 매출 합계 구하기",
    "5-4": "홀수 번째 손님 이벤트", "5-5": "부스 운영 결산 완성",
    "6-1": "이번 학기 활동 목록 만들기", "6-2": "몇 번째 활동이었지?", "6-3": "새로운 활동 추가하기",
    "6-4": "활동 계획이 바뀌었어요", "6-5": "동아리 활동 기록장 완성",
    "7-1": "오늘의 재고 전체 확인하기", "7-2": "이 과자 있나요?", "7-3": "품절 위기 과자 찾기",
    "7-4": "진열대 하나로 합치기", "7-5": "가격 순으로 정렬하기", "7-6": "매점 재고 보고서 완성",
    "8-1": "아침 방송 시작 멘트", "8-2": "오늘 담당 학생 소개하기", "8-3": "남은 방송 시간 계산하기",
    "8-4": "방송 인사말 만들기", "8-5": "하루 방송 스케줄 완성",
    "9-1": "오늘의 일기 저장하기", "9-2": "어제 일기 다시 읽어보기", "9-3": "일기장에 이어 쓰기",
    "9-4": "한 주간의 다짐 모아보기", "9-5": "학교생활 기록 보관함 완성",
    "10-1": "오늘 할 일 관리하기", "10-2": "급식 만족도 통계 내기", "10-3": "매점 자동 계산 + 기록",
    "10-4": "우리 반 출석 관리 함수", "10-5": "학교생활 앱 최종 완성",
}
problems = list(PROBLEM_NAMES.keys())
problem = st.selectbox("문제 번호", problems, format_func=lambda p: f"{p}. {PROBLEM_NAMES[p]}")
code = st.text_area("코드 작성", height=250, placeholder="def solution():\n    ...")
desc = st.text_input("코드 설명 (필수)", placeholder="코드에 대한 설명을 입력하세요")

if "last_submitted_at" not in st.session_state:
    st.session_state.last_submitted_at = 0

elapsed = time.time() - st.session_state.last_submitted_at
cooldown = 5
is_cooling = elapsed < cooldown

btn_label = f"⏳ {int(cooldown - elapsed) + 1}초 후 제출 가능" if is_cooling else "🚀 제출하기"

if st.button(btn_label, use_container_width=True, disabled=is_cooling):
    if not code.strip():
        st.warning("코드를 입력하세요!")
    elif not desc.strip():
        st.warning("코드 설명을 입력하세요!")
    else:
        try:
            supabase.table("submissions").insert({
                "name": user["name"],
                "problem": problem,
                "code": code,
                "description": desc,
                "grade": user.get("grade"),
                "class": user.get("class"),
            }).execute()
            st.session_state.last_submitted_at = time.time()
            st.success(f"✅ 제출 완료! ({problem})")
            st.balloons()
        except Exception as e:
            st.error(f"제출 오류: {e}")

st.markdown("---")
st.markdown("### 📊 내 제출 현황")

try:
    res = supabase.table("submissions") \
        .select("id, submitted_at, problem, score_total, score_function, score_understanding, score_challenge, score_time, feedback, wrong_reason, code, description") \
        .eq("name", user["name"]) \
        .order("submitted_at", desc=True) \
        .execute()

    if res.data:
        for row in res.data:
            total = row["score_total"] or 0
            time_str = to_kst(row["submitted_at"])
            is_graded = total > 0
            score_html = f'<div style="color:#4f46e5; font-weight:900; font-size:1.2rem;">{total}점</div>' if is_graded else '<div style="color:#aaa; font-size:0.95rem;">채점 중</div>'
            wrong_badge = f'<span style="background:#fee2e2; color:#dc2626; padding:2px 8px; border-radius:10px; font-size:0.75rem; font-weight:700; margin-left:8px;">⚠️ 오답</span>' if row.get("wrong_reason") else ""

            st.markdown(f"""
            <div style="background:white; border:1px solid #e0e4f0; border-radius:10px;
                        padding:14px 18px; margin-bottom:4px;
                        display:flex; justify-content:space-between; align-items:center;
                        box-shadow:0 2px 6px rgba(0,0,0,0.04);">
                <div>
                    <span style="color:#4f46e5; font-weight:700;">{row['problem']}</span>{wrong_badge}
                    <span style="color:#aaa; font-size:0.85rem; margin-left:12px;">{time_str}</span>
                </div>
                {score_html}
            </div>
            """, unsafe_allow_html=True)

            with st.expander("📊 상세 점수 및 코드 보기"):
                if is_graded:
                    st.markdown(f"""
                    <div style="display:flex; gap:12px; margin-bottom:10px;">
                        <div style="background:#f5f7fa; border-radius:8px; padding:8px 14px; text-align:center;">
                            <div style="color:#888; font-size:0.75rem;">기능</div>
                            <div style="color:#4f46e5; font-weight:700; font-size:1rem;">{row.get('score_function') or 0}<span style="color:#bbb; font-size:0.8rem;">/40</span></div>
                        </div>
                        <div style="background:#f5f7fa; border-radius:8px; padding:8px 14px; text-align:center;">
                            <div style="color:#888; font-size:0.75rem;">코드 설명</div>
                            <div style="color:#4f46e5; font-weight:700; font-size:1rem;">{row.get('score_understanding') or 0}<span style="color:#bbb; font-size:0.8rem;">/40</span></div>
                        </div>
                        <div style="background:#f5f7fa; border-radius:8px; padding:8px 14px; text-align:center;">
                            <div style="color:#888; font-size:0.75rem;">도전</div>
                            <div style="color:#4f46e5; font-weight:700; font-size:1rem;">{row.get('score_challenge') or 0}<span style="color:#bbb; font-size:0.8rem;">/20</span></div>
                        </div>
                        <div style="background:#4f46e5; border-radius:8px; padding:8px 14px; text-align:center;">
                            <div style="color:#c7d2fe; font-size:0.75rem;">합계</div>
                            <div style="color:white; font-weight:900; font-size:1rem;">{total}<span style="color:#c7d2fe; font-size:0.8rem;">/100</span></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    if row.get("feedback"):
                        st.warning(f"💬 선생님 피드백: {row['feedback']}")
                if row.get("wrong_reason"):
                    st.error(f"⚠️ 오답 이유: {row['wrong_reason']}")
                if row.get("description"):
                    st.caption(f"내 설명: {row['description']}")
                st.code(row.get("code") or "", language="python")
    else:
        st.info("아직 제출한 과제가 없어요.")
except Exception as e:
    st.error(f"데이터 로드 오류: {e}")
