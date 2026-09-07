"""
doubt_agent_service.py — 24/7 Instant AI Tutor & Doubt Clearing Service
Provides instant, student-friendly AI tutoring, concept clarification, and interactive problem solving.
"""

import logging
from typing import Dict, Any, Optional, List
from backend.app.agents.base import BaseAgent
from backend.app.models.schemas import DoubtRequest, DoubtResponse

logger = logging.getLogger(__name__)


class DoubtAgentService(BaseAgent):
    def __init__(self):
        super().__init__(name="DoubtClearingAgent", role="24/7 AI Computer Science Tutor & Mentor")

    def resolve_doubt(self, req: DoubtRequest) -> DoubtResponse:
        """Process user query and return clear, educational step-by-step guidance."""
        history_context = ""
        if req.chat_history:
            turns = []
            for item in req.chat_history[-4:]:
                sender = item.get("sender", "user")
                text = item.get("text", "")
                turns.append(f"{sender.upper()}: {text}")
            history_context = "\n[RECENT CONVERSATION HISTORY]:\n" + "\n".join(turns) + "\n"

        code_ctx = f"\n[ATTACHED CODE CONTEXT]:\n```\n{req.code_context}\n```\n" if req.code_context else ""

        prompt = f"""
You are an encouraging, expert AI Computer Science Professor and Programming Mentor available 24/7.
A student or teacher has asked a question to clear their doubt.

{history_context}{code_ctx}
[CURRENT USER DOUBT / QUESTION]:
"{req.query}"

Respond strictly with valid JSON using the following key format:
{{
  "answer": "Comprehensive, clear, encouraging explanation with code examples if applicable. Use bullet points and clean structure.",
  "key_takeaways": [
    "Takeaway 1: Summary of key rule or principle",
    "Takeaway 2: Important tip to remember"
  ],
  "related_topics": [
    "Suggested Follow-up Topic 1",
    "Suggested Follow-up Topic 2"
  ]
}}
"""
        llm_response = self.invoke_llm(prompt)
        parsed = self.parse_json_safely(llm_response, fallback=None)

        if parsed and "answer" in parsed:
            return DoubtResponse(
                answer=parsed.get("answer", "Here is the explanation for your doubt."),
                key_takeaways=parsed.get("key_takeaways", []),
                related_topics=parsed.get("related_topics", [])
            )

        return self._heuristic_fallback(req)

    def _heuristic_fallback(self, req: DoubtRequest) -> DoubtResponse:
        query_lower = req.query.lower()
        ans = ""
        takeaways = []
        related = []

        if "recursion" in query_lower:
            ans = """### 🔄 Understanding Recursion vs Iteration

**Recursion** is when a function calls itself to break down a problem into smaller sub-problems.
**Key Components of Recursion:**
1. **Base Case:** The condition where the function stops calling itself.
2. **Recursive Step:** The call to itself with modified arguments moving towards the base case.

```python
# Example: Factorial with Recursion
def factorial(n):
    if n <= 1:  # Base Case
        return 1
    return n * factorial(n - 1)  # Recursive Step
```
"""
            takeaways = ["Every recursive function MUST have a base case to avoid Infinite Recursion", "Recursion uses the call stack, which consumes memory (O(N) space)"]
            related = ["Tail Call Optimization", "Stack Overflow Exceptions", "Dynamic Programming"]

        elif "binary search" in query_lower:
            ans = """### 🔍 Binary Search Algorithm

Binary search finds an item in a **sorted array** by repeatedly dividing the search interval in half.
- **Time Complexity:** O(log N)
- **Space Complexity:** O(1) iterative

```python
def binary_search(arr, target):
    low = 0
    high = len(arr) - 1
    while low <= high:
        mid = (low + high) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1
```
"""
            takeaways = ["Array MUST be sorted before binary search", "Time complexity reduces from O(N) linear to O(log N) logarithmic"]
            related = ["Binary Search Trees (BST)", "Two Pointer Approach", "Divide and Conquer"]

        else:
            ans = f"""### 💡 AI Tutor Insights for Your Query

**Question:** "{req.query}"

**Key Explanation:**
When tackling programming concepts or debugging doubts:
1. **Identify the Core Principle:** Break down the code execution step-by-step.
2. **Verify Inputs & Edge Cases:** Ensure null pointers, empty lists, or boundary index conditions are validated.
3. **Analyze Complexity:** Check how the operation scales with input size (Big-O notation).

```python
# Best practice structure
try:
    # Process logic safely
    pass
except Exception as e:
    print(f"Error handling: {{e}}")
```
"""
            takeaways = ["Break complex problems into smaller sub-functions", "Test edge cases (empty input, zero, negative numbers)"]
            related = ["Data Structures & Algorithms", "Clean Code Best Practices", "Unit Testing"]

        return DoubtResponse(
            answer=ans,
            key_takeaways=takeaways,
            related_topics=related
        )


doubt_agent_service = DoubtAgentService()
