# AI Code Review Agent

An automated pull-request review system that analyzes Python code changes on GitHub and
posts structured, actionable feedback directly on the PR.

When a PR is opened or updated, a GitHub webhook hits this app's FastAPI server. The
app fetches the PR diff via the GitHub API, checks out the PR branch locally, runs
[Ruff](https://docs.astral.sh/ruff/) for code-quality/formatting issues and
[Semgrep](https://semgrep.dev/) for insecure or risky patterns, then hands the diff and
findings to an LLM that acts as a senior reviewer — filtering noise, assigning severity,
and explaining issues in plain language. The resulting review is posted back to the PR
through the GitHub API.

Stack: FastAPI, Pydantic, GitPython, Ruff, Semgrep, the OpenAI API, Docker, AWS EC2.

## Status

Under active, incremental development. Currently implemented:

- Core Pydantic data models (`app/models/`): `RepositoryInfo`, `PullRequestInfo`,
  `AnalysisResult`/`Finding`, `ReviewContext`, `ReviewResult`/`ReviewComment`.
- Typed settings loaded from `.env` (`app/core/config.py`).
- A minimal FastAPI app with a `/health` endpoint (`app/main.py`).

Not yet built: webhook ingestion, the GitHub API client, repository checkout, the
Ruff/Semgrep runners, LLM review generation, orchestration, deployment, and the
evaluation framework.

## Local development

```bash
uv sync
cp .env.example .env  # fill in GITHUB_TOKEN, GITHUB_WEBHOOK_SECRET, OPENAI_API_KEY
uv run uvicorn app.main:app --reload
```

Then check `GET http://127.0.0.1:8000/health`.

Run tests with:

```bash
uv run pytest
```
