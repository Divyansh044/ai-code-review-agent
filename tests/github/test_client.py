import json

import httpx
import pytest

from app.github.client import GitHubClient
from app.models import RepositoryInfo, ReviewComment, Severity

REPO = RepositoryInfo(
    owner="octo-org",
    name="widgets",
    full_name="octo-org/widgets",
    default_branch="main",
    clone_url="https://github.com/octo-org/widgets.git",
)

FILES_URL = "https://api.github.com/repos/octo-org/widgets/pulls/42/files?per_page=100"
FILES_URL_PAGE_2 = "https://api.github.com/repos/octo-org/widgets/pulls/42/files?per_page=100&page=2"


def make_client(handler) -> GitHubClient:
    transport = httpx.MockTransport(handler)
    http_client = httpx.AsyncClient(base_url="https://api.github.com", transport=transport)
    return GitHubClient(token="test-token", http_client=http_client)


async def test_get_pull_request_files_single_page() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == FILES_URL
        return httpx.Response(200, json=[{"filename": "app/main.py"}, {"filename": "README.md"}])

    client = make_client(handler)
    files = await client.get_pull_request_files(REPO, 42)

    assert files == ["app/main.py", "README.md"]


async def test_get_pull_request_files_follows_pagination() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url == FILES_URL:
            return httpx.Response(
                200,
                json=[{"filename": "a.py"}, {"filename": "b.py"}],
                headers={"Link": f'<{FILES_URL_PAGE_2}>; rel="next"'},
            )
        if url == FILES_URL_PAGE_2:
            return httpx.Response(200, json=[{"filename": "c.py"}])
        raise AssertionError(f"unexpected request: {url}")

    client = make_client(handler)
    files = await client.get_pull_request_files(REPO, 42)

    assert files == ["a.py", "b.py", "c.py"]


async def test_get_pull_request_diff_returns_raw_text() -> None:
    diff_text = "diff --git a/app/main.py b/app/main.py\n+print('hi')\n"

    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://api.github.com/repos/octo-org/widgets/pulls/42"
        assert request.headers["accept"] == "application/vnd.github.v3.diff"
        return httpx.Response(200, text=diff_text)

    client = make_client(handler)
    diff = await client.get_pull_request_diff(REPO, 42)

    assert diff == diff_text


async def test_create_review_sends_expected_payload_and_auth_header() -> None:
    comment = ReviewComment(
        file="app/main.py",
        line=10,
        severity=Severity.HIGH,
        title="Unused import",
        explanation="`os` is imported but never used.",
        suggestion="Remove the import.",
    )

    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://api.github.com/repos/octo-org/widgets/pulls/42/reviews"
        assert request.headers["authorization"] == "Bearer test-token"

        payload = json.loads(request.content)
        assert payload["body"] == "Looks good overall."
        assert payload["event"] == "COMMENT"
        assert payload["comments"] == [
            {
                "path": "app/main.py",
                "line": 10,
                "side": "RIGHT",
                "body": "**[HIGH] Unused import**\n\n`os` is imported but never used.\n\n**Suggestion:** Remove the import.",
            }
        ]
        return httpx.Response(200, json={"id": 1})

    client = make_client(handler)
    result = await client.create_review(REPO, 42, "Looks good overall.", [comment])

    assert result == {"id": 1}


async def test_error_response_raises_http_status_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "Not Found"})

    client = make_client(handler)

    with pytest.raises(httpx.HTTPStatusError):
        await client.get_pull_request_diff(REPO, 42)
