# Sprint Goals 10-12 (Outcome-First)

## Sprint 10 - Organize Cloud Files Like a Real Library
Design and ship a practical cloud file-management UX in the desktop client: view labels, edit labels, browse by label/folder grouping, preview thumbnails, and mark files for deletion from AWS.

Success signal: users can confidently manage cloud files without dropping to API-level tools.

## Sprint 11 - Curate Local Media Before Upload
Build a local review and cleanup workflow that lets users inspect folder images/videos, keep what matters, remove throwaways locally, apply subject labels, and then upload only curated files.

Success signal: users reduce upload noise and improve search quality with better labels.

## Sprint 12 - Remove Desktop Thumbnail Refresh Bottleneck
Improve desktop list refresh performance so thumbnails appear quickly during cloud-library curation, with concurrent loading and in-session thumbnail caching.

Success signal: list refresh is no longer painfully slow for typical image-heavy pages.

## Sequencing Logic
1. Sprint 10 improves cloud-side management and retrieval confidence.
2. Sprint 11 improves upstream data quality before upload.
3. Sprint 12 removes UI latency friction before process tooling migration.

## Guardrails to Keep 2-Hour Sprints Ambitious
- Minimum completion bar per sprint: at least 3 code deliverables plus validation.
- If planned tasks finish early, immediately pull from stretch backlog.
- Sprint cannot close before 90 minutes unless all stretch items are complete.
- Every closeout records planned vs actual by task.
- During development sprints, use test fixtures from `test_images` and end each sprint by clearing cloud test media so final validation starts from zero files.
