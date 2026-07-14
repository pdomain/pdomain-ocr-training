---
Status: active
Owner: CT
Created: 2026-07-14
Last verified: 2026-07-14
---

# Durable decisions

## Agent Index

- **Status:** active
- **Last verified:** 2026-07-14
- **Read when:** investigating changed direction, retired documents, or durable rationale.
- **Search terms:** decisions, implementation deviations, tombstones, retirement.

### 2026-07-14 — Preserve shipped evaluation deviations in current architecture

- **Context:** The completed backend plan projected a single-threshold IoU
  approximation and reuse of `detect.evaluate()`.
- **Decision:** Keep the shipped private lazy backend and its dedicated
  detection loop with a true 0.50–0.95 COCO threshold sweep as current truth in
  [`docs/architecture/00-overview.md`](../architecture/00-overview.md).
- **Rationale:** The implementation improved metric fidelity without changing
  the torch-free boundary or synchronous runner contract.
- **Evidence:** Commit `5960fc9`; `pdomain_ocr_training/_eval_backend.py`;
  `tests/test_eval_backend.py`; `tests/test_eval_backend_wiring.py`.
- **Remaining work:** Optional real-dataset GPU smoke testing remains deferred
  in [`intent-map.md`](intent-map.md).

### 2026-07-14 — Implementation verified: Real DocTR eval backend plan

- **Old path:** `docs/archive/plans/2026-05-22-doctr-eval-backend.md`
- **Outcome:** Implementation verified; deletion is pending the doc-retirer gate.
- **Superseded by:** [`docs/architecture/00-overview.md`](../architecture/00-overview.md)
- **Removal commit:** Pending the doc-retirer gate.
- **Rationale kept:** This file's preceding deviation decision and the current
  architecture preserve the durable design.
- **Remaining work:** Optional GPU smoke testing is deferred in
  [`intent-map.md`](intent-map.md).

### 2026-07-14 — Implementation verified: Glyph-feature eval slicing design

- **Old path:** `docs/specs/2026-05-22-glyph-feature-eval-slicing-design.md`
- **Outcome:** Implementation verified; deletion is pending the doc-retirer gate.
- **Superseded by:** [`docs/architecture/00-overview.md`](../architecture/00-overview.md)
- **Removal commit:** Pending the doc-retirer gate.
- **Rationale kept:** The architecture preserves the serialized dependency
  boundary, basename crop-id join, and slice semantics.
- **Remaining work:** Sidecar-writer ownership remains a needs-owner-decision
  item in [`intent-map.md`](intent-map.md).
