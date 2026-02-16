# Sprint 4 Plan (Scale + Cost Optimization)

## Goal
Scale the system for larger family libraries while reducing redundant storage and strengthening Terraform security posture.

## Scope
- Global content-hash deduplication across family users.
- High-scale desktop management view for large file sets.
- Dual-tier storage architecture for originals vs previews.
- Checkov implementation for Terraform static policy scanning in CI.

## Workstreams

### 1) Global Deduplication (Family-wide)
- Define canonical content hash strategy (e.g., SHA-256 over normalized bytes).
- Add dedupe lookup path before upload-init completion flow.
- Ensure duplicate detections reference existing object rather than re-uploading.
- Preserve folder labels and metadata references for all logical file entries.

### 2) Scalable Desktop Library View
- Improve list usability for large libraries (status triage, filtering, responsive updates).
- Keep queue/sync operations responsive while large tables are visible.
- Provide practical operator workflows for failures/skips/duplicates.

### 3) Dual-Tier Storage Strategy
- Keep originals in lowest-cost acceptable tier (slow retrieval acceptable).
- Generate/store 4K-friendly preview derivatives in fast-access tier.
- Define lifecycle and retrieval paths for preview-first UX.
- Document fallback behavior when preview is unavailable.

### 4) Terraform Security Scanning with Checkov
- Add Checkov config/profile for Terraform directories.
- Add CI step/job to run Checkov for infrastructure changes.
- Define baseline policy for pass/fail and approved suppressions.
- Document local and CI usage in deployment/security docs.

## Acceptance Criteria
- Duplicate images discovered across users upload once and are linked logically.
- Desktop management workflows remain responsive at multi-thousand-item scale.
- Preview opens are responsive for normal usage while originals may take longer to retrieve.
- Checkov runs in CI on Terraform changes and blocks high-severity policy violations.
- Any Checkov suppressions are explicit, justified, and documented.

## Out of Scope
- Full album collaboration feature set.
- AI-based image classification.
- Reworking all Terraform modules beyond policy-driven changes.

## Risks
- False-positive or noisy Checkov policies may initially slow merges.
- Global dedupe requires careful ownership/reference integrity to avoid data mix-ups.
- Preview generation/storage can increase request cost if derivative policy is oversized.

## Suggested Implementation Order
1. Checkov CI integration and baseline policy.
2. Global dedupe core design + backend data model updates.
3. Desktop scale-management view improvements.
4. Preview/original dual-tier implementation and benchmark pass.

## Validation Plan
- Run compile/tests + Terraform fmt/validate + Checkov checks in CI.
- Load-test dedupe and desktop list responsiveness on representative file sets.
- Compare monthly cost metrics before/after Sprint 4 rollout.
