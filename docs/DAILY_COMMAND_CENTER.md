# Daily Command Center

## Today’s Top 3 Outcomes
- [x] Sprint 4 scope completed (#53, #44, #42, #43 closed)
- [x] Checkov Terraform security scanning enabled in CI with policy docs
- [x] Global dedupe + scalable queue triage + dual-tier storage strategy delivered

## In Progress
- Sprint 5 planning and sequencing (observability, reindex safety, geolocation governance)

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
- Issues closed in Sprint 4: #53, #44, #42, #43
- Recent PRs merged: #54, #55, #56, #57, #58

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

## Monthly Cost Dashboard (Sprint 3)

### Purpose
- Separate cost growth from image volume growth vs metadata overhead.
- Validate that video-skip policy is reducing avoidable storage/request cost.

### Metrics to Capture Monthly
- `sync_images_uploaded`: count of images uploaded by managed-folder sync.
- `sync_videos_skipped`: count of videos skipped by sync policy.
- `dynamodb_photo_item_avg_size`: average photo metadata item size (sampled).
- `s3_total_storage_gb`: total S3 bytes in photos bucket (converted to GB).
- `s3_put_requests`: monthly S3 PUT request count.

### Review Notes
- Rising storage with stable upload count suggests larger image sizes or reduced dedupe efficiency.
- Rising DynamoDB item size with stable upload count suggests metadata expansion.
- If skipped videos drops unexpectedly, verify sync video policy behavior in desktop client.

### Monthly Cost Review Commands
```powershell
aws cloudwatch get-metric-statistics --namespace AWS/S3 --metric-name NumberOfObjects --dimensions Name=BucketName,Value=<photo-bucket>,Name=StorageType,Value=AllStorageTypes --statistics Average --start-time (Get-Date).AddDays(-31).ToUniversalTime().ToString("o") --end-time (Get-Date).ToUniversalTime().ToString("o") --period 86400
aws cloudwatch get-metric-statistics --namespace AWS/DynamoDB --metric-name ConsumedWriteCapacityUnits --dimensions Name=TableName,Value=<photos-table> --statistics Sum --start-time (Get-Date).AddDays(-31).ToUniversalTime().ToString("o") --end-time (Get-Date).ToUniversalTime().ToString("o") --period 86400
gh issue create --repo demo2327/MillerPic --title "Monthly Sprint 3 cost dashboard - $(Get-Date -Format yyyy-MM)" --body "Capture: sync_images_uploaded, sync_videos_skipped, dynamodb_photo_item_avg_size, s3_total_storage_gb, s3_put_requests. Include variance vs prior month and actions."
```

## End-of-day Notes
- What shipped: Sprint 4 scale/cost/security scope complete and merged.
- What is next: execute Sprint 5 hardening and governance tasks.
