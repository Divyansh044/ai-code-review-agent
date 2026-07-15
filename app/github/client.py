from typing import Any, Self

import httpx

from app.models import RepositoryInfo, ReviewComment

GITHUB_API_BASE_URL = "https://api.github.com"


def _format_comment_body(comment: ReviewComment) -> str:
    parts = [f"**[{comment.severity.value.upper()}] {comment.title}**", "", comment.explanation]
    if comment.suggestion:
        parts += ["", f"**Suggestion:** {comment.suggestion}"]
    return "\n".join(parts)


class GitHubClient:
    def __init__(self, token: str, http_client: httpx.AsyncClient | None = None) -> None:
        self._client = http_client or httpx.AsyncClient(base_url=GITHUB_API_BASE_URL, timeout=30.0)
        self._client.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.aclose()

    async def get_pull_request_files(self, repository: RepositoryInfo, pr_number: int) -> list[str]:
        filenames: list[str] = []
        url: str | None = f"/repos/{repository.full_name}/pulls/{pr_number}/files"
        params: dict[str, Any] | None = {"per_page": 100}

        while url:
            response = await self._client.get(url, params=params)
            response.raise_for_status()
            filenames.extend(item["filename"] for item in response.json())

            next_link = response.links.get("next")
            url = next_link["url"] if next_link else None
            params = None

        return filenames

    async def get_pull_request_diff(self, repository: RepositoryInfo, pr_number: int) -> str:
        response = await self._client.get(
            f"/repos/{repository.full_name}/pulls/{pr_number}",
            headers={"Accept": "application/vnd.github.v3.diff"},
        )
        response.raise_for_status()
        return response.text

    async def create_review(
        self,
        repository: RepositoryInfo,
        pr_number: int,
        summary: str,
        comments: list[ReviewComment],
        event: str = "COMMENT",
    ) -> dict[str, Any]:
        body = {
            "body": summary,
            "event": event,
            "comments": [
                {
                    "path": comment.file,
                    "line": comment.line,
                    "side": "RIGHT",
                    "body": _format_comment_body(comment),
                }
                for comment in comments
            ],
        }
        response = await self._client.post(
            f"/repos/{repository.full_name}/pulls/{pr_number}/reviews", json=body
        )
        response.raise_for_status()
        return response.json()
