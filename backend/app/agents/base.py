"""
base.py — Phase 5.1
Base Agent interface with Google Gemini LLM integration, prompt handling,
JSON output parsing, and fallback heuristic mechanisms for offline/mock execution.
"""

import json
import logging
import re
from typing import Dict, Any, Optional, List

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


def clean_json_response(raw_text: str) -> str:
    """Extract clean JSON string from Markdown code block wrappers if present."""
    if not raw_text:
        return "{}"
    cleaned = raw_text.strip()
    # Remove ```json ... ``` wrappers
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return cleaned


class BaseAgent:
    """
    Abstract Base Class for specialized AI agents.
    Provides LLM invocation with fallbacks to static heuristics.
    """

    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.llm = self._init_llm()

    def _init_llm(self):
        """Initialize Google Gemini LLM via LangChain integration if API key exists."""
        if settings.GEMINI_API_KEY:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                return ChatGoogleGenerativeAI(
                    google_api_key=settings.GEMINI_API_KEY,
                    model=settings.DEFAULT_LLM_MODEL,
                    temperature=0.2,
                    max_retries=2,
                )
            except Exception as e:
                logger.warning(f"Failed to initialize ChatGoogleGenerativeAI for agent '{self.name}': {e}")
        return None

    def invoke_llm(self, prompt: str) -> Optional[str]:
        """Invoke LLM if available, returning the response string or None if unconfigured/failed."""
        if not self.llm:
            return None
        try:
            response = self.llm.invoke(prompt)
            return response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            logger.error(f"LLM invocation failed for agent '{self.name}': {e}")
            return None

    def parse_json_safely(self, text: str, fallback: Any = None) -> Any:
        """Parse LLM output as JSON with cleanup and fallback."""
        if not text:
            return fallback if fallback is not None else {}
        cleaned = clean_json_response(text)
        try:
            return json.loads(cleaned)
        except Exception as e:
            logger.warning(f"JSON parsing failed for agent '{self.name}': {e}. Raw text snippet: {cleaned[:100]}...")
            return fallback if fallback is not None else {}
