# Sprint 14 Plan - Desktop UX Restructure (Sync-First)

## Goal Statement
Restructure the desktop app into a simple, shippable user experience centered on sync visibility, clear task separation, and practical local curation before upload.

## Product Direction Inputs
Source: `docs/DESKTOP_UX_SPEC_DRAFT.md` (interview-based requirements).

Core direction:
- Minimize complexity on each screen.
- Stop mixing unrelated workflows on one page.
- Make sync state understandable at a glance.
- Improve library/album label clarity.
- Add local curation tools that reduce noisy uploads.

## User Outcomes
1. I can immediately see if configured folders are healthy and syncing.
2. I can switch between Sync, Library, Curation, and Settings without context confusion.
3. I can manage labels and album actions from consistent, context-aware menus.
4. I can curate local photo bursts (compare/select/rotate/label) before upload.

## In Scope
- App shell/navigation restructure:
  - top-level tabs/screens: Sync, Library, Curation, Settings
  - remove all-in-one screen dependence
- Sync screen MVP:
  - configured folders and per-folder state
  - queue summary (queued/uploading/failed)
  - ETA and retry/action affordances
- Library UX refinement:
  - explicit context indicator (all photos vs current album)
  - right-click action model consistency
  - hybrid label editing UX (chips/check + typeahead add)
- Curation MVP tools:
  - burst/similar grouping scaffold
  - side-by-side selection compare
  - basic rotate operations
  - bulk label apply

## Out of Scope (for this sprint)
- Share-link feature set (`#20`, `#21`, `#22`)
- Abuse-drill/cost governance issues (`#24`, `#25`, `#64`)
- Advanced image editing beyond rotation
- Heavy metrics/dashboard overlays

## Issue Mapping (Sprint 14)
1. D14-1 Desktop shell split into Sync/Library/Curation/Settings tabs.
2. D14-2 Sync screen redesign with folder health + queue status + ETA.
3. D14-3 Library context clarity + unified label/album interactions.
4. D14-4 Local curation MVP (group, compare, rotate, bulk-label).

Linked issues:
- #87 D14-1: Desktop shell split into Sync/Library/Curation/Settings
- #88 D14-2: Sync screen redesign (folder health + queue + ETA)
- #89 D14-3: Library UX clarity + unified label/album interactions
- #90 D14-4: Local curation MVP (group, compare, rotate, bulk-label)

## Acceptance Criteria
- Default app flow presents clear sync state without requiring log inspection.
- Task separation is visible and consistent across top-level screens.
- Library actions differ correctly by context (all photos vs album view).
- Label workflows are understandable and not duplicated across conflicting controls.
- Curation workflow supports practical best-pick reduction before upload.

## 2-Hour Timebox Strategy
- 25 min: shell/tab refactor and navigation state.
- 35 min: Sync screen UI/state + queue health wiring.
- 35 min: Library context + unified label/album menu interactions.
- 20 min: Curation MVP scaffolding (group/compare/rotate/bulk-label entry points).
- 5 min: test pass + sprint issue linkage updates.

## Definition of Done
- Sprint 14 issue set is created and linked to this plan.
- New desktop UX architecture is implemented behind the top-level screens.
- MVP acceptance criteria are met and validated in desktop smoke checks.
- Sprint 14 closeout can point to concrete user-visible UX improvements, not only backend changes.
