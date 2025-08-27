from __future__ import annotations

import json
from typing import Any

import pandas as pd


def decisions_ndjson_to_df(paths: list[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for p in paths:
        with open(p, encoding="utf-8") as f:
            for line in f:
                try:
                    rows.append(json.loads(line))
                except Exception:
                    continue
    if not rows:
        return pd.DataFrame()

    def row_to_rec(r):
        cls = r.get("classification", {})
        feats = r.get("features", {})
        return {
            "messageId": r.get("messageId", ""),
            "subject": feats.get("subject", ""),
            "body": feats.get("body", ""),
            "category1_type": cls.get("category1_type", ""),
            "category2_sender_identity": cls.get("category2_sender_identity", ""),
            "category3_context": cls.get("category3_context", ""),
            "category4_handler": cls.get("category4_handler", ""),
        }

    return pd.DataFrame([row_to_rec(r) for r in rows])
