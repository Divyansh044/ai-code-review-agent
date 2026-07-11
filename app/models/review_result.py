from pydantic import BaseModel

from app.models.analysis_result import Severity


class ReviewComment(BaseModel):
    file: str
    line: int
    severity: Severity
    title: str
    explanation: str
    suggestion: str | None = None


class ReviewResult(BaseModel):
    summary: str
    comments: list[ReviewComment] = []
    overall_recommendation: str
