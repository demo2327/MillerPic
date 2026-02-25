# Desktop UX Specification Draft (Interview-Based)

## Purpose
Define a shippable desktop UX direction based on product-owner interview input, with clear scope for upcoming sprint planning.

## Product Positioning
- The desktop app should be **simple and minimal**, not a single dense control panel.
- Primary value should center on **sync visibility/control**, with clear separation of tasks by screen.
- The app should support **local curation before upload** so users can reduce photo volume and improve quality.

## Top-Level Information Architecture (V1)
Use first-class navigation (tabs or equivalent top-level screens):
1. **Sync**
2. **Library**
3. **Curation**
4. **Settings**

No single all-in-one screen for all workflows.

---

## Screen Requirements

## 1) Sync Screen (Primary)
### Goal
Give users immediate confidence in what folders are configured and whether sync is healthy.

### Must-Have Content
- Configured sync folders list
- Per-folder state: healthy / error / paused
- Queue health summary: queued / uploading / failed counts
- Estimated time remaining for active sync activity

### Must-Have Actions
- Add/remove configured folder
- Start/pause/resume sync
- Retry failed items
- Drill into folder-level issues

### UX Constraints
- Status should be readable at a glance without opening logs.
- Errors should map to actionable controls (retry, open folder, re-auth, etc.).

---

## 2) Library Screen (Cloud)
### Goal
Manage cloud photos/albums/labels with clear context.

### Must-Have Content
- Photo list/grid with preview
- Album context indicator (when viewing an album)
- Search and label visibility

### Must-Have Interactions
- Right-click context menu in **Show All** mode:
  - Manage Labels
  - Add to Album
- Right-click context menu in **Album View** mode:
  - Manage Labels
  - Add to Album
  - Remove from Current Album

### Label Editing Pattern
- Default UX: **Hybrid chips + typeahead add**
  - Suggested labels as chips/checkmarks
  - Typeahead/manual add for custom labels

### UX Constraints
- Current context (all photos vs specific album) must always be obvious.
- Avoid duplicated label actions in multiple confusing places.

---

## 3) Curation Screen (Local)
### Goal
Help users reduce noisy photo sets before upload.

### Must-Have Tools (MVP)
- Duplicate/similar burst grouping
- Side-by-side compare picks
- Basic rotate operations
- Bulk apply labels

### Workflow Intent
- Review local folders
- Pick best shots from bursts
- Apply labels in bulk
- Send curated set to upload queue

### UX Constraints
- Fast review flow, minimal context switching.
- Favor visual decision workflows over metadata-heavy forms.

---

## 4) Settings Screen
### Goal
Keep operational and auth configuration out of core workflows.

### Must-Have Content
- API endpoint and auth/session controls
- App preferences relevant to sync/curation defaults
- Diagnostic toggle(s) and version/build info

---

## Non-Goals for MVP
- Dense dashboard with all controls visible simultaneously
- Advanced photo editing beyond rotation
- Heavy analytics/metrics-first home screen

---

## MVP Acceptance Criteria
1. User can open app and immediately understand sync health and folder configuration state.
2. User can navigate between Sync, Library, Curation, Settings without mixed-context confusion.
3. User can manage labels and add/remove album membership via context-appropriate flows.
4. User can curate local bursts (compare/select/rotate/label) before upload.
5. Core workflows are usable without requiring the output log panel for routine actions.

---

## Implementation Notes for Planning
- Treat this as a UX restructuring initiative, not just incremental button additions.
- Plan should prioritize:
  1. Navigation/frame refactor (tabbed screens)
  2. Sync screen redesign and state model
  3. Library context clarity + unified label UX
  4. Curation MVP tools

---

## Open Questions (for next interview pass)
1. Preferred default landing screen: Sync or Library?
2. Thumbnail-first vs metadata-first view in Curation?
3. Bulk action affordances: toolbar vs right-click vs keyboard-first?
4. Definition of “similar” for burst grouping (time-window only vs visual similarity)?
