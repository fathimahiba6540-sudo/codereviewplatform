import os
import hashlib
from typing import List, Dict, Any, Tuple

EXTENSION_LANGUAGE_MAP = {
    ".py": "Python",
    ".dart": "Dart",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".c": "C",
    ".h": "C",
    ".cpp": "C++",
    ".hpp": "C++",
    ".cc": "C++",
    ".go": "Go",
    ".rs": "Rust",
    ".php": "PHP",
    ".rb": "Ruby",
    ".cs": "C#",
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".scss": "CSS",
    ".sass": "CSS",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".toml": "TOML",
    ".xml": "XML",
    ".md": "Markdown",
    ".sh": "Shell",
    ".bat": "Batch",
    ".ps1": "PowerShell",
    ".sql": "SQL",
    ".dockerfile": "Dockerfile",
}

IGNORED_DIRECTORIES = {
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "env",
    "build",
    "dist",
    "__pycache__",
    ".dart_tool",
    ".idea",
    ".vscode",
    "coverage",
    ".pytest_cache",
}


class RepoParser:
    """Service for parsing codebase structure, file metrics, languages, and framework detection."""

    @classmethod
    def calculate_file_hash(cls, file_path: str) -> str:
        """Calculate MD5 hash of file content."""
        hasher = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    @classmethod
    def count_file_lines(cls, file_path: str) -> int:
        """Count line count of a text file safely."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return sum(1 for _ in f)
        except Exception:
            return 0

    @classmethod
    def detect_framework(cls, root_dir: str, file_paths: List[str]) -> str:
        """Detect primary software framework or tech stack based on file patterns."""
        filenames = {os.path.basename(p).lower() for p in file_paths}

        if "pubspec.yaml" in filenames:
            return "Flutter / Dart"
        if "pom.xml" in filenames or "build.gradle" in filenames:
            return "Java / Spring Boot"
        if "cargo.toml" in filenames:
            return "Rust"
        if "go.mod" in filenames:
            return "Go"

        if "package.json" in filenames:
            pkg_json_path = next((p for p in file_paths if os.path.basename(p).lower() == "package.json"), None)
            if pkg_json_path and os.path.exists(pkg_json_path):
                try:
                    with open(pkg_json_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read().lower()
                        if "next" in content:
                            return "Next.js"
                        elif "react" in content:
                            return "React"
                        elif "vue" in content:
                            return "Vue.js"
                        elif "express" in content:
                            return "Node.js / Express"
                except Exception:
                    pass
            return "Node.js / JavaScript"

        if "requirements.txt" in filenames or "pyproject.toml" in filenames or "setup.py" in filenames:
            req_path = next((p for p in file_paths if os.path.basename(p).lower() in ["requirements.txt", "pyproject.toml"]), None)
            if req_path and os.path.exists(req_path):
                try:
                    with open(req_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read().lower()
                        if "fastapi" in content:
                            return "FastAPI / Python"
                        elif "django" in content:
                            return "Django / Python"
                        elif "flask" in content:
                            return "Flask / Python"
                except Exception:
                    pass
            return "Python"

        return "Generic Codebase"

    @classmethod
    def parse_repository(cls, repo_dir: str) -> Dict[str, Any]:
        """Traverse directory, parse all source files, calculate LOC, languages, and metadata."""
        parsed_files = []
        language_counts = {}
        total_loc = 0
        total_files = 0
        all_relative_paths = []

        for root, dirs, files in os.walk(repo_dir):
            # Exclude ignored directories in place
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRECTORIES]

            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, repo_dir)
                all_relative_paths.append(rel_path)

                ext = os.path.splitext(file)[1].lower()
                language = EXTENSION_LANGUAGE_MAP.get(ext, "Other")

                file_size = os.path.getsize(full_path)
                lines = cls.count_file_lines(full_path)
                content_hash = cls.calculate_file_hash(full_path)

                parsed_files.append({
                    "filename": file,
                    "file_path": rel_path.replace("\\", "/"),
                    "full_path": full_path,
                    "language": language,
                    "file_size_bytes": file_size,
                    "line_count": lines,
                    "content_hash": content_hash
                })

                total_files += 1
                total_loc += lines
                language_counts[language] = language_counts.get(language, 0) + 1

        # Sort detected languages by file count
        sorted_languages = sorted(language_counts.keys(), key=lambda l: language_counts[l], reverse=True)
        detected_framework = cls.detect_framework(repo_dir, [f["full_path"] for f in parsed_files])

        return {
            "total_files": total_files,
            "total_lines_of_code": total_loc,
            "detected_languages": sorted_languages,
            "language_counts": language_counts,
            "framework": detected_framework,
            "files": parsed_files
        }
