"""
test_agents.py — Unit tests for Phase 5 AI agents.
"""

import pytest

from backend.app.agents.state import AgentState
from backend.app.agents.code_review_agent import CodeReviewAgent
from backend.app.agents.bug_finder_agent import BugFinderAgent
from backend.app.agents.code_smell_agent import CodeSmellAgent
from backend.app.agents.security_agent import SecurityAgent
from backend.app.agents.documentation_agent import DocumentationAgent
from backend.app.agents.test_generator_agent import TestGeneratorAgent
from backend.app.agents.summary_agent import SummaryAgent, calculate_grade


@pytest.fixture
def sample_state() -> AgentState:
    return {
        "project_id": "test-proj-123",
        "project_title": "Sample E-Commerce API",
        "framework": "FastAPI",
        "total_files": 2,
        "total_lines_of_code": 150,
        "detected_languages": ["Python"],
        "files_context": [
            {
                "file_id": "f1",
                "file_path": "app/main.py",
                "filename": "main.py",
                "language": "python",
                "line_count": 80,
                "content": """import os
api_key = "AWS_SECRET_KEY=1234567890abcdef1234567890abcdef"

def execute_query(user_input):
    query = "SELECT * FROM users WHERE username = '" + user_input + "'"
    return query

def divide_val(a, b):
    try:
        val = a / 0
    except:
        pass
    return val
"""
            }
        ]
    }


def test_code_review_agent(sample_state):
    agent = CodeReviewAgent()
    findings = agent.analyze(sample_state)
    assert isinstance(findings, list)


def test_bug_finder_agent(sample_state):
    agent = BugFinderAgent()
    findings = agent.analyze(sample_state)
    assert len(findings) > 0
    assert any(f["title"] == "Swallowed Exception / Bare Except" for f in findings)


def test_code_smell_agent(sample_state):
    agent = CodeSmellAgent()
    findings = agent.analyze(sample_state)
    assert isinstance(findings, list)


def test_security_agent(sample_state):
    agent = SecurityAgent()
    findings = agent.analyze(sample_state)
    assert len(findings) > 0
    assert any("SQL Injection" in f["title"] or "Secret" in f["title"] for f in findings)


def test_documentation_agent(sample_state):
    agent = DocumentationAgent()
    docs = agent.analyze(sample_state)
    assert "readme_markdown" in docs
    assert docs["title"] == "Sample E-Commerce API"


def test_test_generator_agent(sample_state):
    agent = TestGeneratorAgent()
    tests = agent.analyze(sample_state)
    assert len(tests) > 0
    assert tests[0]["target_file"] == "app/main.py"


def test_summary_agent_scoring(sample_state):
    bug_agent = BugFinderAgent()
    sec_agent = SecurityAgent()
    sample_state["bug_findings"] = bug_agent.analyze(sample_state)
    sample_state["security_findings"] = sec_agent.analyze(sample_state)

    summary_agent = SummaryAgent()
    scores, summary_text = summary_agent.aggregate(sample_state)

    assert "overall_score" in scores
    assert "grade" in scores
    assert isinstance(summary_text, str)
    assert len(summary_text) > 0


def test_calculate_grade():
    assert calculate_grade(98.0) == "A+"
    assert calculate_grade(90.0) == "A"
    assert calculate_grade(80.0) == "B"
    assert calculate_grade(70.0) == "C"
    assert calculate_grade(60.0) == "D"
    assert calculate_grade(40.0) == "F"
