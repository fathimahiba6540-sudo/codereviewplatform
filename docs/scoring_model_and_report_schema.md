# Review Scoring Model & Report Schema

## 1. Quality Scoring Model Calculation

The overall composite score is a weighted sum (0 - 100) calculated from four sub-metrics:

$$\text{Composite Score} = (0.35 \times \text{Maintainability}) + (0.30 \times \text{Security}) + (0.20 \times \text{Performance}) + (0.15 \times \text{Readability})$$

### Score Components
1. **Maintainability (35%)**:
   - Deductions for long functions (> 50 lines), deep nesting (> 4 levels), code duplicate ratio, and cyclomatic complexity.
2. **Security (30%)**:
   - Deductions based on issue severity:
     - **CRITICAL** (Hardcoded secrets, SQLi): -25 pts per finding
     - **HIGH** (XSS, weak cryptography): -15 pts per finding
     - **MEDIUM** (Missing input validation): -8 pts per finding
     - **LOW** (Minor config weakness): -3 pts per finding
3. **Performance (20%)**:
   - Deductions for $O(N^2)$ loops, unindexed DB queries, synchronous blocking calls in async loops.
4. **Readability (15%)**:
   - Deductions for poor naming conventions, missing docstrings/comments, unused variables.

### Grade Mapping Thresholds
- **A+ / A**: $90 - 100$ (Excellent quality, minimal issues)
- **B**: $80 - 89.9$ (Good quality, minor recommendations)
- **C**: $70 - 79.9$ (Moderate quality, actionable bugs/smells present)
- **D**: $60 - 69.9$ (Poor quality, security or critical bug risks)
- **F**: $< 60$ (Critical issues, refactoring strongly required)

---

## 2. Comprehensive Report Output Schema (Pydantic / JSON)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ReviewReport",
  "type": "object",
  "properties": {
    "review_id": { "type": "string" },
    "project_id": { "type": "string" },
    "created_at": { "type": "string", "format": "date-time" },
    "overall_score": { "type": "number", "minimum": 0, "maximum": 100 },
    "grade": { "type": "string", "enum": ["A+", "A", "B", "C", "D", "F"] },
    "scores": {
      "type": "object",
      "properties": {
        "maintainability": { "type": "number" },
        "security": { "type": "number" },
        "performance": { "type": "number" },
        "readability": { "type": "number" }
      },
      "required": ["maintainability", "security", "performance", "readability"]
    },
    "findings": {
      "type": "object",
      "properties": {
        "bugs": { "type": "array" },
        "security_vulnerabilities": { "type": "array" },
        "code_smells": { "type": "array" }
      }
    },
    "documentation": { "type": "object" },
    "generated_tests": { "type": "array" }
  },
  "required": ["review_id", "project_id", "overall_score", "grade", "scores", "findings"]
}
```
