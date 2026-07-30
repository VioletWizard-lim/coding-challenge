import streamlit as st
from supabase import create_client
import time
from datetime import datetime
from problem_data import SUBJECTS

st.set_page_config(page_title="실시간 랭킹", page_icon="🏆", layout="centered")

@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["supabase"]["url"],
        st.secrets["supabase"]["key"]
    )

supabase = get_supabase()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
[data-testid="stSidebarNav"] { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }

* { font-family: 'Noto Sans KR', sans-serif; }
[data-testid="stAppViewContainer"] { background: #f5f7fa; }
.block-container { max-width: 700px !important; padding-top: 40px !important; }

.lb-title {
    text-align: center; font-size: 2.5rem; font-weight: 900;
    color: #1a1a2e; margin-bottom: 8px;
}
.lb-sub { text-align: center; color: #aaa; font-size: 0.9rem; margin-bottom: 32px; }

.rank-card {
    display: flex; align-items: center;
    background: white; border: 1px solid #e0e4f0;
    border-radius: 14px; padding: 18px 24px; margin-bottom: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.rank-card.gold { border-color: #FFD700; box-shadow: 0 4px 16px rgba(255,215,0,0.2); background: #fffdf0; }
.rank-card.silver { border-color: #C0C0C0; background: #fafafa; }
.rank-card.bronze { border-color: #CD7F32; background: #fffaf5; }
.rank-icon { font-size: 2rem; width: 50px; text-align: center; }
.rank-num { font-size: 1.2rem; font-weight: 900; color: #ccc; width: 50px; text-align: center; }
.rank-name { flex: 1; font-size: 1.2rem; font-weight: 700; color: #1a1a2e; margin-left: 16px; }
.rank-score { font-size: 1.5rem; font-weight: 900; color: #4f46e5; }
.rank-score.gold-score { color: #d4a800; }
.empty-msg { text-align: center; color: #aaa; padding: 60px 0; font-size: 1.1rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="lb-title">🏆 실시간 코딩 랭킹 🏆</div>', unsafe_allow_html=True)

def load_leaderboard(subject, year, grade=None, class_=None):
    try:
        query = supabase.table("submissions") \
            .select("name, problem, score_total, submitted_at, grade, class") \
            .eq("subject", subject) \
            .eq("year", year) \
            .gt("score_total", 0)

        if grade:
            query = query.eq("grade", grade)
        if class_:
            query = query.eq("class", class_)

        res = query.execute()

        # 학생별, 문제별 최신 채점만 반영
        best = {}  # {name: {problem: {score, at}}}
        for row in res.data:
            name = row["name"]
            problem = row["problem"]
            at = row["submitted_at"]
            score = row["score_total"] or 0
            if name not in best:
                best[name] = {}
            if problem not in best[name] or at > best[name][problem]["at"]:
                best[name][problem] = {"score": score, "at": at}

        scores = {}
        for name, problems in best.items():
            total = sum(p["score"] for p in problems.values())
            last_at = max(p["at"] for p in problems.values())
            scores[name] = {"total": total, "last_at": last_at}

        rank_list = [{"name": k, "total": v["total"], "last_at": v["last_at"]} for k, v in scores.items()]
        rank_list.sort(key=lambda x: (-x["total"], x["last_at"]))
        return rank_list
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
        return []

def load_classes(subject, year):
    try:
        res = supabase.table("submissions") \
            .select("grade, class") \
            .eq("subject", subject) \
            .eq("year", year) \
            .gt("score_total", 0) \
            .execute()
        seen = set()
        result = []
        for row in res.data:
            g = row.get("grade") or ""
            c = row.get("class") or ""
            if g and c:
                key = (g, c)
                if key not in seen:
                    seen.add(key)
                    result.append(key)
        result.sort()
        return result
    except:
        return []

def load_years():
    try:
        res = supabase.table("submissions").select("year").gt("score_total", 0).execute()
        years = sorted({row["year"] for row in res.data if row.get("year")}, reverse=True)
        return years
    except:
        return []

user = st.session_state.get("user")
is_student = bool(user and user.get("role") == "student")

# ── 과목 / 연도 선택 ──────────────────────────────────────
subject_list = list(SUBJECTS.keys())
sel_col1, sel_col2 = st.columns(2)
with sel_col1:
    sel_subject = st.selectbox("과목", subject_list, key="lb_subject") if len(subject_list) > 1 else subject_list[0]
with sel_col2:
    current_year = datetime.now().year
    year_options = load_years()
    if current_year not in year_options:
        year_options = sorted(year_options + [current_year], reverse=True)
    sel_year = st.selectbox("연도", year_options, key="lb_year")

if is_student and sel_subject == "프로그래밍":
    user_grade = user.get("programming_grade") or user.get("grade")
    user_class = user.get("programming_class") or user.get("class")
elif is_student:
    user_grade = user.get("grade")
    user_class = user.get("class")
else:
    user_grade = None
    user_class = None

# ── 반 선택 / 탭 (타이틀 바로 아래) ──────────────────────
if user_grade and user_class:
    tab1, tab2 = st.tabs([f"🏫 {user_grade}학년 {user_class}반 랭킹", "🌍 전체 랭킹"])
else:
    classes_list = load_classes(sel_subject, sel_year)
    options = ["전체"] + [f"{g}학년 {c}반" for g, c in classes_list]
    selected = st.selectbox("반 선택", options, label_visibility="collapsed")

# ── 메인으로 / 자동 새로고침 ──────────────────────────────
col1, col2 = st.columns(2)
with col1:
    if st.button("🏠 메인으로", use_container_width=True):
        st.switch_page("app.py")
with col2:
    auto_refresh = st.toggle("🔄 자동 새로고침 (30초)", value=True)

placeholder = st.empty()

def render(rank_list, subtitle=""):
    with placeholder.container():
        if subtitle:
            st.markdown(f'<div class="lb-sub">{subtitle}</div>', unsafe_allow_html=True)

        if not rank_list:
            st.markdown('<div class="empty-msg">아직 점수가 없어요 😊</div>', unsafe_allow_html=True)
            return

        icons = ["🥇", "🥈", "🥉"]
        classes = ["gold", "silver", "bronze"]

        for i, item in enumerate(rank_list):
            rank = i + 1
            card_class = classes[i] if i < 3 else ""
            icon_html = f'<div class="rank-icon">{icons[i]}</div>' if i < 3 else f'<div class="rank-num">{rank}</div>'
            score_class = "gold-score" if i == 0 else ""

            st.markdown(f"""
            <div class="rank-card {card_class}">
                {icon_html}
                <div class="rank-name">{item['name']}</div>
                <div class="rank-score {score_class}">{item['total']}점</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f'<div class="lb-sub">총 {len(rank_list)}명 참여 중</div>', unsafe_allow_html=True)

if user_grade and user_class:
    with tab1:
        render(load_leaderboard(sel_subject, sel_year, grade=user_grade, class_=user_class),
               subtitle=f"{sel_year} · {sel_subject} · {user_grade}학년 {user_class}반 학생들의 랭킹")
    with tab2:
        render(load_leaderboard(sel_subject, sel_year), subtitle=f"{sel_year} · {sel_subject} 전체 학생 랭킹")
else:
    if selected == "전체":
        render(load_leaderboard(sel_subject, sel_year), subtitle=f"{sel_year} · {sel_subject} 전체 학생 랭킹")
    else:
        idx = options.index(selected) - 1
        g, c = classes_list[idx]
        render(load_leaderboard(sel_subject, sel_year, grade=g, class_=c), subtitle=f"{sel_year} · {sel_subject} · {g}학년 {c}반 학생들의 랭킹")

if auto_refresh:
    time.sleep(30)
    st.rerun()
