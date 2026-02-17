# Daily Command Center

## Mission for Tomorrow (Highest Priority)
**Primary objective:** Reduce and triage remaining Checkov failures with budget-aware decisions, then lock in the next remediation order.

## Top 3 Outcomes (Tomorrow)
- [ ] Publish an updated Checkov findings snapshot (failed + skipped + deltas from prior run).
- [ ] Produce a decision table for all remaining failed checks: remediate now, suppress with governance, or defer.
- [ ] Open/refresh implementation issues for the next approved remediation wave.

## Current Security Baseline (As of Last Run)
- Checkov scan verifies suppressions are now recognized when placed **inside** Terraform resource blocks.
- Active suppressed controls currently expected:
	- `CKV_AWS_50` (Lambda X-Ray)
	- `CKV_AWS_18` (S3 access logging)
	- `CKV2_AWS_57` (static sensitive config secret rotation)
- Remaining failed controls to prioritize for decisioning:
	- `CKV_AWS_117`, `CKV_AWS_272`, `CKV_AWS_173`, `CKV_AWS_144`, `CKV_AWS_145`, `CKV2_AWS_62`
	- Plus smaller-count findings (`CKV_AWS_119`, `CKV_AWS_149`, `CKV_AWS_40`, `CKV_AWS_273`, `CKV2_AWS_73`, `CKV_AWS_158`, `CKV_AWS_338`)

## Execution Plan (Tomorrow)

### 1) Morning Verification Loop (Must-do first)
```powershell
gh workflow run ci-checks.yml -f run_checkov=true
gh run list --workflow ci-checks.yml --event workflow_dispatch --limit 3
```

### 2) Pull and Summarize Findings
```powershell
# Replace <RUN_ID> with latest workflow_dispatch run
gh run view <RUN_ID> --log > .tmp_checkov.log

# Quick summary lines
Select-String -Path .tmp_checkov.log -Pattern "Passed checks|Failed checks|Skipped checks"
```

### 3) Normalize Findings by Check ID
```powershell
$raw = Get-Content .tmp_checkov.log -Raw
$clean = [regex]::Replace($raw, "`e\[[0-9;]*[A-Za-z]", "")
$clean = [regex]::Replace($clean, '\x1B\[[0-9;]*[A-Za-z]', '')
$matches = [regex]::Matches($clean, 'Check:\s*(CKV2?_AWS_\d+)[\s\S]*?FAILED for resource:\s*([^\r\n]+)')
$rows = foreach($m in $matches){ [pscustomobject]@{ Check=$m.Groups[1].Value; Resource=$m.Groups[2].Value } }
$rows | Sort-Object Check,Resource -Unique | Group-Object Check | Sort-Object Name | Select-Object Name,Count
```

### 4) Decision Gate (Required before code changes)
For each failed check, assign one of:
- **Remediate now** (low cost / high security return)
- **Suppress with governance** (temporary budget exception with owner + review date)
- **Defer** (explicitly tracked, no silent carryover)

### 5) Implementation Batch Rules
- Keep each PR focused to one control family when possible.
- Every suppression must include: reason, compensating controls, owner, review date.
- Every remediation PR must include Terraform plan summary + cost note.

## Tomorrow Success Criteria
- A single up-to-date Checkov findings summary is posted in repo docs/issues.
- Next remediation batch is approved and queued with explicit owners.
- No ambiguity remains on skipped checks vs failed checks.

## Rapid Commands
```powershell
terraform -chdir=infrastructure fmt -check -recursive
terraform -chdir=infrastructure validate
terraform -chdir=infrastructure plan
terraform -chdir=infrastructure/bootstrap validate
gh run list --workflow ci-checks.yml --limit 10
```

## Risk Watch
- **False confidence risk:** suppression comments outside resource blocks may be ignored by Checkov in this environment.
- **Cost creep risk:** enabling VPC/KMS/replication controls without cost review can move monthly baseline.
- **Tracking risk:** deferred checks without issue ownership can stall.

## End-of-day Exit Conditions (Tomorrow)
- Checkov snapshot refreshed and archived.
- Decision table complete for all remaining failed controls.
- Next implementation issues updated and assigned.
