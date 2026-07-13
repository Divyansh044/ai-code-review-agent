from typing import Any

from app.models import PullRequestInfo, RepositoryInfo


def parse_pull_request_event(payload: dict[str, Any]) -> PullRequestInfo:
    repo_payload = payload["repository"]
    pr_payload = payload["pull_request"]

    repository = RepositoryInfo(
        owner=repo_payload["owner"]["login"],
        name=repo_payload["name"],
        full_name=repo_payload["full_name"],
        default_branch=repo_payload["default_branch"],
        clone_url=repo_payload["clone_url"],
    )

    return PullRequestInfo(
        number=pr_payload["number"],
        title=pr_payload["title"],
        body=pr_payload.get("body"),
        author=pr_payload["user"]["login"],
        head_sha=pr_payload["head"]["sha"],
        head_ref=pr_payload["head"]["ref"],
        base_ref=pr_payload["base"]["ref"],
        repository=repository,
    )
