# Cloud Agent Backlog

## Goal

Use cloud agents to accelerate delivery while keeping scope small, testable, and merge-safe.

## Operating Model

- One focused outcome per agent branch.
- Keep PRs small (about 3-8 files when possible).
- Require acceptance criteria in every task brief.
- Merge in dependency order (P0 first).
- Avoid overlapping edits to same files across concurrent agents.

## Branch/PR Convention

- Branch: `agent/<area>-<short-task-name>`
- PR title: `feat(<area>): <summary>` or `chore(<area>): <summary>`
- PR body must include:
  - summary
  - acceptance checklist
  - risk/rollback
  - test evidence

## Priority Roadmap

## Sprint Status

- Sprint 1: Complete (issues #11, #12, #14, #26 closed)
- Sprint 2: Ready to start (#13, #15, #16 open)
- Closeout report: `docs/SPRINT_1_CLOSEOUT.md`

### P0 (Do first)

1. Upload finalize flow (`upload-complete`) + pending/active states
2. Soft delete + trash review + hard delete endpoint
3. Metadata patch with `subjects` support
4. Users and Albums table provisioning in Terraform

### P1 (After P0)

5. `GET /photos/{photoId}` metadata endpoint
6. Basic search endpoint (filename + subjects)
7. Desktop app: folder upload queue (init/upload/complete per file)

### P2 (Later)

8. Album endpoints (create/list/add/remove photo)
9. SharedLinks table + sharing endpoints (deferred by decision)
10. Desktop quality pass (progress UI, retries, better error UX)

## Dependency Graph

- Task 1 is prerequisite for tasks 2, 3, and 7.
- Task 3 is prerequisite for task 6.
- Task 4 is prerequisite for task 8.
- Task 8 is prerequisite for task 9.

---

## Agent Task Briefs (Copy/Paste)

## Task A1 — Upload finalize flow

**Title**: Implement pending upload + `POST /photos/upload-complete`

**Objective**:
- Change upload lifecycle so metadata is pending at upload-init and active only after explicit completion.

**Scope**:
- backend handlers for upload-init and upload-complete
- list behavior to return only active photos by default
- Terraform route/integration/permission for new endpoint

**Requirements**:
- `POST /photos/upload-url` writes status `PENDING`
- `POST /photos/upload-complete` validates object exists in S3, then marks `ACTIVE`
- Return simple JSON responses (existing style)
- Backward compatibility for existing ACTIVE rows

**Acceptance criteria**:
- Upload-init returns 200 and creates pending row
- Upload-complete returns 200 and row transitions to active
- List endpoint excludes pending rows by default
- Compile checks and terraform validate pass

**Non-goals**:
- Multipart uploads
- Thumbnail generation

---

## Task A2 — Soft delete + trash + hard delete

**Title**: Add soft delete lifecycle with trash review and permanent delete

**Objective**:
- Introduce safe deletion with recovery window and explicit hard delete endpoint.

**Scope**:
- `DELETE /photos/{photoId}` => soft delete
- `GET /photos/trash` => list deleted rows
- `DELETE /photos/{photoId}/hard` => permanent delete (metadata + S3 object)

**Requirements**:
- Soft delete fields: `DeletedAt`, `DeletedBy`, `RetentionUntil`
- Default retention: 60 days
- Normal list excludes deleted rows
- Hard delete requires photo to be in deleted state

**Acceptance criteria**:
- Soft deleted rows appear in trash endpoint
- Normal list excludes soft deleted rows
- Hard delete removes row and object (or returns clear not-found semantics)

**Non-goals**:
- Restore endpoint (can be follow-up)

---

## Task A3 — Metadata patch with subjects

**Title**: Add metadata update endpoint with `subjects`

**Objective**:
- Support user-friendly searchable metadata field named `subjects`.

**Scope**:
- `PATCH /photos/{photoId}`
- Accept fields: `fileName`, `description`, `subjects`, `takenAt`

**Requirements**:
- `subjects` is flat string list
- sanitize/normalize: trim, dedupe, max reasonable count
- authorization uses JWT `sub` ownership

**Acceptance criteria**:
- Patch updates only allowed fields
- Invalid payload returns 400 with simple JSON error
- List response includes updated fields where relevant

**Non-goals**:
- NLP tagging
- typed subject taxonomy

---

## Task A4 — Users and Albums Terraform tables

**Title**: Provision Users and Albums DynamoDB tables

**Objective**:
- Add minimal table infrastructure to support upcoming album features.

**Scope**:
- Terraform only (no sharing table yet)
- `Users` table keyed by UserId (Google sub)
- `Albums` table keyed by UserId + AlbumId

**Requirements**:
- on-demand billing
- PITR enabled
- sensible tags and naming conventions

**Acceptance criteria**:
- `terraform validate` passes
- `terraform plan` shows only intended resources
- outputs updated if needed

**Non-goals**:
- Album endpoints
- Shared links resources

---

## Task A5 — Get photo detail endpoint

**Title**: Add `GET /photos/{photoId}` metadata endpoint

**Objective**:
- Return full metadata for one photo record owned by current user.

**Scope**:
- backend handler + API route + Terraform wiring

**Acceptance criteria**:
- 200 for owned photo
- 404 for missing photo
- 401/403 behavior consistent with current auth checks

---

## Task A6 — Basic search endpoint

**Title**: Add search by `fileName` and `subjects`

**Objective**:
- Provide initial search endpoint for desktop/web use.

**Scope**:
- `GET /photos/search?q=...`
- search across filename and subjects

**Acceptance criteria**:
- returns only ACTIVE, non-deleted photos
- basic pagination support

---

## Parallelization Plan

Safe to run in parallel:
- A4 (Terraform tables) in parallel with A1
- A5 can run after A1
- A3 and A2 can run after A1, but avoid editing same handler sections simultaneously

Suggested order:
1) A1
2) A2 + A3 + A4
3) A5
4) A6
5) Desktop folder upload and album features

## Handoff Checklist For Each Agent

- Pull latest main
- Create task branch
- Implement only assigned scope
- Run local checks
- Open PR with acceptance evidence
- Link follow-up issues for out-of-scope findings
