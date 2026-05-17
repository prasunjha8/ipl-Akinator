import pandas as pd
import numpy as np
import os
from groq import Groq

groq_client = Groq(api_key="GROQ_API_KEY")

# ── LOAD ─────────────────────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(_HERE, 'ipl_master_players_final.csv'))

# ── VECTOR SPACE ──────────────────────────────────────────────────────────────
VECTOR_COLUMNS = [
    'is_opener', 'is_finisher', 'is_death_bowler', 'is_economical',
    'is_wicketkeeper', 'is_captain', 'is_power_hitter', 'is_spinner',
    'is_pacer', 'is_all_rounder', 'is_anchor', 'is_clutch',
    'active_recent', 'early_ipl_era', 'one_franchise',
    'played_for_csk', 'played_for_mi', 'played_for_rcb',
    'played_for_kkr', 'played_for_srh', 'played_for_dc',
    'played_for_rr', 'played_for_pbks', 'won_ipl_title',
    'won_orange_cap', 'won_purple_cap', 'is_international_star',
]
VECTOR_COLUMNS = list(dict.fromkeys(VECTOR_COLUMNS))

# Build player vectors: True→1.0, False→0.0
vector_df = df.set_index('player_name')[VECTOR_COLUMNS].copy()
for col in VECTOR_COLUMNS:
    vector_df[col] = vector_df[col].map({True: 1.0, False: 0.0, 1: 1.0, 0: 0.0}).fillna(0.0)

player_vectors = {
    name: vector_df.loc[name].values
    for name in vector_df.index
}

# ── SCORING CONSTANTS ─────────────────────────────────────────────────────────
MATCH_REWARD          = 3.0
NEGATIVE_MATCH_REWARD = 1.5
MAYBE_MATCH_REWARD    = 1.0
MAYBE_MISMATCH        = 0.3
CONTRADICTION_PENALTY = 5.0

# ── QUESTION MAP ──────────────────────────────────────────────────────────────
QUESTION_MAP = {
    'is_opener':           "Does your player typically open the batting?",
    'is_finisher':         "Is your player known for finishing innings in the lower order?",
    'is_death_bowler':     "Does your player bowl in the death overs (17–20)?",
    'is_economical':       "Is your player known for being economical (economy < 7.5)?",
    'is_wicketkeeper':     "Is your player a wicket-keeper?",
    'is_captain':          "Has your player captained an IPL team?",
    'is_power_hitter':     "Is your player known as a big power hitter?",
    'is_anchor':           "Is your player known for anchoring the innings (calm, steady)?",
    'is_spinner':          "Is your player a spinner?",
    'is_pacer':            "Is your player a fast bowler?",
    'is_all_rounder':      "Is your player a genuine all-rounder (bats AND bowls significantly)?",
    'is_clutch':           "Is your player famous for performing under pressure in big moments?",
    'won_orange_cap':      "Has your player won the Orange Cap (most runs in a season)?",
    'won_purple_cap':      "Has your player won the Purple Cap (most wickets in a season)?",
    'won_ipl_title':       "Has your player won an IPL title?",
    'is_international_star': "Is your player a well-known international star (not just domestic)?",
    'one_franchise':       "Has your player spent their entire IPL career at one franchise?",
    'active_recent':       "Is your player still active in IPL (2022 onwards)?",
    'early_ipl_era':       "Was your player prominent in the early IPL era (before 2013)?",
    'played_for_csk':      "Has your player played for Chennai Super Kings?",
    'played_for_mi':       "Has your player played for Mumbai Indians?",
    'played_for_rcb':      "Has your player played for Royal Challengers Bangalore?",
    'played_for_kkr':      "Has your player played for Kolkata Knight Riders?",
    'played_for_srh':      "Has your player played for Sunrisers Hyderabad?",
    'played_for_rr':       "Has your player played for Rajasthan Royals?",
    'played_for_dc':       "Has your player played for Delhi Capitals / Daredevils?",
    'played_for_pbks':     "Has your player played for Punjab Kings / Kings XI?",
    'played_for_lsg':     "Has your player played for Lucknow Super Giants?",
}

# ── FEATURE DESCRIPTIONS FOR GROQ ────────────────────────────────────────────
feature_descriptions = {
    'is_opener':        'opens the batting (bats at position 1 or 2)',
    'is_finisher':      'finishes innings in lower order (bats 7+ and scores big)',
    'is_death_bowler':  'bowls in overs 17-20 (death overs)',
    'is_economical':    'has economy rate below 7.5 runs per over',
    'is_wicketkeeper':  'is a wicket-keeper batsman',
    'is_captain':       'has captained an IPL team',
    'is_power_hitter':  'hits sixes frequently and has high strike rate',
    'is_spinner':       'is a spin bowler (off-spin or leg-spin)',
    'is_pacer':         'is a fast/pace bowler',
    'is_all_rounder':   'both bats AND bowls significantly in IPL',
    'is_anchor':        'bats steadily to anchor the innings, not a big hitter',
    'is_clutch':        'performs in high-pressure moments like finals and playoffs',
    'won_orange_cap':   'won the Orange Cap (most runs in an IPL season)',
    'won_purple_cap':   'won the Purple Cap (most wickets in an IPL season)',
    'won_ipl_title':    'won the IPL trophy',
    'is_international_star': 'is a well-known international cricketer',
    'one_franchise':    'played for only ONE IPL team their entire career',
    'active_recent':    'played IPL in 2022, 2023, or 2024',
    'early_ipl_era':    'played IPL before 2013 (early seasons)',
    'played_for_csk':   'played for Chennai Super Kings',
    'played_for_mi':    'played for Mumbai Indians',
    'played_for_rcb':   'played for Royal Challengers Bangalore',
    'played_for_kkr':   'played for Kolkata Knight Riders',
    'played_for_srh':   'played for Sunrisers Hyderabad',
    'played_for_rr':    'played for Rajasthan Royals',
    'played_for_dc':    'played for Delhi Capitals or Delhi Daredevils',
    'played_for_pbks':  'played for Punjab Kings or Kings XI Punjab',
    
}

# ── QUESTION GENERATION ───────────────────────────────────────────────────────
def col_to_question(col, top_candidates=None):
    fallback = QUESTION_MAP.get(col, f"Is '{col.replace('_', ' ')}' true of your player?")

    if not top_candidates:
        return fallback

    candidate_preview = ", ".join(top_candidates[:6])
    feature_meaning = feature_descriptions.get(col, col.replace('_', ' '))

    prompt = f"""IPL cricket guessing game. Top candidates: {candidate_preview}

Write exactly one YES/NO question to ask if the mystery player: {feature_meaning}

Requirements:
- Under 12 words
- End with ?
- No player names
- Only output the question, nothing else
- Do not start with "Does the mystery player" — be creative"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=30
        )
        question = response.choices[0].message.content.strip().strip('"').strip("'")
        if (len(question) > 10 and "?" in question
                and "mystery" not in question.lower()
                and "indian premier league" not in question.lower()
                and len(question.split()) <= 15):
            return question
        return fallback
    except Exception:
        return fallback


# ── SCORING ENGINE ────────────────────────────────────────────────────────────
def _get_scores(user_vec, user_answered_mask):
    scores = []
    for name, p_vec in player_vectors.items():
        score = 0.0
        contradictions = 0
        for idx in range(len(VECTOR_COLUMNS)):
            if user_answered_mask[idx] == 0:
                continue
            user_ans   = user_vec[idx]
            player_val = p_vec[idx]

            if user_ans == 1.0 and player_val == 1.0:
                score += MATCH_REWARD
            elif user_ans == 1.0 and player_val == 0.0:
                score -= CONTRADICTION_PENALTY
                contradictions += 1
            elif user_ans == -1.0 and player_val == 0.0:
                score += NEGATIVE_MATCH_REWARD
            elif user_ans == -1.0 and player_val == 1.0:
                score -= CONTRADICTION_PENALTY
                contradictions += 1
            elif user_ans == 0.5 and player_val == 1.0:
                score += MAYBE_MATCH_REWARD
            elif user_ans == 0.5 and player_val == 0.0:
                score -= MAYBE_MISMATCH

        if contradictions >= 3:
            score -= contradictions * 3

        scores.append((name, score))

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores


def _entropy_of_feature(feature_idx, top_candidates):
    values = [player_vectors[name][feature_idx] for name in top_candidates]
    count_true  = sum(values)
    count_false = len(values) - count_true
    if count_true == 0 or count_false == 0:
        return -1
    p_true  = count_true  / len(values)
    p_false = count_false / len(values)
    return -(p_true * np.log2(p_true) + p_false * np.log2(p_false))


def _pick_best_question(user_vec, user_answered_mask, asked_features, permanently_asked=None):
    scores = _get_scores(user_vec, user_answered_mask)
    top_candidates = [name for name, _ in scores[:30]]

    best_idx     = None
    best_entropy = -1
    fallback_idx = None

    blocked = permanently_asked if permanently_asked else asked_features

    for idx, feature in enumerate(VECTOR_COLUMNS):
        if feature in blocked:
            continue

        fallback_idx = idx

        values = [player_vectors[name][idx] for name in top_candidates]
        if len(set(values)) < 2:
            continue

        e = _entropy_of_feature(idx, top_candidates)
        if e > best_entropy:
            best_entropy = e
            best_idx     = idx

    return best_idx if best_idx is not None else fallback_idx


# ── SESSION ───────────────────────────────────────────────────────────────────
class AkinatorSession:
    def __init__(self):
        self.user_vec           = np.zeros(len(VECTOR_COLUMNS))
        self.user_answered_mask = np.zeros(len(VECTOR_COLUMNS))
        self.asked_features     = set()
        self.permanently_asked  = set()
        self.history            = []
        self.score_history      = []
        self._turn              = 0
        self._max_turns         = 12

    def best_question(self):
        idx = _pick_best_question(
            self.user_vec,
            self.user_answered_mask,
            self.asked_features,
            self.permanently_asked,
        )
        if idx is None:
            return None, None
        return VECTOR_COLUMNS[idx], 1.0

    def answer(self, col, response):
        """response: 'yes' | 'no' | 'maybe' | 'unsure'"""
        if col not in VECTOR_COLUMNS:
            return
        idx = VECTOR_COLUMNS.index(col)
        self.asked_features.add(col)
        self.permanently_asked.add(col)
        self._turn += 1

        if response == 'yes':
            self.user_vec[idx]           =  1.0
            self.user_answered_mask[idx] =  1
        elif response == 'no':
            self.user_vec[idx]           = -1.0
            self.user_answered_mask[idx] =  1
        elif response == 'maybe':
            self.user_vec[idx]           =  0.5
            self.user_answered_mask[idx] =  1
        else:  # don't know
            self.user_vec[idx]           =  0.0
            self.user_answered_mask[idx] =  0

        self.history.append((col, response))

        top3 = self.top_guesses(3)
        self.score_history.append({
            "turn":     self._turn,
            "feature":  col,
            "response": response,
            "top3":     top3
        })

    def top_guesses(self, n=3):
        scores = _get_scores(self.user_vec, self.user_answered_mask)
        top    = scores[:n]

        if not top or top[0][1] <= 0:
            results = []
            for name, score in top:
                row = df[df['player_name'] == name]
                results.append({
                    "player":     name,
                    "confidence": 0,
                    "score":      round(score, 1),
                    "runs":       int(row['total_runs'].values[0]) if len(row) else 0,
                    "wickets":    int(row['total_wickets'].values[0]) if len(row) else 0,
                })
            return results

        top_score    = top[0][1]
        second_score = top[1][1] if len(top) > 1 else 0

        results = []
        for name, score in top:
            if score == top_score:
                confidence = min(99, round(60 + (score / max(top_score, 1)) * 35, 1))
            else:
                drop = (top_score - score) / max(top_score - second_score, 1)
                confidence = round(max(5, (1 - drop * 0.6) * 60), 1)

            row = df[df['player_name'] == name]
            results.append({
                "player":     name,
                "confidence": confidence,
                "score":      round(score, 1),
                "runs":       int(row['total_runs'].values[0]) if len(row) else 0,
                "wickets":    int(row['total_wickets'].values[0]) if len(row) else 0,
            })
        return results

    @property
    def pool_size(self):
        scores = _get_scores(self.user_vec, self.user_answered_mask)
        return sum(1 for _, s in scores if s >= 0)

    @property
    def should_guess(self):
        if self._turn < 4:
            return False
        scores = _get_scores(self.user_vec, self.user_answered_mask)
        top = scores[:2]
        if len(top) >= 2:
            gap = top[0][1] - top[1][1]
            if gap >= 8.0 and top[0][1] > 10.0:
                return True
        if self._turn >= self._max_turns:
            return True
        return False