from app.webhooks.parser import parse_pull_request_event
from tests.webhooks.sample_payloads import build_pull_request_payload


def test_parses_pull_request_and_repository_fields() -> None:
    payload = build_pull_request_payload()

    pull_request = parse_pull_request_event(payload)

    assert pull_request.number == 42
    assert pull_request.title == "Add retry logic to the HTTP client"
    assert pull_request.body == "Fixes flaky requests under load."
    assert pull_request.author == "octocat"
    assert pull_request.head_sha == "abc123"
    assert pull_request.head_ref == "feature/retry-logic"
    assert pull_request.base_ref == "main"
    assert pull_request.changed_files == []

    repository = pull_request.repository
    assert repository.owner == "octo-org"
    assert repository.name == "widgets"
    assert repository.full_name == "octo-org/widgets"
    assert repository.default_branch == "main"
    assert repository.clone_url == "https://github.com/octo-org/widgets.git"
