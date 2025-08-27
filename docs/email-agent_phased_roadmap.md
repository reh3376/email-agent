# Email Agent — Phased Implementation Roadmap (with Expanded Phase 2)

This document defines a sequenced plan for evolving the **email-agent** into a robust, testable, desktop-ready application. Each task includes a **Definition of Done (DoD)** and **Test Steps** so the coding agent and reviewers can reliably mark items complete.

> **How to use this roadmap**
>
> - Treat each **Phase** as a milestone. Open a GitHub Tracking Issue per phase using the template at the end.
> - Each **Task** should map to one or more GitHub Issues/PRs.
> - Gates promote to the next phase only after all prior tasks pass and acceptance checks are met.

---

## Conventions

- **CLI name:** `email-agent` (installed via `pyproject.toml` `[project.scripts]`).
- **API base URL:** default `http://127.0.0.1:8765`.
- **Output modes:** human-friendly (Rich) by default; `--json` yields machine-friendly output.
- **Modes:** Commands run in **offline** mode (in-process services) when no `--api` or env `EMAIL_AGENT_API` is set; otherwise **HTTP** mode via the REST API.
- **Tests:** prefer `pytest`, `respx` (for httpx mocks), Rich snapshot tests (ANSI stripped), and Textual Pilot for TUI smoke tests.
- **Docs:** Place phase-specific docs under `/docs`. Keep README high-level.

---

# Phase 1 — Repo Hygiene & CI Foundation

**Goal:** Establish predictable builds, linting, and tests.

### Task P1-T1: Rename `archieve/` → `archive/`

- **DoD:** Folder renamed; imports/paths updated; repo builds.
- **Test Steps:** `uv run pytest -q`; search codebase for `archieve` → 0 results.

### Task P1-T2: Add CI workflow

- **DoD:** `.github/workflows/ci.yml` runs on PRs and `main`.
- **CI Steps:** `uv venv`, install `.[dev]`, `ruff check`, `ruff format --check`, `pytest --cov`.
- **Test Steps:** Open PR → CI passes; coverage artifact uploaded or comment posted.

### Task P1-T3: Pre-commit hooks (optional)

- **DoD:** `.pre-commit-config.yaml` with ruff/black/markdownlint; hook installed.
- **Test Steps:** Commit with formatting issues → hook blocks; fix → pass.

---

# Phase 2 — CLI Entry Points & Basic Health Endpoints (Expanded)

**Design goals**

- One unified CLI: **Typer**-based `email-agent …`
- Beautiful terminal output (**Rich**), with `--json` for machine use
- An interactive **TUI (Textual)**: `email-agent tui`
- Works **offline** (direct service calls) and **online** (HTTP via API)
- Clear mapping from CLI commands → API endpoints

**New modules & files**

```
src/email_assistant/cli/
  __init__.py
  app.py            # Typer app (entry point)
  client.py         # HTTP client wrapper (httpx) + offline shim
  render.py         # Rich renderers (tables, panels, progress)
  tui.py            # Textual dashboard
  commands/
    serve.py        # `email-agent serve`
    health.py       # `email-agent health`, `version`
    classify.py     # `email-agent classify …`
    rules.py        # `email-agent rules …`
    decisions.py    # `email-agent decisions …`
```

Add to `pyproject.toml`:

```toml
[project.scripts]
email-agent = "email_assistant.cli.app:main"
```

### Task P2-T1: CLI skeleton (Typer)

- **DoD:** `email-agent --help` shows `serve`, `health`, `version`, `classify`, `rules`, `decisions`, `tui`. All accept `--api` and `--json` (where applicable).
- **Test Steps:**
  1. `email-agent --help` → command list printed
  2. `email-agent version --json` → JSON with `app`, `git_sha`

### Task P2-T2: Health & Version endpoints + CLI commands

- **DoD:** API exposes `GET /health -> {"status":"ok"}` and `GET /version -> {"app","git_sha","ml_model"}`. CLI `email-agent health` and `email-agent version` call API when available, otherwise offline shim.
- **Test Steps:**
  1. Run API: `email-agent serve`
  2. `email-agent health` → “ok” (Rich panel) / `--json` returns JSON
  3. Stop API; `email-agent health` → offline self-check returns “ok (offline)”

### Task P2-T3: HTTP client + offline shim

- **DoD:** `AgentClient` auto-detects mode: **HTTP** if `--api`/`EMAIL_AGENT_API` set, else **offline**. Graceful error messages; non-zero exit codes on failure.
- **Test Steps:**
  1. Server running → command uses HTTP path
  2. Server down → command uses offline path (or fails with helpful hint if not supported)

### Task P2-T4: Rich renderers (tables/panels)

- **DoD:** Human-friendly output for health, version, rules, decisions; `--json` bypasses Rich.
- **Test Steps:** `email-agent decisions list` renders a table; `email-agent rules list` renders grouped rules with highlighted predicates.

### Task P2-T5: Classify / Rules / Decisions (offline first)

- **DoD:**
  - `email-agent classify text "…" [--threshold 0.6] [--dry-run]`
  - `email-agent rules list`, `rules test --email path/to.eml|--json path/to.json`
  - `email-agent decisions list [--limit 50]`, `decisions tail` (follow NDJSON of today)
- **Test Steps:** Offline classify returns labels/confidence; rules test prints matched rule IDs and predicates; decisions list & tail work against local NDJSON.

### Task P2-T6: Wire CLI to API (HTTP mode)

- **DoD:** Every CLI command uses HTTP when `--api` or env var is set; otherwise offline. Command-to-endpoint map below is implemented.
- **Test Steps:** Start API and run `email-agent classify text "hi" --api http://127.0.0.1:8765` → server receives POST; disable server → command falls back to offline or shows helpful error.

**Command → Endpoint map**

| CLI command                       | HTTP endpoint                     | Method |
| --------------------------------- | --------------------------------- | ------ |
| `email-agent health`              | `/health`                         | GET    |
| `email-agent version`             | `/version`                        | GET    |
| `email-agent classify text`       | `/ml/classify`                    | POST   |
| `email-agent rules list`          | `/rules`                          | GET    |
| `email-agent rules test`          | `/rules/test` (or `/ml/explain`)  | POST   |
| `email-agent decisions list/tail` | `/decisions?limit=N` or `/stream` | GET    |

> Adjust mapping to match the actual API surface; the CLI client isolates differences.

### Task P2-T7: TUI dashboard (Textual)

- **DoD:** `email-agent tui` provides tabs:
  - **Status** (health, version)
  - **Classify** (input box + results: labels/confidences/traces)
  - **Rules** (list, quick-test with sample email)
  - **Decisions** (live tail of today’s NDJSON)
  - Keybindings: `F5` refresh; `q` quit; `t` toggle HTTP/offline
- **Test Steps:** Launch TUI; Status shows “ok”; run a sample in Classify tab; kill server then toggle to offline → Status updates to “ok (offline)”.

### Task P2-T8: `serve` command

- **DoD:** `email-agent serve [--host 127.0.0.1 --port 8765 --reload]` boots uvicorn with the FastAPI app import path.
- **Test Steps:** `email-agent serve --reload` works; `curl http://127.0.0.1:8765/health` returns 200.

### Task P2-T9: Tests for CLI & TUI

- **DoD:** Pytest suite covers:
  - Typer commands via `CliRunner`
  - HTTP mode with `respx` (httpx mock)
  - Offline mode via FastAPI `TestClient` or direct service calls
  - Rich output snapshots (ANSI stripped)
  - Textual Pilot smoke test that opens TUI and validates Status text
- **Test Steps:** `pytest -q` passes locally and in CI.

### Task P2-T10: Docs & completions

- **DoD:** `docs/cli.md` with examples (offline and HTTP); shell completions (`email-agent --install-completion …`); README “Try It” section updated.
- **Test Steps:** Copy-paste commands work; completion installs on at least one shell.

**Acceptance for Phase 2**

- CLI installed and discoverable
- Commands work in both offline and HTTP modes
- TUI exposes Status, Classify, Rules, Decisions; mode toggle works
- Rich outputs look good; `--json` produces clean machine output
- Tests cover happy/error paths; CI green

---

# Phase 3 — Configuration & Secrets Hardening

**Goal:** Documented, validated config with OS keychain usage.

### Task P3-T1: `docs/configuration.md`

- **DoD:** Minimal and full `app.config.json` examples and all keys documented.
- **Test Steps:** New engineer can run “minimal config” successfully.

### Task P3-T2: Config validation

- **DoD:** Pydantic/JSON Schema validation at startup with human-readable errors.
- **Test Steps:** Start with invalid key → fails fast and points to offending path.

### Task P3-T3: Keychain adapters

- **DoD:** Detect macOS Keychain / Windows DPAPI / Linux libsecret; fallback to encrypted file with warning.
- **Test Steps:** Round-trip save/get secret tests on each OS (mocked if necessary).

---

# Phase 4 — Data Governance & Durability

**Goal:** Safer long-term storage of decisions and versioned stores.

### Task P4-T1: Store versioning

- **DoD:** Add `version` and `$schema` fields to `taxonomy/rules/contacts`.
- **Test Steps:** Loader refuses missing/older major versions unless `--migrate` is provided.

### Task P4-T2: Migrations command

- **DoD:** `email-agent migrate --from vX --to vY` updates on-disk JSON with backups.
- **Test Steps:** Run migration on a sample old store → upgraded file + `.bak` created.

### Task P4-T3: Decision log rotation & compaction

- **DoD:** NDJSON auto-gzips after N days; manifest index (SQLite or Parquet) for fast history queries.
- **Test Steps:** Create >2 days logs; run compactor; verify `.ndjson.gz` and index row count.

---

# Phase 5 — Rule Engine Explainability & ML Status

**Goal:** Transparent decisions; observable ML lifecycle.

### Task P5-T1: Decision “trace”

- **DoD:** Each decision includes `trace` (matched rules, predicates, rule IDs, model confidences).
- **Test Steps:** Post sample email → returned `trace` lists rules & confidences.

### Task P5-T2: `/ml/status` endpoint

- **DoD:** Returns model timestamp, feature count, train samples, and eval metrics (accuracy/F1).
- **Test Steps:** `curl /ml/status` shows non-null metrics; after retrain, values update.

### Task P5-T3: Scheduled retrain

- **DoD:** Nightly job retrains if new labeled feedback exists; persists model + metrics.
- **Test Steps:** Add labeled data; trigger job; metrics reflect change.

---

# Phase 6 — Provider Adapters (Email & Calendar)

**Goal:** Stable interfaces + tested integrations.

### Task P6-T1: Define provider interface

- **DoD:** Abstract `EmailProvider` & `CalendarProvider` (methods: `list`, `send`, `watch`, `normalize`, `classify_meeting`, etc.).
- **Test Steps:** Unit tests assert required methods & error semantics.

### Task P6-T2: Gmail & Outlook adapters

- **DoD:** Implement adapters; include rate-limit/backoff; redact PII in logs.
- **Test Steps:** Use recorded fixtures (VCR) for deterministic tests; live toggles via env var.

### Task P6-T3: IMAP puller (read-only)

- **DoD:** Minimal IMAP adapter for generic providers; clear config knobs.
- **Test Steps:** Point to test IMAP server; verify pull → normalize → classify → decision saved.

### Task P6-T4: Conflict detection endpoint

- **DoD:** `/calendar/conflicts` returns conflicts with reasons & suggested actions.
- **Test Steps:** Overlapping events fixture; endpoint returns conflict list.

---

# Phase 7 — Observability & Privacy Guardrails

**Goal:** Privacy-first telemetry and safety rails.

### Task P7-T1: Structured logging + redaction

- **DoD:** JSON logs; redact emails, subjects, tokens via deterministic patterns; opt-in debug mode.
- **Test Steps:** Emit logs with PII in test; assert redacted output.

### Task P7-T2: Policy guardrails

- **DoD:** Allow/deny matrix for actions (e.g., no auto-send external; “dangerous” actions require confirmation).
- **Test Steps:** Attempt blocked action → `403` with `policy_violation` response.

### Task P7-T3: Rate limit & circuit breaker

- **DoD:** Per-provider token buckets; breaker trips on repeated 5xx; half-open probes.
- **Test Steps:** Fixture forces 5xx → breaker opens; recovery closes it.

---

# Phase 8 — Desktop Packaging & Tray UI

**Goal:** True local desktop experience with a small UI.

### Task P8-T1: System service manifests

- **DoD:** Provide macOS LaunchAgent plist, Windows Service installer (or NSSM recipe), Linux systemd user unit.
- **Test Steps:** Install service; reboot; `/health` returns 200.

### Task P8-T2: Tray UI (Tauri/Electron) skeleton

- **DoD:** Tray app shows health/version, last N decisions, and “pause rules” toggle.
- **Test Steps:** Start tray → toggling “pause” flips a flag; Status visible; decisions update.

### Task P8-T3: Local backup/restore

- **DoD:** UI & CLI to zip/unzip JSON stores + models with version metadata.
- **Test Steps:** Backup; delete local stores; restore; app boots with same data.

---

# Phase 9 — Documentation & Developer Experience

**Goal:** Clear docs and contribution flow.

### Task P9-T1: `docs/desktop.md`

- **DoD:** Install, auto-start, log locations, backup/restore, troubleshooting.
- **Test Steps:** New user sets up from scratch on each OS using doc only.

### Task P9-T2: `docs/api-cookbook.md`

- **DoD:** cURL examples for classify, feedback, rules CRUD, graph queries, conflicts.
- **Test Steps:** Copy-paste commands work against a dev server.

### Task P9-T3: Issue/PR templates & labels

- **DoD:** `.github/ISSUE_TEMPLATE/{bug,feature}.md`, priority labels (`P1`..`P9`), area labels (`ml`, `rules`, `providers`, `ui`, `infra`). Automations optional.
- **Test Steps:** New issue uses template; labels applied via triage rules.

### Task P9-T4: `ROADMAP.md`

- **DoD:** Mirrors these phases with status badges and links to tracking issues.
- **Test Steps:** Each phase item links to at least one GitHub Issue/PR.

---

## Phase Gates (Promote Only When All Pass)

- **G1 (after Phase 1):** CI green on `main` for 5 consecutive commits; no `archieve` references remain.
- **G2 (after Phase 2):** CLI & TUI run in offline and HTTP modes; `/health` & `/version` implemented; Textual TUI smoke test passes.
- **G3 (after Phase 3):** App fails fast on bad config; at least one OS uses OS keychain for secrets (mocked acceptable in CI).
- **G4 (after Phase 5):** Every decision includes `trace`; `/ml/status` reports non-zero metrics.
- **G5 (after Phase 6):** One email and one calendar provider pass recorded-fixture tests; IMAP read-only works.
- **G6 (after Phase 7):** Logs are JSON and PII-redacted; policy guardrails block disallowed actions.
- **G7 (after Phase 8):** Service autostarts on macOS/Windows/Linux; tray UI reflects health and toggles pause.
- **G8 (after Phase 9):** A new dev can set up, run, classify, and view decisions using only docs.

---

## Tracking Issue Template (copy/paste)

```md
## Phase <N> Tracking

**Goal**
<short statement of what the phase achieves>

**Tasks**

- [ ] P<N>-T1: <title>
- [ ] P<N>-T2: <title>
- [ ] P<N>-T3: <title>

**Definition of Done**

- <bullet list>

**Test Steps**

1. ...
2. ...

**Artifacts**

- PRs: #
- Docs: link
- Builds: link

**Risks/Mitigations**

- <risk> → <mitigation>

**Status**

- ☐ Not started ☐ In progress ☐ Blocked ☐ Done
```
