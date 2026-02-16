# Productivity Setup (Top 7)

This project now includes:

1. Issue templates (`.github/ISSUE_TEMPLATE/*`)
2. PR template (`.github/pull_request_template.md`)
3. CI checks (`.github/workflows/ci-checks.yml`)
4. VS Code tasks (`.vscode/tasks.json`)
5. Daily command center (`docs/DAILY_COMMAND_CENTER.md`)

## GitHub Project Board (recommended)

Create a GitHub Project with columns:
- Backlog
- In Progress
- Blocked
- Done

Suggested custom fields:
- Priority (P0/P1/P2)
- Area (backend/infrastructure/desktop/android/docs)
- Target date

## Branch Protection

Protect `main` with:
- Require pull request before merging
- Require at least 1 approval
- Dismiss stale approvals when new commits are pushed
- Enforce for admins
- Disallow force pushes and deletions

## Daily Workflow

1. Fill `docs/DAILY_COMMAND_CENTER.md`
2. Pick top 3 outcomes
3. Work from issue templates + acceptance criteria
4. Open PR using template
5. Ensure CI checks pass before merge
