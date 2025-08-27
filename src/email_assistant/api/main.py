from __future__ import annotations

import datetime
import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..config import ensure_dirs, load_config
from ..ml.classifier import load_model
from ..ml.classifier import predict as predict_local
from ..stores import JsonStore, NdjsonStore

app = FastAPI(title="Email Assistant Local API")

CFG = load_config("app.config.json")
ensure_dirs(CFG)

taxonomy_store = JsonStore(CFG["stores"]["taxonomy"])
rules_store = JsonStore(CFG["stores"]["ruleset"])
contacts_store = JsonStore(CFG["stores"]["contacts"])
decisions_store = NdjsonStore(CFG["stores"]["decisions"])

MODEL_PATH = "src/email_assistant/models/classifier.pt"


class FeedbackBatch(BaseModel):
    items: list[dict]


@app.get("/taxonomy")
def get_taxonomy():
    return JSONResponse(content=taxonomy_store.read() or {})


@app.put("/taxonomy")
def put_taxonomy(payload: dict):
    taxonomy_store.write(payload)
    return payload


@app.get("/rules")
def get_rules():
    return JSONResponse(content=rules_store.read() or {})


@app.put("/rules")
def put_rules(payload: dict):
    rules_store.write(payload)
    return payload


@app.get("/decisions")
def list_decisions(limit: int = Query(1000, ge=1, le=10000)):
    return JSONResponse(content=decisions_store.scan(limit=limit))


@app.post("/decisions")
def record_decision(payload: dict):
    decisions_store.append(payload)
    return JSONResponse(status_code=201, content=payload)


@app.post("/learn/feedback")
def post_feedback(payload: FeedbackBatch):
    return {"accepted": len(payload.items), "graphUpserts": 0}


@app.get("/graph/query")
def graph_query(lang: str = Query("sparql"), q: str = Query(...), limit: int = 1000):
    return {"columns": [], "rows": []}


@app.post("/graph/ingest")
def graph_ingest(payload: dict):
    triples = payload.get("batch", {}).get("triples", [])
    return {"tripleCount": len(triples), "errors": []}


@app.post("/ml/classify")
def classify(payload: dict):
    subject, body = payload.get("subject", ""), payload.get("body", "")
    if not os.path.exists(MODEL_PATH):
        raise HTTPException(
            status_code=400, detail="Model not trained. Run scripts/train_classifier.py"
        )
    hv, model, L = load_model(MODEL_PATH)
    out = predict_local(hv, model, L, [subject + " " + body])[0]
    return {
        "messageId": payload.get("messageId", ""),
        "timestamp": datetime.datetime.now().astimezone().isoformat(),
        "classification": out,
        "features": {"subject": subject, "body": body},
        "rulesMatched": [],
        "actions": [],
    }
