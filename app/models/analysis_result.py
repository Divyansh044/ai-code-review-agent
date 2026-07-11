from enum import StrEnum

from pydantic import BaseModel


class Severity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Finding(BaseModel):
    tool: str
    rule_id: str
    file: str
    line: int
    message: str
    severity: Severity


class AnalysisResult(BaseModel):
    tool: str
    success: bool
    findings: list[Finding] = []
    error: str | None = None
