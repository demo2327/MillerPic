# Dual-Tier Image Storage Strategy (Sprint 4 / A25)

## Objective
Store high-resolution originals in lower-cost storage while serving responsive preview images for day-to-day browsing.

## Decision Inputs (Locked)
- Previews should be comfortable for 4K display (not original-level fidelity).
- High-resolution original retrieval can be slow (hours acceptable).
- User experience target is responsive preview opening, not instant original retrieval.

## Recommended Architecture

## Object Classes
- **Original object** (`originals/...`)
  - Full resolution source image.
  - Lifecycle to low-cost tier for long-term archive.
  - Access path: direct presigned retrieval for explicit “download original” workflows.
- **Preview object** (`previews/...`)
  - 4K-friendly derivative (e.g., long edge bounded, modern codec).
  - Stored in fast-access class for normal gallery and open-image workflows.
  - Access path: default display/download URL in app UX.

## Data Model Additions
For each logical photo record:
- `OriginalObjectKey`
- `PreviewObjectKey`
- `PreviewWidth`
- `PreviewHeight`
- `PreviewContentType`
- `DerivationStatus` (`PENDING|READY|FAILED`)

## Lifecycle + Retrieval Assumptions
- Preview objects remain in fast-access storage.
- Original objects transition aggressively to cheaper storage classes after retention windows.
- Original retrieval SLA can be long; preview retrieval should remain responsive for typical use.

## Request Routing Policy
- Default UI path fetches preview URL.
- Explicit “download original” path requests original URL and surfaces potential delay.
- If preview is unavailable, fallback behavior:
  - show placeholder + regeneration request,
  - avoid blocking normal list operations.

## Cost Tradeoff Model

## Cost Increases
- Additional preview bytes stored.
- Additional write/compute cost for derivative generation.
- Extra metadata fields for preview descriptors.

## Cost Decreases / Avoided Cost
- Original bytes can be archived more aggressively without harming browsing UX.
- Reduced high-latency original retrieval pressure for routine viewing.
- Better control over user-perceived performance at lower long-term archive cost.

## Practical Cost Lens
Compare monthly:
- `preview_storage_gb` + `preview_get_requests`
- `original_storage_gb` + `original_retrieval_requests`

Optimization target: keep preview cost predictable while minimizing hot-storage burden of originals.

## Candidate Tiering Baseline
- Previews: S3 Standard or Intelligent-Tiering frequent access path.
- Originals: lifecycle toward lower-cost classes with long retrieval acceptance.

## Rollback-Safe Migration Plan
1. **Phase 1 (Additive):** introduce preview generation and metadata fields; keep current original path intact.
2. **Phase 2 (Read Preference):** switch UI/read path to prefer previews, keep original fallback.
3. **Phase 3 (Lifecycle Tightening):** apply more aggressive original lifecycle transitions after preview hit-rate confidence.
4. **Rollback:** revert read preference to original path and suspend lifecycle tightening; existing originals remain accessible.

## Validation Checklist
- Preview open experience remains responsive on representative client networks.
- Original download path still works with explicit latency expectations.
- Cost dashboard shows preview-vs-original split after rollout.
- No data loss risk during additive migration phases.
