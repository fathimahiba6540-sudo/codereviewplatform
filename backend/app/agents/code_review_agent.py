"""
code_review_agent.py — Phase 5.2
Code Review Agent for general code quality, maintainability, readability,
variable naming, unused imports, duplication, and function sizing across languages.
"""

import logging
import re
from typing import List, Dict, Any

from backend.app.agents.base import BaseAgent
from backend.app.agents.state import AgentState, CodeFinding

logger = logging.getLogger(__name__)


class CodeReviewAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Code Review Agent",
            role="Evaluates overall code maintainability, readability, naming conventions, and modularity."
        )

    def analyze(self, state: AgentState) -> List[CodeFinding]:
        files_context = state.get("files_context", [])
        if not files_context:
            return []

        # Attempt LLM-based analysis
        prompt = self._build_prompt(files_context, state.get("detected_languages", []))
        raw_output = self.invoke_llm(prompt)
        if raw_output:
            parsed = self.parse_json_safely(raw_output, fallback=[])
            if isinstance(parsed, list):
                return self._normalize_findings(parsed)

        # Fallback heuristic static analysis
        return self._heuristic_analysis(files_context)

    def _build_prompt(self, files: List[Dict[str, Any]], languages: List[str]) -> str:
        files_snippet = ""
        for f in files[:8]:  # analyze up to 8 files for prompt size limit
            files_snippet += f"\n--- File: {f.get('file_path')} ({f.get('language')}) ---\n{f.get('content', '')[:1200]}\n"

        return f"""
You are an expert Senior Code Reviewer. Analyze the following project code files for general code quality, maintainability, readability, variable naming, and function complexity.

Project Languages: {', '.join(languages)}

Source Files:
{files_snippet}

Respond ONLY with a valid JSON array of finding objects with the following format:
[
  {{
    "title": "Short descriptive title",
    "file_path": "path/to/file",
    "line_number": 15,
    "severity": "MEDIUM",
    "category": "QUALITY",
    "description": "Explanation of code quality issue",
    "suggestion": "How to improve or refactor"
  }}
]
Valid severities: HIGH, MEDIUM, LOW, INFO.
"""

    def _normalize_findings(self, raw_list: List[Dict[str, Any]]) -> List[CodeFinding]:
        findings = []
        for item in raw_list:
            findings.append(CodeFinding(
                title=str(item.get("title", "Code Quality Suggestion")),
                file_path=str(item.get("file_path", "unknown")),
                line_number=item.get("line_number"),
                severity=str(item.get("severity", "MEDIUM")).upper(),
                category="QUALITY",
                description=str(item.get("description", "")),
                suggestion=str(item.get("suggestion", "")),
            ))
        return findings

    def _heuristic_analysis(self, files: List[Dict[str, Any]]) -> List[CodeFinding]:
        findings: List[CodeFinding] = []

        for f in files:
            file_path = f.get("file_path", "")
            content = f.get("content", "")
            lines = content.splitlines()

            # Check line length
            for idx, line in enumerate(lines, start=1):
                if len(line) > 120 and not line.strip().startswith("//") and not line.strip().startswith("#"):
                    findings.append(CodeFinding(
                        title="Excessive Line Length",
                        file_path=file_path,
                        line_number=idx,
                        severity="LOW",
                        category="QUALITY",
                        description=f"Line {idx} exceeds 120 characters ({len(line)} chars).",
                        suggestion="Break line across multiple lines for better readability."
                    ))

            # Check for TODOs / FIXMEs left in code
            for idx, line in enumerate(lines, start=1):
                if re.search(r"\b(TODO|FIXME|HACK|XXX)\b", line, re.IGNORECASE):
                    findings.append(CodeFinding(
                        title="Pending TODO / Refactor Comment",
                        file_path=file_path,
                        line_number=idx,
                        severity="INFO",
                        category="QUALITY",
                        description=f"Found temporary note: '{line.strip()}'",
                        suggestion="Address unresolved TODO before production deployment."
                    ))

            # Check for large file
            if len(lines) > 300:
                findings.append(CodeFinding(
                    title="Large Module / Source File",
                    file_path=file_path,
                    line_number=1,
                    severity="MEDIUM",
                    category="QUALITY",
                    description=f"File contains {len(lines)} lines of code, exceeding single-responsibility recommendations.",
                    suggestion="Consider splitting this file into smaller, focused modules."
                ))

        return findings
