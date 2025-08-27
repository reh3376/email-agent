from fastapi.testclient import TestClient

from email_assistant.api.main import app


def test_api_smoke():
    client = TestClient(app)
    res = client.get("/taxonomy")
    assert res.status_code == 200
