# Sprint 10 Plan - Cloud File Organization UX

## Sprint Window (Timestamped)
- Planned duration: 120 minutes
- Planned start: 2026-02-18 12:00 local
- Planned end: 2026-02-18 14:00 local
- Actual start: 2026-02-18 12:08:39 -05:00
- Actual end: 2026-02-18 18:30:00 -05:00 (recovery closeout draft)

## Goal Statement
Deliver a usable cloud file-management experience in the desktop app so users can view labels, edit labels, browse files by label/folder, preview thumbnails, and mark files for deletion from AWS.

## User Outcomes
1. I can see how each cloud file is labeled.
2. I can edit labels for one file or multiple files.
3. I can browse cloud files grouped by label/folder-style collections.
4. I can see thumbnails in list/browse views.
5. I can mark files for deletion from AWS from inside the list view.
6. Thumbnails load quickly because they are generated at upload time and stored in cloud storage.

## In Scope
- Cloud library view with grouping modes:
  - Group by label/subject
  - Group by logical folder bucket (based on object path prefix)
- File row/card metadata:
  - filename
  - labels/subjects
  - created date
  - deletion status
- Label editing UX:
  - add label
  - remove label
  - save with optimistic feedback
- Thumbnail support:
  - generate thumbnails during upload processing
  - store thumbnails in cloud storage for fast retrieval and lower bandwidth
  - request/display thumbnail URLs in list and grouped views
  - fallback placeholder if thumbnail unavailable
- Deletion workflow:
  - select one or many items
  - mark for deletion (trash flow if backend supports it)
  - clear status feedback in UI and logs

## Out of Scope (for this sprint)
- Full visual redesign/theme overhaul
- AI auto-labeling
- Full restore/versioning UI unless backend already exposes it

## Acceptance Criteria
- A user can list cloud files and visually inspect labels in one screen.
- A user can update labels and see updated values on refresh.
- A user can switch between grouped views and find files faster.
- Thumbnails render from cloud-stored thumbnail assets for uploaded image files.
- A user can mark selected cloud files for deletion and see success/failure results.
- End-of-sprint cleanup resets cloud test media to empty before final validation cycle.

## 2-Hour Timebox Strategy
- 30 min: UX scaffolding for grouped cloud file view.
- 35 min: label read/edit operations and validation feedback.
- 25 min: thumbnail rendering and fallback handling.
- 20 min: deletion action from list + result feedback.
- 10 min: compile/smoke validation.

## Development Data Policy
- Use assets from `test_images` for development and validation runs.
- End each sprint with cloud media cleanup so the next sprint starts from an empty cloud library.
- Run final end-of-sprint verification from a clean cloud state (no residual prior-test media).

## Sprint End Cleanup Runbook
1. Capture baseline counts before cleanup.
  - List cloud photos and record count in sprint closeout.
2. Delete cloud media test set.
  - If desktop delete/trash is available, perform bulk-select delete from app UI.
  - If not yet available, run API delete/trash calls for all listed photo IDs.
3. Verify empty cloud state.
  - Re-run list call and confirm `count = 0` (or empty photos array).
4. Re-seed only if needed for immediate validation.
  - Upload selected fixtures from `test_images`.
5. End sprint clean.
  - If no immediate follow-up validation is planned, repeat cleanup and confirm zero files.
6. Record evidence in closeout.
  - Note pre-clean count, post-clean count, method used (UI/API), and any failures.

## Dependencies
- Backend endpoints for list/search/patch labels/trash-delete must be reachable.
- Upload pipeline must support thumbnail generation + cloud storage write on upload.
- Thumbnail URL/read path must be exposed by existing APIs or metadata response fields.

## Definition of Done
- Feature is demoable end-to-end for at least 5 cloud files with mixed labels.
- No blocker-level errors in desktop compile checks.
- Sprint closeout includes known limitations and carryover.

## Execution Checkpoints
- 2026-02-18 12:08:39 -05:00: Sprint started.
- 2026-02-18 12:31:36 -05:00: Completed slices:
  - cloud list grouping (`none`/`label`/`folder`)
  - label view/edit for selected file via `PATCH /photos/{photoId}`
  - selected and bulk cloud delete actions in desktop client
  - thumbnail creation/storage path on upload (`thumbnailUploadUrl` + `ThumbnailKey`)
  - thumbnail metadata surfaced in list/search/get APIs and desktop preview wiring
- 2026-02-18 18:30:00 -05:00: Recovery audit completed; draft closeout recorded in `docs/SPRINT_10_CLOSEOUT.md`.
