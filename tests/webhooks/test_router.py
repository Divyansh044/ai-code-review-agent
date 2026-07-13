import hashlib
import hmac
import json

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import app
from tests.webhooks.sample_payloads import build_pull_request_payload

TEST_SECRET = "test-webhook-secret"


def _test_settings() -> Settings:
    return Settings(
        github_token="test-token",
        github_webhook_secret=TEST_SECRET,
        openai_api_key="test-key",
    )


@pytest.fixture(autouse=True)
def override_settings():
    app.dependency_overrides[get_settings] = _test_settings
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def sign(body: bytes) -> str:
    return "sha256=" + hmac.new(TEST_SECRET.encode(), body, hashlib.sha256).hexdigest()


def post_event(client: TestClient, event: str, payload: dict, signed: bool = True):
    body = json.dumps(payload).encode()
    headers = {"X-GitHub-Event": event, "Content-Type": "application/json"}
    if signed:
        headers["X-Hub-Signature-256"] = sign(body)
    return client.post("/webhook/github", content=body, headers=headers)


def test_opened_pull_request_is_accepted(client: TestClient) -> None:
    response = post_event(client, "pull_request", build_pull_request_payload("opened"))
    assert response.status_code == 202
    assert response.json() == {"status": "accepted", "pull_request": 42, "action": "opened"}


def test_synchronize_pull_request_is_accepted(client: TestClient) -> None:
    response = post_event(client, "pull_request", build_pull_request_payload("synchronize"))
    assert response.status_code == 202


def test_closed_pull_request_action_is_ignored(client: TestClient) -> None:
    response = post_event(client, "pull_request", build_pull_request_payload("closed"))
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"


def test_ping_event_is_ignored(client: TestClient) -> None:
    response = post_event(client, "ping", {"zen": "Keep it logically awesome."})
    assert response.status_code == 200
    assert response.json() == {"status": "ignored", "reason": "ping"}


def test_unhandled_event_type_is_ignored(client: TestClient) -> None:
    response = post_event(client, "issues", {"action": "opened"})
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"


def test_invalid_signature_is_rejected(client: TestClient) -> None:
    payload = build_pull_request_payload("opened")
    body = json.dumps(payload).encode()
    headers = {
        "X-GitHub-Event": "pull_request",
        "X-Hub-Signature-256": "sha256=" + "0" * 64,
    }
    response = client.post("/webhook/github", content=body, headers=headers)
    assert response.status_code == 401


def test_missing_signature_is_rejected(client: TestClient) -> None:
    response = post_event(client, "pull_request", build_pull_request_payload("opened"), signed=False)
    assert response.status_code == 401
