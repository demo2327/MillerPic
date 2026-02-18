# Sprint 11 Kickoff Checklist (Tomorrow Start)

## Goal
Start Sprint 11 with a clean, low-risk execution path for local media review + curation before upload.

## 15-Minute Startup Sequence
1. Confirm repo state.
   - `git status --short`
   - Expected: clean working tree on `sprint11-kickoff`.
2. Run baseline validations before changes.
   - `pytest backend/tests -q`
   - `terraform -chdir=infrastructure fmt -check -recursive`
3. Launch desktop client for baseline behavior snapshot.
   - VS Code Task: `Desktop: Run App`
4. Review Sprint 11 scope and acceptance criteria.
   - `docs/SPRINT_11_PLAN.md`

## Sprint 11 Day-1 Build Order
1. Add local review state model in desktop client.
   - keep/reject flags per file
   - deterministic selection state
2. Add local media review panel UX.
   - next/previous navigation
   - clear selected file context
3. Add guarded local delete action.
   - explicit confirmation dialog
   - success/failure logs per file
4. Wire pre-upload labels into existing queue path.
   - include labels in upload payload
   - verify labels are searchable post-upload

## Day-1 Validation Targets
- No startup crashes in desktop app.
- Keep/reject toggles persist during session.
- Local delete cannot run without confirmation.
- Upload flow still succeeds for curated subset.

## End-of-Day Exit Criteria
- At least one end-to-end demo path works:
  - load folder -> mark keep/reject -> delete rejects locally -> upload curated files with labels
- Compile checks pass.
- Sprint notes updated with known carryover.

## Notes
- Keep Sprint 11 PR scope code-focused; avoid unrelated doc churn in the same branch.
- If time is short, prioritize safe local delete guardrails over visual polish.