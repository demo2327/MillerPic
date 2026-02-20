# Sprint 13 Closeout - Label-Defined Albums + Upload Date Labels (Closed)

## Window
- Planned duration: 120 minutes
- Actual execution: split across Sprint 13 delivery sessions
- Status: closed
- Closeout date: 2026-02-20

## Scope Completed
1. Label-defined album backend model (single organization primitive).
   - Implemented album rule endpoints:
     - `POST /albums`
     - `GET /albums`
     - `GET /albums/{albumId}/photos` (derived by label intersection)
     - `POST /albums/{albumId}/photos/{photoId}/apply-labels`
     - `POST /albums/{albumId}/photos/{photoId}/remove-labels`
   - Added shared handler utilities for auth and label normalization.

2. Desktop album user workflow shipped.
   - Create/list/view/show-all album flows.
   - Context-aware right-click actions:
     - `Manage Labels...`
     - `Add to Album...`
     - `Remove from Current Album...` (album view only)
   - Checkbox-based label management UX.
   - Album delete action and album selection clarity improvements.

3. Upload metadata enrichment delivered (Issue #84).
   - Added server-side image date extraction in `upload_complete`.
   - Normalized extracted value to `date:YYYY-MM-DD`.
   - Merged date label into `Subjects` with case-insensitive dedupe.

4. Deployment readiness hardening for albums.
   - Updated Lambda artifact signing script to include album handlers.
   - Included shared `albums_common` module in album artifact packaging.

## Validation Evidence
- Backend handler tests:
  - `pytest backend/tests/test_albums.py backend/tests/test_upload.py backend/tests/test_search.py -q` => `13 passed` (album/API tranche)
- Upload metadata tests:
  - `pytest backend/tests/test_upload.py -q` => `7 passed` (date-label extraction coverage)
- Compile checks:
  - `python -m py_compile backend/src/handlers/upload.py backend/src/handlers/download.py backend/src/handlers/list.py desktop-client/app.py`
- Terraform formatting check:
  - `terraform -chdir=infrastructure fmt -check -recursive`

## Issue / PR Traceability
- Issues closed:
  - #17
  - #18
  - #19
  - #83
  - #84
- PRs merged:
  - #85 Sprint 13: label-defined album APIs, desktop album UX, docs/infrastructure wiring
  - #86 Issue #84: upload metadata date-label extraction

## Acceptance Criteria Mapping
- Album definitions persist as label rules: met.
- Album photo listing derived from current labels: met.
- Add-to-album adds missing labels only: met.
- Remove-from-album supports user-selected label removal: met.
- Upload adds normalized metadata date label when available: met.
- Tests and docs aligned to delivered semantics: met.

## Known Risks / Carryover
1. Live AWS apply for album routes remains blocked by deploy IAM permissions (`kms:TagResource`, `ec2:CreateSecurityGroup`) in the current deployment principal.
2. Desktop local fallback mode is in place so users can continue album workflows until IAM/deploy permissions are resolved.

Exit criteria met on 2026-02-20.
