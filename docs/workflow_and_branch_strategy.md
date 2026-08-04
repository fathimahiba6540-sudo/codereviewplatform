# Development Workflow & Branch Strategy

## 1. Branch Strategy (Git Flow)

- `main` / `master`: Production-ready code. All release versions tagged.
- `develop`: Integration branch for completed feature phases.
- `feature/<phase-name>` or `feature/<issue-title>`: Branch for active development of individual project phases (e.g. `feature/phase-1-setup`, `feature/phase-2-database`).
- `hotfix/<fix-title>`: Emergency patches directly merged back to `main` and `develop`.

## 2. Pull Request & Commit Rules

1. Every PR must pass static analysis (Ruff / Black for Python, Flutter linter for Dart).
2. Use clear Conventional Commits format:
   - `feat(backend): add authentication endpoints`
   - `feat(frontend): implement login screen UI`
   - `docs: update architecture diagram`
   - `chore: update dependencies`
3. Never check in secrets, credentials, `.env` files, or binary uploads.

## 3. Workflow Steps per Phase

1. Pull latest `develop`.
2. Create branch `feature/phase-X`.
3. Implement required code and documentation.
4. Run static validation & unit tests.
5. Create Pull Request and merge into `develop`.
