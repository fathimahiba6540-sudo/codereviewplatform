"""
summary_agent.py — Phase 5.8
Summary & Scoring Aggregator Agent consolidating all agent findings into
sub-metric quality scores, letter grade, and executive dashboard summary.
"""

import logging
from typing import Dict, Any, List, Tuple

from backend.app.agents.base import BaseAgent
from backend.app.agents.state import AgentState, AgentScores, CodeFinding

logger = logging.getLogger(__name__)


def calculate_grade(overall_score: float) -> str:
    """Convert numerical score (0-100) to letter grade."""
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


class SummaryAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Summary Agent",
            role="Consolidates findings from all agents, calculates sub-scores, grade, and executive summary."
        )

    def aggregate(self, state: AgentState) -> Tuple[AgentScores, str]:
        code_review = state.get("code_review_findings", [])
        bugs = state.get("bug_findings", [])
        smells = state.get("code_smell_findings", [])
        security = state.get("security_findings", [])

        all_findings = code_review + bugs + smells + security

        # Compute component scores starting from 100
        maintainability = max(0.0, 100.0 - (len(code_review) * 4.0 + len(smells) * 3.0))
        security_score = max(0.0, 100.0 - (len([s for s in security if s.get('severity') == 'HIGH']) * 20.0 + len(security) * 8.0))
        performance = max(0.0, 100.0 - (len([b for b in bugs if b.get('severity') == 'HIGH']) * 15.0 + len(bugs) * 5.0))
        readability = max(0.0, 100.0 - (len(smells) * 5.0 + len(code_review) * 2.0))

        overall_score = round(
            (maintainability * 0.30) +
            (security_score * 0.35) +
            (performance * 0.20) +
            (readability * 0.15),
            1
        )
        grade = calculate_grade(overall_score)

        scores: AgentScores = {
            "maintainability_score": round(maintainability, 1),
            "security_score": round(security_score, 1),
            "performance_score": round(performance, 1),
            "readability_score": round(readability, 1),
            "overall_score": overall_score,
            "grade": grade,
        }

        # Attempt LLM executive summary synthesis
        prompt = self._build_prompt(state, scores, all_findings)
        raw_summary = self.invoke_llm(prompt)
        if raw_summary and len(raw_summary.strip()) > 30:
            summary_text = raw_summary.strip()
        else:
            summary_text = self._heuristic_summary(state, scores, all_findings)

        return scores, summary_text

    def _build_prompt(self, state: AgentState, scores: AgentScores, findings: List[CodeFinding]) -> str:
        high_severity = [f for f in findings if f.get("severity") == "HIGH"]
        return f"""
You are the Chief Technology Officer and Lead Code Auditor.
Synthesize an executive code review summary for project "{state.get('project_title')}".

Project Statistics:
- Total Files: {state.get('total_files', 0)}
- Lines of Code: {state.get('total_lines_of_code', 0)}
- Framework: {state.get('framework', 'Generic')}
- Overall Grade: {scores.get('grade')} (Score: {scores.get('overall_score')}/100)

Sub-scores:
- Security: {scores.get('security_score')}/100
- Maintainability: {scores.get('maintainability_score')}/100
- Performance: {scores.get('performance_score')}/100
- Readability: {scores.get('readability_score')}/100

Total Findings: {len(findings)} ({len(high_severity)} Critical/High)

Provide a 2-3 paragraph professional executive summary highlighting key strengths, critical security or bug risks, and high-priority refactoring recommendations.
"""

    def _heuristic_summary(self, state: AgentState, scores: AgentScores, findings: List[CodeFinding]) -> str:
        high_count = len([f for f in findings if f.get("severity") == "HIGH"])
        title = state.get("project_title", "Project")
        grade = scores.get("grade", "C")
        overall = scores.get("overall_score", 70.0)

        return f"""Analysis completed for {title}. The codebase received an overall quality grade of {grade} ({overall}/100).
A total of {len(findings)} findings were identified across code review, runtime bug inspection, code smells, and security auditing, including {high_count} high-severity issues.

Security rating is {scores.get('security_score')}/100, while maintainability is rated at {scores.get('maintainability_score')}/100.
High-priority recommendations include resolving critical security findings, eliminating bare exception handlers, and refactoring large or deeply nested functions.
"""
