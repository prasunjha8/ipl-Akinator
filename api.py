from fastapi import FastAPI
from engine import AkinatorSession, col_to_question, _get_scores, VECTOR_COLUMNS
import numpy as np
import uuid

app = FastAPI()
sessions = {}

@app.post("/start")
def start():
    sid = str(uuid.uuid4())
    sessions[sid] = AkinatorSession()
    s = sessions[sid]
    col, _ = s.best_question()

    # All players equally likely at start
    blank_vec  = np.zeros(len(VECTOR_COLUMNS))
    blank_mask = np.zeros(len(VECTOR_COLUMNS))
    scores = _get_scores(blank_vec, blank_mask)
    top_candidates = [name for name, _ in scores[:8]]

    question = col_to_question(col, top_candidates)
    return {
        "session_id": sid,
        "question":   question,
        "col":        col,
        "pool_size":  s.pool_size
    }

@app.post("/answer")
def answer(body: dict):
    sid  = body["session_id"]
    col  = body["col"]
    resp = body["response"]

    if sid not in sessions:
        return {"error": "session_expired"}

    s = sessions[sid]
    s.answer(col, resp)

    if s.should_guess:
        return {
            "action":        "guess",
            "guesses":       s.top_guesses(),
            "score_history": s.score_history,
            "pool_size":     s.pool_size
        }

    next_col, _ = s.best_question()
    scores = _get_scores(s.user_vec, s.user_answered_mask)
    top_candidates = [name for name, _ in scores[:8]]
    question = col_to_question(next_col, top_candidates)

    return {
        "action":        "question",
        "question":      question,
        "col":           next_col,
        "pool_size":     s.pool_size,
        "guesses":       s.top_guesses(),
        "score_history": s.score_history
    }

@app.post("/continue")
def continue_game(body: dict):
    sid = body["session_id"]
    if sid not in sessions:
        return {"error": "session_expired"}
    
    s = sessions[sid]
    s._max_turns = s._turn + 20  # ← give 20 more from current position
    
    next_col, _ = s.best_question()
    if next_col is None:
        return {"error": "no_more_questions"}
    
    scores = _get_scores(s.user_vec, s.user_answered_mask)
    top_candidates = [name for name, _ in scores[:8]]
    question = col_to_question(next_col, top_candidates)
    
    return {
        "action":    "question",
        "question":  question,
        "col":       next_col,
        "pool_size": s.pool_size,
        "guesses":   s.top_guesses()
    }
@app.post("/reset_questions")
def reset_questions(body: dict):
    sid = body["session_id"]
    if sid not in sessions:
        return {"error": "session_expired"}
    
    s = sessions[sid]
    s.asked_features = set()
    # Do NOT clear permanently_asked ← this prevents repeats
    s._max_turns = s._turn + 20
    
    next_col, _ = s.best_question()
    if next_col is None:
        return {"error": "truly_no_questions"}
    
    scores = _get_scores(s.user_vec, s.user_answered_mask)
    top_candidates = [name for name, _ in scores[:8]]
    question = col_to_question(next_col, top_candidates)
    
    return {
        "action":    "question",
        "question":  question,
        "col":       next_col,
        "pool_size": s.pool_size,
        "guesses":   s.top_guesses()
    }