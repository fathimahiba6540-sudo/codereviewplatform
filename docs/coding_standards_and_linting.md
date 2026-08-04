# Coding Standards & Linting Rules

## 1. Python (FastAPI Backend)
- **Style Guide**: PEP 8 compliance.
- **Formatter**: `black` (88-character line length).
- **Linter**: `ruff` for fast static checks and import sorting.
- **Type Annotations**: Mandatory type hints on all function arguments and return types.
- **Async Conventions**: Use `async def` for I/O bound router endpoints; synchronous helper methods for compute/DB operations.

## 2. Dart / Flutter (Frontend App)
- **Style Guide**: Effective Dart standards enforced via `flutter_lints`.
- **Formatting**: `flutter format .` with single quotes preferred (`prefer_single_quotes`).
- **Widgets**: Enforce `const` constructors where applicable (`prefer_const_constructors`).
- **State Management**: Keep UI components decoupled from network services via Provider / Riverpod state services.

## 3. Version Control & File Formatting
- UTF-8 encoding across all files.
- UNIX line endings (`\n`) in git repositories.
- Meaningful commit messages following Conventional Commits format (`feat:`, `fix:`, `docs:`, `chore:`).
