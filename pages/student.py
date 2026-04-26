import streamlit as st
from supabase import create_client

st.set_page_config(page_title="과제 제출", page_icon="📝", layout="centered")

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
</style>
""", unsafe_allow_html=True)

# ── 헤더 ──────────────────────────────────────────────────
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

# 버튼 3개 한 줄
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🏆 랭킹 보기", use_container_width=True):
        st.switch_page("pages/leaderboard.py")
with col2:
    st.empty()
with col3:
    if st.button("🚪 로그아웃", use_container_width=True):
        st.session_state.user = None
        st.switch_page("app.py")

st.markdown("---")
st.markdown("### 📝 과제 제출")

problems = [f"{i}-{j}" for i in range(1, 10) for j in range(1, 4)]
problem = st.selectbox("문제 번호", problems)
code = st.text_area("코드 작성", height=250, placeholder="def solution():\n    ...")
desc = st.text_input("설명 (선택)", placeholder="코드에 대한 간단한 설명을 입력하세요")

if st.button("🚀 제출하기", use_container_width=True):
    if not code.strip():
        st.warning("코드를 입력하세요!")
    else:
        try:
            supabase.table("submissions").insert({
                "name": user["name"],
                "problem": problem,
                "code": code,
                "description": desc
            }).execute()
            st.success(f"✅ 제출 완료! ({problem})")
            st.balloons()
        except Exception as e:
            st.error(f"제출 오류: {e}")

st.markdown("---")
st.markdown("### 📊 내 제출 현황")

try:
    res = supabase.table("submissions") \
        .select("submitted_at, problem, score_total") \
        .eq("name", user["name"]) \
        .order("submitted_at", desc=True) \
        .execute()

    if res.data:
        for row in res.data:
            total = row["score_total"] or 0
            time_str = row["submitted_at"][:16].replace("T", " ")
            if total > 0:
                score_html = f'<div style="color:#4f46e5; font-weight:900; font-size:1.2rem;">{total}점</div>'
            else:
                score_html = '<div style="color:#aaa; font-size:0.95rem;">채점 중</div>'

            st.markdown(f"""
            <div style="background:white; border:1px solid #e0e4f0; border-radius:10px;
                        padding:14px 18px; margin-bottom:10px;
                        display:flex; justify-content:space-between; align-items:center;
                        box-shadow:0 2px 6px rgba(0,0,0,0.04);">
                <div>
                    <span style="color:#4f46e5; font-weight:700;">{row['problem']}</span>
                    <span style="color:#aaa; font-size:0.85rem; margin-left:12px;">{time_str}</span>
                </div>
                {score_html}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("아직 제출한 과제가 없어요.")
except Exception as e:
    st.error(f"데이터 로드 오류: {e}")
