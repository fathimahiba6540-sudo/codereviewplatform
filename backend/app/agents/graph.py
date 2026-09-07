"""
graph.py — Phase 5.1 & 5.8
LangGraph StateGraph Multi-Agent Orchestration Pipeline.
Coordinates 7 specialized AI agents to execute full-stack code reviews.
"""

import logging
from typing import Dict, Any

from langgraph.graph import StateGraph, END

from backend.app.agents.state import AgentState
from backend.app.agents.code_review_agent import CodeReviewAgent
from backend.app.agents.bug_finder_agent import BugFinderAgent
from backend.app.agents.code_smell_agent import CodeSmellAgent
from backend.app.agents.security_agent import SecurityAgent
from backend.app.agents.documentation_agent import DocumentationAgent
from backend.app.agents.test_generator_agent import TestGeneratorAgent
from backend.app.agents.summary_agent import SummaryAgent

logger = logging.getLogger(__name__)

# Initialize agent instances
code_review_agent = CodeReviewAgent()
bug_finder_agent = BugFinderAgent()
code_smell_agent = CodeSmellAgent()
security_agent = SecurityAgent()
documentation_agent = DocumentationAgent()
test_generator_agent = TestGeneratorAgent()
summary_agent = SummaryAgent()


def code_review_node(state: AgentState) -> Dict[str, Any]:
    logger.info(f"Running CodeReviewNode for project '{state.get('project_id')}'")
    findings = code_review_agent.analyze(state)
    return {"code_review_findings": findings}


def bug_finder_node(state: AgentState) -> Dict[str, Any]:
    logger.info(f"Running BugFinderNode for project '{state.get('project_id')}'")
    findings = bug_finder_agent.analyze(state)
    return {"bug_findings": findings}


def code_smell_node(state: AgentState) -> Dict[str, Any]:
    logger.info(f"Running CodeSmellNode for project '{state.get('project_id')}'")
    findings = code_smell_agent.analyze(state)
    return {"code_smell_findings": findings}


def security_node(state: AgentState) -> Dict[str, Any]:
    logger.info(f"Running SecurityNode for project '{state.get('project_id')}'")
    findings = security_agent.analyze(state)
    return {"security_findings": findings}


def documentation_node(state: AgentState) -> Dict[str, Any]:
    logger.info(f"Running DocumentationNode for project '{state.get('project_id')}'")
    docs = documentation_agent.analyze(state)
    return {"documentation_output": docs}


def test_generator_node(state: AgentState) -> Dict[str, Any]:
    logger.info(f"Running TestGeneratorNode for project '{state.get('project_id')}'")
    tests = test_generator_agent.analyze(state)
    return {"test_cases": tests}


def summary_scoring_node(state: AgentState) -> Dict[str, Any]:
    logger.info(f"Running SummaryScoringNode for project '{state.get('project_id')}'")
    scores, summary_text = summary_agent.aggregate(state)
    return {"scores": scores, "summary": summary_text}


def build_review_graph() -> StateGraph:
    """Build and compile the LangGraph workflow graph for multi-agent code analysis."""
    workflow = StateGraph(AgentState)

    # Add agent execution nodes
    workflow.add_node("code_review", code_review_node)
    workflow.add_node("bug_finder", bug_finder_node)
    workflow.add_node("code_smell", code_smell_node)
    workflow.add_node("security", security_node)
    workflow.add_node("documentation", documentation_node)
    workflow.add_node("test_generator", test_generator_node)
    workflow.add_node("summary_scoring", summary_scoring_node)

    # Connect workflow edges (Parallel execution -> Aggregator node -> END)
    workflow.set_entry_point("code_review")
    workflow.add_edge("code_review", "bug_finder")
    workflow.add_edge("bug_finder", "code_smell")
    workflow.add_edge("code_smell", "security")
    workflow.add_edge("security", "documentation")
    workflow.add_edge("documentation", "test_generator")
    workflow.add_edge("test_generator", "summary_scoring")
    workflow.add_edge("summary_scoring", END)

    return workflow.compile()


# Compiled LangGraph pipeline singleton
review_pipeline_graph = build_review_graph()
