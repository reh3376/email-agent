from __future__ import annotations

import datetime
import os
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException, Path, Query, Response

from ..attachment_manager import AttachmentManager, AttachmentStats
from ..config import ensure_dirs, load_config
from ..ml.classifier import load_model
from ..ml.classifier import predict as predict_local
from ..rules_engine import create_rules_engine
from ..scheduler import EmailScheduler
from ..stores import JsonStore, NdjsonStore
from .models import (
    Classification,
    ClassificationRequest,
    ClassificationResponse,
    Decision,
    EmailFeatures,
    FeedbackBatch,
    FeedbackResponse,
    GraphIngestRequest,
    GraphIngestResponse,
    GraphQueryResponse,
    Ruleset,
    SchedulePreview,
    Taxonomy,
    VersionInfo,
)

# Constants
MESSAGE_ID_DESC = "Message ID"
ATTACHMENT_FILENAME_DESC = "Attachment filename"

app = FastAPI(
    title="Email Assistant Local API",
    version="1.0.0",
    description="Local API for Email Assistant desktop application with MCP integration",
)

CFG = load_config("app.config.json")
ensure_dirs(CFG)

taxonomy_store = JsonStore(CFG["stores"]["taxonomy"])
rules_store = JsonStore(CFG["stores"]["ruleset"])
contacts_store = JsonStore(CFG["stores"]["contacts"])
decisions_store = NdjsonStore(CFG["stores"]["decisions"])

MODEL_PATH = "src/email_assistant/models/classifier.pt"

# Version stores for taxonomy and rules
taxonomy_versions: dict[str, Taxonomy] = {}
rules_versions: dict[str, Ruleset] = {}

# Scheduler instance
scheduler = EmailScheduler()

# Attachment manager instance
attachment_manager = AttachmentManager(
    base_path=CFG.get("attachments", {}).get("basePath", "./data/attachments"),
    retention_days=CFG.get("attachments", {}).get("retentionDays", 90),
)


@app.get("/taxonomy", response_model=Taxonomy)
def get_taxonomy():
    """Get current taxonomy configuration."""
    data = taxonomy_store.read()
    if not data:
        raise HTTPException(status_code=404, detail="Taxonomy not found")
    return Taxonomy(**data)


@app.put("/taxonomy", response_model=Taxonomy)
def put_taxonomy(taxonomy: Taxonomy):
    """Update taxonomy configuration."""
    data = taxonomy.model_dump()
    taxonomy_store.write(data)
    # Store version
    version_key = f"{taxonomy.version}_{datetime.datetime.now().isoformat()}"
    taxonomy_versions[version_key] = taxonomy
    return taxonomy


def _convert_legacy_ruleset(data: dict) -> dict:
    """Convert legacy ruleset format to current format."""
    if "rules" not in data:
        return data

    data["rules"] = [_convert_single_rule(rule) for rule in data["rules"]]
    return data


def _convert_single_rule(rule: dict) -> dict:
    """Convert a single rule from legacy to current format."""
    return {
        "id": rule.get("id", ""),
        "name": rule.get("id", "").replace("-", " ").title(),
        "description": rule.get("description", ""),
        "priority": rule.get("priority", 100),
        "enabled": True,
        "conditions": _extract_conditions(rule),
        "actions": _extract_actions(rule),
    }


def _extract_conditions(rule: dict) -> list:
    """Extract conditions from legacy rule format."""
    conditions = []
    if "when" not in rule:
        return conditions

    for when_group in rule["when"]:
        if "allOf" in when_group:
            conditions.extend(_convert_all_of_conditions(when_group["allOf"]))

    return conditions


def _convert_all_of_conditions(all_of_conditions: list) -> list:
    """Convert allOf conditions to current format."""
    return [
        {
            "field": cond.get("path", "").replace("$.", ""),
            "operator": cond.get("op", "exists"),
            "value": cond.get("value", True),
            "logic": "AND",
        }
        for cond in all_of_conditions
    ]


def _extract_actions(rule: dict) -> list:
    """Extract actions from legacy rule format."""
    if "then" not in rule:
        return []

    return [
        {
            "type": action.get("type", "unknown"),
            "parameters": {k: v for k, v in action.items() if k != "type"},
        }
        for action in rule["then"]
    ]


@app.get("/rules", response_model=Ruleset)
def get_rules():
    """Get current ruleset configuration."""
    data = rules_store.read()
    if not data:
        raise HTTPException(status_code=404, detail="Ruleset not found")

    # Convert legacy format if needed
    if data.get("rules") and len(data["rules"]) > 0:
        first_rule = data["rules"][0]
        if "when" in first_rule or "then" in first_rule:
            data = _convert_legacy_ruleset(data)

    return Ruleset(**data)


@app.put("/rules", response_model=Ruleset)
def put_rules(ruleset: Ruleset):
    """Update ruleset configuration."""
    data = ruleset.model_dump()
    rules_store.write(data)
    # Store version
    version_key = f"{ruleset.version}_{datetime.datetime.now().isoformat()}"
    rules_versions[version_key] = ruleset
    return ruleset


@app.get("/decisions", response_model=list[Decision])
def list_decisions(
    date: str | None = Query(None, description="Filter by date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=10000),
):
    """List email decisions."""
    decisions = decisions_store.scan(date=date, limit=limit)
    return [Decision(**d) for d in decisions]


@app.post("/decisions", response_model=Decision, status_code=201)
def record_decision(decision: Decision):
    """Create new decision record."""
    # Generate ID if not provided
    if not decision.id:
        decision.id = str(uuid.uuid4())

    # Add timestamp if not provided
    if not decision.timestamp:
        decision.timestamp = datetime.datetime.now()

    try:
        # Convert to dict with JSON-compatible datetime
        data = decision.model_dump(mode="json")
        decisions_store.append(data)
        return decision
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record decision: {str(e)}")


@app.get("/decisions/{id}", response_model=Decision)
def get_decision_by_id(id: str = Path(..., description="Decision ID")):
    """Get decision by ID."""
    # Search through decisions
    decisions = decisions_store.scan(limit=10000)
    for decision in decisions:
        if decision.get("id") == id:
            return Decision(**decision)
    raise HTTPException(status_code=404, detail="Decision not found")


@app.get("/taxonomy/versions", response_model=list[VersionInfo])
def get_taxonomy_versions():
    """List taxonomy versions."""
    versions = []
    for key, taxonomy in taxonomy_versions.items():
        version, created = key.split("_", 1)
        versions.append(
            VersionInfo(
                version=version,
                createdAt=datetime.datetime.fromisoformat(created),
                description=f"Taxonomy {version}",
            )
        )
    return versions


@app.post("/taxonomy/versions", response_model=VersionInfo, status_code=201)
def create_taxonomy_version(taxonomy: Taxonomy):
    """Create new taxonomy version."""
    version_key = f"{taxonomy.version}_{datetime.datetime.now().isoformat()}"
    taxonomy_versions[version_key] = taxonomy

    return VersionInfo(
        version=taxonomy.version,
        createdAt=datetime.datetime.now(),
        description=f"Taxonomy {taxonomy.version}",
    )


@app.get("/rules/versions", response_model=list[VersionInfo])
def get_rules_versions():
    """List ruleset versions."""
    versions = []
    for key, ruleset in rules_versions.items():
        version, created = key.split("_", 1)
        versions.append(
            VersionInfo(
                version=version,
                createdAt=datetime.datetime.fromisoformat(created),
                description=f"Ruleset {version}",
            )
        )
    return versions


@app.post("/rules/versions", response_model=VersionInfo, status_code=201)
def create_rules_version(ruleset: Ruleset):
    """Create new ruleset version."""
    version_key = f"{ruleset.version}_{datetime.datetime.now().isoformat()}"
    rules_versions[version_key] = ruleset

    return VersionInfo(
        version=ruleset.version,
        createdAt=datetime.datetime.now(),
        description=f"Ruleset {ruleset.version}",
    )


@app.get("/scheduler/preview", response_model=SchedulePreview)
def get_scheduler_preview(
    schedule: str = Query(..., description="Schedule expression"),
    count: int = Query(10, ge=1, le=100, description="Number of future runs"),
):
    """Preview next scheduled runs."""
    try:
        next_runs = scheduler.get_next_runs(schedule, count)
        return SchedulePreview(schedule=schedule, nextRuns=next_runs)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/learn/feedback", response_model=FeedbackResponse)
def post_feedback(feedback: FeedbackBatch):
    """Submit learning feedback."""
    processed_count = 0
    graph_updates = 0

    for item in feedback.items:
        result = _process_feedback_item(item)
        processed_count += result["processed"]
        graph_updates += result["graph_updates"]

    return FeedbackResponse(accepted=processed_count, graphUpserts=graph_updates)


def _process_feedback_item(item) -> dict:
    """Process a single feedback item."""
    result = {"processed": 0, "graph_updates": 0}

    try:
        if item.decisionId and _update_decision_feedback(item):
            result["processed"] = 1

        if item.correctedClassification:
            result["graph_updates"] = 1

    except Exception as e:
        print(f"Error processing feedback item: {e}")

    return result


def _update_decision_feedback(item) -> bool:
    """Update decision with feedback data."""
    for days_back in range(7):  # Check last 7 days
        date = datetime.datetime.now() - datetime.timedelta(days=days_back)
        if _update_decision_for_date(item, date):
            return True
    return False


def _update_decision_for_date(item, date) -> bool:
    """Try to update decision for a specific date."""
    try:
        decisions = list(decisions_store.scan(date=date))
        for decision in decisions:
            if decision.get("id") == item.decisionId:
                _apply_feedback_to_decision(decision, item)
                decisions_store.append(decision)
                return True
    except Exception:
        pass
    return False


def _apply_feedback_to_decision(decision: dict, item) -> None:
    """Apply feedback to a decision object."""
    decision["feedback"] = {
        "correctedClassification": item.correctedClassification.model_dump()
        if item.correctedClassification
        else None,
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        "notes": item.notes,
    }


@app.get("/graph/query", response_model=GraphQueryResponse)
def graph_query(
    lang: str = Query("sparql", pattern="^(sparql|cypher)$"),
    q: str = Query(..., description="Query string"),
    limit: int = Query(1000, ge=1, le=10000),
):
    """Query graph database."""
    # For now, return mock data as Oxigraph integration is pending
    # In production, this would execute the query against Oxigraph

    if lang == "sparql":
        # Example SPARQL query response structure
        return GraphQueryResponse(
            columns=["subject", "predicate", "object"],
            rows=[
                ["email:123", "classification:type", "work"],
                ["email:123", "classification:sender", "colleague"],
                ["email:456", "classification:type", "personal"],
                ["email:456", "classification:sender", "friend"],
            ][:limit],
        )
    else:
        # Example Cypher query response structure
        return GraphQueryResponse(
            columns=["node", "relationship", "property"],
            rows=[
                ["Email", "CLASSIFIED_AS", "work"],
                ["Email", "SENT_BY", "colleague"],
                ["Email", "HAS_ATTACHMENT", "true"],
                ["Email", "PRIORITY", "high"],
            ][:limit],
        )


@app.post("/graph/ingest", response_model=GraphIngestResponse)
def graph_ingest(request: GraphIngestRequest):
    """Ingest data into graph."""
    errors = []
    processed_triples = 0

    # Validate and process triples
    triples = request.batch.get("triples", [])

    for triple in triples:
        try:
            # Validate triple structure
            if not isinstance(triple, (list, tuple)) or len(triple) != 3:
                errors.append(f"Invalid triple format: {triple}")
                continue

            subject, predicate, obj = triple

            # Here we would normally insert into Oxigraph
            # For now, we just validate the data
            if all(isinstance(x, str) for x in [subject, predicate, obj]):
                processed_triples += 1
            else:
                errors.append(f"Triple components must be strings: {triple}")

        except Exception as e:
            errors.append(f"Error processing triple: {str(e)}")

    return GraphIngestResponse(
        tripleCount=processed_triples,
        errors=errors[:10],  # Limit error messages
    )


@app.post("/ml/classify", response_model=ClassificationResponse)
def classify(request: ClassificationRequest):
    """Classify email using ML model."""
    if not os.path.exists(MODEL_PATH):
        raise HTTPException(
            status_code=400, detail="Model not trained. Run scripts/train_classifier.py"
        )

    # Load model and classify
    hv, model, label_spaces = load_model(MODEL_PATH)
    text = f"{request.subject} {request.body}"
    classification_dict = predict_local(hv, model, label_spaces, [text])[0]

    # Create classification object
    classification = Classification(**classification_dict)

    # Create features object
    features = EmailFeatures(
        subject=request.subject,
        body=request.body,
        from_=request.from_,
        to=request.to,
    )

    # Apply rules engine
    rules_matched = []
    actions_list = []

    # Load current ruleset and create engine
    ruleset_data = rules_store.read()
    if ruleset_data and "rules" in ruleset_data:
        engine = create_rules_engine(ruleset_data["rules"])

        # Prepare email data for rules evaluation
        email_data = {
            "subject": request.subject,
            "body": request.body,
            "from": request.from_,
            "to": request.to or [],
            "hasAttachments": False,
            "attachmentCount": 0,
        }

        # Evaluate rules
        matches = engine.evaluate(email_data, classification)

        # Extract matched rule names and actions
        for match in matches:
            rules_matched.append(match.rule_name)
            actions_list.extend(match.actions)

    return ClassificationResponse(
        messageId=request.messageId or str(uuid.uuid4()),
        timestamp=datetime.datetime.now(),
        classification=classification,
        features=features,
        rulesMatched=rules_matched,
        actions=actions_list,
    )


@app.get("/attachments/stats", response_model=AttachmentStats)
def get_attachment_stats():
    """Get attachment storage statistics."""
    return attachment_manager.get_stats()


@app.get("/attachments/{messageId}", response_model=list[dict[str, Any]])
def list_attachments(message_id: str = Path(..., alias="messageId", description=MESSAGE_ID_DESC)):
    """List all attachments for an email."""
    return attachment_manager.list_attachments(message_id)


@app.get("/attachments/{messageId}/{filename}")
def get_attachment(
    message_id: str = Path(..., alias="messageId", description=MESSAGE_ID_DESC),
    filename: str = Path(..., description=ATTACHMENT_FILENAME_DESC),
):
    """Download a specific attachment."""
    content = attachment_manager.get_attachment(message_id, filename)
    if content is None:
        raise HTTPException(status_code=404, detail="Attachment not found")

    # Guess content type from filename
    content_type = "application/octet-stream"
    if filename.lower().endswith(".pdf"):
        content_type = "application/pdf"
    elif filename.lower().endswith((".jpg", ".jpeg")):
        content_type = "image/jpeg"
    elif filename.lower().endswith(".png"):
        content_type = "image/png"

    return Response(
        content=content,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.delete("/attachments/{messageId}/{filename}")
def delete_attachment(
    message_id: str = Path(..., alias="messageId", description=MESSAGE_ID_DESC),
    filename: str = Path(..., description=ATTACHMENT_FILENAME_DESC),
):
    """Remove an attachment."""
    deleted = attachment_manager.delete_attachment(message_id, filename)
    if not deleted:
        raise HTTPException(status_code=404, detail="Attachment not found")

    return {"status": "deleted", "messageId": message_id, "filename": filename}
