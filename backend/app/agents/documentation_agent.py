"""
documentation_agent.py — Phase 5.6
Documentation Agent generating project README, setup steps,
architecture summaries, and module overviews.
"""

import logging
from typing import Dict, Any, List

from backend.app.agents.base import BaseAgent
from backend.app.agents.state import AgentState

logger = logging.getLogger(__name__)


class DocumentationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Documentation Agent",
            role="Generates project documentation, README guides, setup instructions, and architecture summaries."
        )

    def analyze(self, state: AgentState) -> Dict[str, Any]:
        files_context = state.get("files_context", [])
        title = state.get("project_title", "Software Project")
        framework = state.get("framework", "Generic")
        languages = state.get("detected_languages", [])

        prompt = self._build_prompt(title, framework, languages, files_context)
        raw_output = self.invoke_llm(prompt)
        if raw_output:
            parsed = self.parse_json_safely(raw_output, fallback={})
            if isinstance(parsed, dict) and "readme_markdown" in parsed:
                return parsed

        return self._heuristic_documentation(title, framework, languages, files_context)

    def _build_prompt(self, title: str, framework: str, languages: List[str], files: List[Dict[str, Any]]) -> str:
        files_list_str = "\n".join([f"- {f.get('file_path')}" for f in files[:15]])

        return f"""
You are a Technical Writer and Software Architect.
Generate comprehensive documentation for the project titled "{title}".
Framework: {framework}
Primary Languages: {', '.join(languages)}

Project Files:
{files_list_str}

Respond ONLY with a valid JSON object with the following schema:
{{
  "title": "{title}",
  "overview": "High-level summary of the project architecture and features.",
  "readme_markdown": "# {title}\\n\\n## Overview\\n...",
  "installation": "Step-by-step setup and installation instructions.",
  "usage": "Usage guidelines and command line / API invocation examples.",
  "project_structure": "Explanation of main folders and key modules."
}}
"""

    def _heuristic_documentation(
        self,
        title: str,
        framework: str,
        languages: List[str],
        files: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        file_tree = "\n".join([f"  - `{f.get('file_path')}` ({f.get('language')})" for f in files[:20]])
        langs_str = ", ".join(languages) if languages else "Codebase"

        overview = f"A {framework} project written in {langs_str} containing {len(files)} source files."
        
        readme = f"""# {title}

## Overview
{overview}

## Tech Stack
- **Framework**: {framework}
- **Languages**: {langs_str}

## Repository Structure
{file_tree}

## Getting Started

### Prerequisites
- Install appropriate runtime environments for {langs_str}.

### Installation
```bash
# Clone repository and navigate to project directory
cd project
```

### Running the Application
Refer to main entry points in the source files.
"""

        return {
            "title": title,
            "overview": overview,
            "readme_markdown": readme,
            "installation": f"Install required dependencies for {langs_str} environment.",
            "usage": "Run project main module using standard ecosystem tools.",
            "project_structure": f"Contains {len(files)} files categorized across {langs_str} modules.",
        }
