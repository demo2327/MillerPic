# Sprint 14 Closeout - Desktop UX Restructure (Closed)

## Window
- Planned duration: 120 minutes
- Actual execution: completed in focused implementation session
- Status: closed
- Closeout date: 2026-02-25

## Scope Completed
1. Desktop shell restructure to top-level screens.
   - Added first-class tabs: **Sync**, **Library**, **Curation**, **Settings**.
   - Removed all-in-one workflow dependence by grouping controls into task-focused screens.

2. Sync screen redesign (at-a-glance status).
   - Added sync overview with:
     - sync status text
     - queue health counts (queued/uploading/failed/completed)
     - ETA estimation while uploads are active
   - Enhanced managed folder table with per-folder columns:
     - state
     - last sync timestamp
     - error detail
   - Persisted folder sync state in desktop local state.

3. Library workflow continuity under new shell.
   - Kept album, search, and cloud photo workflows functional in Library tab.
   - Preserved context-aware right-click album/label interactions from Sprint 13.

4. Local curation MVP screen.
   - Added Curation tab with:
     - folder scan of local media
     - burst/similar grouping scaffold
     - KEEP/REJECT decision actions
     - bulk label application
     - side-by-side compare for two selected items
     - rotate left/right for selected images
     - queue selected KEEP items into upload queue

## Validation Evidence
- Compile checks:
  - `python -m py_compile backend/src/handlers/upload.py backend/src/handlers/download.py backend/src/handlers/list.py desktop-client/app.py`
- Desktop diagnostics:
  - no errors reported for `desktop-client/app.py`

## Issue / PR Traceability
- Sprint 14 implementation issues:
  - #87 D14-1: Desktop shell split into Sync/Library/Curation/Settings
  - #88 D14-2: Sync screen redesign (folder health + queue + ETA)
  - #89 D14-3: Library UX clarity + unified label/album interactions
  - #90 D14-4: Local curation MVP (group, compare, rotate, bulk-label)

## Acceptance Criteria Mapping
- Sync health visible without log dependency: met.
- Task separation across top-level screens: met.
- Library context and label/album interactions preserved in dedicated screen: met.
- Curation MVP tools available pre-upload: met.

## Known Risks / Carryover
1. Curation grouping currently uses filename/time heuristics (scaffold) and is not full visual similarity detection.
2. ETA is estimate-based from in-session observed upload durations.
3. Deeper UX polish pass (layout density, keyboard shortcuts, visual refinements) can continue in Sprint 15.

Exit criteria met on 2026-02-25.
