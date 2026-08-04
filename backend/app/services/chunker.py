"""
chunker.py — Phase 4.2
Smart code chunking service.

Strategy:
- Python: chunk at function/class boundaries using AST
- All other languages: sliding window by line count with overlap
- Each chunk carries rich metadata for retrieval and agent context
"""
import ast
import os
from typing import List, Dict, Any, Optional


# Chunking configuration
DEFAULT_CHUNK_LINES = 60       # lines per chunk for non-Python
CHUNK_OVERLAP_LINES = 10       # overlap between consecutive chunks
MIN_CHUNK_CHARS = 50           # discard chunks shorter than this
MAX_CHUNK_CHARS = 8000         # safety cap per chunk


def _line_window_chunks(
    content: str,
    file_path: str,
    language: str,
    file_id: Optional[str],
    project_id: str,
    chunk_lines: int = DEFAULT_CHUNK_LINES,
    overlap: int = CHUNK_OVERLAP_LINES,
) -> List[Dict[str, Any]]:
    """Split content into overlapping line-window chunks."""
    lines = content.splitlines()
    chunks = []
    step = max(1, chunk_lines - overlap)
    chunk_index = 0

    for start in range(0, len(lines), step):
        end = min(start + chunk_lines, len(lines))
        chunk_text = "\n".join(lines[start:end]).strip()

        if len(chunk_text) < MIN_CHUNK_CHARS:
            continue
        if len(chunk_text) > MAX_CHUNK_CHARS:
            chunk_text = chunk_text[:MAX_CHUNK_CHARS]

        chunks.append({
            "chunk_id": f"{project_id}::{file_path}::chunk{chunk_index}",
            "project_id": project_id,
            "file_id": file_id,
            "file_path": file_path,
            "language": language,
            "chunk_index": chunk_index,
            "line_start": start + 1,
            "line_end": end,
            "content": chunk_text,
            "chunk_type": "window",
        })
        chunk_index += 1

        if end >= len(lines):
            break

    return chunks


def _python_ast_chunks(
    content: str,
    file_path: str,
    file_id: Optional[str],
    project_id: str,
) -> List[Dict[str, Any]]:
    """
    Chunk Python files at function and class definition boundaries using AST.
    Falls back to line-window chunking if AST parsing fails.
    """
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return _line_window_chunks(content, file_path, "Python", file_id, project_id)

    lines = content.splitlines()
    chunks = []
    chunk_index = 0
    covered_lines: set = set()

    def extract_node_chunk(node: ast.AST) -> None:
        nonlocal chunk_index
        start_line = node.lineno - 1      # 0-indexed
        end_line = node.end_lineno        # exclusive

        node_lines = lines[start_line:end_line]
        chunk_text = "\n".join(node_lines).strip()

        if len(chunk_text) < MIN_CHUNK_CHARS:
            return

        # If the node is too large, fall back to sub-window chunking
        if len(chunk_text) > MAX_CHUNK_CHARS:
            sub_chunks = _line_window_chunks(
                chunk_text, file_path, "Python", file_id, project_id
            )
            for sc in sub_chunks:
                sc["chunk_id"] = f"{project_id}::{file_path}::chunk{chunk_index}"
                sc["chunk_index"] = chunk_index
                sc["line_start"] = start_line + 1
                sc["line_end"] = end_line
                sc["chunk_type"] = "ast_large"
                chunks.append(sc)
                chunk_index += 1
            covered_lines.update(range(start_line, end_line))
            return

        chunks.append({
            "chunk_id": f"{project_id}::{file_path}::chunk{chunk_index}",
            "project_id": project_id,
            "file_id": file_id,
            "file_path": file_path,
            "language": "Python",
            "chunk_index": chunk_index,
            "line_start": start_line + 1,
            "line_end": end_line,
            "content": chunk_text,
            "chunk_type": "ast_node",
            "node_name": getattr(node, "name", None),
            "node_type": type(node).__name__,
        })
        chunk_index += 1
        covered_lines.update(range(start_line, end_line))

    # Extract top-level classes and functions first
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            # Only process top-level or class-level nodes (not nested functions inside functions)
            if hasattr(node, "lineno"):
                extract_node_chunk(node)

    # Collect module-level code not covered by any function/class
    module_lines = [
        (i, line)
        for i, line in enumerate(lines)
        if i not in covered_lines
    ]
    if module_lines:
        module_text = "\n".join(line for _, line in module_lines).strip()
        if len(module_text) >= MIN_CHUNK_CHARS:
            if len(module_text) > MAX_CHUNK_CHARS:
                module_text = module_text[:MAX_CHUNK_CHARS]
            chunks.append({
                "chunk_id": f"{project_id}::{file_path}::chunk{chunk_index}",
                "project_id": project_id,
                "file_id": file_id,
                "file_path": file_path,
                "language": "Python",
                "chunk_index": chunk_index,
                "line_start": 1,
                "line_end": len(lines),
                "content": module_text,
                "chunk_type": "module_level",
                "node_name": "__module__",
                "node_type": "Module",
            })

    # If AST yielded nothing, fall back to line windows
    if not chunks:
        return _line_window_chunks(content, file_path, "Python", file_id, project_id)

    return sorted(chunks, key=lambda c: c["line_start"])


class CodeChunker:
    """
    Service that takes a source file's content and splits it into
    retrievable chunks with metadata for vector store ingestion.
    """

    @classmethod
    def chunk_file(
        cls,
        content: str,
        file_path: str,
        language: str,
        project_id: str,
        file_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Chunk a single file's content into a list of chunk dicts.

        Args:
            content:    Full text content of the file.
            file_path:  Relative path of the file (used in chunk metadata).
            language:   Detected language (e.g. 'Python', 'TypeScript').
            project_id: UUID of the owning project.
            file_id:    UUID of the File DB record (optional).

        Returns:
            List of chunk dicts, each containing:
                chunk_id, project_id, file_id, file_path, language,
                chunk_index, line_start, line_end, content, chunk_type
        """
        if not content or not content.strip():
            return []

        if language == "Python":
            return _python_ast_chunks(content, file_path, file_id, project_id)

        return _line_window_chunks(content, file_path, language, file_id, project_id)

    @classmethod
    def chunk_project_files(
        cls,
        files: List[Dict[str, Any]],
        project_id: str,
        repo_dir: str,
    ) -> List[Dict[str, Any]]:
        """
        Chunk all ingestible files in a project.

        Args:
            files:      List of file dicts from RepoParser.parse_repository()
            project_id: UUID of the owning project.
            repo_dir:   Absolute path to the extracted repository root.

        Returns:
            Flat list of all chunk dicts across all files.
        """
        from backend.app.services.repo_parser import RepoParser

        all_chunks = []
        for file_info in files:
            if not file_info.get("is_ingestible", False):
                continue

            full_path = file_info.get("full_path") or os.path.join(
                repo_dir, file_info["file_path"]
            )
            content = RepoParser.read_file_content(full_path)
            if not content:
                continue

            chunks = cls.chunk_file(
                content=content,
                file_path=file_info["file_path"],
                language=file_info["language"],
                project_id=project_id,
                file_id=file_info.get("db_file_id"),
            )
            all_chunks.extend(chunks)

        return all_chunks
