from pydantic import BaseModel

from app.models.analysis_result import AnalysisResult
from app.models.pull_request_info import PullRequestInfo


class ReviewContext(BaseModel):
    pull_request: PullRequestInfo
    diff: str
    analysis_results: list[AnalysisResult] = []
