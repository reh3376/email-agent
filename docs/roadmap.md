# Email Assistant (Desktop) — Functional Spec & Roadmap (FSD)

_Last updated: 2025-08-27_

A stand‑alone desktop app (Windows/macOS/Linux) that runs locally.
App polls configured email accounts on a schedule, classifies + summarizes mail,
performs rule-based actions, and sends a single digest email with one‑click
actions.
All local APIs are defined by **OpenAPI 3.1** and surfaced to agents via
**Model Context Protocol (MCP)** using the OpenAPI schema as the source of
truth.

---

## 0) What changed in this version

- **Storage model** → well-governed **JSON** + **append‑only NDJSON** (no
  relational DB). Active taxonomy & ruleset are versioned JSON files; daily
  decisions are NDJSON for audit.
- **Graph layer** → embedded **Oxigraph (pyoxigraph)** as the default local
  graph store (file‑backed, installer‑friendly). Optional Neo4j via Bolt
  remains supported.
- **OpenAPI 3.1 + MCP** → the local FastAPI serves an OpenAPI 3.1 file
  consumed directly by your MCP toolkit (registered as an OpenAPI tool).
- **Local classifier** → lightweight **PyTorch** classifier (hashing
  vectorizer + multi‑head linear) augments the fine‑tuned LLM; includes a
  training script that reads NDJSON decisions.
- **Scheduler** → presets (hourly, every X minutes ≥15, daily/weekday at
  time) plus Cron/RRULE; preview next runs.
- **Contacts schema** → rules can carry a rich contact object when
  `add_contact` fires.
- **Taxonomy versioning** → taxonomy has `type: "email_categories"` and
  `version` (v2).

---

## 1) Scope & Goals

- Offline‑first, privacy‑focused, local processing.
- User‑extensible **Scheduler**, **Classifications**, **Conditions**,
  **Actions**, with your five categories as defaults.
- Two calendars max (primary required). Two email accounts max (primary
  required). Up to three drives. Primary attachment path required.
- Behavioral defaults: mark unread → read after classification; optional
  foldering to `conversations/<domain>/<localpart>`.

---

## 2) Runtime & Platform

- **Language/Runtime**: Python 3.11+.
- **Local API**: **FastAPI** on `127.0.0.1:8765` (OpenAPI 3.1).
- **Packaging/Tooling**: **UV** for env/install; **Ruff** for lint/format;
  dependencies pinned in `pyproject.toml`.
- **Graph**: default **Oxigraph** (embedded, file‑backed); optional **Neo4j**
  via Bolt.

---

## 3) Settings

- **Appearance**: theme (light/dark/auto).
- **App auth**: username/password or Microsoft/Google; optional 2FA (TOTP).
- **Calendars**: Google, Outlook/Graph (primary required).
- **Email**: Gmail, Outlook/Graph, Exchange (EWS/Graph), IMAP/SMTP (primary
  required).
- **Files (≤3)**: Local (required as primary), OneDrive, Google Drive,
  Dropbox.
- **AI**: OpenAI‑compatible base URL + key; choose base/fine‑tuned model.
- **Scheduler**: Simple/Cron/RRULE; frequency floor **15 minutes**; preview
  next runs.

---

## 4) Data & Schemas (JSON‑only)

- **Taxonomy**: versioned JSON; `type: "email_categories"`, `version: "v2"`;
  validated by JSON Schema (`schemas/taxonomy.schema.json`).
- **Ruleset**: versioned JSON; validated by JSON Schema
  (`schemas/ruleset.schema.json`); supports contact payload on `add_contact`.
- **Decisions**: append‑only NDJSON (one file per day) capturing
  classification, rules matched, actions, calendar conflict flags
  (`schemas/decision.schema.json`).
- **Contacts**: JSON list validated by `schemas/contacts.schema.json`.

Starter files (current defaults):

- `data/taxonomy_v2.json` and `data/ruleset_v2.json` (active “v2” versions).
- `data/contacts.json` (empty list by default).
- `data/decisions/YYYY‑MM‑DD.ndjson` (append‑only).

---

## 5) Classification Taxonomy (5 categories; user‑tunable labels)

- `0 reviewed` (control)
- `1 type` (e.g., work/WhiskeyHouse, personal, professional, other)
- `2 sender identity` (friend, contact, co‑worker, vendor, marketer, org,
  enterprise, malicious, other)
- `3 context` (request for meeting, request for information, promotional,
  unsolicited, notification, junk, other)
- `4 handler` (user action required, no action required)

> Users can rename categories and extend labels; downstream rules/actions use
> the active taxonomy.

---

## 6) Local Model (augmenting LLM)

- **Vectorizer**: deterministic hashing + bucket‑level IDF (no vocabulary
  storage).
- **Model**: multi‑head linear (4 heads for categories 1–4).
- **Training**: `scripts/train_classifier.py` builds a table from decisions
  NDJSON + taxonomy v2, fits, and saves
  `src/email_assistant/models/classifier.pt`.
- **Serving**: `/ml/classify` uses the saved model to emit the 5‑tuple
  classification; the LLM uses that as a prior for explanation & edge cases.

---

## 7) Rules & Actions (DSL)

- JSON rules; prioritized; validated by schema; predicates support
  `exists/eq/in/lt/lte/gt/gte/regex`.
- Core flows:
  - **Meetings**: detect meeting intent → `handler = user action required`;
    set/save-to-folder optionally; conflict checks.
  - **Requests for Information**: `handler = user action required`.
  - **Notifications (travel/appointment/deadline)**: auto‑create if no
    conflict; flag if conflict.
  - **Promotional**: no auto‑action.
  - **Junk/Malicious**: report junk + delete.
- `add_contact` supports a rich contact object (emails/phones/addresses).

---

## 8) OpenAPI 3.1 + MCP - Accessable via Docker MCP

- File: `openapi_3_1.json` (source of truth).
- Key routes:
  - `GET/PUT /taxonomy`, `GET/POST /taxonomy/versions`
  - `GET/PUT /rules`, `GET/POST /rules/versions`
  - `GET /scheduler/preview`
  - `GET/POST /decisions`, `GET /decisions/<built-in function id>`
  - `POST /learn/feedback`
  - `POST /graph/ingest`, `GET /graph/query` (SPARQL default)
  - `POST /ml/classify`
- `info.x-mcp` explains intended use, safety notes, and exposed resources for
  agents.

---

## 9) Learning Loop

1. **Ingest & Infer** — pull unread mail on schedule; extract features; local
   classifier proposes categories; rules propose actions.
2. **Decide & Act** — write immutable **Decision** (NDJSON), execute actions,
   emit explanation text.
3. **Teach** — `/learn/feedback` records corrections; graph links messages,
   decisions, rules, and corrections.
4. **Retrain** — nightly, retrain local model over decisions + feedback; bump
   prompt/model versions.
5. **Audit** — query graph for "why" via SPARQL (Oxigraph).

---

## 10) Digest & One‑click Actions

- Single daily HTML digest with one‑click actions routed to signed endpoints
  (HMAC, idempotent).
- Sections: conflicts/alerts, meetings, RFIs, notifications, promotions, junk.

---

## 11) Repository & Build

- **Layout**:
  - `src/email_assistant/` (FastAPI app, ML, stores, models/)
  - `schemas/` (governed JSON Schemas)
  - `data/` (taxonomy v2, ruleset v2, contacts, decisions/)
  - `scripts/` (`run_api.py`, `train_classifier.py`)
  - `tests/` (smoke tests)
- **Tooling**: UV for env; Ruff for lint/format; PyTest for tests; packaged
  via `pyproject.toml`.

**Quickstart**

```bash
uv venv .venv && source .venv/bin/activate
uv pip install -e ".[dev]"
uv run python scripts/run_api.py
uv run python scripts/train_classifier.py --data data/decisions \
  --out src/email_assistant/models/classifier.pt
```

---

## 12) Providers & Limits

- **Email**: Gmail, Outlook/Graph, Exchange (EWS/Graph), IMAP/SMTP (max 2
  accounts, primary required).
- **Calendar**: Google, Outlook/Graph (max 2, primary required).
- **Drives**: Local/OneDrive/GDrive/Dropbox (≤3); local primary attachment dir
  required.

---

## 13) Security & Non‑Negotiables

- Local‑only service on `127.0.0.1`.
- Secrets in OS Keychain; PII‑scrubbed logs.
- Timezone for conflict checks: `America/Kentucky/Louisville`.
- OpenAPI 3.1 is the single source of truth; MCP agents must use only
  OpenAPI‑defined operations.

---

## 14) Attachment Management Framework

### Storage Strategy

- **Base Path**: Primary attachment directory from settings (required)
- **Structure**: `{base}/YYYY-MM-DD/{messageId}/{filename}`
- **Deduplication**: SHA256 hash-based; store once, reference many
- **Metadata**: Track filename, MIME type, size, hash, storage path in Decision records

### Processing Pipeline

1. **Download**: Fetch attachments during email processing
2. **Scan**: Optional virus/malware scanning integration point
3. **Hash**: Generate SHA256 for deduplication and integrity
4. **Store**: Save to structured directory with proper permissions
5. **Index**: Update Decision record with attachment metadata

### Access Controls

- **Permissions**: User-only read/write (700) on attachment directories
- **Cleanup**: Configurable retention policy (default: 90 days)
- **Backup**: Exclude from cloud sync by default (privacy)

### API Endpoints

- `GET /attachments/{messageId}`: List attachments for an email
- `GET /attachments/{messageId}/{filename}`: Download specific attachment
- `DELETE /attachments/{messageId}/{filename}`: Remove attachment
- `GET /attachments/stats`: Storage usage statistics

### Security Considerations

- **Path Traversal**: Validate all paths; reject `..` and absolute paths
- **File Types**: Configurable allowed/blocked MIME types
- **Size Limits**: Per-file (default: 25MB) and total storage quotas
- **Encryption**: Optional at-rest encryption for sensitive attachments

---

## 15) Current Defaults Snapshot

- **Taxonomy v2** and **Ruleset v2** are active (see `data/`).
- Scheduler: hourly; advanced scheduling available.
- Rules match behaviors listed above.

---

## 16) Next Milestones

- Wire **Oxigraph** read/write (`/graph/ingest`, `/graph/query`) and SPARQL
  templates for common "why" queries.
- Rule editor UI and taxonomy manager in the desktop shell.
- MCP packaging: register `openapi_3_1.json` in Docker MCP toolkit; expose
  resources `taxonomy_active`, `ruleset_active`, `samples`, `decisions_today`.

---

## 17) Implementation Roadmap

For a detailed phased implementation plan with specific tasks, definitions of done, and test steps, see:
**[📋 Email Agent Phased Implementation Roadmap](./email-agent_phased_roadmap.md)**

This roadmap provides a systematic approach to evolving the email-agent into a robust, testable, desktop-ready application through 9 phases covering everything from repository hygiene to full desktop deployment.
