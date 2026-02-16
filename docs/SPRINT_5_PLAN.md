# Sprint 5 Plan (Checkov Low-Cost Remediation)

## Goal
Reduce Checkov findings using the lowest-cost remediation set first, preserving budget headroom.

## Scope
- Remediate `CKV2_AWS_61` (S3 lifecycle configuration).
- Remediate `CKV_AWS_116` (Lambda DLQ configuration).
- Remediate `CKV2_AWS_57` (Secrets Manager automatic rotation).
- Re-run Checkov baseline and capture delta.

## Acceptance Criteria
- Findings for `CKV2_AWS_61`, `CKV_AWS_116`, and `CKV2_AWS_57` are resolved.
- CI Checkov job confirms reduced total failures.
- Any infra additions include cost notes in PR body.
- Sprint closeout includes variable/fixed cost impact summary.

## Cost Guardrails
- Prefer existing resources over new always-on services.
- For DLQ, use right-sized queue policy and avoid unnecessary retention/storage overhead.
- For rotation, keep schedule practical (not overly frequent) to control invocation/API costs.

## Out of Scope
- Remediation of high-cost checks (`CKV_AWS_144`, `CKV_AWS_145`, `CKV_AWS_117`).
- Suppression policy rollout for skipped checks (handled in Sprint 6).

## Validation Plan
- Terraform fmt/validate + CI checks.
- Manual Checkov run via workflow_dispatch (`run_checkov=true`).
- Before/after findings table captured in sprint notes.
