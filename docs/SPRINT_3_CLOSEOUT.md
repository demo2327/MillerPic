# Sprint 3 Closeout

## Sprint Goal
Deliver the user-sync foundation for desktop workflows, including managed-folder sync behavior, video policy enforcement, and metadata enrichment.

## Scope Delivered
- #39 A20: Desktop managed folders + incremental sync
- #41 A22: Video policy gate (skip videos in sync)
- #40 A21: Auto-subject enrichment (EXIF date, geolocation, folder labels)

## Pull Requests Merged
- #47: managed folders + incremental sync foundation
- #48: enforce video skip policy in sync
- #49: auto-subject enrichment from EXIF and folder hierarchy
- #50: Sprint 3 cost impact review docs
- #51: Sprint 3 monthly cost dashboard checklist

## User-Facing Outcomes
- Users can add/remove managed folders and run repeatable sync jobs.
- Sync uploads only new/changed image files from managed folders.
- Local deletions do not trigger cloud deletion behavior.
- Video files are detected and explicitly marked as skipped in sync reporting.
- Subjects are auto-generated from folder hierarchy and EXIF metadata when available.

## Operational Outcomes
- Sprint 3 tracker state is clean: #39, #40, #41 are closed and no open sprint-3 issues remain.
- Cost review coverage added for Sprint 3 variable-cost effects and monitoring counters.
- Daily command center now includes a monthly Sprint 3 cost dashboard checklist.

## Cost Impact Summary
- Fixed AWS baseline: no material change (no new always-on services introduced).
- Variable costs:
  - image sync automation can increase successful upload/request volume,
  - video skip policy reduces avoidable large-object storage and request growth,
  - subject enrichment adds small metadata overhead in DynamoDB item size.
- Net: storage footprint and image upload volume remain dominant cost drivers.

## Validation Evidence
- CI checks passed on merged PRs (#47, #48, #49, #50, #51):
  - Python backend unit tests
  - Python compile checks
  - Terraform fmt/validate
  - Terraform plan (optional)

## Risks / Follow-ups
- EXIF metadata quality varies by device/file source and may affect subject consistency.
- Managed-folder scans may need optimization as library size grows.
- Sprint 4 should prioritize global dedupe and scalable file-management UI to control growth and improve throughput.
