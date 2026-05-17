import streamlit as st
import requests

API_URL = "http://localhost:8000"

st.set_page_config(page_title="IPL Akinator", page_icon="🏏", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background-color: #0F172A !important;
    color: #F1F5F9;
    font-family: 'Inter', sans-serif;
}
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stBottom"] { background: transparent !important; }
section[data-testid="stSidebar"] { display: none; }

/* All buttons base */
.stButton > button {
    width: 100% !important;
    padding: 0.85rem 1.5rem !important;
    border-radius: 14px !important;
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    border: none !important;
    cursor: pointer !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease !important;
    letter-spacing: 0.3px !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
}

/* Yes button — col 1 */
div[data-testid="column"]:nth-child(1) .stButton > button {
    background: linear-gradient(135deg, #10B981, #059669) !important;
    color: white !important;
    box-shadow: 0 4px 20px rgba(16,185,129,0.35) !important;
}
/* No button — col 2 */
div[data-testid="column"]:nth-child(2) .stButton > button {
    background: linear-gradient(135deg, #EF4444, #DC2626) !important;
    color: white !important;
    box-shadow: 0 4px 20px rgba(239,68,68,0.35) !important;
}
/* Unsure button — col 3 */
div[data-testid="column"]:nth-child(3) .stButton > button {
    background: linear-gradient(135deg, #6366F1, #4F46E5) !important;
    color: white !important;
    box-shadow: 0 4px 20px rgba(99,102,241,0.35) !important;
}
/* Start / Play again button */
.start-btn .stButton > button {
    background: linear-gradient(135deg, #3B82F6, #2563EB) !important;
    color: white !important;
    font-size: 1.2rem !important;
    padding: 1rem 2rem !important;
    box-shadow: 0 4px 24px rgba(59,130,246,0.4) !important;
}

.card {
    background: linear-gradient(135deg, #1E293B, #0F172A);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 20px;
    padding: 2.5rem 2rem;
    text-align: center;
    box-shadow: 0 25px 60px rgba(0,0,0,0.5);
    margin-bottom: 2rem;
}
.question-text {
    font-size: 1.75rem;
    font-weight: 700;
    color: #F1F5F9;
    line-height: 1.4;
    margin: 0.5rem 0 1.5rem;
}
.meta-row {
    display: flex;
    justify-content: space-between;
    color: #64748B;
    font-size: 0.85rem;
    font-weight: 600;
    margin-bottom: 0.75rem;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}
.guess-card {
    background: #1E293B;
    border: 1px solid rgba(255,255,255,0.06);
    border-left: 4px solid #3B82F6;
    border-radius: 14px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.guess-card.top { border-left-color: #10B981; }
.player-name { font-size: 1.2rem; font-weight: 700; color: #F1F5F9; }
.player-meta { font-size: 0.85rem; color: #64748B; margin-top: 3px; }
.badge {
    padding: 0.3rem 0.8rem;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 700;
    background: #3B82F6;
    color: white;
    white-space: nowrap;
}
.badge.top { background: #10B981; }
.reasoning {
    background: rgba(99,102,241,0.1);
    border: 1px solid rgba(99,102,241,0.25);
    border-radius: 10px;
    padding: 0.75rem 1rem;
    font-size: 0.85rem;
    color: #A5B4FC;
    margin-top: 1rem;
    text-align: left;
}
</style>
""", unsafe_allow_html=True)

# ── STATE INIT ────────────────────────────────────────────────────────────────
for key, val in [("session_id", None), ("action", None), ("turn", 1),
                 ("question", ""), ("col", ""), ("pool_size", 788), ("guesses", [])]:
    if key not in st.session_state:
        st.session_state[key] = val

# ── ACTIONS ───────────────────────────────────────────────────────────────────
def start_game():
    try:
        res = requests.post(f"{API_URL}/start").json()
        st.session_state.update({
            "session_id": res["session_id"],
            "question":   res["question"],
            "col":        res["col"],
            "pool_size":  res["pool_size"],
            "action":     "question",
            "guesses":    [],
            "turn":       1,
        })
    except Exception as e:
        st.error(f"Cannot reach backend: {e}")

def send_answer(response):
    try:
        res = requests.post(f"{API_URL}/answer", json={
            "session_id": st.session_state.session_id,
            "col":        st.session_state.col,
            "response":   response,
        }).json()
        st.session_state.action = res["action"]
        st.session_state.turn  += 1
        if res["action"] == "question":
            st.session_state.update({
                "question":  res["question"],
                "col":       res["col"],
                "pool_size": res["pool_size"],
                "guesses":   res.get("guesses", []),
            })
        else:
            st.session_state.guesses = res["guesses"]
    except Exception as e:
        st.error(f"Backend error: {e}")

# ── SCREENS ───────────────────────────────────────────────────────────────────
if st.session_state.session_id is None:
    st.markdown("""
    <div class="card">
        <div style="font-size:4rem;margin-bottom:0.5rem">🏏</div>
        <h1 style="font-size:2.8rem;font-weight:900;margin:0;
                   background:linear-gradient(135deg,#3B82F6,#10B981);
                   -webkit-background-clip:text;-webkit-text-fill-color:transparent">
            IPL Akinator
        </h1>
        <p style="color:#64748B;font-size:1.1rem;margin-top:0.75rem">
            Think of any IPL player — past or present.<br>
            The AI will figure out who it is.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="start-btn">', unsafe_allow_html=True)
        if st.button("Start Game 🚀"):
            start_game()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.action == "question":
    progress = min(1.0, st.session_state.turn / 20.0)
    pool     = st.session_state.pool_size

    # Live top guesses sidebar strip
    guesses = st.session_state.guesses
    if guesses:
        st.markdown(f"""
        <div class="reasoning">
            🧠 Currently leaning toward:
            {'  ·  '.join(f"<b>{g['player']}</b> ({g['confidence']}%)" for g in guesses[:2])}
            &nbsp;·&nbsp; {pool} candidates left
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="card">
        <div class="meta-row">
            <span>Question {st.session_state.turn} / 20</span>
            <span>{pool} players remaining</span>
        </div>
        <div class="question-text">{st.session_state.question}</div>
    </div>
    """, unsafe_allow_html=True)

    st.progress(progress)
    st.markdown("<br>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("👍  Yes"):
            send_answer("yes"); st.rerun()
    with c2:
        if st.button("👎  No"):
            send_answer("no"); st.rerun()
    with c3:
        if st.button("🤷  Not sure"):
            send_answer("unsure"); st.rerun()

elif st.session_state.action == "guess":
    st.markdown("""
    <div class="card">
        <div style="font-size:3rem">🎯</div>
        <h2 style="font-size:2rem;font-weight:900;color:#10B981;margin:0.5rem 0 0.25rem">
            Here's my guess
        </h2>
        <p style="color:#64748B;font-size:1rem">Ranked by confidence</p>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.guesses:
        st.warning("Nobody matched your answers. Try again with a different player!")
    else:
        for i, g in enumerate(st.session_state.guesses):
            top_class = "top" if i == 0 else ""
            st.markdown(f"""
            <div class="guess-card {top_class}">
                <div>
                    <div class="player-name">{'🥇 ' if i==0 else ''}{g['player']}</div>
                    <div class="player-meta">🏏 {g['runs']} runs &nbsp;·&nbsp; 🎳 {g['wickets']} wickets</div>
                </div>
                <div class="badge {top_class}">{g['confidence']}% match</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="start-btn">', unsafe_allow_html=True)
        if st.button("Play Again 🔄"):
            for key in ["session_id","action","turn","question","col","pool_size","guesses"]:
                del st.session_state[key]
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)