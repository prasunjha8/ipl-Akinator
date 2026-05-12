from fastapi import FastAPI
from pydantic import BaseModel
from engine import AkinatorSession, col_to_question
import uuid, json

app      = FastAPI()
sessions = {}   # session_id → AkinatorSession

@app.post("/start")
def start():
    sid     = str(uuid.uuid4())
    sessions[sid] = AkinatorSession()
    col, _  = sessions[sid].best_question()
    return {"session_id": sid, "question": col_to_question(col),
            "col": col, "pool_size": sessions[sid].pool_size}

@app.post("/answer")
def answer(body: dict):
    sid, col, resp = body["session_id"], body["col"], body["response"]
    s = sessions[sid]
    s.answer(col, resp)
    if s.should_guess:
        return {"action": "guess", "guesses": s.top_guesses(), "pool_size": s.pool_size}
    next_col, _ = s.best_question()
    return {"action": "question", "question": col_to_question(next_col),
            "col": next_col, "pool_size": s.pool_size, "guesses": s.top_guesses()}
