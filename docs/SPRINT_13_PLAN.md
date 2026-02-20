# Sprint 13 Plan - Label-Defined Albums (Single Organization Model)

## Goal Statement
Deliver Album UX without introducing a second organizational primitive by defining albums as saved label rules.

## Product Rule (Canonical)
- Labels are the only backend organization primitive.
- An album is a saved rule: `requiredLabels` (AND match), for example `Bob + 2026`.
- Album membership is derived at read time from photo labels.

## User Experience Outcomes
1. I can create an album by defining one or more labels.
2. Album views automatically show photos that match the album labels.
3. Using “add to album” on a photo adds any missing album labels to that photo.
4. Using “remove from album” on a photo asks which album labels should be removed from that photo.
5. Photos automatically receive a date label from image metadata at upload time when available.

## Issue Mapping (Primary)
1. #17 A11: Album create/list endpoints (reframed as album rule definitions).
2. #18 A12: Add/remove photo behavior (reframed as label add/remove operations based on album rule).
3. #19 A13: Tests + OpenAPI/docs coverage for the new semantics.
4. #83 Sprint 13 pivot: albums are label-defined views.

## In Scope
- Album rule endpoints:
  - `POST /albums` (name + `requiredLabels`)
  - `GET /albums`
  - `GET /albums/{albumId}/photos` (derived by label intersection)
- Album action endpoints:
  - `POST /albums/{albumId}/photos/{photoId}/apply-labels` (add missing album labels)
  - `POST /albums/{albumId}/photos/{photoId}/remove-labels` (remove selected album labels)
- Validation semantics:
  - case-insensitive label normalization
  - dedupe label entries
  - ownership checks for album and photo
- Upload metadata enrichment:
  - extract photo-taken timestamp from image metadata during upload when present
  - add normalized date label (for example `date:2026-02-20`) to photo labels
  - do not duplicate existing date labels
- Tests and docs:
  - unit tests for derived membership and label mutation behavior
  - unit tests for upload metadata date-label extraction behavior
  - OpenAPI/docs aligned to final request/response payloads

## Out of Scope (for this sprint)
- Manual album membership table and dual membership sync logic.
- Share-links feature set (`#20`, `#21`, `#22`).
- Abuse-drill/cost governance work (`#24`, `#25`, `#64`).
- Jira/Confluence workspace provisioning.

## Acceptance Criteria
- Album definitions persist as label rules (not explicit photo membership rows).
- Album photo listing is derived from current photo labels and updates automatically.
- “Add to album” adds only missing album labels to selected photo.
- “Remove from album” supports user-selected removal of album labels from selected photo.
- Upload flow adds a normalized date label from image metadata when available.
- Backend tests pass and OpenAPI/docs match implemented semantics.

## 2-Hour Timebox Strategy
- 25 min: define album rule data model and endpoint contracts.
- 35 min: implement create/list/derived-photo listing handlers.
- 35 min: implement apply/remove label actions with validation.
- 15 min: upload metadata date-label extraction + unit tests.
- 10 min: OpenAPI/docs + issue/PR linkage.

## Definition of Done
- Issues `#17`, `#18`, `#19`, and `#83` closed by merged PR(s) under label-defined semantics.
- No separate backend organizational model beyond labels.
- Upload process enriches labels with normalized metadata-based date when available.
- Tests/compile checks pass and docs reflect user-facing workflow.
