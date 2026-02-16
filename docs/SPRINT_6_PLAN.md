# Sprint 6 Plan (Checkov Suppression Governance)

## Goal
Introduce controlled, auditable skips for selected checks to protect budget while keeping security posture explicit.

## Scope
- Add explicit skip/suppression for `CKV_AWS_50` (Lambda X-Ray).
- Add explicit skip/suppression for `CKV_AWS_18` (S3 access logging).
- Document business justification, owner, and review cadence for each suppression.
- Re-run Checkov baseline and confirm expected pass/fail profile.

## Acceptance Criteria
- `CKV_AWS_50` and `CKV_AWS_18` are suppressed with justification in config and docs.
- Suppression entries include owner and next review date.
- CI output remains clear on which checks are skipped and why.
- Follow-up issue is created to reassess skipped checks at next budget review.

## Cost Guardrails
- No automatic enabling of X-Ray or S3 access logging in this sprint.
- No hidden always-on services introduced by suppression implementation.
- Keep suppression scope minimal (only the two approved checks).

## Out of Scope
- Re-evaluating high-cost checks in this sprint.
- Implementing additional suppressions outside approved list.

## Next Step After Sprint 6
- Revisit remaining checks with fresh cost/security review:
  - `CKV_AWS_117`, `CKV_AWS_272`, `CKV_AWS_173`, `CKV_AWS_144`, `CKV_AWS_145`, `CKV2_AWS_62`.
