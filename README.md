# Email Assistant (Desktop) — Local API + JSON Stores + Embedded Graph + Classifier

[![CI](https://github.com/reh3376/email-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/reh3376/email-agent/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🤝 Collaboration

This repository follows a structured collaboration workflow with branch protection
rules. See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for detailed guidelines.

**Key Points:**
- All changes require PR approval from @reh3376
- Developers work in `dev/<username>/<feature>` branches
- All CI checks must pass before merging
- Main branch is protected from direct pushes

---

A privacy-focused, offline-first desktop email assistant that runs locally and
provides intelligent email processing through a FastAPI-based service.
The assistant classifies emails, applies rule-based actions, manages contacts,
and integrates with calendars—all while keeping your data completely local.
User / Application settings allow user to define email addresses, calendars,
and file systems. As well as control classification categories, conditional
actions, agent based actions, and level of email agents involvement and
learning capacity.

## 🚀 Quick Start

> **Requirements:** Python 3.11+ and [UV](https://github.com/astral-sh/uv)
> package manager

```bash
# 1. Clone and navigate to the repository
git clone https://github.com/reh3376/email-agent.git
cd email-agent

# 2. Create and activate virtual environment
uv venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
uv pip install -e ".[dev]"

# 4. Start the API server
uv run python scripts/run_api.py

# 5. Train the local classifier (optional)
uv run python scripts/train_classifier.py --data data/decisions --out src/email_assistant/models/classifier.pt
```

The API will be available at `http://127.0.0.1:8765` with interactive
documentation at `http://127.0.0.1:8765/docs`.

## 🏗️ Architecture Overview

The Email Assistant is built with a modular architecture centered around:

- **🔌 FastAPI Service** - Local REST API (port 8765) with OpenAPI 3.1 specification
- **📊 JSON-based Storage** - Governed JSON files with schema validation for
  configuration and data
- **🧠 Hybrid Classification** - Local PyTorch classifier + fine-tuned LLM integration
- **📈 Graph Database** - Embedded Oxigraph for relationship tracking and audit trails
- **🔄 Rule Engine** - Flexible DSL for email processing automation
- **🗓️ Calendar Integration** - Google Calendar and Outlook support with
  conflict detection
- **🤖 MCP Integration** - Model Context Protocol support for AI agent interactions

### Key Components

```text
src/email_assistant/
├── api/                 # FastAPI routes and endpoints
├── ml/                  # Machine learning models and vectorization
├── models/              # Trained model storage
├── config.py           # Configuration management
└── stores.py           # JSON and NDJSON data persistence

data/                   # Data storage
├── taxonomy_v2.json    # Email classification categories
├── ruleset_v2.json     # Processing rules configuration
├── contacts.json       # Contact database
└── decisions/          # Daily decision logs (NDJSON)

schemas/                # JSON Schema definitions
├── taxonomy.schema.json
├── ruleset.schema.json
├── contacts.schema.json
└── decision.schema.json
```

## 📧 Email Classification System

The assistant uses a **5-category classification taxonomy** that's fully customizable:

| Category        | Purpose    | Example Labels                       |
| --------------- | ---------- | ------------------------------------ |
| **0. Reviewed** | Control    | `reviewed`                           |
| **1. Type**     | Email type | `work/WhiskeyHouse`, `personal`,     |
|                 |            | `professional`                       |
| **2. Sender**   | Who sent   | `friend`, `co-worker`, `vendor`,     |
| **Identity**    | it         | `marketer`                           |
| **3. Context**  | What it's  | `meeting request`,                   |
|                 | about      | `information request`, `promotional` |
| **4. Handler**  | Action     | `user action required`,              |
|                 | needed     | `no action required`                 |

## ⚙️ Configuration & Data Files

### Core Data Files

- **`data/taxonomy_v2.json`** - Defines classification categories and labels
- **`data/ruleset_v2.json`** - Contains processing rules with conditions and actions
- **`data/contacts.json`** - Stores contact information with rich metadata
- **`data/decisions/YYYY-MM-DD.ndjson`** - Daily append-only decision logs

### Example Rule Structure

```json
{
  "id": "meeting-detect-set-handler",
  "description": "Meeting requests require user action",
  "priority": 700,
  "when": [
    {
      "allOf": [
        {
          "path": "$.classification.category3_context",
          "op": "eq",
          "value": "request for meeting"
        }
      ]
    }
  ],
  "then": [
    {
      "type": "set_handler",
      "params": { "value": "user action required" }
    }
  ]
}
```

## 🔌 API Reference

### Core Endpoints

| Endpoint          | Method   | Description                    |
| ----------------- | -------- | ------------------------------ |
| `/taxonomy`       | GET/PUT  | Manage classification taxonomy |
| `/rules`          | GET/PUT  | Manage processing rules        |
| `/decisions`      | GET/POST | Access decision history        |
| `/ml/classify`    | POST     | Classify email content         |
| `/learn/feedback` | POST     | Submit learning feedback       |
| `/graph/query`    | GET      | Query relationship graph       |
| `/graph/ingest`   | POST     | Add graph data                 |

### Example API Usage

```python
import httpx

# Classify an email
response = httpx.post("http://127.0.0.1:8765/ml/classify", json={
    "messageId": "msg_123",
    "subject": "Meeting Request: Project Review",
    "body": "Can we schedule a meeting to review the project status?"
})

classification = response.json()
print(classification["classification"])
# Output: {"category1_type": "work",
#          "category3_context": "request for meeting", ...}
```

## 🧠 Machine Learning Pipeline

### Local Classifier Training

```bash
# Train on historical decision data
uv run python scripts/train_classifier.py \
  --data data/decisions \
  --out src/email_assistant/models/classifier.pt \
  --epochs 10
```

The classifier uses:

- **Hashing Vectorizer** - Deterministic feature extraction without vocabulary storage
- **Multi-head Linear Model** - 4 separate heads for categories 1-4
- **PyTorch Backend** - Lightweight and fast inference

### Learning Loop

1. **Ingest & Infer** - Process incoming emails with local classifier + LLM
2. **Decide & Act** - Apply rules and log immutable decisions
3. **Teach** - Collect user feedback and corrections
4. **Retrain** - Nightly model updates from accumulated data
5. **Audit** - Query decision history via graph database

## 🗓️ Calendar & Contact Integration

### Supported Providers

| Provider      | Email     | Calendar         | Status       |
| ------------- | --------- | ---------------- | ------------ |
| **Google**    | Gmail API | Google Calendar  | ✅ Supported |
| **Microsoft** | Graph API | Outlook Calendar | ✅ Supported |
| **Exchange**  | EWS/Graph | Exchange         | ⏳ Planned   |
| **IMAP/SMTP** | Generic   | N/A              | ✅ Supported |

### Conflict Detection

The assistant automatically checks for calendar conflicts when processing
meeting requests:

```json
{
  "calendar": {
    "conflict": true,
    "conflictDetails": [
      {
        "start": "2025-01-15T14:00:00Z",
        "end": "2025-01-15T15:00:00Z",
        "title": "Existing Meeting"
      }
    ]
  }
}
```

## 🛡️ Security & Privacy

- **Local-Only Processing** - No data leaves your machine
- **Encrypted Storage** - Secrets stored in OS keychain
- **PII Scrubbing** - Personally identifiable information removed from logs
- **Audit Trail** - Complete decision history in graph database
- **Schema Validation** - All data validated against JSON schemas

## 🧪 Development & Testing

### Running Tests

```bash
# Run all tests
uv run pytest tests/

# Run with coverage
uv run pytest --cov=src/email_assistant tests/

# Lint and format code
uv run ruff check --fix .
uv run ruff format .
```

### Project Structure

```text
  email-agent/
├── src/email_assistant/     # Main application code
│   ├── api/                 # FastAPI routes and endpoints
│   ├── ml/                  # Machine learning components
│   ├── models/              # Trained model storage
│   ├── config.py           # Configuration management
│   └── stores.py           # Data persistence layer
├── schemas/                 # JSON Schema definitions
│   ├── taxonomy.schema.json
│   ├── ruleset.schema.json
│   ├── contacts.schema.json
│   └── decision.schema.json
├── data/                    # Application data
│   ├── taxonomy_v2.json     # Classification categories
│   ├── ruleset_v2.json      # Processing rules
│   ├── contacts.json        # Contact database
│   └── decisions/           # Decision logs (NDJSON)
├── scripts/                 # Utility scripts
│   ├── run_api.py          # Start API server
│   └── train_classifier.py # Train ML model
├── tests/                   # Test files
├── pyproject.toml          # Python project configuration
└── README.md               # This file
```

## 🤖 Model Context Protocol (MCP) Integration

The Email Assistant is designed to work seamlessly with MCP-compatible AI agents:

```bash
# Register with MCP toolkit
mcp register openapi_3_1.json --name email-assistant --url http://127.0.0.1:8765
```

Exposed MCP resources:

- `taxonomy_active` - Current classification taxonomy
- `ruleset_active` - Active processing rules
- `samples` - Example classifications
- `decisions_today` - Today's decisions

## 📖 Configuration Examples

### Basic Settings

```json
{
  "stores": {
    "root": "data/",
    "taxonomy": "data/taxonomy_v2.json",
    "ruleset": "data/ruleset_v2.json",
    "contacts": "data/contacts.json",
    "decisions": "data/decisions/"
  },
  "graphdb": {
    "type": "oxigraph",
    "dataDir": "data/graph/"
  },
  "timezone": "America/Kentucky/Louisville"
}
```

### Email Provider Setup

```json
{
  "email": {
    "primary": {
      "provider": "gmail",
      "credentials": "stored_in_keychain"
    },
    "secondary": {
      "provider": "outlook",
      "credentials": "stored_in_keychain"
    }
  }
}
```

## 🚀 Advanced Usage

### Custom Rule Development

Create sophisticated rules using JSONPath conditions:

```json
{
  "id": "high-priority-vendor",
  "priority": 800,
  "when": [
    {
      "allOf": [
        {
          "path": "$.classification.category2_sender_identity",
          "op": "eq",
          "value": "vendor"
        },
        {
          "path": "$.message.subject",
          "op": "regex",
          "value": "URGENT|HIGH PRIORITY"
        }
      ]
    }
  ],
  "then": [
    { "type": "set_flag", "params": { "key": "urgent", "value": true } },
    { "type": "set_handler", "params": { "value": "user action required" } }
  ]
}
```

### Graph Database Queries

```bash
# Query decision patterns
curl -X GET "http://127.0.0.1:8765/graph/query" \
  -G -d "q=SELECT ?sender ?count WHERE { ?sender :email_count ?count } ORDER BY DESC(?count)"
```

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes** following the coding standards
4. **Add tests** for new functionality
5. **Run the test suite** (`uv run pytest`)
6. **Commit your changes** (`git commit -m 'feat: add amazing feature'`)
7. **Push to the branch** (`git push origin feature/amazing-feature`)
8. **Open a Pull Request**

### Coding Standards

- Follow [PEP 8](https://pep8.org/) style guidelines
- Use [Ruff](https://github.com/astral-sh/ruff) for linting and formatting
- Add type hints for all function parameters and return values
- Write docstrings for all public functions and classes
- Maintain test coverage above 80%

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE)
file for details.

## 🔗 Links

- **GitHub Repository**: [https://github.com/reh3376/email-agent](https://github.com/reh3376/email-agent)
- **API Documentation**: `http://127.0.0.1:8765/docs` (when running locally)
- **Project Roadmap**: [roadmap.md](roadmap.md)

---

**Built with ❤️ for privacy-conscious email management**
