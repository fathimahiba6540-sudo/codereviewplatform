"""
report_schema.py — Phase 6.2
Pydantic schemas for versioned code review reports, security findings,
documentation outputs, test cases, and quality score breakdowns.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class FindingItemSchema(BaseModel):
    title: str
    file_path: str
    line_number: Optional[int] = None
    severity: str = Field(..., description="HIGH, MEDIUM, LOW, INFO")
    category: str = Field(..., description="SECURITY, BUG, CODE_SMELL, QUALITY")
    description: str
    suggestion: str


class ScoreBreakdownSchema(BaseModel):
    maintainability_score: float = Field(..., ge=0.0, le=100.0)
    security_score: float = Field(..., ge=0.0, le=100.0)
    performance_score: float = Field(..., ge=0.0, le=100.0)
    readability_score: float = Field(..., ge=0.0, le=100.0)
    overall_score: float = Field(..., ge=0.0, le=100.0)
    grade: str = Field(..., example="A")
    quality_threshold: str = Field(..., example="HIGH_QUALITY")  # HIGH_QUALITY, MEDIUM_QUALITY, LOW_QUALITY


class SecurityReportSchema(BaseModel):
    total_vulnerabilities: int
    critical_high_count: int
    findings: List[FindingItemSchema] = []


class DocumentationReportSchema(BaseModel):
    title: str
    overview: str
    readme_markdown: str
    installation: str
    usage: str
    project_structure: Optional[str] = None


class TestCaseItemSchema(BaseModel):
    target_file: str
    test_type: str = Field(..., description="UNIT, INTEGRATION, EDGE_CASE")
    test_name: str
    code: str
    description: str


class TestsReportSchema(BaseModel):
    total_tests_generated: int
    test_cases: List[TestCaseItemSchema] = []


class ReviewReportSchema(BaseModel):
    """
    Versioned master JSON schema envelope for complete AI code review reports.
    """
    schema_version: str = "1.0.0"
    review_id: str
    project_id: str
    created_at: datetime
    scores: ScoreBreakdownSchema
    summary: str
    findings: Dict[str, List[FindingItemSchema]]
    security_report: SecurityReportSchema
    documentation: DocumentationReportSchema
    tests_report: TestsReportSchema
