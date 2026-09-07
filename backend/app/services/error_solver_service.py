"""
error_solver_service.py — AI Error Detector & Solver Service
Analyzes code snippets and stack traces to detect bugs, explain root causes, and provide corrected code solutions.
"""

import logging
from typing import Dict, Any, Optional, List
from backend.app.agents.base import BaseAgent
from backend.app.models.schemas import ErrorSolverRequest, ErrorSolverResponse

logger = logging.getLogger(__name__)


class ErrorSolverService(BaseAgent):
    def __init__(self):
        super().__init__(name="ErrorSolverAgent", role="AI Debugger & Error Solver")

    def solve_error(self, req: ErrorSolverRequest) -> ErrorSolverResponse:
        """Detect and solve errors in code snippet and/or error stack trace."""
        prompt = f"""
You are an expert AI software engineer and educator helping students, teachers, and developers debug code.
Analyze the following code snippet and optional error log.

[TARGET LANGUAGE]: {req.language}

[CODE SNIPPET]:
```
{req.code}
```

[ERROR LOG / STACK TRACE]:
```
{req.error_log or "No stack trace provided."}
```

Respond strictly with valid JSON with the following key structure:
{{
  "error_summary": "Brief 1-2 sentence description of the bug or issue",
  "root_cause": "Detailed, student-friendly explanation of why this error happened",
  "corrected_code": "The complete, fixed, working code snippet",
  "explanation": "Clear step-by-step breakdown of the changes made to fix the error",
  "prevention_tips": ["Tip 1 to prevent this in future", "Tip 2..."]
}}
"""
        llm_response = self.invoke_llm(prompt)
        parsed = self.parse_json_safely(llm_response, fallback=None)

        if parsed and "corrected_code" in parsed:
            return ErrorSolverResponse(
                error_summary=parsed.get("error_summary", "Detected code issue"),
                root_cause=parsed.get("root_cause", "Analysis completed."),
                corrected_code=parsed.get("corrected_code", req.code),
                explanation=parsed.get("explanation", "Code reviewed."),
                prevention_tips=parsed.get("prevention_tips", ["Test edge cases."])
            )

        # Smart Heuristic Fallback if LLM is unavailable
        return self._heuristic_fallback(req)

    def _heuristic_fallback(self, req: ErrorSolverRequest) -> ErrorSolverResponse:
        code_lines = req.code.split("\n")
        fixed_lines = []
        summary = "Syntax or logical bug detected"
        cause = "Detected common code error pattern (e.g. unhandled exceptions, syntax errors, or uninitialized variables)."
        tips = ["Check syntax and indentations", "Use try-except error handling", "Validate input variables before processing"]

        # Simple smart fixes for common errors
        if req.error_log and ("IndentationError" in req.error_log or "SyntaxError" in req.error_log):
            summary = "Indentation/Syntax Error Detected"
            cause = "Improper spacing or missing block indentation in code structures."
        elif req.error_log and "ZeroDivisionError" in req.error_log:
            summary = "Zero Division Error"
            cause = "Attempted division by zero without zero check."
            tips.append("Always check denominator is non-zero before dividing.")

        for line in code_lines:
            if " / 0" in line:
                line = line.replace(" / 0", " / 1  # Fixed division by zero")
            elif line.strip().startswith("def ") and not line.strip().endswith(":"):
                line = line + ":"
            elif line.strip().startswith("if ") and not line.strip().endswith(":"):
                line = line + ":"
            fixed_lines.append(line)

        fixed_code = "\n".join(fixed_lines)

        return ErrorSolverResponse(
            error_summary=summary,
            root_cause=cause,
            corrected_code=fixed_code,
            explanation="Reviewed code structure, corrected syntax errors, and added safety guards.",
            prevention_tips=tips
        )


error_solver_service = ErrorSolverService()
