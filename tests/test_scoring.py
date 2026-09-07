"""
test_scoring.py — Unit tests for Phase 6 Scoring Engine and Report Schemas.
"""

import pytest
from datetime import datetime

from backend.app.services.scoring_service import (
    ScoringEngine,
    clamp_score,
    determine_grade,
    determine_quality_threshold,
)
from backend.app.models.report_schema import ReviewReportSchema


def test_score_clamping():
    assert clamp_score(150.0) == 100.0
    assert clamp_score(-20.0) == 0.0
    assert clamp_score(87.456) == 87.5


def test_grade_determination():
    assert determine_grade(98.0) == "A+"
    assert determine_grade(90.0) == "A"
    assert determine_grade(82.0) == "B"
    assert determine_grade(72.0) == "C"
    assert determine_grade(60.0) == "D"
    assert determine_grade(30.0) == "F"


def test_quality_threshold_classification():
    assert determine_quality_threshold(90.0) == "HIGH_QUALITY"
    assert determine_quality_threshold(70.0) == "MEDIUM_QUALITY"
    assert determine_quality_threshold(50.0) == "LOW_QUALITY"


def test_scoring_engine_calculation():
    code_review = [{"severity": "LOW"}]
    bugs = [{"severity": "HIGH"}]
    smells = [{"severity": "MEDIUM"}, {"severity": "LOW"}]
    security = [{"severity": "HIGH"}, {"severity": "MEDIUM"}]

    scores = ScoringEngine.calculate_scores(
        code_review_findings=code_review,
        bug_findings=bugs,
        code_smell_findings=smells,
        security_findings=security,
    )

    assert 0.0 <= scores.overall_score <= 100.0
    assert scores.security_score == 65.0  # 100 - (25 + 10)
    assert scores.quality_threshold in ["HIGH_QUALITY", "MEDIUM_QUALITY", "LOW_QUALITY"]


def test_versioned_report_schema_building():
    scores = ScoringEngine.calculate_scores([], [], [], [])

    report = ScoringEngine.build_versioned_report(
        review_id="rev-123",
        project_id="proj-456",
        scores=scores,
        summary_text="Clean code test report.",
        findings_payload={
            "code_review": [],
            "bugs": [],
            "code_smells": [],
            "security": [
                {
                    "title": "Unencrypted Traffic",
                    "file_path": "config.py",
                    "line_number": 5,
                    "severity": "MEDIUM",
                    "category": "SECURITY",
                    "description": "HTTP used instead of HTTPS",
                    "suggestion": "Enforce SSL/TLS",
                }
            ]
        },
        documentation_payload={
            "title": "Test Project",
            "overview": "Overview text",
            "readme_markdown": "# README",
            "installation": "pip install",
            "usage": "python main.py"
        },
        test_cases_payload=[
            {
                "target_file": "main.py",
                "test_type": "UNIT",
                "test_name": "test_main",
                "code": "def test_main(): assert True",
                "description": "Basic main test"
            }
        ],
        created_at=datetime.utcnow(),
    )

    assert report.schema_version == "1.0.0"
    assert report.review_id == "rev-123"
    assert report.security_report.total_vulnerabilities == 1
    assert report.tests_report.total_tests_generated == 1
    assert report.scores.overall_score == 100.0
