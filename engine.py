import pandas as pd
import numpy as np
import os

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
VECTOR_COLUMNS = list(dict.fromkeys(VECTOR_COLUMNS))  # dedup

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
}

def col_to_question(col):
    return QUESTION_MAP.get(col, f"Is '{col.replace('_', ' ')}' true of your player?")


# ── SCORING ENGINE ────────────────────────────────────────────────────────────
def _get_scores(user_vec, user_answered_mask):
    """Score all players; only answered features count."""
    scores = []
    for name, p_vec in player_vectors.items():
        score = 0.0
        contradictions = 0
        for idx in range(len(VECTOR_COLUMNS)):
            if user_answered_mask[idx] == 0:
                continue
            user_ans   = user_vec[idx]    # +1 yes, -1 no
            player_val = p_vec[idx]       # 1.0 true, 0.0 false

            if user_ans == 1.0 and player_val == 1.0:
                score += MATCH_REWARD
            elif user_ans == -1.0 and player_val == 0.0:
                score += NEGATIVE_MATCH_REWARD
            elif user_ans == 1.0 and player_val == 0.0:
                score -= CONTRADICTION_PENALTY
                contradictions += 1
            elif user_ans == -1.0 and player_val == 1.0:
                score -= CONTRADICTION_PENALTY
                contradictions += 1

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


def _pick_best_question(user_vec, user_answered_mask, asked_features):
    scores = _get_scores(user_vec, user_answered_mask)
    top_candidates = [name for name, _ in scores[:30]]

    best_idx     = None
    best_entropy = -1

    for idx, feature in enumerate(VECTOR_COLUMNS):
        if feature in asked_features:
            continue
        values = [player_vectors[name][idx] for name in top_candidates]
        if len(set(values)) < 2:
            continue
        e = _entropy_of_feature(idx, top_candidates)
        if e > best_entropy:
            best_entropy = e
            best_idx     = idx

    return best_idx


# ── SESSION ───────────────────────────────────────────────────────────────────
class AkinatorSession:
    def __init__(self):
        self.user_vec           = np.zeros(len(VECTOR_COLUMNS))
        self.user_answered_mask = np.zeros(len(VECTOR_COLUMNS))
        self.asked_features     = set()
        self.history            = []   # [(col, response)]
        self._turn              = 0

    # ── PUBLIC API (unchanged for api.py) ────────────────────────────────────
    def best_question(self):
        idx = _pick_best_question(
            self.user_vec,
            self.user_answered_mask,
            self.asked_features,
        )
        if idx is None:
            return None, None
        return VECTOR_COLUMNS[idx], 1.0   # col, dummy score

    def answer(self, col, response):
        """response: 'yes' | 'no' | 'unsure'"""
        if col not in VECTOR_COLUMNS:
            return
        idx = VECTOR_COLUMNS.index(col)
        self.asked_features.add(col)
        self._turn += 1

        if response == 'yes':
            self.user_vec[idx]           =  1.0
            self.user_answered_mask[idx] =  1
        elif response == 'no':
            self.user_vec[idx]           = -1.0
            self.user_answered_mask[idx] =  1
        else:  # unsure
            self.user_vec[idx]           =  0.0
            self.user_answered_mask[idx] =  0

        self.history.append((col, response))

    def top_guesses(self, n=3):
        scores = _get_scores(self.user_vec, self.user_answered_mask)
        top    = scores[:n]

        # Normalize to 0–100 relative to top score
        max_score = top[0][1] if top and top[0][1] > 0 else 1
        results   = []
        for name, score in top:
            confidence = round(max(0.0, min(100.0, score / max_score * 100)), 1)
            row = df[df['player_name'] == name]
            results.append({
                "player":     name,
                "confidence": confidence,
                "runs":       int(row['total_runs'].values[0])    if len(row) else 0,
                "wickets":    int(row['total_wickets'].values[0]) if len(row) else 0,
            })
        return results

    @property
    def pool_size(self):
        """Number of players with non-negative score (rough equivalent)."""
        scores = _get_scores(self.user_vec, self.user_answered_mask)
        return sum(1 for _, s in scores if s >= 0)

    @property
    def should_guess(self):
        return self._turn >= 20 or self.pool_size <= 3