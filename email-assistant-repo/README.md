# Email Assistant (Desktop) — Local API + JSON Stores + Embedded Graph + Classifier

This repo provides:
- **FastAPI** app (127.0.0.1) exposed to agents via **MCP** (OpenAPI 3.1 tool).
- **Governed JSON** stores (taxonomy/rules/contacts + append-only decisions.ndjson).
- **Embedded graph** default: `pyoxigraph` (file-backed); optional Neo4j via Bolt.
- **Local classifier** (PyTorch + hashing vectorizer) to augment a fine-tuned LLM.

## Quickstart (with `uv`)

> Requires Python 3.11+.

```bash
# 1) Create environment
uv venv .venv
source .venv/bin/activate

# 2) Install in editable mode with dev tools
uv pip install -e ".[dev]"

# 3) Run the API
uv run python scripts/run_api.py

# 4) Train the local classifier (from sample NDJSON)
uv run python scripts/train_classifier.py --data data/decisions --out src/email_assistant/models/classifier.pt
```

Register `openapi_3_1.json` with your Docker MCP toolkit as an OpenAPI tool.
