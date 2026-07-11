from pydantic import BaseModel

from app.models.repository_info import RepositoryInfo


class PullRequestInfo(BaseModel):
    number: int
    title: str
    body: str | None = None
    author: str
    head_sha: str
    head_ref: str
    base_ref: str
    repository: RepositoryInfo
    changed_files: list[str] = []
