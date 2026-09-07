"""
test_review_pipeline.py — Integration tests for the LangGraph multi-agent pipeline graph.
"""

import pytest
from backend.app.agents.graph import review_pipeline_graph
from backend.app.agents.state import AgentState


def test_full_review_pipeline_graph_execution():
    initial_state: AgentState = {
        "project_id": "integration-test-proj-001",
        "project_title": "Test Microservice",
        "framework": "FastAPI",
        "total_files": 1,
        "total_lines_of_code": 25,
        "detected_languages": ["Python"],
        "files_context": [
            {
                "file_id": "file-1",
                "file_path": "server.py",
                "filename": "server.py",
                "language": "python",
                "line_count": 25,
                "content": """
def dangerous_function(input_val):
    # TODO: Refactor
    password = 'HARDCODED_SUPER_SECRET'
    eval(input_val)
"""
            }
        ]
    }

    final_state = review_pipeline_graph.invoke(initial_state)

    assert "code_review_findings" in final_state
    assert "bug_findings" in final_state
    assert "code_smell_findings" in final_state
    assert "security_findings" in final_state
    assert "documentation_output" in final_state
    assert "test_cases" in final_state
    assert "scores" in final_state
    assert "summary" in final_state

    scores = final_state["scores"]
    assert scores["overall_score"] >= 0.0
    assert scores["grade"] in ["A+", "A", "B", "C", "D", "F"]
