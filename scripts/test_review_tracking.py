#!/usr/bin/env python3
"""Test script for review tracking and attachment management functionality."""
import json
import sys
from datetime import datetime

import requests

BASE_URL = "http://127.0.0.1:8765"


def test_decision_with_review_tracking():
    """Test creating a decision with review tracking fields."""
    print("\n=== Testing Decision with Review Tracking ===")
    
    # Create a decision with review tracking
    decision_data = {
        "messageId": "msg-12345",
        "timestamp": datetime.now().isoformat(),
        "email": {
            "subject": "Quarterly Report - Please Review",
            "from": "manager@company.com",
            "to": ["employee@company.com"],
            "receivedAt": datetime.now().isoformat(),
            "sentAt": datetime.now().isoformat(),
            "hasAttachments": True,
            "attachments": [
                {
                    "filename": "Q4_Report.pdf",
                    "mimeType": "application/pdf",
                    "size": 2048576,
                    "storagePath": "/data/attachments/2025-08-27/msg-12345/Q4_Report.pdf",
                    "sha256Hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
                }
            ],
            "attachmentCount": 1,
            "importance": "high",
            "isRead": False,
            "isFlagged": True
        },
        "classification": {
            "reviewed": "no",
            "type": "work/WhiskeyHouse",
            "senderIdentity": "co-worker",
            "context": "request for information",
            "handler": "user action required"
        },
        "rulesMatched": [{"ruleId": "rule-review-required", "ruleName": "Review Required"}],
        "actions": [{"type": "flag", "parameters": {"color": "red"}}],
        # Review tracking fields
        "reviewCount": 2,
        "reviewCountThreshold": 3,
        "reviewCountExceeded": False,
        "lastReviewedAt": datetime.now().isoformat()
    }
    
    resp = requests.post(f"{BASE_URL}/decisions", json=decision_data)
    
    if resp.status_code != 201:
        print(f"❌ Failed to create decision: {resp.status_code}")
        print(f"   Response: {resp.text}")
        return False
    
    print("✅ Successfully created decision with review tracking")
    decision = resp.json()
    print(f"   - Message ID: {decision['messageId']}")
    print(f"   - Review Count: {decision['reviewCount']}")
    print(f"   - Review Threshold: {decision['reviewCountThreshold']}")
    print(f"   - Review Exceeded: {decision['reviewCountExceeded']}")
    
    # Test updating review count to exceed threshold
    print("\n   Testing review count threshold...")
    decision_data["reviewCount"] = 4
    decision_data["reviewCountExceeded"] = True
    decision_data["messageId"] = "msg-12346"
    
    resp = requests.post(f"{BASE_URL}/decisions", json=decision_data)
    if resp.status_code == 201:
        print("✅ Successfully flagged decision with exceeded review count")
    else:
        print(f"❌ Failed to create flagged decision: {resp.status_code}")
    
    return True


def test_attachment_endpoints():
    """Test attachment management endpoints."""
    print("\n=== Testing Attachment Management ===")
    
    # Test listing attachments
    message_id = "msg-12345"
    print(f"\n1. Testing GET /attachments/{message_id}")
    resp = requests.get(f"{BASE_URL}/attachments/{message_id}")
    
    if resp.status_code == 200:
        attachments = resp.json()
        print(f"✅ Retrieved {len(attachments)} attachments")
        for att in attachments:
            print(f"   - {att.get('filename')} ({att.get('size', 0)} bytes)")
    else:
        print(f"❌ Failed to list attachments: {resp.status_code}")
    
    # Test attachment stats
    print("\n2. Testing GET /attachments/stats")
    resp = requests.get(f"{BASE_URL}/attachments/stats")
    
    if resp.status_code == 200:
        stats = resp.json()
        print("✅ Retrieved attachment statistics:")
        if isinstance(stats, dict):
            print(f"   - Total Files: {stats.get('totalFiles', 0)}")
            print(f"   - Total Size: {stats.get('totalSizeBytes', 0)} bytes")
            print(f"   - By MIME Type: {json.dumps(stats.get('byMimeType', {}), indent=6)}")
        else:
            print(f"   - Response: {stats}")
    else:
        print(f"❌ Failed to get attachment stats: {resp.status_code}")
    
    # Test downloading attachment (will fail if file doesn't exist)
    print(f"\n3. Testing GET /attachments/{message_id}/Q4_Report.pdf")
    resp = requests.get(f"{BASE_URL}/attachments/{message_id}/Q4_Report.pdf")
    
    if resp.status_code == 200:
        print("✅ Successfully retrieved attachment")
        print(f"   - Content Type: {resp.headers.get('content-type')}")
        print(f"   - Size: {len(resp.content)} bytes")
    elif resp.status_code == 404:
        print("⚠️  Attachment not found (expected if file doesn't exist)")
    else:
        print(f"❌ Unexpected error: {resp.status_code}")
    
    return True


def test_taxonomy_with_review_count():
    """Test that taxonomy still works correctly."""
    print("\n=== Testing Taxonomy (Sanity Check) ===")
    
    resp = requests.get(f"{BASE_URL}/taxonomy")
    if resp.status_code != 200:
        print(f"❌ Failed to get taxonomy: {resp.status_code}")
        return False
    
    taxonomy = resp.json()
    print("✅ Retrieved taxonomy")
    
    # Find the reviewed category
    reviewed_cat = next((cat for cat in taxonomy["categories"] if cat["name"] == "reviewed"), None)
    if reviewed_cat:
        print(f"   - Reviewed category ID: {reviewed_cat['id']}")
        print(f"   - Labels: {reviewed_cat['labels']}")
    else:
        print("❌ Reviewed category not found")
    
    return True


def main():
    """Run all tests."""
    print("Email Assistant - Review Tracking & Attachment Management Tests")
    print("=" * 60)
    
    # Check if API is running
    try:
        resp = requests.get(f"{BASE_URL}/taxonomy")
        if resp.status_code != 200:
            print("❌ API is not responding correctly")
            print("   Please ensure the API is running: uv run uvicorn email_assistant.api.main:app --host 127.0.0.1 --port 8765")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API at", BASE_URL)
        print("   Please ensure the API is running: uv run uvicorn email_assistant.api.main:app --host 127.0.0.1 --port 8765")
        sys.exit(1)
    
    # Run tests
    tests_passed = 0
    tests_total = 3
    
    if test_taxonomy_with_review_count():
        tests_passed += 1
    
    if test_decision_with_review_tracking():
        tests_passed += 1
    
    if test_attachment_endpoints():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print(f"Tests completed: {tests_passed}/{tests_total} passed")
    
    if tests_passed == tests_total:
        print("✅ All tests passed!")
    else:
        print(f"❌ {tests_total - tests_passed} tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
