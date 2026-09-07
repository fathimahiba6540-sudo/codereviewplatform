"""
bug_finder_agent.py — Phase 5.3
Bug Finder Agent for detecting runtime risk, null pointers, unhandled exceptions,
infinite loops, division by zero, and logical errors.
"""

import logging
import re
from typing import List, Dict, Any

from backend.app.agents.base import BaseAgent
from backend.app.agents.state import AgentState, CodeFinding

logger = logging.getLogger(__name__)


class BugFinderAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Bug Finder Agent",
            role="Detects runtime errors, null pointer risks, unhandled exceptions, infinite loops, and division by zero."
        )

    def analyze(self, state: AgentState) -> List[CodeFinding]:
        files_context = state.get("files_context", [])
        if not files_context:
            return []

        prompt = self._build_prompt(files_context, state.get("detected_languages", []))
        raw_output = self.invoke_llm(prompt)
        if raw_output:
            parsed = self.parse_json_safely(raw_output, fallback=[])
            if isinstance(parsed, list):
                return self._normalize_findings(parsed)

        return self._heuristic_analysis(files_context)

    def _build_prompt(self, files: List[Dict[str, Any]], languages: List[str]) -> str:
        files_snippet = ""
        for f in files[:8]:
            files_snippet += f"\n--- File: {f.get('file_path')} ({f.get('language')}) ---\n{f.get('content', '')[:1200]}\n"

        return f"""
You are an expert Static Application Bug & Runtime Risk Analyzer.
Examine the following code for software bugs, including:
1. Null pointer / None dereference risks
2. Division by zero risks
3. Infinite loops or missing exit conditions
4. Bare exception handlers / ignored errors (e.g. except: pass or catch (Exception e) {{}})
5. Unreachable or dead code
6. Incorrect boolean conditions or off-by-one errors

Languages: {', '.join(languages)}

Files:
{files_snippet}

Respond ONLY with a valid JSON array of finding objects:
[
  {{
    "title": "Short bug title",
    "file_path": "path/to/file",
    "line_number": 42,
    "severity": "HIGH",
    "category": "BUG",
    "description": "Explanation of potential runtime failure",
    "suggestion": "Corrective code change"
  }}
]
Valid severities: HIGH, MEDIUM, LOW.
"""

    def _normalize_findings(self, raw_list: List[Dict[str, Any]]) -> List[CodeFinding]:
        findings = []
        for item in raw_list:
            findings.append(CodeFinding(
                title=str(item.get("title", "Runtime Bug Risk")),
                file_path=str(item.get("file_path", "unknown")),
                line_number=item.get("line_number"),
                severity=str(item.get("severity", "HIGH")).upper(),
                category="BUG",
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

            for idx, line in enumerate(lines, start=1):
                stripped = line.strip()

                # Bare except block (Python)
                if re.search(r"except\s*:\s*(pass|\.\.\.)?", stripped) or re.search(r"except\s+Exception\s*:\s*pass", stripped):
                    findings.append(CodeFinding(
                        title="Swallowed Exception / Bare Except",
                        file_path=file_path,
                        line_number=idx,
                        severity="HIGH",
                        category="BUG",
                        description="Bare exception handling catches and suppresses all errors, obscuring underlying failures.",
                        suggestion="Catch specific exception types and log or re-raise errors."
                    ))

                # Empty catch block (Java/JS/C++)
                if re.search(r"catch\s*\([^)]*\)\s*\{\s*\}", stripped):
                    findings.append(CodeFinding(
                        title="Empty Catch Block",
                        file_path=file_path,
                        line_number=idx,
                        severity="HIGH",
                        category="BUG",
                        description="Empty catch block silently ignores errors without logging or fallback.",
                        suggestion="Log exception details or handle failure gracefully."
                    ))

                # Potential Division by Zero
                if "/" in stripped and re.search(r"/\s*0(?![0-9\.\w])", stripped):
                    findings.append(CodeFinding(
                        title="Division by Zero Risk",
                        file_path=file_path,
                        line_number=idx,
                        severity="HIGH",
                        category="BUG",
                        description="Direct division by zero expression detected.",
                        suggestion="Add a check ensuring divisor is non-zero before executing division."
                    ))

                # Potential infinite while loop
                if re.search(r"while\s*\(\s*true\s*\)", stripped) or re.search(r"while\s+True\s*:", stripped):
                    if idx + 5 <= len(lines):
                        block = "\n".join(lines[idx-1:idx+5])
                        if "break" not in block and "return" not in block:
                            findings.append(CodeFinding(
                                title="Potential Infinite Loop",
                                file_path=file_path,
                                line_number=idx,
                                severity="HIGH",
                                category="BUG",
                                description="While loop with true condition lacks visible break or return statement in immediate body.",
                                suggestion="Ensure clear loop termination condition is guaranteed."
                            ))

        return findings
