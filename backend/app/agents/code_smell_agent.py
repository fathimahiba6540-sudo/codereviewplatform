"""
code_smell_agent.py — Phase 5.4
Code Smell Detection Agent for structural smells, magic numbers, long functions,
duplicate patterns, and naming violations.
"""

import logging
import re
from typing import List, Dict, Any

from backend.app.agents.base import BaseAgent
from backend.app.agents.state import AgentState, CodeFinding

logger = logging.getLogger(__name__)


class CodeSmellAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Code Smell Agent",
            role="Detects code smells including magic numbers, long methods, high cyclomatic complexity, and naming violations."
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
You are an expert Refactoring and Code Smell Specialist.
Analyze the following code files for structural code smells:
1. Long methods / functions (> 40 lines)
2. Magic numbers / un-named constants in logic checks
3. Deeply nested control flows (> 3 indentation levels)
4. Non-descriptive or bad variable names (e.g., single letter names outside loop indices)
5. Dead code / commented-out code blocks

Languages: {', '.join(languages)}

Files:
{files_snippet}

Respond ONLY with a valid JSON array of finding objects:
[
  {{
    "title": "Short smell title",
    "file_path": "path/to/file",
    "line_number": 20,
    "severity": "LOW",
    "category": "CODE_SMELL",
    "description": "Explanation of structural smell",
    "suggestion": "Refactoring approach"
  }}
]
Valid severities: MEDIUM, LOW, INFO.
"""

    def _normalize_findings(self, raw_list: List[Dict[str, Any]]) -> List[CodeFinding]:
        findings = []
        for item in raw_list:
            findings.append(CodeFinding(
                title=str(item.get("title", "Code Smell Detected")),
                file_path=str(item.get("file_path", "unknown")),
                line_number=item.get("line_number"),
                severity=str(item.get("severity", "MEDIUM")).upper(),
                category="CODE_SMELL",
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

            # Track indentation depth and magic numbers
            for idx, line in enumerate(lines, start=1):
                indent_level = (len(line) - len(line.lstrip())) // 4
                if indent_level >= 4 and not line.strip().startswith("//") and not line.strip().startswith("#"):
                    findings.append(CodeFinding(
                        title="Deeply Nested Control Flow",
                        file_path=file_path,
                        line_number=idx,
                        severity="MEDIUM",
                        category="CODE_SMELL",
                        description=f"Code nesting level reaches {indent_level} indentation levels, increasing cyclomatic complexity.",
                        suggestion="Extract nested blocks into helper methods or use guard clauses."
                    ))

                # Magic numbers in comparison logic (e.g. if x > 86400)
                if re.search(r"if\s+.*[><==]=?\s*\b(86400|3600|1000|60|999|1234)\b", line):
                    findings.append(CodeFinding(
                        title="Magic Number Constant",
                        file_path=file_path,
                        line_number=idx,
                        severity="LOW",
                        category="CODE_SMELL",
                        description="Hardcoded literal number used in condition without explanatory constant name.",
                        suggestion="Define named constant (e.g., SECONDS_IN_DAY = 86400) to improve context."
                    ))

                # Commented-out code blocks
                if re.match(r"^\s*(//|#)\s*(def |class |function |import |from |var |let |const |if |for |while )", line):
                    findings.append(CodeFinding(
                        title="Commented-Out Dead Code",
                        file_path=file_path,
                        line_number=idx,
                        severity="INFO",
                        category="CODE_SMELL",
                        description="Found commented-out executable code block.",
                        suggestion="Remove dead code; rely on git history for code retention."
                    ))

        return findings
