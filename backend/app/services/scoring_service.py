"""
scoring_service.py — Phase 6.1
Quality Scoring Engine calculating maintainability, security, performance,
readability, overall composite grade, quality thresholds, and report schemas.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Tuple

from backend.app.models.report_schema import (
    ScoreBreakdownSchema,
    ReviewReportSchema,
    SecurityReportSchema,
    DocumentationReportSchema,
    TestsReportSchema,
    FindingItemSchema,
    TestCaseItemSchema,
)

logger = logging.getLogger(__name__)


def clamp_score(val: float) -> float:
    """Clamp score between 0.0 and 100.0 rounded to 1 decimal place."""
    return round(max(0.0, min(100.0, float(val))), 1)


def determine_quality_threshold(overall_score: float) -> str:
    """Evaluate quality threshold category for project grade."""
    if overall_score >= 85.0:
        return "HIGH_QUALITY"
    elif overall_score >= 65.0:
        return "MEDIUM_QUALITY"
    else:
        return "LOW_QUALITY"


def determine_grade(overall_score: float) -> str:
    """Map numerical score (0-100) to letter grade."""
    if overall_score >= 95.0:
        return "A+"
    elif overall_score >= 88.0:
        return "A"
    elif overall_score >= 78.0:
        return "B"
    elif overall_score >= 68.0:
        return "C"
    elif overall_score >= 55.0:
        return "D"
    else:
        return "F"


class ScoringEngine:
    """
    Core engine calculating multi-dimensional quality metrics, composite scores,
    and building versioned report schemas.
    """

    @staticmethod
    def calculate_scores(
        code_review_findings: List[Dict[str, Any]],
        bug_findings: List[Dict[str, Any]],
        code_smell_findings: List[Dict[str, Any]],
        security_findings: List[Dict[str, Any]],
    ) -> ScoreBreakdownSchema:
        """
        Calculate weighted component scores and overall composite score.

        Weights:
        - Security: 35%
        - Maintainability: 30%
        - Performance: 20%
        - Readability: 15%
        """
        # Security Score (Base 100)
        sec_high = len([f for f in security_findings if str(f.get("severity", "")).upper() in ["HIGH", "CRITICAL"]])
        sec_med = len([f for f in security_findings if str(f.get("severity", "")).upper() == "MEDIUM"])
        sec_low = len([f for f in security_findings if str(f.get("severity", "")).upper() in ["LOW", "INFO"]])
        security_penalty = (sec_high * 25.0) + (sec_med * 10.0) + (sec_low * 3.0)
        security_score = clamp_score(100.0 - security_penalty)

        # Maintainability Score (Base 100)
        maint_penalty = (len(code_review_findings) * 4.0) + (len(code_smell_findings) * 3.0)
        maintainability_score = clamp_score(100.0 - maint_penalty)

        # Performance Score (Base 100)
        bug_high = len([f for f in bug_findings if str(f.get("severity", "")).upper() in ["HIGH", "CRITICAL"]])
        bug_other = len(bug_findings) - bug_high
        perf_penalty = (bug_high * 15.0) + (bug_other * 5.0)
        performance_score = clamp_score(100.0 - perf_penalty)

        # Readability Score (Base 100)
        readability_penalty = (len(code_smell_findings) * 5.0) + (len(code_review_findings) * 2.0)
        readability_score = clamp_score(100.0 - readability_penalty)

        # Composite Overall Score
        overall = clamp_score(
            (security_score * 0.35) +
            (maintainability_score * 0.30) +
            (performance_score * 0.20) +
            (readability_score * 0.15)
        )

        grade = determine_grade(overall)
        threshold = determine_quality_threshold(overall)

        return ScoreBreakdownSchema(
            maintainability_score=maintainability_score,
            security_score=security_score,
            performance_score=performance_score,
            readability_score=readability_score,
            overall_score=overall,
            grade=grade,
            quality_threshold=threshold,
        )

    @staticmethod
    def build_versioned_report(
        review_id: str,
        project_id: str,
        scores: ScoreBreakdownSchema,
        summary_text: str,
        findings_payload: Dict[str, List[Dict[str, Any]]],
        documentation_payload: Dict[str, Any],
        test_cases_payload: List[Dict[str, Any]],
        created_at: Optional[datetime] = None,
    ) -> ReviewReportSchema:
        """Construct validated Pydantic ReviewReportSchema with version envelope."""
        sec_findings = findings_payload.get("security", [])
        sec_high = len([f for f in sec_findings if str(f.get("severity", "")).upper() in ["HIGH", "CRITICAL"]])

        sec_report = SecurityReportSchema(
            total_vulnerabilities=len(sec_findings),
            critical_high_count=sec_high,
            findings=[FindingItemSchema(**f) for f in sec_findings],
        )

        doc_report = DocumentationReportSchema(
            title=documentation_payload.get("title", "Project Documentation"),
            overview=documentation_payload.get("overview", "Project Overview"),
            readme_markdown=documentation_payload.get("readme_markdown", "# Project"),
            installation=documentation_payload.get("installation", "N/A"),
            usage=documentation_payload.get("usage", "N/A"),
            project_structure=documentation_payload.get("project_structure"),
        )

        test_items = [TestCaseItemSchema(**t) for t in test_cases_payload]
        tests_report = TestsReportSchema(
            total_tests_generated=len(test_items),
            test_cases=test_items,
        )

        formatted_findings = {
            k: [FindingItemSchema(**item) for item in v]
            for k, v in findings_payload.items()
        }

        return ReviewReportSchema(
            schema_version="1.0.0",
            review_id=review_id,
            project_id=project_id,
            created_at=created_at or datetime.utcnow(),
            scores=scores,
            summary=summary_text,
            findings=formatted_findings,
            security_report=sec_report,
            documentation=doc_report,
            tests_report=tests_report,
        )
