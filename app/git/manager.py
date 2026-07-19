import shutil
import stat
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import git

from app.models import PullRequestInfo


def _force_remove_readonly(func: Any, path: str, exc: BaseException) -> None:
    Path(path).chmod(stat.S_IWRITE)
    func(path)


class RepositoryManager:
    def __init__(self, github_token: str) -> None:
        self._github_token = github_token

    @contextmanager
    def checkout_pull_request(self, pull_request: PullRequestInfo) -> Iterator[Path]:
        workdir = Path(tempfile.mkdtemp(prefix="ai-code-review-"))
        try:
            repo = git.Repo.init(workdir)
            origin = repo.create_remote("origin", pull_request.repository.clone_url)

            with repo.config_writer() as config:
                config.set_value("http", "extraheader", f"AUTHORIZATION: bearer {self._github_token}")

            origin.fetch(refspec=f"refs/pull/{pull_request.number}/head", depth=1)
            repo.git.checkout("FETCH_HEAD")

            yield workdir
        finally:
            shutil.rmtree(workdir, onexc=_force_remove_readonly)
