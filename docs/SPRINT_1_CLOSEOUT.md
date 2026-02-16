# Sprint 1 Closeout (Control Tower)

Date: 2026-02-16

## Sprint Goal
Deliver searchable photo metadata capability end-to-end (API + desktop), with CI coverage and infrastructure safety guardrails preserved.

## Completed Scope
- GET photo metadata endpoint: `GET /photos/{photoId}`
- Basic search endpoint: `GET /photos/search?q=...`
- Desktop search UI wired to search endpoint
- Backend lifecycle test suite and CI gate improvements
- Guardrail restoration and validation after drift risk was identified

## Shipped PRs
- #27 — Add `GET /photos/{photoId}` metadata endpoint
- #28 — Add basic search endpoint (filename + subjects)
- #29 — Add backend lifecycle tests + CI gate
- #30 — Desktop search UI wired to search endpoint
- #31 — Restore guardrails and keep sensitive config in Secrets Manager

## Acceptance / Demo Checklist
- [x] Authenticated photo detail returns owned metadata
- [x] Search endpoint returns matching active photos
- [x] Desktop client can query search and display results
- [x] CI compile + backend tests + Terraform checks green
- [x] API throttling and Lambda concurrency guardrails active
- [x] Cost protection resources present (SNS/Budgets/CloudWatch alarms)

## Cost & Risk Impact
- Direct feature cost impact: low (search/get-photo Lambda + API calls)
- Guardrail posture: restored and active
  - API throttling: `20 rps` steady, `40` burst
  - Lambda reserved concurrency: `10` per function
  - Budget threshold: `$25` monthly
  - Forecast alert threshold: `80%`
  - API and Lambda error/throttle alarms enabled
- Sensitive config posture improved
  - JWT issuer/audience and alert email sourced via Secrets Manager data lookup
  - Local `terraform.tfvars` kept uncommitted

## Operational Notes
- Sprint 1 issues are all closed: #11, #12, #14, #26
- Post-merge infrastructure plan is converged (`No changes`)

## Next Sprint (Sprint 2)
Planned open items:
- #13 — Desktop folder upload queue
- #15 — Ops playbook integration
- #16 — Desktop upload queue reliability and UX follow-up

## Go/No-Go
Go for Sprint 2.
