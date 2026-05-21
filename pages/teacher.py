import streamlit as st
from supabase import create_client
from datetime import datetime, timezone, timedelta
import extra_streamlit_components as stx
import streamlit.components.v1 as components

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
cookie_manager = stx.CookieManager(key="teacher_cookies")

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
    white-space: pre; max-height: 260px; overflow-y: auto; margin: 10px 0;
}
.score-total { font-size: 1.4rem; font-weight: 900; color: #4f46e5; }

/* 채점 중 화면 흐림 방지 */
[data-stale="true"] { opacity: 1 !important; }
.stApp { opacity: 1 !important; }

/* Streamlit 햄버거 메뉴 숨기기 */
#MainMenu { visibility: hidden !important; }
header[data-testid="stHeader"] { display: none !important; }
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
        with st.spinner("새로고침 중..."):
            st.cache_data.clear()
        st.rerun()
with col3:
    if st.button("🚪 로그아웃", use_container_width=True):
        try:
            cookie_manager.delete("session")
        except:
            pass
        st.session_state.user = None
        st.switch_page("app.py")

st.markdown("---")

# 'C' 키 단축키(Clear caches) 차단
components.html("""<script>
window.parent.document.addEventListener('keydown', function(e) {
    if ((e.key === 'c' || e.key === 'C') && !e.ctrlKey && !e.metaKey && !e.altKey) {
        var t = e.target;
        if (t.tagName !== 'INPUT' && t.tagName !== 'TEXTAREA' && !t.isContentEditable) {
            e.stopImmediatePropagation();
        }
    }
}, true);
</script>""", height=0)

@st.cache_data(ttl=3600)
def load_submissions():
    res = supabase.table("submissions") \
        .select("*") \
        .order("submitted_at", desc=True) \
        .execute()
    return res.data

@st.fragment(run_every=15)
def notify_new_submissions():
    try:
        res = supabase.table("submissions") \
            .select("id, name, problem") \
            .order("submitted_at", desc=True) \
            .limit(100) \
            .execute()
        current_ids = {r["id"] for r in res.data}

        if st.session_state.get("known_submission_ids") is None:
            st.session_state.known_submission_ids = current_ids
        else:
            new_subs = [r for r in res.data if r["id"] not in st.session_state.known_submission_ids]
            for sub in new_subs:
                st.toast(f"📬 {sub['name']} — {sub['problem']} 제출!", icon="🔔")
            if new_subs:
                st.session_state.known_submission_ids = current_ids
                st.cache_data.clear()
    except:
        pass

notify_new_submissions()

def render_grading(data, key_prefix=""):
    PAGE_SIZE = 15
    total_count = len(data)
    page_key = f"page_{key_prefix}"
    hash_key = f"hash_{key_prefix}"

    # 필터 변경 시 첫 페이지로 리셋
    data_hash = total_count
    if st.session_state.get(hash_key) != data_hash:
        st.session_state[page_key] = 0
        st.session_state[hash_key] = data_hash
    page = st.session_state.get(page_key, 0)
    start = page * PAGE_SIZE
    end = min(start + PAGE_SIZE, total_count)
    page_data = data[start:end]

    top_col1, top_col2, top_col3, top_col4, top_col5 = st.columns([1.2, 1, 1, 3, 1.2])
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
        if st.button("◀ 이전", use_container_width=True, key=f"prev_{key_prefix}", disabled=page == 0):
            st.session_state[page_key] = page - 1
            st.rerun()
    with top_col3:
        if st.button("다음 ▶", use_container_width=True, key=f"next_{key_prefix}", disabled=end >= total_count):
            st.session_state[page_key] = page + 1
            st.rerun()
    with top_col4:
        st.markdown(f"<div style='padding-top:8px; color:#888;'>{start+1}~{end} / 총 {total_count}건</div>", unsafe_allow_html=True)

    for row in page_data:
        row_id = row["id"]
        time_str = to_kst(row["submitted_at"])
        class_info = ""
        if row.get("grade") and row.get("class"):
            class_info = f'<span style="background:#e8f4fd; color:#2563eb; padding:2px 8px; border-radius:12px; font-size:0.8rem; font-weight:700; margin-left:8px;">{row["grade"]}학년 {row["class"]}반</span>'

        with st.container():
            wrong_reason = row.get("wrong_reason") or ""
            wrong_badge = f'<span style="background:#fee2e2; color:#dc2626; padding:2px 10px; border-radius:12px; font-size:0.8rem; font-weight:700; margin-left:8px;">⚠️ 오답: {wrong_reason}</span>' if wrong_reason else ""
            st.markdown(f"""
            <div class="sub-card">
                <div>
                    <span class="sub-name">{row['name']}</span>{class_info}{wrong_badge}
                    <span class="sub-problem">{row['problem']}</span>
                    <span class="sub-time">{time_str}</span>
                </div>
                <div style="color:#aaa; font-size:0.85rem; margin-top:6px;">설명: {row.get('description') or '없음'}</div>
            </div>
            """, unsafe_allow_html=True)
            st.code(row.get('code') or '', language='python')

            c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 1.5])
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

            f1, f2, f3 = st.columns([4, 1, 1])
            with f1:
                feedback_input = st.text_input("감점 이유", value=row.get("feedback") or "", placeholder="감점 이유를 입력하세요 (학생에게 표시됩니다)", key=f"feedback_{key_prefix}_{row_id}", label_visibility="collapsed")
            with f2:
                if st.button("저장", key=f"save_{key_prefix}_{row_id}", use_container_width=True):
                    try:
                        supabase.table("submissions").update({
                            "score_function": s1, "score_understanding": s2,
                            "score_challenge": s3, "score_time": s4,
                            "score_total": total, "feedback": feedback_input
                        }).eq("id", row_id).execute()
                        st.cache_data.clear()
                        st.toast(f"✅ {row['name']} — {row['problem']} 저장 완료! ({total}점)")
                        st.rerun()
                    except Exception as e:
                        st.toast(f"❌ 저장 오류: {e}")
            with f3:
                if st.button("삭제", key=f"del_{key_prefix}_{row_id}", use_container_width=True):
                    try:
                        supabase.table("submissions").delete().eq("id", row_id).execute()
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"삭제 오류: {e}")

            w1, w2, w3 = st.columns([4, 1, 1])
            with w1:
                wrong_input = st.text_input("오답 이유", value=wrong_reason, placeholder="오답 이유를 입력하세요", key=f"wrong_{key_prefix}_{row_id}", label_visibility="collapsed", disabled=total > 0)
            with w2:
                if st.button("⚠️ 오답처리", key=f"wrong_btn_{key_prefix}_{row_id}", use_container_width=True, disabled=total > 0):
                    try:
                        supabase.table("submissions").update({"wrong_reason": wrong_input}).eq("id", row_id).execute()
                        st.cache_data.clear()
                        st.toast(f"⚠️ {row['name']} — {row['problem']} 오답처리 완료!")
                        st.rerun()
                    except Exception as e:
                        st.toast(f"❌ 오류: {e}")
            with w3:
                if st.button("🗑️ 오답 해제", key=f"wrong_clear_{key_prefix}_{row_id}", use_container_width=True, disabled=not wrong_reason):
                    try:
                        supabase.table("submissions").update({"wrong_reason": None}).eq("id", row_id).execute()
                        st.cache_data.clear()
                        st.toast(f"✅ {row['name']} — {row['problem']} 오답 해제 완료!")
                        st.rerun()
                    except Exception as e:
                        st.toast(f"❌ 오류: {e}")
            st.markdown("---")

tab_grade, tab_student, tab_stats, tab_teacher = st.tabs(["📋 채점 관리", "🔍 학생별 코드 확인", "📊 반별 현황", "👤 교사 추가"])

with tab_grade:
    try:
        all_data = load_submissions()
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
        all_data = []

    grade_class_set = sorted(set(
        (r["grade"], r["class"]) for r in all_data if r.get("grade") and r.get("class")
    ))
    gc_options = ["전체"] + [f"{g}학년 {c}반" for g, c in grade_class_set]
    problems = ["전체"] + [f"{i}-{j}" for i in range(1, 10) for j in range(1, 4)]

    fc1, fc2, fc3, fc4 = st.columns([2, 1.5, 2, 1.5])
    with fc1:
        sel_gc = st.selectbox("학년-반", gc_options, key="filter_gc")
    with fc2:
        sel_problem = st.selectbox("문제", problems, key="filter_problem")
    with fc3:
        search = st.text_input("이름 검색", placeholder="예: 홍길동", key="search_name")
    with fc4:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        only_ungraded = st.checkbox("미채점만 보기", key="only_ungraded")

    filtered = all_data
    if sel_gc != "전체":
        idx = gc_options.index(sel_gc) - 1
        sel_grade, sel_class = grade_class_set[idx]
        filtered = [r for r in filtered if r.get("grade") == sel_grade and r.get("class") == sel_class]
    if sel_problem != "전체":
        filtered = [r for r in filtered if r.get("problem") == sel_problem]
    if search:
        filtered = [r for r in filtered if search.lower() in r["name"].lower()]
    if only_ungraded:
        filtered = [r for r in filtered if not (r.get("score_total") or 0) > 0 and not r.get("wrong_reason")]

    render_grading(filtered, key_prefix="grade")

with tab_student:
    try:
        all_data3 = load_submissions()
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
        all_data3 = []

    # 이름 → 학번 매핑
    try:
        users_res = supabase.table("users").select("id, name").eq("role", "student").execute()
        student_id_map = {r["name"]: r["id"][1:6] for r in users_res.data if r.get("id") and len(r["id"]) >= 6}
    except:
        student_id_map = {}

    def student_label(name):
        num = student_id_map.get(name, "")
        return f"{num} {name}" if num else name

    student_names = sorted(set(r["name"] for r in all_data3), key=student_label)

    if not student_names:
        st.info("아직 제출된 데이터가 없어요.")
    else:
        sc1, sc2 = st.columns([2, 4])
        with sc1:
            sel_student = st.selectbox("학생 선택", student_names, format_func=student_label, key="sel_student")
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
            st.markdown(f"**{student_label(sel_student)}** — 총 {len(student_data)}건")
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

with tab_stats:
    import pandas as pd

    try:
        res = supabase.table("submissions") \
            .select("name, problem, score_total, submitted_at, grade, class") \
            .gt("score_total", 0) \
            .execute()
        raw = res.data
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
        raw = []

    if not raw:
        st.info("아직 채점된 데이터가 없어요.")
    else:
        # 반 목록
        try:
            users_res2 = supabase.table("users").select("id, name").eq("role", "student").execute()
            sid_map = {r["name"]: r["id"][1:6] for r in users_res2.data if r.get("id") and len(r["id"]) >= 6}
        except:
            sid_map = {}

        gc_set = sorted(set(
            (r["grade"], r["class"]) for r in raw if r.get("grade") and r.get("class")
        ))
        gc_opts = [f"{g}학년 {c}반" for g, c in gc_set]

        if not gc_opts:
            st.info("반 정보가 없어요.")
        else:
            sel_gc_stats = st.selectbox("반 선택", gc_opts, key="stats_gc")
            sel_g, sel_c = gc_set[gc_opts.index(sel_gc_stats)]

            # 해당 반 데이터, 학생별·문제별 최신 점수
            best = {}
            for row in raw:
                if row.get("grade") != sel_g or row.get("class") != sel_c:
                    continue
                key = (row["name"], row["problem"])
                if key not in best or row["submitted_at"] > best[key]["at"]:
                    best[key] = {"score": row["score_total"] or 0, "at": row["submitted_at"]}

            if not best:
                st.info("해당 반의 채점 데이터가 없어요.")
            else:
                records = [{"학생": k[0], "문제": k[1], "점수": v["score"]} for k, v in best.items()]
                df = pd.DataFrame(records)
                all_problems = [f"{i}-{j}" for i in range(1, 10) for j in range(1, 4)]
                pivot = df.pivot_table(index="학생", columns="문제", values="점수", aggfunc="sum", fill_value=0)
                cols = [p for p in all_problems if p in pivot.columns]
                pivot = pivot[cols]
                pivot.insert(0, "합계", pivot.sum(axis=1))

                # 학번 기준 정렬
                pivot = pivot.reset_index()
                pivot["_sort"] = pivot["학생"].map(lambda n: sid_map.get(n, ""))
                pivot = pivot.sort_values("_sort").drop(columns="_sort")
                pivot["학생"] = pivot["학생"].map(lambda n: f"{sid_map.get(n, '')} {n}".strip())
                pivot = pivot.set_index("학생")

                st.markdown(f"### {sel_gc_stats} 학생별 점수 현황")
                st.dataframe(pivot, use_container_width=True)

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
