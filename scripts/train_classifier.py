from __future__ import annotations

import argparse
import glob
import json
import os
from pathlib import Path

from email_assistant.ml.classifier import fit_classifier, save_model
from email_assistant.ml.pipeline import decisions_ndjson_to_df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="Path to decisions directory")
    ap.add_argument("--taxonomy", default="data/taxonomy_v2.json")
    ap.add_argument("--out", default="src/email_assistant/models/classifier.pt")
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--features", type=int, default=2**18)
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(args.data, "*.ndjson")))
    if not files:
        raise SystemExit("No NDJSON files found in --data")
    df = decisions_ndjson_to_df(files)
    if df.empty:
        raise SystemExit("No records in decisions NDJSON")

    with open(args.taxonomy, encoding="utf-8") as f:
        taxonomy = json.load(f)

    hv, model, L = fit_classifier(df, taxonomy, n_features=args.features, epochs=args.epochs)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    save_model(hv, model, L, args.out)
    print(f"Saved model to {args.out}")


if __name__ == "__main__":
    main()
