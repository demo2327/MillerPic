# Sprint 11 Plan - Local Review + Curation Before Upload

## Sprint Window (Timestamped)
- Planned duration: 120 minutes
- Planned start: 2026-02-19 12:00 local
- Planned end: 2026-02-19 14:00 local
- Actual start: 2026-02-19 10:11:03 -05:00
- Actual end: _in progress_

## Goal Statement
Add a local pre-upload review workflow so users can inspect photos/videos in a folder, decide what to keep or remove locally, and apply subject labels before cloud upload.

## User Outcomes
1. I can review local media before uploading.
2. I can quickly remove obvious throwaway photos from local storage.
3. I can mark files as keep/reject and upload only selected files.
4. I can assign subject labels before upload so search works later.
5. I can identify “short-term utility” images and avoid long-term retention.

## In Scope
- Local folder review mode:
  - load folder contents
  - show thumbnail strip/list
  - keyboard-friendly next/previous navigation
- Curation actions:
  - keep
  - reject
  - delete local file (with confirmation)
  - bulk-select and bulk action support where feasible
- Pre-upload labeling:
  - subject labels at file level
  - optional quick tags (for example: receipt, grocery, temporary)
- Upload integration:
  - upload only kept files
  - pass selected labels to existing upload flow

## Out of Scope (for this sprint)
- ML-based quality scoring
- Duplicate detection across entire historical library
- Complex retention automation policy engine

## Dependencies / Preflight
- Desktop client baseline launches successfully from VS Code task (`Desktop: Run App`).
- Backend upload + metadata endpoints remain reachable and unchanged for current auth model.
- Security remediation from prior incident remains in place:
  - secret-scanning alerts closed
  - bootstrap IAM policy changes applied for operational visibility
- Local test folder is selected and backed up before delete-flow testing.

## Safety Guardrails (Local Delete)
- No local delete action can execute without explicit confirmation.
- Provide per-file success/failure logging for local delete actions.
- Keep default behavior non-destructive until user marks files as rejected.
- Avoid automatic bulk delete on first implementation pass.

## Acceptance Criteria
- A user can review a folder and mark files keep/reject.
- A user can delete selected rejected files from local disk with confirmation.
- A user can upload only selected files.
- Labels assigned in review are searchable after upload.
- Workflow handles a burst set (for example 50+ photos) without confusion.

## 2-Hour Timebox Strategy
- 35 min: local review UI scaffold with thumbnail navigation.
- 30 min: keep/reject state model + filtering.
- 25 min: local delete action with guardrails.
- 20 min: pre-upload labels integrated with upload queue flow.
- 10 min: compile checks + focused smoke run.

## Definition of Done
- End-to-end demo: review folder, delete rejects, upload curated set with labels.
- No destructive action without explicit confirmation.
- Sprint closeout records any performance limitations.

## Execution Checkpoints
- Sprint started: 2026-02-19 10:11:03 -05:00.
- Checkpoint +30m: queue table curation column + keep/reject actions wired.
- Checkpoint +60m: curation filtering (`ALL`/`KEEP`/`REJECT`) and queue refresh behavior complete.
- Checkpoint +90m: guarded local delete for rejected files + upload KEEP-only gating complete.
- Sprint ended: _in progress_
