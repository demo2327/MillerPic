# Sprint 6 Closeout

## Sprint Goal
Implement controlled, auditable Checkov suppressions for budget-approved checks while keeping CI security visibility explicit.

## Scope Delivered
- #61: Controlled suppression governance for `CKV_AWS_50` (Lambda X-Ray) and `CKV_AWS_18` (S3 access logging).
- #64: Follow-up reassessment issue for next budget/security review cycle.

## Pull Requests Merged
- #65: Sprint 6 controlled Checkov skips with governance.

## User/Operator Outcomes
- Checkov output remains actionable without introducing higher recurring-cost services this sprint.
- Exceptions are explicit in Terraform and reviewable in normal PR workflow.
- Security/deployment docs now include a suppression register with owner and review date.

## Security & Governance Outcomes
- Inline Terraform suppressions added only for approved checks:
  - `CKV_AWS_50` on Lambda resources (`infrastructure/lambda.tf`, bootstrap rotation Lambda).
  - `CKV_AWS_18` on S3 buckets (`photos`, `terraform_state`).
- Suppression rationale includes compensating controls and review metadata.
- Ownership and review cadence documented in `docs/SECURITY.md` and `docs/DEPLOYMENT.md`.
- Reassessment issue opened for monthly budget/security checkpoint: #64 (target 2026-03-16).

## Cost Impact Summary
- Fixed AWS baseline: unchanged in Sprint 6 (no new always-on services enabled).
- Variable-cost effect: neutral to slightly reduced risk of unplanned spend because:
  - X-Ray tracing remains disabled (`CKV_AWS_50` suppressed by policy decision).
  - S3 access-log bucket growth and request overhead are deferred (`CKV_AWS_18` suppressed by policy decision).
- Net: Sprint 6 prioritizes budget stability while deferring higher-visibility telemetry controls to a later cost-approved phase.

## Validation Evidence
- Terraform checks passed for Sprint 6 changes:
  - `terraform fmt -check -recursive`
  - `terraform validate`
- CI checks green on merged PR #65:
  - Checkov Terraform scan
  - Terraform fmt/validate/plan jobs
  - Python checks (backend tests + compile checks)

## Remaining Checkov Roadmap (Post Sprint 6)
Reassess deferred findings with monthly budget/security review before remediation:
- `CKV_AWS_117` (Lambda in VPC)
- `CKV_AWS_272` (Lambda code signing)
- `CKV_AWS_173` (Lambda env var KMS)
- `CKV_AWS_144` (S3 replication)
- `CKV_AWS_145` (S3 KMS-by-default)
- `CKV2_AWS_62` (S3 event notifications)

Decision sequence for each deferred check:
1. Estimate monthly and one-time implementation cost.
2. Score security risk reduction and operational impact.
3. Choose one action: remediate, maintain temporary suppression, or redesign control scope.
4. Record outcome in security docs and backlog with next review date.

## Risks / Follow-ups
- Suppressions can become stale if review cadence slips; issue #64 is the enforcement checkpoint.
- Deferred controls may become higher priority if threat model or compliance requirements change.
- Next sprint should include a compact cost-vs-risk matrix for each deferred check to speed decision-making.
