# Desktop App Testability Plan

## Objective
Make `desktop-client/app.py` testable in automation so Copilot can run repeatable validation without manual GUI interaction.

## Why It Is Hard Today
- Tkinter UI and network calls are tightly coupled in one class.
- Most behavior is triggered via button handlers and background threads.
- Thumbnail loading depends on live HTTP + signed URLs.

## Target Testability Architecture (Minimal)
1. Extract non-UI logic into plain Python services:
   - queue curation rules (`KEEP`/`REJECT`, upload eligibility)
   - thumbnail hydration policy (candidate selection, cache usage)
   - API client wrapper (`list`, `search`, `download-url`, upload endpoints)
2. Keep Tkinter layer as a thin adapter:
   - binds events and renders widgets
   - delegates business decisions to services
3. Inject dependencies:
   - HTTP session/client
   - clock/time provider
   - filesystem adapter (for local delete behavior)

## Phase Plan
### Phase 1: Fast Win (recommended first)
- Add focused unit tests for pure functions/classes extracted from queue + thumbnail logic.
- Use `pytest` with fakes/mocks for HTTP and filesystem.
- Keep UI unchanged.

### Phase 2: Integration Confidence
- Add headless integration tests for service layer + state transitions.
- Validate scenarios:
  - mark keep/reject and filter behavior
  - upload KEEP-only gating
  - rejected local delete confirmations and outcomes
  - thumbnail cache hit/miss behavior across refreshes

### Phase 3: UI Smoke (optional)
- Add a very small manual smoke checklist for Tkinter widget wiring.
- Optionally use a UI automation tool later, but not required for core correctness.

## Tooling
- Test runner: `pytest`
- Mocking: built-in `unittest.mock` (or `pytest-mock` if desired)
- HTTP mocking: monkeypatch `requests` or use a fake API client object
- No browser/desktop automation dependency required for initial value

## Definition of Testable
- Core curation + thumbnail performance behavior is validated by deterministic tests.
- At least one test suite can be run by Copilot without manual interaction.
- Manual GUI checks become lightweight confirmation rather than primary validation.

## Proposed First Deliverable
Create `desktop-client/tests/test_queue_curation.py` and `desktop-client/tests/test_thumbnail_hydration.py` against newly extracted service classes.
