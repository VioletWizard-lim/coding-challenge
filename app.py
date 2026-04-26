import streamlit as st
from supabase import create_client

st.set_page_config(
    page_title="파이썬 코딩 챌린지",
    page_icon="🚀",
    layout="centered"
)

@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["supabase"]["url"],
        st.secrets["supabase"]["key"]
    )

supabase = get_supabase()

def login(user_id, password, role):
    try:
        res = supabase.table("users") \
            .select("*") \
            .eq("id", user_id) \
            .eq("password", password) \
            .eq("role", role) \
            .execute()
        return res.data[0] if res.data else None
    except Exception as e:
        st.error(f"DB 연결 오류: {e}")
        return None

if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user:
    role = st.session_state.user["role"]
    if role == "teacher":
        st.switch_page("pages/teacher.py")
    else:
        st.switch_page("pages/student.py")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
* { font-family: 'Noto Sans KR', sans-serif; }

[data-testid="stAppViewContainer"] { background: #f5f7fa; }
.block-container { max-width: 440px !important; padding-top: 80px !important; }

.title-wrap { text-align: center; margin-bottom: 40px; }
.title-wrap h1 { font-size: 2.2rem; font-weight: 900; color: #1a1a2e; margin-bottom: 6px; }
.title-wrap p { color: #888; font-size: 0.95rem; }

.stTabs [data-baseweb="tab-list"] {
    gap: 0; background: #e8eaf0; border-radius: 10px; padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    flex: 1; border-radius: 8px; color: #666; font-weight: 700;
}
.stTabs [aria-selected="true"] {
    background: #4f46e5 !important; color: white !important;
}

.stTextInput input {
    background: white !important;
    border: 1px solid #dde1f0 !important;
    color: #1a1a2e !important;
    border-radius: 8px !important;
}
.stTextInput input:focus {
    border-color: #4f46e5 !important;
    box-shadow: 0 0 0 2px rgba(79,70,229,0.15) !important;
}

.stButton button {
    background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
    color: white !important; border: none !important;
    border-radius: 10px !important; font-weight: 700 !important;
    font-size: 1rem !important; padding: 0.6rem !important;
    width: 100% !important;
}
.stButton button:hover { opacity: 0.85; }
label { color: #555 !important; font-size: 0.85rem !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="title-wrap">
    <h1>🚀 파이썬 코딩 챌린지</h1>
    <p>AI와 함께 코딩을 배워보세요</p>
</div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🎓 학생 로그인", "👨‍🏫 교사 로그인"])

with tab1:
    st.text_input("아이디", key="s_id", placeholder="학번을 입력하세요")
    st.text_input("비밀번호", key="s_pw", type="password", placeholder="비밀번호를 입력하세요")
    if st.button("입장하기", key="s_login"):
        if not st.session_state.s_id or not st.session_state.s_pw:
            st.warning("아이디와 비밀번호를 입력하세요.")
        else:
            user = login(st.session_state.s_id, st.session_state.s_pw, "student")
            if user:
                st.session_state.user = user
                st.switch_page("pages/student.py")
            else:
                st.error("아이디 또는 비밀번호가 틀렸습니다.")
    st.markdown("---")
    if st.button("🏆 실시간 랭킹 보기", key="ranking_btn"):
        st.switch_page("pages/leaderboard.py")

with tab2:
    st.text_input("아이디", key="t_id", placeholder="교사 아이디를 입력하세요")
    st.text_input("비밀번호", key="t_pw", type="password", placeholder="비밀번호를 입력하세요")
    if st.button("입장하기", key="t_login"):
        if not st.session_state.t_id or not st.session_state.t_pw:
            st.warning("아이디와 비밀번호를 입력하세요.")
        else:
            user = login(st.session_state.t_id, st.session_state.t_pw, "teacher")
            if user:
                st.session_state.user = user
                st.switch_page("pages/teacher.py")
            else:
                st.error("아이디 또는 비밀번호가 틀렸습니다.")
