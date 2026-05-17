import streamlit as st
import requests
import base64
from engine import QUESTION_MAP

def get_base64_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

bg = get_base64_image("Gemini_Generated_Image_2q2v582q2v582q2v.png")

API_URL = os.environ.get("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="IPL Akinator",
    page_icon="🏏",
    layout="centered"
)
st.markdown(f"""
<style>
[data-testid="stAppViewContainer"] {{
    background-image: linear-gradient(
        rgba(9,9,11,0.82),
        rgba(9,9,11,0.92)
    ), url("data:image/png;base64,{bg}") !important;
    background-size: cover !important;
    background-position: center top !important;
    background-attachment: fixed !important;
}}
</style>
""", unsafe_allow_html=True)
# ── Global CSS (single block, no f-strings, no quotes inside style values) ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@700;900&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background: #09090B !important;
    color: #FAFAFA !important;
    font-family: 'DM Sans', sans-serif !important;
}
[data-testid="stHeader"] { background: transparent !important; }
section[data-testid="stSidebar"] { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
footer { display: none !important; }
.block-container {
    padding-top: 3rem !important;
    padding-bottom: 3rem !important;
    max-width: 780px !important;
}
.stButton > button {
    width: 100% !important;
    border-radius: 4px !important;
    padding: 0.85rem 1rem !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.92rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    transition: all 0.2s ease !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    background: #18181D !important;
    color: #A1A1AA !important;
    box-shadow: none !important;
}
.stButton > button:hover {
    border-color: #C8A96E !important;
    color: #C8A96E !important;
    transform: translateY(-1px) !important;
    background: rgba(200,169,110,0.06) !important;
}
.stButton > button:active { transform: scale(0.98) !important; }
[data-testid="stProgressBar"] > div {
    background: #3F3F46 !important;
    border-radius: 2px !important;
    height: 2px !important;
}
[data-testid="stProgressBar"] > div > div {
    background: #C8A96E !important;
    border-radius: 2px !important;
}
[data-testid="stImage"] img { border-radius: 4px !important; }
[data-testid="stAlert"] {
    background: #18181D !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 4px !important;
}
div[data-testid="stHorizontalBlock"]
  > div[data-testid="stColumn"]:nth-of-type(1) .stButton > button {
    border-color: rgba(78,204,163,0.4) !important;
    color: #4ECCA3 !important;
}
div[data-testid="stHorizontalBlock"]
  > div[data-testid="stColumn"]:nth-of-type(1) .stButton > button:hover {
    background: rgba(78,204,163,0.08) !important;
    border-color: #4ECCA3 !important;
}
div[data-testid="stHorizontalBlock"]
  > div[data-testid="stColumn"]:nth-of-type(2) .stButton > button {
    border-color: rgba(255,107,107,0.4) !important;
    color: #FF6B6B !important;
}
div[data-testid="stHorizontalBlock"]
  > div[data-testid="stColumn"]:nth-of-type(2) .stButton > button:hover {
    background: rgba(255,107,107,0.08) !important;
    border-color: #FF6B6B !important;
}
div[data-testid="stHorizontalBlock"]
  > div[data-testid="stColumn"]:nth-of-type(3) .stButton > button {
    border-color: rgba(126,191,255,0.4) !important;
    color: #7EBFFF !important;
}
div[data-testid="stHorizontalBlock"]
  > div[data-testid="stColumn"]:nth-of-type(3) .stButton > button:hover {
    background: rgba(126,191,255,0.08) !important;
    border-color: #7EBFFF !important;
}
</style>
""", unsafe_allow_html=True)

# ── Session state ──
defaults = {
    "session_id": None,
    "action": None,
    "turn": 1,
    "question": "",
    "col": "",
    "pool_size": 788,
    "guesses": []
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── Helpers ──
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
        st.error(f"Backend connection failed: {e}")


def send_answer(response):
    try:
        res = requests.post(
            f"{API_URL}/answer",
            json={"session_id": st.session_state.session_id,
                  "col": st.session_state.col,
                  "response": response}
        ).json()
        st.session_state.action = res["action"]
        st.session_state.turn  += 1
        st.session_state.score_history = res.get("score_history", [])  # ← NEW
        if res["action"] == "question":
            st.session_state.question  = res["question"]
            st.session_state.col       = res["col"]
            st.session_state.pool_size = res["pool_size"]
            st.session_state.guesses   = res.get("guesses", [])
        else:
            st.session_state.guesses = res["guesses"]
    except Exception as e:
        st.error(f"Backend error: {e}")


def player_photo_url(name: str) -> str:
    # Name mapping for players whose initials confuse Wikipedia
    NAME_OVERRIDES = {
        "HH Pandya":  "Hardik Pandya",
        "KH Pandya":  "Krunal Pandya",
        "RG Sharma":  "Rohit Sharma",
        "MS Dhoni":   "MS Dhoni",
        "SK Raina":   "Suresh Raina",
        "RA Jadeja":  "Ravindra Jadeja",
        "AB de Villiers": "AB de Villiers",
        "CH Gayle":   "Chris Gayle",
        "SR Tendulkar": "Sachin Tendulkar",
        "V Kohli":    "Virat Kohli",
        "RR Pant":    "Rishabh Pant",
        "JJ Bumrah":  "Jasprit Bumrah",
        "YK Pathan":  "Yusuf Pathan",
        "IK Pathan":  "Irfan Pathan",
        "PP Chawla":  "Piyush Chawla",
        "AM Rahane":  "Ajinkya Rahane",
        "KA Pollard": "Kieron Pollard",
        "DJ Bravo":   "Dwayne Bravo",
        "BA Stokes":  "Ben Stokes",
        "KS Williamson": "Kane Williamson",
        "AR Patel" : "Axar Patel",
        "YS Chahal": "Yuzvendra Chahal",
        "SP Narine": "Sunil Narine",
        "AD Russell" : "Andre Russell",
        "MJ Santner": "Mitchell Santner",
        "SM Curran": "Sam Curran",
        "DL Chahar": "Deepak Chahar",
    }

    search_name = NAME_OVERRIDES.get(name, name)

    try:
        # Try direct Wikipedia lookup with full name
        encoded = search_name.replace(" ", "_")
        r = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}",
            timeout=5,
            headers={'User-Agent': 'IPLAkinator/1.0'}
        )
        if r.status_code == 200:
            data = r.json()
            # Reject if it's not a person page
            if data.get("type") == "standard" and "cricketer" in data.get("description", "").lower():
                thumb = data.get("thumbnail", {}).get("source", "")
                if thumb:
                    for size in ["/80px-", "/100px-", "/150px-", "/220px-", "/320px-"]:
                        thumb = thumb.replace(size, "/400px-")
                    return thumb

        # Fallback: search API
        search_r = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                'action': 'query',
                'list': 'search',
                'srsearch': f"{search_name} cricketer IPL",
                'format': 'json',
                'utf8': 1
            },
            timeout=5,
            headers={'User-Agent': 'IPLAkinator/1.0'}
        )
        if search_r.status_code == 200:
            results = search_r.json().get('query', {}).get('search', [])
            for result in results[:3]:
                title = result['title']
                final_r = requests.get(
                    f"https://en.wikipedia.org/api/rest_v1/page/summary/{title.replace(' ', '_')}",
                    timeout=5,
                    headers={'User-Agent': 'IPLAkinator/1.0'}
                )
                if final_r.status_code == 200:
                    data = final_r.json()
                    desc = data.get("description", "").lower()
                    # Only accept if it's a person/cricketer page
                    if any(word in desc for word in ["cricketer", "cricket", "batsman", "bowler"]):
                        thumb = data.get("thumbnail", {}).get("source", "")
                        if thumb:
                            for size in ["/80px-", "/100px-", "/150px-", "/220px-", "/320px-"]:
                                thumb = thumb.replace(size, "/400px-")
                            return thumb
    except Exception:
        pass

    # Initials avatar fallback
    names = name.split()
    initials = (names[0][0] + names[-1][0]).upper() if len(names) >= 2 else name[0].upper()
    return (
        f"https://ui-avatars.com/api/?name={initials}"
        f"&background=18181D&color=C8A96E&size=400&bold=true&font-size=0.4"
    )


# ══════════════════════════════════════════════════════════════
# HOME SCREEN
# ══════════════════════════════════════════════════════════════
if st.session_state.session_id is None:

    st.write("")
    st.write("")

    st.markdown(
        '<p style="text-align:center;font-family:DM Mono,monospace;'
        'font-size:0.7rem;letter-spacing:0.2em;color:#C8A96E;'
        'text-transform:uppercase;margin-bottom:1.5rem;">'
        'IPL &nbsp;&middot;&nbsp; 2008 &ndash; 2024 &nbsp;&middot;&nbsp; 788 Players</p>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<h1 style="text-align:center;font-family:Cinzel,serif;'
        'font-size:clamp(2.8rem,8vw,5rem);font-weight:900;color:#FAFAFA;'
        'letter-spacing:0.04em;line-height:1;margin:0 0 1.2rem;">PJs IPL AKINATOR</h1>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<p style="text-align:center;color:#71717A;font-size:1rem;'
        'font-weight:300;letter-spacing:0.02em;line-height:1.8;margin:0;">'
        'Think of any IPL player.<br>Answer a few questions.<br>'
        'Watch the machine read your mind.</p>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div style="width:48px;height:1px;background:#C8A96E;'
        'margin:1.8rem auto 2rem;opacity:0.6;"></div>',
        unsafe_allow_html=True
    )

    _, col_c, _ = st.columns([1, 1.6, 1])
    with col_c:
        if st.button("Begin", use_container_width=True):
            start_game()
            st.rerun()

    st.markdown(
        '<p style="text-align:center;color:#3F3F46;'
        'font-family:DM Mono,monospace;font-size:0.72rem;'
        'letter-spacing:0.12em;margin-top:2rem;">UP TO 20 QUESTIONS</p>',
        unsafe_allow_html=True
    )


# ══════════════════════════════════════════════════════════════
# QUESTION SCREEN
# ══════════════════════════════════════════════════════════════
elif st.session_state.action == "question":

    pool     = st.session_state.pool_size
    turn     = st.session_state.turn
    guesses  = st.session_state.guesses
    progress = min(1.0, turn / 20.0)

    st.markdown(
        f'<div style="display:flex;justify-content:space-between;margin-bottom:0.5rem;">'
        f'<span style="font-family:DM Mono,monospace;font-size:0.72rem;'
        f'letter-spacing:0.14em;color:#52525B;text-transform:uppercase;">'
        f'Question {turn} / 20</span>'
        f'<span style="font-family:DM Mono,monospace;font-size:0.72rem;'
        f'letter-spacing:0.14em;color:#52525B;text-transform:uppercase;">'
        f'{pool} remaining</span></div>',
        unsafe_allow_html=True
    )

    st.progress(progress)

    if guesses:
        parts = " &nbsp;&middot;&nbsp; ".join(
            f"<strong style='color:#FAFAFA'>{g['player']}</strong> "
            f"<span style='color:#52525B'>{g['confidence']}%</span>"
            for g in guesses[:2]
        )
        st.markdown(
            f'<div style="margin:1.2rem 0 0.2rem;font-size:0.8rem;color:#52525B;">'
            f'<span style="color:#C8A96E;font-family:DM Mono,monospace;'
            f'font-size:0.7rem;letter-spacing:0.15em;text-transform:uppercase;'
            f'margin-right:0.6rem;">Leaning toward</span>{parts}</div>',
            unsafe_allow_html=True
        )

    st.markdown(
        '<div style="height:1px;background:rgba(255,255,255,0.06);margin:1.4rem 0 1.6rem;"></div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f'<p style="font-family:DM Sans,sans-serif;'
        f'font-size:clamp(1.3rem,4vw,1.75rem);font-weight:500;color:#FAFAFA;'
        f'line-height:1.55;margin:0 0 1.6rem;letter-spacing:-0.01em;">'
        f'{st.session_state.question}</p>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div style="height:1px;background:rgba(255,255,255,0.06);margin-bottom:1.8rem;"></div>',
        unsafe_allow_html=True
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("Yes", use_container_width=True):
            send_answer("yes");  st.rerun()
    with c2:
        if st.button("No", use_container_width=True):
            send_answer("no");   st.rerun()
    with c3:
        if st.button("Maybe", use_container_width=True):
            send_answer("maybe"); st.rerun()
    with c4:
        if st.button("Don't Know", use_container_width=True):
            send_answer("unsure"); st.rerun()

    # ── Score history ──
    if st.session_state.get("score_history"):
        st.markdown('<div style="margin-top:2rem;"></div>', unsafe_allow_html=True)
        with st.expander("📊 Score history so far"):
            for entry in st.session_state.score_history:
                st.markdown(
                    f'**Q{entry["turn"]}** `{entry["feature"]}` → **{entry["response"].upper()}**'
                )
                for g in entry["top3"]:
                    bar = "█" * int(g["confidence"] / 5)
                    st.markdown(
                        f'&nbsp;&nbsp;&nbsp;`{g["player"]:<25}` '
                        f'score: `{g["score"]:+.1f}` &nbsp; confidence: `{g["confidence"]}%` {bar}',
                        unsafe_allow_html=True
                    )
    

# ══════════════════════════════════════════════════════════════
# GUESS SCREEN
# ══════════════════════════════════════════════════════════════
elif st.session_state.action == "guess":

    st.markdown(
        '<div style="font-family:DM Mono,monospace;font-size:0.7rem;'
        'letter-spacing:0.2em;color:#C8A96E;text-transform:uppercase;'
        'text-align:center;margin-bottom:0.8rem;">Result</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<h2 style="font-family:Cinzel,serif;'
        'font-size:clamp(1.8rem,5vw,2.8rem);font-weight:900;color:#FAFAFA;'
        'letter-spacing:0.04em;text-align:center;margin:0;">My Best Guesses</h2>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div style="width:48px;height:1px;background:#C8A96E;'
        'margin:1.5rem auto 2rem;opacity:0.5;"></div>',
        unsafe_allow_html=True
    )

    if not st.session_state.guesses:
        st.warning("No player matched your answers. Try again with a different player.")
    else:
        rank_colors = ["#C8A96E", "#A8A9AD", "#CD7F32"]
        rank_labels = ["Gold", "Silver", "Bronze"]

        for i, g in enumerate(st.session_state.guesses):
            color = rank_colors[i] if i < 3 else "#52525B"
            label = rank_labels[i] if i < 3 else f"#{i+1}"
            photo = player_photo_url(g["player"])

            img_col, info_col = st.columns([1, 3])

            with img_col:
                st.image(photo, use_container_width=True)

            with info_col:
                st.markdown(
                    f'<div style="padding:0.4rem 0 0.4rem 0.8rem;'
                    f'border-left:2px solid {color};margin-bottom:0.4rem;">'
                    f'<div style="font-family:DM Mono,monospace;font-size:0.68rem;'
                    f'letter-spacing:0.18em;color:{color};text-transform:uppercase;'
                    f'margin-bottom:0.4rem;">{label} &nbsp;&middot;&nbsp; {g["confidence"]}% match</div>'
                    f'<div style="font-family:Cinzel,serif;font-size:1.35rem;'
                    f'font-weight:700;color:#FAFAFA;letter-spacing:0.02em;'
                    f'line-height:1.25;margin-bottom:0.6rem;">{g["player"]}</div>'
                    f'<div style="font-family:DM Mono,monospace;font-size:0.78rem;'
                    f'color:#52525B;letter-spacing:0.06em;">'
                    f'{g["runs"]} runs &nbsp;&nbsp; {g["wickets"]} wkts</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

            if i < len(st.session_state.guesses) - 1:
                st.markdown(
                    '<div style="height:1px;background:rgba(255,255,255,0.04);margin:1.2rem 0;"></div>',
                    unsafe_allow_html=True
                )

    st.write("")
    
    # ── Score History Table ──
    if st.session_state.get("score_history"):
        st.markdown(
            '<div style="height:1px;background:rgba(255,255,255,0.06);margin:2rem 0;"></div>',
            unsafe_allow_html=True
        )
        st.markdown(
            '<p style="font-family:DM Mono,monospace;font-size:0.7rem;'
            'letter-spacing:0.2em;color:#C8A96E;text-transform:uppercase;'
            'text-align:center;margin-bottom:1.5rem;">Question Log</p>',
            unsafe_allow_html=True
        )

        for entry in st.session_state.score_history:
            response_colors = {
                "yes": "#4ECCA3", "no": "#FF6B6B",
                "maybe": "#C8A96E", "unsure": "#7EBFFF"
            }
            resp_color = response_colors.get(entry["response"], "#FAFAFA")

            st.markdown(
                f'<div style="margin-bottom:1rem;padding:0.8rem 1rem;'
                f'background:#18181D;border-radius:4px;'
                f'border-left:2px solid {resp_color};">'
                f'<div style="display:flex;justify-content:space-between;margin-bottom:0.6rem;">'
                f'<span style="font-family:DM Mono,monospace;font-size:0.72rem;'
                f'color:#52525B;">Q{entry["turn"]}</span>'
                f'<span style="font-family:DM Mono,monospace;font-size:0.72rem;'
                f'color:{resp_color};text-transform:uppercase;">{entry["response"]}</span>'
                f'</div>'
                f'<div style="font-size:0.9rem;color:#FAFAFA;margin-bottom:0.6rem;">'
                f'{QUESTION_MAP.get(entry["feature"], entry["feature"])}</div>'
                f'<div style="font-family:DM Mono,monospace;font-size:0.72rem;color:#52525B;">'
                + " &nbsp;·&nbsp; ".join(
                    f'<span style="color:#FAFAFA">{g["player"]}</span> '
                    f'<span style="color:{resp_color}">{g["confidence"]}%</span> '
                    f'<span style="color:#3F3F46">({g["score"]:+.1f}pts)</span>'
                    for g in entry["top3"]
                ) +
                f'</div></div>',
                unsafe_allow_html=True
            )
            
            
    st.write("")

    # ── Continue or Play Again ──
    st.markdown(
        '<p style="text-align:center;color:#71717A;font-size:0.85rem;'
        'margin-bottom:1rem;">Not satisfied? Keep going — questions won\'t repeat.</p>',
        unsafe_allow_html=True
    )

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Continue Guessing", use_container_width=True):
            try:
                res = requests.post(
                    f"{API_URL}/continue",
                    json={"session_id": st.session_state.session_id}
                ).json()
                if res.get("action") == "question":
                    st.session_state.action    = "question"
                    st.session_state.question  = res["question"]
                    st.session_state.col       = res["col"]
                    st.session_state.pool_size = res["pool_size"]
                    st.session_state.guesses   = res.get("guesses", [])
                    st.rerun()
                elif res.get("error") == "no_more_questions":
                # Reset asked features on backend and try again
                    res2 = requests.post(
                        f"{API_URL}/reset_questions",
                        json={"session_id": st.session_state.session_id}
                    ).json()
                    if res2.get("action") == "question":
                        st.session_state.action    = "question"
                        st.session_state.question  = res2["question"]
                        st.session_state.col       = res2["col"]
                        st.session_state.pool_size = res2["pool_size"]
                        st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    with c2:
        if st.button("Play Again", use_container_width=True):
            for key in list(defaults.keys()):
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()