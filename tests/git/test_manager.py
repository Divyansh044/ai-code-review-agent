import tempfile
from pathlib import Path

import git
import pytest

from app.git.manager import RepositoryManager
from app.models import PullRequestInfo, RepositoryInfo


def make_fake_github_repo(tmp_path: Path, pr_number: int, file_name: str, file_content: str) -> Path:
    origin_path = tmp_path / "fake-origin"
    repo = git.Repo.init(origin_path, initial_branch="main")

    (origin_path / file_name).write_text(file_content)
    repo.index.add([file_name])
    commit = repo.index.commit("Initial commit")

    repo.git.update_ref(f"refs/pull/{pr_number}/head", commit.hexsha)
    return origin_path


def make_pull_request(clone_url: Path, number: int) -> PullRequestInfo:
    return PullRequestInfo(
        number=number,
        title="Test PR",
        author="octocat",
        head_sha="deadbeef",
        head_ref="feature/x",
        base_ref="main",
        repository=RepositoryInfo(
            owner="octo-org",
            name="widgets",
            full_name="octo-org/widgets",
            default_branch="main",
            clone_url=str(clone_url),
        ),
    )


def test_checkout_pull_request_yields_workspace_with_pr_content(tmp_path: Path) -> None:
    origin = make_fake_github_repo(tmp_path, pr_number=7, file_name="app.py", file_content="print('hi')")
    pull_request = make_pull_request(origin, number=7)

    manager = RepositoryManager(github_token="test-token")

    with manager.checkout_pull_request(pull_request) as workspace:
        assert workspace.exists()
        assert (workspace / "app.py").read_text() == "print('hi')"

    assert not workspace.exists()


def test_checkout_cleans_up_workspace_even_when_fetch_fails(tmp_path: Path) -> None:
    origin = make_fake_github_repo(tmp_path, pr_number=7, file_name="app.py", file_content="print('hi')")
    # Ask for a PR number with no matching refs/pull/<n>/head ref.
    pull_request = make_pull_request(origin, number=999)

    manager = RepositoryManager(github_token="test-token")

    tmp_root = Path(tempfile.gettempdir())
    leftover_before = set(tmp_root.glob("ai-code-review-*"))

    workspace_path = None
    with pytest.raises(git.exc.GitCommandError):
        with manager.checkout_pull_request(pull_request) as workspace:
            workspace_path = workspace

    assert workspace_path is None or not workspace_path.exists()

    leftover_after = set(tmp_root.glob("ai-code-review-*"))
    assert leftover_after == leftover_before
