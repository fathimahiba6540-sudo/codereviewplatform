"""
state.py — Phase 5.1
LangGraph state definitions for the AI multi-agent code review pipeline.
"""

from typing import List, Dict, Any, Optional, TypedDict


class CodeFinding(TypedDict, total=False):
    title: str
    file_path: str
    line_number: Optional[int]
    severity: str  # HIGH, MEDIUM, LOW, INFO
    category: str  # BUG, SECURITY, CODE_SMELL, QUALITY
    description: str
    suggestion: str


class DocumentSection(TypedDict, total=False):
    title: str
    content: str


class TestCase(TypedDict, total=False):
    target_file: str
    test_type: str  # UNIT, INTEGRATION, EDGE_CASE
    test_name: str
    code: str
    description: str


class AgentScores(TypedDict, total=False):
    maintainability_score: float
    security_score: float
    performance_score: float
    readability_score: float
    overall_score: float
    grade: str


class AgentState(TypedDict, total=False):
    """
    Shared memory/context schema passed across all nodes in the LangGraph pipeline.
    """
    project_id: str
    project_title: str
    framework: str
    total_files: int
    total_lines_of_code: int
    detected_languages: List[str]
    
    # Ingested context
    files_context: List[Dict[str, Any]]
    chunks_context: List[Dict[str, Any]]
    
    # Agent Outputs
    code_review_findings: List[CodeFinding]
    bug_findings: List[CodeFinding]
    code_smell_findings: List[CodeFinding]
    security_findings: List[CodeFinding]
    documentation_output: Dict[str, Any]
    test_cases: List[TestCase]
    
    # Aggregated Results & Summary
    summary: str
    scores: AgentScores
    errors: List[str]
