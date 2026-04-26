import streamlit as st
from supabase import create_client

st.set_page_config(page_title="채점 관리", page_icon="👨‍🏫", layout="wide")

if "user" not in st.session_state or not st.session_state.user:
    st.switch_page("app.py")
if st.session_state.user["role"] != "teacher":
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
[data-testid="stAppViewContainer"] { background: #f5f7fa; }
.block-container { padding-top: 30px !important; }
h3 { color: #1a1a2e !important; }
label { color: #555 !important; }

.stTextInput input { background: white !important; border-color: #dde1f0 !important; color: #1a1a2e !important; }
.stNumberInput input { background: white !important; border-color: #dde1f0 !important; color: #1a1a2e !important; text-align: center; }
.stButton > button {
    background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
    color: white !important; border: none !important;
    border-radius: 8px !important; font-weight: 700 !important;
}
.sub-card {
    background: white; border: 1px solid #e0e4f0;
    border-radius: 12px; padding: 18px 20px; margin-bottom: 16px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.sub-name { color: #1a1a2e; font-weight: 700; font-size: 1.1rem; }
.sub-problem { color: #4f46e5; font-weight: 700; margin-left: 10px; }
.sub-time { color: #aaa; font-size: 0.85rem; margin-left: 10px; }
.code-block {
    background: #f8f9fc; border: 1px solid #e0e4f0;
    border-radius: 8px; padding: 12px;
    font-family: 'Courier New', monospace; font-size: 0.85rem;
    color: #4f46e5; white-space: pre-wrap;
    max-height: 150px; overflow-y: auto; margin: 10px 0;
}
.score-total { font-size: 1.4rem; font-weight: 900; color: #4f46e5; }
</style>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([4, 1, 1])
with col1:
    st.markdown(f"### 👨‍🏫 {user['name']} 선생님 — 채점 관리")
with col2:
    if st.button("🏆 랭킹 보기"):
        st.switch_page("pages/leaderboard.py")
with col3:
    if st.button("로그아웃"):
        st.session_state.user = None
        st.switch_page("app.py")

st.markdown("---")

tab_grade, tab_teacher = st.tabs(["📋 채점 관리", "👤 교사 추가"])

with tab_grade:
    col_search, col_refresh = st.columns([4, 1])
    with col_search:
        search = st.text_input("🔍 이름/학번 검색", placeholder="예: 홍길동, s2301")
    with col_refresh:
        st.markdown("<br>", unsafe_allow_html=True)
        refresh = st.button("🔄 새로고침")

    @st.cache_data(ttl=10)
    def load_submissions(teacher_id):
        students = supabase.table("users") \
            .select("name") \
            .eq("teacher_id", teacher_id) \
            .eq("role", "student") \
            .execute()
        student_names = [s["name"] for s in students.data]
        if not student_names:
            return []
        res = supabase.table("submissions") \
            .select("*") \
            .in_("name", student_names) \
            .order("submitted_at", desc=True) \
            .execute()
        return res.data

    if refresh:
        st.cache_data.clear()

    try:
        data = load_submissions(user["id"])
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
        data = []

    if search:
        data = [row for row in data if search.lower() in row["name"].lower()]

    st.markdown(f"**총 {len(data)}건** (내 반 학생 제출)")

    for row in data:
        row_id = row["id"]
        time_str = row["submitted_at"][:16].replace("T", " ")

        with st.container():
            st.markdown(f"""
            <div class="sub-card">
                <div>
                    <span class="sub-name">{row['name']}</span>
                    <span class="sub-problem">{row['problem']}</span>
                    <span class="sub-time">{time_str}</span>
                </div>
                <div style="color:#aaa; font-size:0.85rem; margin-top:6px;">설명: {row.get('description') or '없음'}</div>
                <div class="code-block">{row['code']}</div>
            </div>
            """, unsafe_allow_html=True)

            c1, c2, c3, c4, c5, c6 = st.columns([2, 2, 2, 2, 1.5, 1])
            with c1:
                s1 = st.number_input("기능(40)", 0, 40, int(row.get("score_function") or 0), key=f"s1_{row_id}")
            with c2:
                s2 = st.number_input("이해도(30)", 0, 30, int(row.get("score_understanding") or 0), key=f"s2_{row_id}")
            with c3:
                s3 = st.number_input("도전(20)", 0, 20, int(row.get("score_challenge") or 0), key=f"s3_{row_id}")
            with c4:
                s4 = st.number_input("제출시간(10)", 0, 10, int(row.get("score_time") or 0), key=f"s4_{row_id}")
            with c5:
                total = s1 + s2 + s3 + s4
                st.markdown(f"<br><div class='score-total'>합계: {total}점</div>", unsafe_allow_html=True)
            with c6:
                st.markdown("<br>", unsafe_allow_html=True)
                save_col, del_col = st.columns(2)
                with save_col:
                    if st.button("저장", key=f"save_{row_id}"):
                        try:
                            supabase.table("submissions").update({
                                "score_function": s1,
                                "score_understanding": s2,
                                "score_challenge": s3,
                                "score_time": s4,
                                "score_total": total
                            }).eq("id", row_id).execute()
                            st.cache_data.clear()
                            st.success(f"저장 완료! ({total}점)")
                        except Exception as e:
                            st.error(f"저장 오류: {e}")
                with del_col:
                    if st.button("삭제", key=f"del_{row_id}"):
                        try:
                            supabase.table("submissions").delete().eq("id", row_id).execute()
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"삭제 오류: {e}")
            st.markdown("---")

with tab_teacher:
    st.markdown("### 👤 교사 계정 추가")
    with st.container():
        st.markdown('<div style="background:white; border:1px solid #e0e4f0; border-radius:12px; padding:20px; margin-bottom:20px; box-shadow:0 2px 8px rgba(0,0,0,0.05);">', unsafe_allow_html=True)
        new_id   = st.text_input("교사 아이디", placeholder="예: teacher02")
        new_pw   = st.text_input("비밀번호", type="password", placeholder="비밀번호 입력")
        new_name = st.text_input("이름", placeholder="예: 박선생")
        if st.button("➕ 교사 추가"):
            if not new_id or not new_pw or not new_name:
                st.warning("모든 항목을 입력하세요.")
            else:
                try:
                    supabase.table("users").insert({
                        "id": new_id, "password": new_pw,
                        "name": new_name, "role": "teacher"
                    }).execute()
                    st.success(f"✅ '{new_name}' 선생님 계정이 추가되었습니다!")
                except Exception as e:
                    if "duplicate" in str(e).lower():
                        st.error("이미 존재하는 아이디예요.")
                    else:
                        st.error(f"추가 오류: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("### 📋 현재 교사 목록")
    try:
        teachers = supabase.table("users").select("id, name").eq("role", "teacher").execute()
        for t in teachers.data:
            st.markdown(f"""
            <div style="background:white; border:1px solid #e0e4f0; border-radius:8px;
                        padding:12px 18px; margin-bottom:8px;
                        box-shadow:0 2px 6px rgba(0,0,0,0.04);">
                <span style="color:#4f46e5; font-weight:700;">{t['id']}</span>
                <span style="color:#1a1a2e; margin-left:16px;">{t['name']} 선생님</span>
            </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"교사 목록 로드 오류: {e}")
