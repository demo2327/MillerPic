# Daily Command Center

## Current Status (2026-02-18)
- ✅ Checkov baseline is clean on failures in CI (`Failed checks: 0`).
- ✅ Compile checks and backend unit tests are passing.
- ✅ Lambda code signing workflow is in place and validated.
- ✅ Working tree is clean before today’s sprint updates.

## Sprint Focus (Today)
1. Remove CI Checkov noise from non-repository scan paths.
2. Keep release workflow stable (sign artifacts before Terraform apply).
3. Run one fresh CI baseline after changes.
4. Publish sprint closeout notes.

## Verification Commands
```powershell
gh workflow run ci-checks.yml -f run_checkov=true
$env:GH_PAGER='cat'
gh run list --workflow ci-checks.yml --limit 5
```

## Signing + Deploy Workflow (Reference)
```powershell
# 1) Ensure bootstrap outputs exist
terraform -chdir=infrastructure/bootstrap output lambda_artifacts_bucket_name
terraform -chdir=infrastructure/bootstrap output lambda_signing_profile_name

# 2) Sign handler artifacts
./infrastructure/sign-lambda-artifacts.ps1 `
  -ArtifactsBucket <bucket-name> `
  -SigningProfileName <signer-profile> `
  -Region us-east-1

# 3) Deploy infrastructure with generated artifact versions
terraform -chdir=infrastructure plan
terraform -chdir=infrastructure apply
```

## End-of-Day Exit Criteria
- CI workflow run is successful.
- No new Checkov failures introduced.
- Sprint closeout markdown committed.
