"""
security_agent.py — Phase 5.5
Security Audit Agent scanning for hardcoded secrets, SQL injection,
XSS risks, weak crypto/auth patterns, and sensitive info leaks.
"""

import logging
import re
from typing import List, Dict, Any

from backend.app.agents.base import BaseAgent
from backend.app.agents.state import AgentState, CodeFinding

logger = logging.getLogger(__name__)


class SecurityAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Security Agent",
            role="Audits code for OWASP Top 10 vulnerabilities, exposed secrets, SQL injection, and XSS risks."
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
You are a Principal Cybersecurity Penetration Tester and Code Auditor.
Examine the code for security vulnerabilities:
1. Hardcoded API keys, passwords, access tokens, or private keys
2. SQL Injection risks (string concatenation in database queries)
3. Cross-Site Scripting (XSS) vectors or unsanitized innerHTML usage
4. Insecure cryptographic algorithms (e.g. MD5, SHA1 for passwords)
5. Sensitive data logged or exposed in client responses

Languages: {', '.join(languages)}

Files:
{files_snippet}

Respond ONLY with a valid JSON array of finding objects:
[
  {{
    "title": "Short security vulnerability title",
    "file_path": "path/to/file",
    "line_number": 12,
    "severity": "HIGH",
    "category": "SECURITY",
    "description": "Vulnerability description and potential impact",
    "suggestion": "Remediation step or secure implementation sample"
  }}
]
Valid severities: HIGH, MEDIUM, LOW.
"""

    def _normalize_findings(self, raw_list: List[Dict[str, Any]]) -> List[CodeFinding]:
        findings = []
        for item in raw_list:
            findings.append(CodeFinding(
                title=str(item.get("title", "Security Risk")),
                file_path=str(item.get("file_path", "unknown")),
                line_number=item.get("line_number"),
                severity=str(item.get("severity", "HIGH")).upper(),
                category="SECURITY",
                description=str(item.get("description", "")),
                suggestion=str(item.get("suggestion", "")),
            ))
        return findings

    def _heuristic_analysis(self, files: List[Dict[str, Any]]) -> List[CodeFinding]:
        findings: List[CodeFinding] = []

        secret_patterns = [
            (r"(api[_-]?key|secret[_-]?key|auth[_-]?token|password)\s*[:=]\s*['\"]([^'\"]{8,})['\"]", "Hardcoded Secret / API Key"),
            (r"BEGIN\s+PRIVATE\s+KEY", "Exposed Private Key Block"),
            (r"aws_access_key_id\s*=", "Exposed AWS Access Key Identifier"),
        ]

        sql_patterns = [
            r"SELECT\s+.*\s+FROM\s+.*\+\s*\w+",
            r"f[\"'].*SELECT\s+.*FROM.*\{",
            r"cursor\.execute\(['\"].*%s.*['\"]\s*%",
        ]

        for f in files:
            file_path = f.get("file_path", "")
            content = f.get("content", "")
            lines = content.splitlines()

            for idx, line in enumerate(lines, start=1):
                # 1. Hardcoded secrets check
                for pattern, title in secret_patterns:
                    if re.search(pattern, line, re.IGNORECASE) and not "example" in line.lower() and not "env" in line.lower():
                        findings.append(CodeFinding(
                            title=title,
                            file_path=file_path,
                            line_number=idx,
                            severity="HIGH",
                            category="SECURITY",
                            description="Hardcoded credential or private token embedded directly in source code.",
                            suggestion="Store sensitive tokens in environment variables or a secrets manager."
                        ))

                # 2. SQL Injection check
                for pattern in sql_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        findings.append(CodeFinding(
                            title="Potential SQL Injection Vector",
                            file_path=file_path,
                            line_number=idx,
                            severity="HIGH",
                            category="SECURITY",
                            description="Dynamic string formatting or concatenation used in SQL statement execution.",
                            suggestion="Use parameterized queries or ORM query builders to prevent SQL injection."
                        ))

                # 3. Weak Hash Check (MD5/SHA1)
                if re.search(r"\b(md5|sha1)\s*\(", line, re.IGNORECASE) and not "checksum" in line.lower():
                    findings.append(CodeFinding(
                        title="Weak Cryptographic Hash Algorithm",
                        file_path=file_path,
                        line_number=idx,
                        severity="MEDIUM",
                        category="SECURITY",
                        description="MD5/SHA1 algorithms are vulnerable to collision attacks and should not be used for security.",
                        suggestion="Upgrade to SHA-256, SHA-512, or bcrypt/argon2 for password hashing."
                    ))

        return findings
