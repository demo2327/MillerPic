# MillerPic — Copilot Instructions

## Project Overview
Family photo storage platform on AWS serverless architecture (S3, Lambda, API Gateway, DynamoDB), with a Python/Tkinter desktop client for curation and sync. Product direction: **curate-before-upload** — only "keep" decisions reach the cloud, so storage cost stays low and the library stays clean by construction.

## Repo Structure (accurate as of 2026-07)
- `backend/` — Python Lambda handlers (`src/handlers/`) + pytest suite (`tests/`).
- `desktop-client/` — Python/Tkinter desktop app (`app.py`) with Sync / Library / Curation / Settings tabs. Curation review mode (keyboard-driven filmstrip + burst detection + sticky label chips) lives here.
- `infrastructure/` — Terraform for the app stack; `infrastructure/bootstrap/` — Terraform for bootstrap resources (state backend, signing).
- `docs/` — architecture, security, deployment, sprint plans/closeouts.

**Note:** README/SPECIFICATION.md describe a React web gallery and React Native Android app as done — neither exists yet. Reality is the Python backend + Python desktop client only. Treat those docs as aspirational, not current state, unless verified otherwise.

## Git Workflow — REQUIRED
- **Always create a feature branch and open a pull request for any code, infrastructure, or config change.** Never commit directly to `main`, even for small fixes, housekeeping, or docs.
- Base new branches on an up-to-date `main`.
- Use descriptive branch names (e.g. `feature/curation-labeling`, `fix/appledouble-sidecar`).
- Write a clear PR description: summary, what changed, test evidence, risk/rollback.
- Reference related GitHub issues in commit messages/PR descriptions (`closes #NN`) where applicable.
- Do not push to `main` directly even if branch protection can be bypassed — the bypass exists for emergencies, not routine workflow.

## Testing & Validation
- Backend: `cd backend; python -m pytest -q` (or via the venv at `desktop-client/.venv`).
- Desktop: `python -m pytest desktop-client/tests -q`.
- Compile check: `python -m py_compile backend/src/handlers/upload.py backend/src/handlers/download.py backend/src/handlers/list.py desktop-client/app.py`.
- Terraform: `terraform -chdir=infrastructure fmt -check -recursive` and `terraform -chdir=infrastructure plan` before merging infra changes.
- Run relevant tests before opening a PR; keep them green.

## Conventions
- Desktop app class: `MillerPicDesktopApp` in `desktop-client/app.py`.
- Curation decisions/labels persist per-folder in gitignored `desktop-client/curation_state/` (sidecar files keyed by a hash of the folder path) — restored automatically on re-scan.
- Checkov suppressions require an inline `#checkov:skip=CKV_XXX: <reason>` comment placed **inside** the resource block, with Owner/ReviewBy recorded, and must be mirrored in `docs/SECURITY.md`'s suppression register.
- MCP server versions are pinned in `.vscode/mcp.json`; review monthly per `docs/MCP_SETUP.md`.