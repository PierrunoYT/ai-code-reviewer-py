from typing import List, Optional, TypedDict, Dict, Any
from ai_code_reviewer_py.enums import IssueSeverity, IssueCategory

class AIReviewIssue(TypedDict):
    severity: IssueSeverity
    description: str
    suggestion: str
    category: IssueCategory
    citation: Optional[str]
    auto_fixable: bool

class AIReviewResponse(TypedDict):
    score: int
    summary: str
    issues: List[AIReviewIssue]
    suggestions: List[str]
    security: List[str]
    performance: List[str]
    dependencies: List[str]
    accessibility: List[str]
    sources: Optional[List[str]]
    confidence: int

class CommitDetails(TypedDict):
    hash: str
    message: str
    author: str
    date: str

class FileDetails(TypedDict):
    path: str
    content: str

class RepositorySummaryResponse(TypedDict):
    overall_score: int
    executive_summary: str
    architecture_assessment: Dict[str, Any]
    security_assessment: Dict[str, Any]
    code_quality: Dict[str, Any]
    dependencies: Dict[str, Any]
    key_findings: List[str]
    immediate_actions: List[str]
    long_term_recommendations: List[str]
    sources: Optional[List[str]]
    confidence: int