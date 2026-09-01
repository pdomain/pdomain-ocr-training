---
Status: draft
Owner: CT
Created: 2026-08-31
Last verified: 2026-08-31
Kind: plan
---

# Fine-Grained Typography Phase Two Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce real training crops, then build and evaluate the typography model, starting from the smallest baseline that can be beaten.

**Architecture:** The shared contracts and cross-source preparation already exist. Phase two adds crop production in `pdomain-source-data`, the model in `pdomain-ocr-training`, and optional synthetic supplements in `pdomain-ocr-synth`.

**Tech Stack:** Python `>=3.11,<3.14` for `pdomain-source-data` and `pdomain-ocr-training`, Python `>=3.13,<3.14` for `pdomain-ocr-synth`. Pydantic v2, PyArrow, Pillow, PyTorch, torchvision, pytest, Ruff, basedpyright, Docgraph.

---

This plan does not authorize implementation. Begin each task only after explicit approval.

## Agent Index

- **Kind:** plan
- **Status:** draft
- **Owner:** CT
- **Last verified:** 2026-08-31
- **Read when:** implementing typography crop production, the formatting model, or synthetic typography.
- **Search terms:** typography phase two, formatting model, training crops, monotonic alignment, whole-word baseline.

## Architecture

The shared contracts and cross-source preparation already exist. `pdomain-source-data` gains crop
production, `pdomain-ocr-training` gains the model, and `pdomain-ocr-synth` gains optional synthetic
supplements. Nothing in this phase changes OCR recognition or page-region behaviour.

## Tech Stack

Python `>=3.11,<3.14` for `pdomain-source-data` and `pdomain-ocr-training`, and Python
`>=3.13,<3.14` for `pdomain-ocr-synth`. Pydantic v2, PyArrow, Pillow, PyTorch, torchvision, pytest,
Ruff, basedpyright, and Docgraph.

## Goal

Get from shipped contracts to a measured model. Phase one built the parser, the span types, and the
cross-source preparation. Phase two produces the crops those contracts describe, trains the smallest
baseline, and only then builds the contextual model.

## What changed since the 2026-08-21 plan

Four of its findings change this plan. Read [the corpus
re-verification](../research/2026-08-31-typography-corpus-reverification.md) first.

Training cannot start with the model. Nothing crops pixels from a page image, nothing calls the
shipped alignment functions, and the labeler preparation stage emits geometry as absent. Crop
production comes first and is the whole of Phase 2A.

The human labeler is not required for the baseline, but it is required for the contextual model.
The existing recognition and page-region models can supply geometry directly, which yields
silver-tier labels good enough to build and measure the whole-word baseline. The contextual grapheme
model depends on exact span boundaries, so it waits for reviewed geometry from the labeler exchange.
That exchange must start alongside Phase 2A, not after it.

The recommended alignment is monotonic, warm-started from forced alignment, rather than free
cross-attention.

The synthetic renderer must not depend on `pdomain-book-tools`, because that package requires a full
training stack. It carries a torch-free mirror of the span types instead.

Two tasks from that plan are deferred rather than dropped. Task 13, contextual stress tests and weak
supervision, waits until the contextual model has a measured baseline to regress against. Task 15,
shadow-inference integration, waits until the offline acceptance gate passes. Neither belongs in
phase two.

## Global constraints

- Do not implement, download fonts, train, commit, or deploy without explicit owner approval.
- Preserve all raw source bytes and unrelated working-tree changes.
- Keep synthetic assets out of real validation and test partitions.
- Run each repository's own CI and Docgraph gate before every checkpoint.
- Never combine cross-repository changes in one commit.
- Every generated dataset lives outside Git behind a content-addressed manifest.

## Dependency order

1. Crop production in `pdomain-source-data`, which unblocks the baseline.
2. The formatting package and whole-word baseline in `pdomain-ocr-training`, on silver-tier
   model-generated geometry.
3. The labeler exchange, which is Task 9A of the 2026-08-21 plan. Start it in parallel with step 1,
   because step 4 cannot begin until reviewed geometry exists.
4. The contextual grapheme model, then calibration and evaluation, on reviewed geometry.
5. The runner protocol extension.
6. Synthetic typography in `pdomain-ocr-synth`, gated on the real-scan comparison.

## Phase 2A: Produce training crops

### Task A1: Generate OCR geometry for PGDP pages

**Files:**

- Create: `/workspaces/pdomain/pdomain-source-data/pdomain_source_data/geometry/__init__.py`
- Create: `/workspaces/pdomain/pdomain-source-data/pdomain_source_data/geometry/recognize.py`
- Extend: `/workspaces/pdomain/pdomain-source-data/pdomain_source_data/cli.py`
- Create: `/workspaces/pdomain/pdomain-source-data/tests/geometry/test_recognize.py`

- [ ] **Step 1: Write the geometry contract tests**

Assert that a geometry record carries page identity, image hash, model name, model version,
configuration hash, and per-word boxes with recognized text and confidence. Assert that rerunning
with unchanged inputs and pinned versions produces byte-identical records.

- [ ] **Step 2: Run the existing recognition and page-region models over a pilot book**

Do not write a new recognizer. Call the existing models through their published contracts and record
their versions. Start with one book so failures are cheap.

Run: `uv run pdomain-source-data geometry --task typography --config <pilot.toml> --output <dir>`

This adds a `geometry` verb to `COMMANDS` in `pdomain_source_data/cli.py`, which currently offers
only ingest, inventory, audit, match, align-books, materialize, prepare-labeler,
prepare-labeler-book, materialize-labeler, import-corrections, promote, export-training, and split.

- [ ] **Step 3: Record geometry as evidence, not as truth**

Geometry produced this way is unreviewed. Mark it `silver` and never `gold`. The labeler exchange
remains the only route to `gold`.

Run: `cd /workspaces/pdomain/pdomain-source-data && make ci`

Expected: geometry records for one book with hashes and model versions. Rollback removes the
geometry output directory; nothing else consumes it yet.

### Task A2: Project F2 spans onto OCR tokens and cut crops

**Files:**

- Create: `/workspaces/pdomain/pdomain-source-data/pdomain_source_data/tasks/typography/crops.py`
- Extend: `/workspaces/pdomain/pdomain-source-data/pdomain_source_data/cli.py`
- Create: `/workspaces/pdomain/pdomain-source-data/tests/tasks/typography/test_crops.py`

- [ ] **Step 1: Write projection tests against known pages**

Use pages whose spans are known by hand. Assert that `align_tokens` and `project_style_span` from
`pdomain-book-tools` are called, that a span crossing a token boundary splits only in the crop
projection, and that the canonical source span stays whole.

- [ ] **Step 2: Write crop extraction tests**

Assert a target-word crop and a short-line crop are produced for every retained token. Assert that
crop boxes stay inside the page, that truncated crops are flagged, and that every crop records the
grapheme range it covers.

- [ ] **Step 3: Implement extraction and emit a dataset manifest**

Emit target-word crops, short-line crops, recognized text, grapheme spans, label states, confidence
tier, and provenance. The manifest is content-addressed and lives outside Git.

- [ ] **Step 4: Exclude what the guidelines make unreliable**

Three rules, each stated here so an implementer need not re-read the research.

Headings must not contribute bold negatives. The formatting guidelines forbid marking bold in a
heading, so visually bold heading text is recorded as not bold and would poison the negative set.

Small-caps case is never an observation. An all-small-caps run is written uppercase and a chapter's
opening word is re-cased, so case inside `<sc>` records a formatter's classification. Do not derive
a small-caps negative from letter case alone.

An unknown guideline era blocks the italic and letter-spacing distinction. Where the era is unknown
or names only a producing pipeline, mark italic spans `unknown` for `letter_spaced` rather than
confidently italic, because `<i>` also covered letter-spaced text before March 2007.

Run: `uv run pdomain-source-data crops --task typography --config <pilot.toml> --output <dir>`

This adds a `crops` verb to `COMMANDS`. The CLI takes `--task`, `--config`, `--output`, and
`--dry-run`; it has no per-book flag, so the pilot book is named in the config.

Expected: a crop manifest with counts by label, tier, and exclusion reason. Rollback deletes the
manifest; the geometry records survive.

### Task A3: Build the leakage-safe split manifest

**Files:**

- Extend: `/workspaces/pdomain/pdomain-source-data/pdomain_source_data/splits/manifest.py`
- Create: `/workspaces/pdomain/pdomain-source-data/tests/splits/test_typography_splits.py`

- [ ] **Step 1: Write leakage tests**

Assert no leakage group spans two partitions, that grouping joins volumes, duplicate scans,
Gutenberg variants, and Standard Ebooks derivatives, and that rerunning produces a byte-identical
manifest.

- [ ] **Step 2: Reserve controlled challenge sets outside random allocation**

Reserve poetry, tables, headings, captions, blackletter, poor scans, and slanted roman. The corpus
remains single-language, so record the language challenge set as unavailable rather than empty.

Run: `cd /workspaces/pdomain/pdomain-source-data && make ci`

Expected: an immutable split manifest with its seed, grouping version, and input hashes.

**Checkpoint.** Phase 2A is complete when a crop manifest and a split manifest exist, reproduce
byte-identically, and report label counts. Report those counts before starting Phase 2B, because
they decide whether the rare labels can be trained at all.

## Phase 2B: Build and measure the model

### Task B1: Add the formatting package and torch-free configuration

**Files:**

- Create: `/workspaces/pdomain/pdomain-ocr-training/pdomain_ocr_training/formatting/__init__.py`
- Create: `/workspaces/pdomain/pdomain-ocr-training/pdomain_ocr_training/formatting/config.py`
- Create: `/workspaces/pdomain/pdomain-ocr-training/pdomain_ocr_training/formatting/dataset.py`
- Create: `/workspaces/pdomain/pdomain-ocr-training/tests/formatting/test_config.py`
- Create: `/workspaces/pdomain/pdomain-ocr-training/tests/formatting/test_dataset.py`

- [ ] **Step 1: Write configuration tests that forbid Torch at import**

`FormattingConfig` carries manifest paths, active labels, encoder choice, crop size, batch size,
learning rate, confidence weights, sampling caps, seed, calibration split, and output directory.
Importing configuration must not import Torch.

- [ ] **Step 2: Write masking and sampling tests**

Assert unknown and quarantine labels contribute zero loss and never become negatives. Assert that
rare labels sample under a per-book cap, that confidence tiers apply weights, and that no test
group reaches the training loader.

Run: `cd /workspaces/pdomain/pdomain-ocr-training && make ci AI=1`

Expected: existing recognition and detection tests unchanged.

### Task B2: Build the whole-word baseline and measure what it cannot represent

**Files:**

- Create: `/workspaces/pdomain/pdomain-ocr-training/pdomain_ocr_training/formatting/baseline.py`
- Create: `/workspaces/pdomain/pdomain-ocr-training/pdomain_ocr_training/formatting/evaluate.py`
- Extend: `/workspaces/pdomain/pdomain-ocr-training/pyproject.toml`
- Create: `/workspaces/pdomain/pdomain-ocr-training/tests/formatting/test_baseline.py`

- [ ] **Step 1: Implement a multi-label whole-word classifier**

Use a small torchvision backbone with independent sigmoid logits. Report majority, rule-only, and
neural results on book-grouped splits.

- [ ] **Step 2: Report the unrepresentable-span fraction**

This is the point of the baseline. Copying one word label to every grapheme cannot express a word
whose style changes internally. Report that fraction under each mixed-style definition in the
re-verification, since they span a factor of 20.

The Phase 4 gate measures the 14,639 words whose style differs among their word characters. That
excludes the 66,099 words separated only by trailing punctuation, which a parser rule already
resolves. Report the 3,999 letter-adjacent words separately as the headline diagnostic, because no
word-level model plus a punctuation rule can reach them.

Run: `uv run pdomain-ocr-training-formatting --config experiments/formatting/word-baseline.toml`

`[project.scripts]` currently declares only `pdomain-ocr-training-detect` and
`pdomain-ocr-training-recog`, so this task adds the formatting entry point.

Expected: a checkpoint, frozen configuration, input manifest hashes, per-label metrics, calibrated
probabilities, latency measurements, and the unrepresentable-span fraction. Rollback removes the
baseline registry pointer.

### Task B3: Add the contextual grapheme model with monotonic alignment

**Depends on:** reviewed geometry from the labeler exchange, Task 9A of the
[2026-08-21 plan](2026-08-21-fine-grained-typography-model.md). Unreviewed model-generated geometry
trains the baseline in Task B2 but must not train this model. A part-of-word span boundary is only as
good as the geometry beneath it. Do not begin this task on silver-tier geometry.

**Files:**

- Create: `/workspaces/pdomain/pdomain-ocr-training/pdomain_ocr_training/formatting/model.py`
- Create: `/workspaces/pdomain/pdomain-ocr-training/pdomain_ocr_training/formatting/alignment.py`
- Create: `/workspaces/pdomain/pdomain-ocr-training/pdomain_ocr_training/formatting/losses.py`
- Create: `/workspaces/pdomain/pdomain-ocr-training/pdomain_ocr_training/formatting/train.py`
- Create: `/workspaces/pdomain/pdomain-ocr-training/tests/formatting/test_model.py`
- Create: `/workspaces/pdomain/pdomain-ocr-training/tests/formatting/test_alignment.py`
- Create: `/workspaces/pdomain/pdomain-ocr-training/tests/formatting/test_losses.py`

- [ ] **Step 1: Write shape, overlap, and invariance tests**

For batch `B`, graphemes `G`, and labels `L`, assert grapheme logits `[B,G,L]`, word logits `[B,L]`,
and valid masks `[B,G,L]`. Two labels may be positive at one grapheme. Padding must not change valid
logits. Unknown labels contribute zero loss.

- [ ] **Step 2: Write monotonic alignment tests**

Assert the text-to-image alignment is monotonic and non-decreasing, and that it can be warm-started
from a supplied forced alignment.

Measure boundary error against a small checked-in fixture of rendered words whose glyph boxes are
exact, generated once and committed with the test. Do not depend on the Phase 2C renderer, which is
gated and may never run. Boundary error should stay under half an average advance width. If the
fixture cannot establish that, record the result and raise it as a decision rather than proceeding
to the contextual model.

- [ ] **Step 3: Implement the two-view model**

A high-resolution target-word view and a short-line context view. Learned grapheme and position
embeddings, target-box and word-boundary embeddings, geometry and confidence projections, monotonic
alignment to image features, independent sigmoid logits, and a pooled whole-word head. No text
decoding.

- [ ] **Step 4: Group correlated heads and use neighbour context**

Bold, small caps, and letter spacing are relative judgements. Group their heads and give the model
the surrounding line, following the published attribute-recognition result.

- [ ] **Step 5: Train the locked comparison set**

Run the whole-word baseline, word-only image queries, word-only text-conditioned queries, and the
two-view contextual model over the same groups and seeds. Make no claim before book-level confidence
intervals exist.

Run: `cd /workspaces/pdomain/pdomain-ocr-training && make ci AI=1`

Expected: all formatting and existing OCR tests pass. Rollback repoints the registry to the
baseline.

### Task B4: Add calibration, abstention, and full evaluation

**Files:**

- Create: `/workspaces/pdomain/pdomain-ocr-training/pdomain_ocr_training/formatting/calibration.py`
- Extend: `/workspaces/pdomain/pdomain-ocr-training/pyproject.toml`
- Create: `/workspaces/pdomain/pdomain-ocr-training/pdomain_ocr_training/formatting/review_artifacts.py`
- Create: `/workspaces/pdomain/pdomain-ocr-training/tests/formatting/test_calibration.py`
- Create: `/workspaces/pdomain/pdomain-ocr-training/tests/formatting/test_metrics.py`

- [ ] **Step 1: Write exact metric fixtures**

Cover per-label grapheme precision, recall, and F1, exact span match, span overlap, and boundary
distance. Also cover whole-word exact accuracy, mixed-style exact accuracy under the declared
definition, overlap agreement, calibration error, Brier score, selective risk, and book bootstrap
intervals.

- [ ] **Step 2: Bound boundary metrics by the guideline tolerance**

Punctuation placement at a tag boundary is enforced only as a soft warning upstream, so span edges
vary by one character. Report boundary distance against that tolerance rather than against an exact
truth the source cannot supply.

- [ ] **Step 3: Fit per-label temperature scaling on calibration groups only**

Store temperatures, support, calibration error before and after, tool version, and manifest hash.

- [ ] **Step 4: Emit review artifacts**

Each artifact carries crop, page thumbnail, recognized text, source text, ground truth, prediction,
per-label confidence, abstention result, provenance, warnings, and hashes.

Run: `uv run pdomain-ocr-training-formatting-eval --config experiments/formatting/grapheme-v1-eval.toml`

Expected: overall and sliced metrics, book-level intervals, latency at batch one and production
batch, calibration plots, and review artifacts.

- [ ] **Step 5: Human acceptance checkpoint**

The owner supplies numeric gates for quality, regression margin, calibration, abstention, and
latency. Without them the phase stays experimental.

### Task B5: Extend the runner protocols

**Files:**

- Extend: `/workspaces/pdomain/pdomain-ocr-training/pdomain_ocr_training/protocols.py`
- Create: `/workspaces/pdomain/pdomain-ocr-training/tests/formatting/test_protocols.py`

- [ ] **Step 1: Add formatting methods to both protocols**

`ITrainingRunner` and `IEvalRunner` are fixed method pairs rather than a registry, so formatting
needs `train_formatting` and `evaluate_formatting` added to both. Do not modify `RecognitionConfig`
or the recognition methods.

- [ ] **Step 2: Keep the public surface torch-free**

Assert that importing the protocols and the formatting configuration does not import Torch.

Run: `cd /workspaces/pdomain/pdomain-ocr-training && make ci AI=1`

Expected: existing runner implementations still satisfy their protocols.

## Phase 2C: Synthetic typography, gated

Start this only if Phase 2B shows a label whose real support is too thin to train. On current counts
that is letter spacing, at nine positives, and possibly resolved font changes.

### Task C1: Mirror the span contract without a training dependency

**Files:**

- Create: `/workspaces/pdomain/pdomain-ocr-synth/src/pdomain_ocr_synth/typography/spans.py`
- Create: `/workspaces/pdomain/pdomain-ocr-synth/tests/typography/test_spans.py`

- [ ] **Step 1: Define a torch-free label and span mirror**

`pdomain-book-tools` requires Torch, torchvision, torchaudio, transformers, and python-doctr, so the
renderer must not depend on it. Mirror the labels and half-open grapheme spans and test them against
fixtures exported from the canonical package.

- [ ] **Step 2: Add a contract-drift test**

Assert the mirrored label set matches a checked-in fixture of the canonical set, so divergence fails
the build rather than the dataset.

Run: `make ci AI=1`

Expected: the renderer's dependency set is unchanged and still excludes Torch. Rollback deletes the
`typography` package; the existing renderer is untouched.

### Task C2: Add the pinned font manifest and mixed-span renderer

**Files:**

- Create: `/workspaces/pdomain/pdomain-ocr-synth/src/pdomain_ocr_synth/typography/font_manifest.py`
- Create: `/workspaces/pdomain/pdomain-ocr-synth/src/pdomain_ocr_synth/typography/mixed_renderer.py`
- Create: `/workspaces/pdomain/pdomain-ocr-synth/tests/typography/test_mixed_renderer.py`

- [ ] **Step 1: Pin every font by hash, version, license, axes, and features**

Read feature support from the pinned binary, never from the family's reputation. Group forks and
renamed derivatives under one lineage identifier for splitting.

- [ ] **Step 2: Render exact mixed spans and keep cluster truth**

Shape complete context with HarfBuzz before extracting crops. Record source range, style set,
cluster, contributing glyphs, and clipping for every grapheme. Ligature graphemes share one cluster
and never receive invented character boxes.

Run: `cd /workspaces/pdomain/pdomain-ocr-synth && make ci AI=1`

Expected: deterministic renders under a fixed seed, with a manifest naming every font hash and
feature used. Rollback removes the generated dataset directory; no real data is touched.

### Task C3: Measure whether synthetic data helps real scans

- [ ] **Step 1: Run the real-only and synthetic-only controls**

Synthetic-only exposes the domain gap and can never be promoted.

Run: `uv run pdomain-ocr-training-formatting --config experiments/formatting/synthetic-only.toml`

Expected: a synthetic-only result reported beside the real-only control, never promoted. Rollback
repoints the registry to the real-only checkpoint.

- [ ] **Step 2: Run the curriculum matrix and apply the existing gate**

The synthetic gate is unchanged from the 2026-08-21 design. Synthetic data passes only when all of
the following hold:

- At least 1.0 absolute macro grapheme F1 and 2.0 absolute mixed-style exact-word improvement on
  immutable real validation.
- No common label loses more than 1.0.
- No audited stratum loses more than 2.0.
- Calibration and abstention are no worse after recalibration.
- The result persists across three seeds and after removing evaluation words seen in synthetic
  text.

## Acceptance criteria

Phase 2A passes when crop and split manifests reproduce byte-identically, every crop carries
provenance and a confidence tier, no leakage group spans partitions, and label counts are published.

Phase 2B passes when all of the following hold:

- The baseline beats majority and rule-only comparisons on book-grouped data and reports its
  unrepresentable-span fraction.
- The contextual model improves mixed-style exact accuracy and per-label grapheme F1 over the
  baseline and both ablations, without regressing whole-word performance beyond an agreed margin.
- Calibrated abstention meets an owner-set risk target.

Phase 2C passes only on the synthetic gate above.

## Rollback

Each stage writes a content-addressed directory and a manifest only after validation. A failed stage
leaves its prior version active. Promotion moves one manifest pointer and rollback restores the
previous one. No stage mutates stored source bytes. Existing recognition and page-region outputs stay
authoritative until the typography gate passes.

## Decisions taken on 2026-09-01

- The Phase 4 gate measures the 14,639 word-character mixed-style cases and reports the 3,999
  letter-adjacent cases separately.
- Unreviewed model-generated geometry may train the whole-word baseline at silver tier. The
  contextual grapheme model requires reviewed geometry.

## Human decisions this plan still needs

- The numeric quality, calibration, abstention, and latency gates, once Phase 2A publishes counts.
- Whether `letter_spaced` waits for real positives or enters as a synthetic-only experimental label.
- The controlled font-change vocabulary, now that `<f>` appears 1,138 times across 11 projects.
- Whether the torch-free span mirror in the renderer is acceptable, or whether the dependency
  boundary should be solved another way.
