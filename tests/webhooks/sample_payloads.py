from typing import Any


def build_pull_request_payload(action: str = "opened") -> dict[str, Any]:
    return {
        "action": action,
        "pull_request": {
            "number": 42,
            "title": "Add retry logic to the HTTP client",
            "body": "Fixes flaky requests under load.",
            "user": {"login": "octocat"},
            "head": {"sha": "abc123", "ref": "feature/retry-logic"},
            "base": {"ref": "main"},
        },
        "repository": {
            "owner": {"login": "octo-org"},
            "name": "widgets",
            "full_name": "octo-org/widgets",
            "default_branch": "main",
            "clone_url": "https://github.com/octo-org/widgets.git",
        },
    }
