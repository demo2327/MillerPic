# Sprint 12 Plan - Desktop Thumbnail Performance

## Goal Statement
Reduce list-refresh latency in the desktop client so thumbnail-heavy pages become responsive enough for daily use.

## Priority Order
1. Desktop testability fast-win (extract pure thumbnail hydration logic + add automated tests).
2. Runtime performance improvements (concurrency, cache reuse, timeout caps).
3. UI stability and validation evidence.

## User Outcomes
1. Photo list refresh feels fast enough to use repeatedly during curation.
2. Thumbnails appear progressively instead of stalling on long sequential fetches.
3. Repeated refreshes of the same data are significantly faster due to caching.
4. UX remains stable without changing the existing list/label workflow.

## In Scope
- Desktop testability fast-win (Priority 1):
  - extract pure thumbnail hydration candidate logic from Tkinter event flow
  - add automated tests for candidate selection and cache-hit behavior
  - keep UI wiring thin while preserving current behavior
- Desktop thumbnail hydration optimization:
  - concurrent thumbnail fetch pipeline
  - in-memory session cache keyed by `photoId`
  - fetch attempt and timeout caps to avoid long-tail stalls
- List refresh UX consistency:
  - retain current table/grouping/label-edit behavior
  - preserve selected-item thumbnail preview flow
- Validation and evidence:
  - compile diagnostics for desktop app
  - observed before/after behavior notes for refresh responsiveness

## Out of Scope (for this sprint)
- Jira/Confluence workspace provisioning and templates
- Backend data model changes or new APIs
- Full end-to-end desktop GUI automation harness

## Acceptance Criteria
- Priority 1 extraction + tests are implemented and runnable by Copilot.
- List thumbnail hydration no longer runs strictly sequentially.
- Repeated list refreshes reuse session cache when photo IDs are unchanged.
- Desktop app compiles cleanly after changes.
- Existing list/label interaction flow remains unchanged for users.

## 2-Hour Timebox Strategy
- 30 min: identify thumbnail hydration bottleneck and define constraints.
- 40 min: implement concurrent fetch + cache path.
- 25 min: verify UI behavior and add status improvements.
- 15 min: compile checks + closeout notes.
- 10 min: issue/PR traceability updates.

## Constraints Note
Network RTT and signed-URL generation still affect first-load latency; optimization focuses on reducing avoidable client-side serial delay.

## Definition of Done
- Desktop list thumbnails load concurrently with visible progressive improvement.
- Cache reuse is active during the current app session.
- Compile validation passes and closeout evidence is documented.
