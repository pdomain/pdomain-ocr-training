---
kind: handoff
status: "active"
created: "2026-08-21"
created_at: "2026-08-21T11:53:34Z"
owner: CT
branch: master
scope: fine-grained-typography-phase-one
worktree: /workspaces/pdomain/pdomain-ocr-training
base_commit: 8ddb146787573000072eddc75c99191daf5c6b82
supersedes: ""
---

# Fine-grained typography phase one handoff

## Goal

Begin the approved fine-grained typography implementation with the shared canonical contracts and lossless PGDP F2 parser in `pdomain-book-tools`. Do not begin model training, create `pdomain-source-data`, or modify the labeler SPA until the shared contract and parser gates pass.

## Done

- Completed and committed the source-backed typography research, system design, and cross-repository implementation plan in `pdomain-ocr-training` at commit `8ddb146`.
- Completed and committed the typography review, page-completion, contextual-evidence, event-store, and correction-export design in `pdomain-ocr-labeler-spa` at commit `96e8048`.
- Chose `pdomain-source-data` as the future shared data-preparation boundary for recognition, detection, typography, glyph forms, and page regions.
- Defined the PGDP, Project Gutenberg, and Standard Ebooks work and edition evidence graph.
- Defined field-level page-ground-truth fusion. The scan is authoritative for visible typography, human SPA corrections are authoritative after review, PGDP F2 is the strongest initial page-local formatting source, Gutenberg supplies final-text and post-processing evidence, and Standard Ebooks remains transformed weak evidence.
- Defined geometry-optional inbound labeling bundles. The SPA runs the existing recognition and page-region models, creates geometry, aligns source evidence, and returns immutable correction bundles.
- Chose the two-view target-word and short-line contextual model as the first production experiment. The word-only model remains the smallest baseline and missing-context fallback.
- Confirmed that no implementation code, model, source-data repository, font download, or deployment was created during design.

## Not done

- No `pdomain-book-tools` typography package exists yet.
- No canonical label, span, annotation, correction, source-evidence, or page-record types exist yet.
- No lossless F2 tokenizer, parser, source-offset map, note quarantine, project-rule resolver, or OCR alignment code exists yet.
- No release of the shared contract has been prepared or published.
- No `pdomain-source-data` repository exists.
- No SPA typography implementation plan has been written. Its approved design exists, but the Superpowers workflow still requires a task-level plan before SPA code changes.
- No training, synthetic generation, or inference implementation has started.

## Failed approaches

- A typography-only `pdomain-typography-data` repository was rejected. The shared preparation concerns belong in `pdomain-source-data`, with isolated task modules.
- Treating PGDP, Gutenberg, and Standard Ebooks as independent corpora was rejected. They require explicit work, edition, artifact, and derivation edges.
- Selecting one corpus as the page's single ground-truth authority was rejected. Ground truth must be fused per field and grapheme with retained evidence.
- Assuming source corpora provide OCR geometry was rejected. The labeler produces and reviews OCR geometry when it is absent.
- Extending the existing inclusive code-point `CharRange` contract was rejected. The approved SPA design replaces it with half-open Unicode grapheme spans and does not require legacy compatibility.
- Making the word-only model gate contextual training was rejected. It remains a baseline, ablation, and fallback.

## Decisions

- Page completion will require both corrected text and reviewed typography for every retained word.
- Every required launch label has an explicit positive, negative, or unknown state. Required unknown states block page completion.
- Whole-word labels are derived from full-coverage grapheme spans and cannot disagree with them.
- Drop caps remain structural context rather than general inline spans.
- Corrections are append-only and bind to stable word IDs, page content hashes, image hashes, corrected-text hashes, taxonomy versions, and grapheme-map versions.
- `pdomain-book-tools` owns canonical portable contracts and F2 parsing.
- `pdomain-ocr-labeler-spa` owns OCR execution for labeling bundles, geometry correction, typography review, page completion, durable correction history, and correction export.
- `pdomain-source-data` will own acquisition-manifest ingestion, cross-source matching, immutable bundles, correction import, audit, leakage-safe splits, materialization, and promotion. It will not crawl sources or run OCR.
- `pdomain-ocr-training` owns formatting datasets, the contextual model, losses, evaluation, calibration, and model export.
- `pdomain-ocr-synth` owns synthetic typography rendering under the shared contract.

## State

- `pdomain-ocr-training` is clean on `master` at `8ddb146`.
- `pdomain-ocr-labeler-spa` is clean on `master` at `96e8048`.
- `pdomain-book-tools` was clean when checked and was at `fb68660`.
- Both design repositories passed their commit hooks and Docgraph strict checks. Existing stale and advisory findings remain unrelated to this work.
- Nothing has been pushed in this session.

## Pointers

- Research: `docs/research/2026-08-21-fine-grained-typography-model-research.md`
- Canonical design: `docs/specs/2026-08-21-fine-grained-typography-model-design.md`
- Cross-repository implementation plan: `docs/plans/2026-08-21-fine-grained-typography-model.md`
- SPA design: `/workspaces/pdomain/pdomain-ocr-labeler-spa/docs/specs/2026-08-21-typography-review-and-training-export-design.md`
- First implementation repository: `/workspaces/pdomain/pdomain-book-tools`
- Live PGDP corpus: `/workspaces/pdomain-data/pgdp-corpus`
- Gutenberg corpus: `/workspaces/gutenberg-corpus`
- Standard Ebooks corpus: `/workspaces/standardebooks-corpus`

## Resume steps

1. Read `/workspaces/pdomain/pdomain-book-tools/AGENTS.md`, `CONVENTIONS.md`, `DOCGRAPH.md`, `docs/context/current-state.md`, and `docs/context/intent-map.md` before any edit.
2. Read Tasks 1 through 5A in `docs/plans/2026-08-21-fine-grained-typography-model.md`. Treat the plan as the execution authority.
3. Confirm all involved working trees are clean and check for active handoffs or in-flight branches in `pdomain-book-tools`.
4. Use the Superpowers worktree workflow to create an isolated `pdomain-book-tools` implementation worktree.
5. Start Task 1 with test-driven development. Add canonical labels and overlapping half-open grapheme-span types only.
6. Run the focused tests and the repository's required Python gate before the Task 1 checkpoint.
7. Continue Tasks 2 through 5 only in dependency order: provenance-rich records, lossless F2 tokenizer, resolved spans and project rules, then alignment to available local OCR geometry. Geometry returned through labeler bundles belongs to Task 9A and is not a dependency for this phase.
8. Stop before Task 5A publication. Publishing the shared contract requires explicit approval of the exact version and destination.
9. Do not create `pdomain-source-data` until the shared contract has passed CI and an immutable release has been approved.
10. After the shared contract phase, write and obtain approval for the separate SPA task-level implementation plan before changing SPA code.

## First checkpoint acceptance

Task 1 is ready for review only when:

- Unicode extended grapheme boundaries use one versioned implementation;
- spans use validated half-open `[start, end)` indices;
- overlapping and multi-label spans remain independent;
- label states preserve positive, negative, unknown, and conflict without inferring negatives from absence;
- serialization round-trips byte-stably under the approved canonical form;
- the new public imports remain Torch-free;
- focused tests, Ruff, basedpyright, and the repository's required CI gate pass;
- no unrelated working-tree changes are included.

Task 2 adds the annotation-level rule that whole-word labels derive from complete span coverage and cannot disagree with canonical spans.
