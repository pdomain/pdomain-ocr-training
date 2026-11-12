---
Status: active
Owner: CT
Created: 2026-11-06
Last verified: 2026-11-12
Kind: process
---

# Roadmap

## Agent Index

- **Kind:** process
- **Status:** active
- **Last verified:** 2026-11-12
- **Read when:** choosing the next unfinished training or evaluation task.
- **Search terms:** roadmap, typography crops, formatting model, separate repository, dep-refresh.

Nothing here authorizes implementation. The sections below run in order.

Shipped detection, recognition, layout, and evaluation are in [Architecture: pdomain-ocr-training](architecture/00-overview.md). Who owns the surrounding code is in [Where training work lives](architecture/suite-boundaries.md). Decisions we are not ready to build are in the [intent map](context/intent-map.md).

The [phase-two plan](plans/2026-08-31-fine-grained-typography-phase-two.md) is the task checklist. The August 21 plan is historical.

## Already in place

- This package trains detection, recognition, and layout, and it evaluates detection and recognition. Glyph slices are read from a sidecar. They are not written here.
- `pdomain-book-contracts` 0.3.0 holds the typography types and the F2 reader. `pdomain-book-tools` re-exports them.
- `pdomain-source-data` can align supplied OCR words and project styles. `align_page` does not write pixel crops.
- `pdomain-pgdp-measure` measures scan geometry, alignment, typography, and glyphs without torch.
- `pdomain-ocr-synth` renders detection and recognition crops with HarfBuzz and FreeType. It does not yet render mixed-span formatting pages.
- The labeler writes the glyph sidecar. A recorded run of glyph slices on real data is still missing.

## Now: crops before the formatting model

Crop production comes before any formatting model.

1. In `pdomain-source-data`, connect geometry, pixel crops, and a leakage-safe split manifest. That work stays in source-data.

   Source-data does not depend on `pdomain-pgdp-measure` today. Its intent map already forbids a second scan-measurement library. Source-data should call `pdomain-pgdp-measure` for scan measurement instead of writing another measurer.

   Silver-tier geometry may come from unreviewed batch recognition. That geometry can train only the whole-word baseline. It never becomes gold.
2. Start the labeler exchange at the same time. The contextual grapheme model waits for reviewed geometry. The baseline does not.

## Next, in this package

1. Add a formatting path that does not change recognition training. The order inside that path is a torch-free `FormattingConfig`, then a whole-word baseline, then a contextual grapheme model with monotonic alignment. Calibration, abstention, and evaluation come after those.
2. Set the numeric quality, calibration, abstention, and latency gates after the crop step publishes counts. Those thresholds are not chosen yet.

   The Phase 4 population is separate. Mixed-style exact accuracy uses the 14,639 words whose style differs among their word characters. It reports the 3,999 letter-adjacent words separately. Those counts are parser-dependent. An independent audit counted 1,541 core-mixed words under a stricter rule. They are not release gates until acceptance fixtures exist.

## Later, and gated

1. In `pdomain-ocr-synth`, reuse the `pdomain-book-contracts` span types. Add the pinned font manifest and mixed-span renderer. Then measure whether synthetic pages help real scans.

   Start that work only if phase 2B shows a label whose real support is too thin to train. On current counts that is letter spacing, at nine positives, and possibly resolved font changes.

   Synthetic data passes only on immutable real-scan validation. Macro grapheme F1 must rise by at least 1.0 absolute point. Mixed-style exact-word accuracy must rise by at least 2.0. No common label may lose more than 1.0 F1 point. No audited stratum may lose more than 2.0. Calibration and abstention must not worsen after recalibration.

   The result must hold across at least three seeds or edition-group bootstrap resamples. It must also hold after evaluation words found in synthetic text are excluded.
2. Contextual stress tests and weak supervision, and shadow-inference integration, stay deferred. They were tasks 13 and 15 of the August 21 plan. They wait until the contextual model has a measured baseline and the offline acceptance gate has passed.

## Keep out of this package

- A second training stack for PP-OCRv5 or an HTR engine. Compare those in a new repository first. The comparison needs reproducible accuracy, runtime, model size, and license evidence. See [Where training work lives](architecture/suite-boundaries.md).
- A typeface or glyph classifier, until the owner confirms the scope. If it is built, it is a separate model package.
- Inference deployment. A provider protocol may enter `pdomain-book-tools`. The heavy torch implementation stays in a deployment package or an optional adapter. The owner still has to name the packager and the hardware targets.
- F2 parsing, span types, corpus matching, scan measurement, and the glyph sidecar writer. Those owners are already set.

## Decisions that are not tasks yet

The full notes are in the [intent map](context/intent-map.md) and the spec section "Human decisions still required".

- Close the dep-refresh issue, or restore GitHub Actions and branch protection. On 2026-11-06 master was not protected, the workflows were already gone in `736ebc6`, and Actions was disabled. The issue is [Weekly dep-refresh cannot auto-land](issues/2026-08-08-dep-refresh-cannot-auto-land.md).
- Whether `letter_spaced` waits for more real scanned positives or enters only as an experimental synthetic label. `<g>` has nine positives across five projects. That is enough for fixtures and too few to train. The deferral is volume, not absence.
- The controlled font-change vocabulary, including every project-specific `<f>` rule. `<f>` appears 1,138 times across 11 projects.
- The remaining spec choices:
  - underline versus italic
  - gold/silver/bronze loss weights
  - human-audit precision for edition matches and for projected labels
  - Gutenberg and Standard Ebooks ingestion
  - a later drop-cap output
  - jurisdictions and artifact licenses
  - the phase-one OFL font lineages and the legal reading for raster datasets and trained weights
  - whether font acquisition stays interactive or uses a reviewed hash-pinned fetcher

A real-dataset GPU evaluation smoke test stays deferred until a stable fixture and a GPU CI lane exist.
