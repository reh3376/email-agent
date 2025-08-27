#!/usr/bin/env python3
"""Test script to demonstrate Email Assistant API functionality."""

from __future__ import annotations

import sys
from datetime import datetime

import requests

API_BASE = "http://127.0.0.1:8765"


def test_taxonomy():
    """Test taxonomy endpoints."""
    print("\n=== Testing Taxonomy Endpoints ===")

    # Try to get current taxonomy
    response = requests.get(f"{API_BASE}/taxonomy")
    if response.status_code == 404:
        print("No taxonomy found, creating default...")

        # Create default taxonomy
        taxonomy = {
            "type": "email_categories",
            "version": "v1",
            "categories": [
                {"id": 0, "name": "reviewed", "labels": ["yes", "no"]},
                {
                    "id": 1,
                    "name": "type",
                    "labels": [
                        "personal",
                        "work",
                        "newsletter",
                        "marketing",
                        "transactional",
                        "social",
                        "spam",
                    ],
                },
                {
                    "id": 2,
                    "name": "senderIdentity",
                    "labels": ["known", "unknown", "service", "company", "automated"],
                },
                {
                    "id": 3,
                    "name": "context",
                    "labels": [
                        "general",
                        "project",
                        "event",
                        "financial",
                        "health",
                        "education",
                        "travel",
                    ],
                },
                {
                    "id": 4,
                    "name": "handler",
                    "labels": ["read", "respond", "schedule", "file", "delete", "delegate"],
                },
            ],
        }

        response = requests.put(f"{API_BASE}/taxonomy", json=taxonomy)
        print(f"Created taxonomy: {response.status_code}")

    # Get taxonomy
    response = requests.get(f"{API_BASE}/taxonomy")
    print(f"Get taxonomy: {response.status_code}")
    if response.ok:
        print(f"Categories: {[c['name'] for c in response.json()['categories']]}")

    # Test versions
    response = requests.get(f"{API_BASE}/taxonomy/versions")
    print(f"List versions: {response.status_code}")


def test_rules():
    """Test rules endpoints."""
    print("\n=== Testing Rules Endpoints ===")

    # Try to get current rules
    response = requests.get(f"{API_BASE}/rules")
    if response.status_code == 404:
        print("No ruleset found, creating default...")

        # Create default ruleset
        ruleset = {
            "type": "email_rules",
            "version": "v1",
            "rules": [
                {
                    "id": "rule-1",
                    "name": "Auto-file newsletters",
                    "priority": 1,
                    "enabled": True,
                    "conditions": [
                        {"field": "classification.type", "operator": "eq", "value": "newsletter"}
                    ],
                    "actions": [
                        {"type": "save_to_folder", "parameters": {"folder": "Newsletters"}},
                        {"type": "mark_read"},
                    ],
                },
                {
                    "id": "rule-2",
                    "name": "Flag urgent work emails",
                    "priority": 2,
                    "enabled": True,
                    "conditions": [
                        {"field": "classification.type", "operator": "eq", "value": "work"},
                        {
                            "field": "subject",
                            "operator": "regex",
                            "value": "(urgent|asap|important)",
                        },
                    ],
                    "actions": [{"type": "flag", "parameters": {"color": "red"}}],
                },
            ],
        }

        response = requests.put(f"{API_BASE}/rules", json=ruleset)
        print(f"Created ruleset: {response.status_code}")

    # Get rules
    response = requests.get(f"{API_BASE}/rules")
    print(f"Get rules: {response.status_code}")
    if response.ok:
        rules = response.json().get("rules", [])
        print(f"Rules: {[r['name'] for r in rules]}")


def test_scheduler():
    """Test scheduler preview."""
    print("\n=== Testing Scheduler ===")

    schedules = ["every_15_minutes", "daily", "*/30 * * * *", "RRULE:FREQ=DAILY;BYHOUR=9,17"]

    for schedule in schedules:
        response = requests.get(
            f"{API_BASE}/scheduler/preview", params={"schedule": schedule, "count": 3}
        )
        print(f"\nSchedule '{schedule}': {response.status_code}")
        if response.ok:
            data = response.json()
            print("Next runs:")
            for run in data["nextRuns"][:3]:
                print(f"  - {run}")


def test_classification():
    """Test ML classification (will fail without trained model)."""
    print("\n=== Testing ML Classification ===")

    # Test email
    email = {
        "subject": "Urgent: Project deadline tomorrow",
        "body": (
            "Hi team, just a reminder that our project deadline is tomorrow at 5 PM. "
            "Please make sure all deliverables are ready."
        ),
        "from": "john.doe@company.com",
        "to": ["team@company.com"],
    }

    response = requests.post(f"{API_BASE}/ml/classify", json=email)
    print(f"Classify email: {response.status_code}")

    if response.status_code == 400:
        print("Expected: Model not trained yet")
    elif response.ok:
        result = response.json()
        print(f"Classification: {result.get('classification')}")
        print(f"Rules matched: {result.get('rulesMatched')}")


def test_decisions():
    """Test decision storage."""
    print("\n=== Testing Decisions ===")

    # Create a decision
    decision = {
        "messageId": "msg-123",
        "timestamp": datetime.now().isoformat(),
        "email": {
            "subject": "Test email",
            "from": "test@example.com",
            "to": ["user@example.com"],
            "receivedAt": datetime.now().isoformat(),
        },
        "classification": {
            "reviewed": "no",
            "type": "personal",
            "senderIdentity": "known",
            "context": "general",
            "handler": "read",
        },
        "rulesMatched": [],
        "actions": [],
    }

    response = requests.post(f"{API_BASE}/decisions", json=decision)
    print(f"Create decision: {response.status_code}")

    if response.ok:
        created = response.json()
        decision_id = created.get("id")
        print(f"Decision ID: {decision_id}")

        # List decisions
        response = requests.get(f"{API_BASE}/decisions", params={"limit": 5})
        print(f"List decisions: {response.status_code}")
        if response.ok:
            decisions = response.json()
            print(f"Found {len(decisions)} decisions")

        # Get specific decision
        if decision_id:
            response = requests.get(f"{API_BASE}/decisions/{decision_id}")
            print(f"Get decision by ID: {response.status_code}")


def test_graph():
    """Test graph endpoints."""
    print("\n=== Testing Graph Endpoints ===")

    # Test query
    response = requests.get(
        f"{API_BASE}/graph/query", params={"q": "SELECT * WHERE { ?s ?p ?o } LIMIT 10"}
    )
    print(f"Graph query: {response.status_code}")

    # Test ingest
    ingest_data = {
        "batch": {
            "triples": [
                {"subject": "email:123", "predicate": "hasType", "object": "work"},
                {"subject": "email:123", "predicate": "fromSender", "object": "john@example.com"},
            ]
        }
    }

    response = requests.post(f"{API_BASE}/graph/ingest", json=ingest_data)
    print(f"Graph ingest: {response.status_code}")
    if response.ok:
        result = response.json()
        print(f"Ingested {result['tripleCount']} triples")


def main():
    """Run all tests."""
    print("Email Assistant API Test Suite")
    print("=" * 50)

    # Check if API is running
    try:
        response = requests.get(f"{API_BASE}/openapi.json")
        if not response.ok:
            print("Error: API is not responding properly")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print(f"Error: Cannot connect to API at {API_BASE}")
        print("Make sure the API is running: uv run python scripts/run_api.py")
        sys.exit(1)

    # Run tests
    test_taxonomy()
    test_rules()
    test_scheduler()
    test_classification()
    test_decisions()
    test_graph()

    print("\n" + "=" * 50)
    print("All tests completed!")
    print("\nCheck API documentation at: http://127.0.0.1:8765/docs")


if __name__ == "__main__":
    main()
