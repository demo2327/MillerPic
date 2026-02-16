# Daily Command Center

## Today’s Top 3 Outcomes
- [x] Sprint 1 merged end-to-end (API search/detail, desktop search UI, tests)
- [x] Guardrails restored and deployed (throttle, concurrency, budgets, alarms)
- [x] Sensitive config moved to Secrets Manager data-source flow

## In Progress
- Sprint 2 docs hardening: ops playbook integration and monthly guardrail checklist

## Blockers
- None

## Next Commands
```powershell
# Example quick loop
.\desktop-client\.venv\Scripts\python -m py_compile .\desktop-client\app.py
terraform -chdir=infrastructure fmt -check -recursive
terraform -chdir=infrastructure validate
```

## PRs / Issues Today
- Issues closed in Sprint 1: #11, #12, #14, #26
- PRs merged: #27, #28, #29, #30, #31

## Incident Cheat-Sheet (Rollback-Safe)

### Ownership
- Incident commander: platform owner on call
- Terraform operator: infra owner
- API verifier: backend owner
- Communications: project owner (status + issue updates)

### 1) Fast Triage (Read-only)
```powershell
terraform -chdir=infrastructure plan
gh run list --repo demo2327/MillerPic --limit 10
```

### 2) Guardrail Drift Check (Read-only)
```powershell
terraform -chdir=infrastructure fmt -check -recursive
terraform -chdir=infrastructure validate
terraform -chdir=infrastructure plan
```

### 3) Safe Rollback Trigger
```powershell
gh workflow run "CI Checks" --repo demo2327/MillerPic
```

### 4) Post-Restore Verification
```powershell
.\desktop-client\.venv\Scripts\python.exe -m py_compile .\backend\src\handlers\upload.py .\backend\src\handlers\download.py .\backend\src\handlers\list.py .\desktop-client\app.py
```

### 5) Evidence Capture
- Add command outputs to the active incident issue.
- Record who executed rollback and exact UTC timestamp.
- Link related PRs and workflow runs before resolving the incident.

## Monthly Guardrail Review Checklist

### Ownership + Cadence
- Owner: infra owner
- Reviewer: backend owner
- Cadence: first business day of each month
- Artifact: checklist update in the monthly ops issue

### Throttle Thresholds
- Verify API throttle defaults in Terraform are unchanged from approved baseline.
- Confirm no accidental route-level throttle overrides were introduced.
- If values changed unintentionally, open rollback PR immediately.

### Lambda Concurrency Thresholds
- Confirm reserved concurrency matches approved values for critical handlers.
- Validate there are no handlers with unexpected unbounded concurrency.
- If drift is found, restore previous known-good values and attach plan output.

### Budget + Alarm Thresholds
- Verify monthly budget limits and forecast alerts match expected guardrail values.
- Confirm alarm actions still route to the correct notification targets.
- If thresholds were edited outside approved change control, revert and re-validate.

### Monthly Execution Commands (Rollback-Safe)
```powershell
terraform -chdir=infrastructure fmt -check -recursive
terraform -chdir=infrastructure validate
terraform -chdir=infrastructure plan
gh issue create --repo demo2327/MillerPic --title "Monthly guardrail review - $(Get-Date -Format yyyy-MM)" --body "Checklist run completed. Attach plan summary, threshold verification, and owner sign-off."
```

## End-of-day Notes
- What shipped: Sprint 1 scope complete; guardrail drift corrected and reapplied.
- What is next: close Sprint 2 with issue hygiene and closeout notes.
