import streamlit as st
from supabase import create_client
import time

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
/* 사이드바 메뉴 숨기기 */
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

def load_leaderboard():
    try:
        res = supabase.table("submissions") \
            .select("name, score_total, submitted_at") \
            .gt("score_total", 0) \
            .execute()

        scores = {}
        for row in res.data:
            name = row["name"]
            total = row["score_total"] or 0
            if name not in scores:
                scores[name] = {"total": 0, "last_at": row["submitted_at"]}
            scores[name]["total"] += total
            if row["submitted_at"] > scores[name]["last_at"]:
                scores[name]["last_at"] = row["submitted_at"]

        rank_list = [{"name": k, "total": v["total"], "last_at": v["last_at"]} for k, v in scores.items()]
        rank_list.sort(key=lambda x: (-x["total"], x["last_at"]))
        return rank_list
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
        return []

col1, col2 = st.columns(2)
with col1:
    if st.button("🏠 메인으로", use_container_width=True):
        st.switch_page("app.py")
with col2:
    auto_refresh = st.toggle("🔄 자동 새로고침 (30초)", value=True)
placeholder = st.empty()

def render(rank_list):
    with placeholder.container():
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

render(load_leaderboard())

if auto_refresh:
    time.sleep(30)
    st.rerun()
