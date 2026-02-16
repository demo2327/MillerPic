# Sprint 3 Plan (User Sync Foundation)

## Goal
Turn desktop uploads into a repeatable folder-sync workflow with metadata enrichment and clear operator UX.

## Scope
- Managed folders persist across app restarts.
- Sync job uploads only newly discovered image files from managed folders.
- Local deletes do not remove cloud copies.
- Video files are detected and skipped with explicit queue/output status.
- Output log becomes optional dialog (open on demand, not always visible).
- Metadata enrichment sends additional `subjects` tokens:
  - Date taken (when EXIF available)
  - Geolocation token(s) (when EXIF GPS available)
  - Folder hierarchy labels

## Acceptance Criteria
- User can add/remove managed folders and see them loaded after restart.
- Running sync twice without file changes produces no duplicate uploads.
- New files added under managed folders are uploaded on next sync.
- Removed local files are not deleted from AWS.
- Video files are not uploaded and appear as skipped in sync summary.
- Output dialog can be opened/closed without affecting sync execution.
- Subjects sent to backend include folder labels and available EXIF metadata.

## Out of Scope
- Backend hard-delete/reconcile behavior for local deletions.
- Full dedup across cloud objects by content hash (planned Sprint 4).
- AI image labeling.

## Risks
- EXIF parsing variability across file formats/devices.
- Privacy concerns for geolocation metadata if default behavior is not explicit.
- Folder scans may become slow on very large trees without indexing.

## Suggested Implementation Order
1. Managed folder persistence + sync command shell.
2. Video exclusion + sync summary model.
3. Output dialog refactor.
4. Metadata extraction and folder-label subject generation.
5. End-to-end regression pass on queue/sync interactions.
