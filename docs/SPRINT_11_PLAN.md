# Sprint 11 Plan - Local Review + Curation Before Upload

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
