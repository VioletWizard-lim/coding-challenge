import streamlit as st
from supabase import create_client
from datetime import datetime, timezone, timedelta

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

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
* { font-family: 'Noto Sans KR', sans-serif; }
[data-testid="stSidebarNav"] { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }
[data-testid="stAppViewContainer"] { background: #f5f7fa; }
.block-container { padding-top: 60px !important; }
h3 { color: #1a1a2e !important; }
label { color: #555 !important; }
.stTextInput input { background: white !important; border-color: #dde1f0 !important; color: #1a1a2e !important; }
.stNumberInput input { background: white !important; border-color: #dde1f0 !important; color: #1a1a2e !important; text-align: center; }
.stButton > button {
    background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
    color: white !important; border: none !important;
    border-radius: 8px !important; font-weight: 700 !important;
    white-space: nowrap !important;
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
    background: #f8f9fc; border: 1px solid #e0e4f0; border-radius: 8px; padding: 12px;
    font-family: 'Courier New', monospace; font-size: 0.85rem; color: #4f46e5;
    white-space: pre-wrap; max-height: 150px; overflow-y: auto; margin: 10px 0;
}
.score-total { font-size: 1.4rem; font-weight: 900; color: #4f46e5; }
</style>
""", unsafe_allow_html=True)

# ── 헤더 ──────────────────────────────────────────────────
col_title, col1, col2, col3 = st.columns([4, 1.2, 1.2, 1.2])
with col_title:
    st.markdown(f"### 👨‍🏫 {user['name']} 선생님 — 채점 관리")
with col1:
    if st.button("🏆 랭킹", use_container_width=True):
        st.switch_page("pages/leaderboard.py")
with col2:
    if st.button("🔄 새로고침", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
with col3:
    if st.button("🚪 로그아웃", use_container_width=True):
        st.session_state.user = None
        st.switch_page("app.py")

st.markdown("---")

@st.cache_data(ttl=10)
def load_submissions():
    res = supabase.table("submissions") \
        .select("*") \
        .order("submitted_at", desc=True) \
        .execute()
    return res.data

def render_grading(data, key_prefix=""):
    top_col1, top_col2 = st.columns([1, 5])
    with top_col1:
        if st.button("💾 전체 저장", use_container_width=True, key=f"save_all_{key_prefix}"):
            try:
                count = 0
                for row in data:
                    rid = row["id"]
                    s1 = st.session_state.get(f"s1_{key_prefix}_{rid}", int(row.get("score_function") or 0))
                    s2 = st.session_state.get(f"s2_{key_prefix}_{rid}", int(row.get("score_understanding") or 0))
                    s3 = st.session_state.get(f"s3_{key_prefix}_{rid}", int(row.get("score_challenge") or 0))
                    s4 = st.session_state.get(f"s4_{key_prefix}_{rid}", int(row.get("score_time") or 0))
                    total = s1 + s2 + s3 + s4
                    supabase.table("submissions").update({
                        "score_function": s1, "score_understanding": s2,
                        "score_challenge": s3, "score_time": s4, "score_total": total
                    }).eq("id", rid).execute()
                    count += 1
                st.cache_data.clear()
                st.success(f"✅ {count}건 전체 저장 완료!")
                st.rerun()
            except Exception as e:
                st.error(f"저장 오류: {e}")
    with top_col2:
        st.markdown(f"<div style='padding-top:8px; color:#888;'>총 {len(data)}건</div>", unsafe_allow_html=True)

    for row in data:
        row_id = row["id"]
        time_str = to_kst(row["submitted_at"])
        class_info = ""
        if row.get("grade") and row.get("class"):
            class_info = f'<span style="background:#e8f4fd; color:#2563eb; padding:2px 8px; border-radius:12px; font-size:0.8rem; font-weight:700; margin-left:8px;">{row["grade"]}학년 {row["class"]}반</span>'

        with st.container():
            st.markdown(f"""
            <div class="sub-card">
                <div>
                    <span class="sub-name">{row['name']}</span>{class_info}
                    <span class="sub-problem">{row['problem']}</span>
                    <span class="sub-time">{time_str}</span>
                </div>
                <div style="color:#aaa; font-size:0.85rem; margin-top:6px;">설명: {row.get('description') or '없음'}</div>
                <div class="code-block">{row['code']}</div>
            </div>
            """, unsafe_allow_html=True)

            c1, c2, c3, c4, c5, c6 = st.columns([2, 2, 2, 2, 1.5, 1])
            with c1:
                s1 = st.number_input("기능(40)", 0, 40, int(row.get("score_function") or 0), key=f"s1_{key_prefix}_{row_id}")
            with c2:
                s2 = st.number_input("이해도(30)", 0, 30, int(row.get("score_understanding") or 0), key=f"s2_{key_prefix}_{row_id}")
            with c3:
                s3 = st.number_input("도전(20)", 0, 20, int(row.get("score_challenge") or 0), key=f"s3_{key_prefix}_{row_id}")
            with c4:
                s4 = st.number_input("제출시간(10)", 0, 10, int(row.get("score_time") or 0), key=f"s4_{key_prefix}_{row_id}")
            with c5:
                total = s1 + s2 + s3 + s4
                st.markdown(f"<br><div class='score-total'>합계: {total}점</div>", unsafe_allow_html=True)
            with c6:
                st.markdown("<br>", unsafe_allow_html=True)
                save_col, del_col = st.columns(2)
                with save_col:
                    if st.button("저장", key=f"save_{key_prefix}_{row_id}"):
                        try:
                            supabase.table("submissions").update({
                                "score_function": s1,
                                "score_understanding": s2,
                                "score_challenge": s3,
                                "score_time": s4,
                                "score_total": total
                            }).eq("id", row_id).execute()
                            st.cache_data.clear()
                            st.toast(f"✅ {row['name']} — {row['problem']} 저장 완료! ({total}점)")
                        except Exception as e:
                            st.toast(f"❌ 저장 오류: {e}")
                with del_col:
                    if st.button("삭제", key=f"del_{key_prefix}_{row_id}"):
                        try:
                            supabase.table("submissions").delete().eq("id", row_id).execute()
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"삭제 오류: {e}")
            st.markdown("---")

tab_filtered, tab_all, tab_student, tab_teacher = st.tabs(["🏫 반별/문제별 채점", "📋 전체 목록", "🔍 학생별 코드 확인", "👤 교사 추가"])

with tab_filtered:
    try:
        all_data = load_submissions()
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
        all_data = []

    # 반 목록 동적 추출
    grade_set = sorted(set(r["grade"] for r in all_data if r.get("grade")))
    class_set = sorted(set(r["class"] for r in all_data if r.get("class")))
    problems = ["전체"] + [f"{i}-{j}" for i in range(1, 10) for j in range(1, 4)]

    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        sel_grade = st.selectbox("학년", ["전체"] + grade_set, key="filter_grade")
    with fc2:
        sel_class = st.selectbox("반", ["전체"] + class_set, key="filter_class")
    with fc3:
        sel_problem = st.selectbox("문제", problems, key="filter_problem")

    filtered = all_data
    if sel_grade != "전체":
        filtered = [r for r in filtered if r.get("grade") == sel_grade]
    if sel_class != "전체":
        filtered = [r for r in filtered if r.get("class") == sel_class]
    if sel_problem != "전체":
        filtered = [r for r in filtered if r.get("problem") == sel_problem]

    render_grading(filtered, key_prefix="filtered")

with tab_all:
    try:
        all_data2 = load_submissions()
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
        all_data2 = []

    search = st.text_input("🔍 이름/학번 검색", placeholder="예: 홍길동, s2301", key="search_all")
    if search:
        all_data2 = [r for r in all_data2 if search.lower() in r["name"].lower()]

    render_grading(all_data2, key_prefix="all")

with tab_student:
    try:
        all_data3 = load_submissions()
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
        all_data3 = []

    # 학생 목록 추출
    student_names = sorted(set(r["name"] for r in all_data3))

    if not student_names:
        st.info("아직 제출된 데이터가 없어요.")
    else:
        sc1, sc2 = st.columns([2, 4])
        with sc1:
            sel_student = st.selectbox("학생 선택", student_names, key="sel_student")
        with sc2:
            problems_all = ["전체"] + [f"{i}-{j}" for i in range(1, 10) for j in range(1, 4)]
            sel_prob = st.selectbox("문제 선택", problems_all, key="sel_prob_student")

        student_data = [r for r in all_data3 if r["name"] == sel_student]
        if sel_prob != "전체":
            student_data = [r for r in student_data if r["problem"] == sel_prob]

        student_data.sort(key=lambda x: x["submitted_at"], reverse=True)

        if not student_data:
            st.info("해당 조건의 제출물이 없어요.")
        else:
            st.markdown(f"**{sel_student}** — 총 {len(student_data)}건")
            for row in student_data:
                time_str = to_kst(row["submitted_at"])
                total = row.get("score_total") or 0
                score_badge = f'<span style="color:#4f46e5; font-weight:900;">{total}점</span>' if total > 0 else '<span style="color:#aaa;">채점 중</span>'
                class_badge = ""
                if row.get("grade") and row.get("class"):
                    class_badge = f'<span style="background:#e8f4fd; color:#2563eb; padding:2px 8px; border-radius:12px; font-size:0.8rem; font-weight:700; margin-left:8px;">{row["grade"]}학년 {row["class"]}반</span>'

                with st.expander(f"**{row['problem']}** · {time_str} · {total}점" if total > 0 else f"**{row['problem']}** · {time_str} · 채점 중"):
                    st.markdown(f'<div style="margin-bottom:8px;">{class_badge} {score_badge}</div>', unsafe_allow_html=True)
                    if row.get("description"):
                        st.caption(f"설명: {row['description']}")
                    st.code(row.get("code") or "", language="python")

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
                        padding:12px 18px; margin-bottom:8px; box-shadow:0 2px 6px rgba(0,0,0,0.04);">
                <span style="color:#4f46e5; font-weight:700;">{t['id']}</span>
                <span style="color:#1a1a2e; margin-left:16px;">{t['name']} 선생님</span>
            </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"교사 목록 로드 오류: {e}")
