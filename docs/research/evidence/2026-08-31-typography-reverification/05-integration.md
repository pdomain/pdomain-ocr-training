# Integration survey: fine-grained typography model placement

Read-only survey of `/workspaces/pdomain/*`. No files modified.

## Headline finding

This exact question was already researched, designed, and partly built. On
2026-08-21, `pdomain-ocr-training` committed a cross-repo research doc, design
spec, and 15-task implementation plan for precisely this model:

- `pdomain-ocr-training/docs/research/2026-08-21-fine-grained-typography-model-research.md`
- `pdomain-ocr-training/docs/specs/2026-08-21-fine-grained-typography-model-design.md`
- `pdomain-ocr-training/docs/plans/2026-08-21-fine-grained-typography-model.md`
- `pdomain-ocr-training/docs/handoff/2026-08-21-115334-fine-grained-typography-phase-one.md`

The design's repository split is exactly the brief's four options, combined
rather than chosen between: canonical F2 parsing and span types in
`pdomain-book-tools` (Tasks 1-5A), corpus matching/manifests in a **new**
dedicated repo `pdomain-source-data` (Tasks 6-9), synthetic generation in
`pdomain-ocr-synth` (Tasks 9B-9E), and the model/training task in
`pdomain-ocr-training` (Tasks 10-14).

**Status as of today (git evidence, not doc claims):**

| Repo | Plan tasks | Status |
|---|---|---|
| `pdomain-book-tools` | 1-5A | **Done and released** (tags through v0.26.2; typography/F2 code merged via `feature/fine-grained-typography-phase-one` and later branches) |
| `pdomain-source-data` | 6-9 | **Repo created, substantially built** (ingest/inventory/audit CLI for pgdp/gutenberg/standard-ebooks; `tasks/typography/` implemented) |
| `pdomain-ocr-synth` | 9B-9E | **Not started** (no `typography/` subpackage; existing PGDP work there is a separate M14/M15a/M15b scan-measurement track, see below) |
| `pdomain-ocr-training` | 10-14 | **Not started** (no `formatting/` subpackage; only the design docs exist) |

So the open work is exactly the two things the parent-agent's message flagged:
the ocr-training training task (Tasks 10-14) and the ocr-synth synthetic
generator extension (Tasks 9B-9E). Both are gated behind explicit owner
approval per the plan ("This plan does not authorize implementation").

---

## 1. Per-repo purpose, layout, contracts, gates, governance

| Repo | Purpose | Python | Package | Test/lint/typecheck | DOCGRAPH.md |
|---|---|---|---|---|---|
| `pdomain-book-tools` | Foundation OCR/layout/image-processing library; all `pdomain-*` depend on it | `>=3.11,<3.14` | `pdomain_book_tools/` | `make test/lint/format/ci AI=1`; ruff + basedpyright | yes |
| `pdomain-ocr-training` | Torch/DocTR training + eval for detect/recog; torch-free base install | `>=3.11,<3.14` | `pdomain_ocr_training/` | `make test/lint/typecheck/ci`; basedpyright strict, `failOnWarnings=true` | yes |
| `pdomain-pgdp-api-client` | Mirrors PGDP projects to disk before archival; fetch-only, no parsing | `>=3.11,<3.14` | `pdomain_pgdp_api_client/` | `make ci AI=1`; ruff+basedpyright strict | yes |
| `pdomain-source-data` | Shared corpus prep: identity, cross-source matching, corrections, splits, task exports (pgdp/gutenberg/standard-ebooks; recognition/detection/typography/glyph_forms/page_regions) | `>=3.11,<3.14` | `pdomain_source_data/` | `make test/lint/typecheck/ci`; basedpyright strict | yes |
| `pdomain-ocr-synth` | Recipe-driven synthetic OCR training-data generator (Cló Gaelach first target) | `>=3.13,<3.14` | `src/pdomain_ocr_synth/` | `make ci AI=1` | yes |
| `pdomain-ocr-cli` | Wraps book-tools OCR/layout into a `pdomain-ocr` CLI (scan → txt) | `>=3.11,<3.14` | `pdomain_ocr_cli/` | `make ci AI=1` | yes; **not relevant** — no typography code, not part of the dependency chain |
| `pd-ocr-trainer` | Legacy trainer (NiceGUI UI + DocTR train scripts); source of the verbatim-moved `detect.py`/`recog.py` now living in `pdomain-ocr-training` | `>=3.13,<3.14` | `src/pd_ocr_trainer/` | `make ci AI=1` | yes; **legacy, being superseded** by `pdomain-ocr-training` |
| `ml-training` (workspace-root) | Not a repo — a data directory (`all/`), essentially empty here | n/a | n/a | n/a | no; **not relevant** |

`pdomain-ocr-labeler-spa` and `pdomain-ocr-trainer-spa` also exist in the
workspace and are named as consumers/producers in the plan (SPA runs OCR +
typography review UI; trainer SPA will eventually expose a "formatting"
classifier run). They were out of the assigned repo list; noted only for the
dependency graph in §7.

---

## 2. `pdomain-book-tools` OCR/layout/typography contracts

**Page hierarchy** (`pdomain_book_tools/ocr/`):
- `Document` (`document.py`) → `Page` (`page.py`: `width`, `height`, `page_index`, `blocks`, `bounding_box`, `review`) → `Block` (`block.py`: `BlockChildType.WORDS|BLOCKS`, `BlockCategory.BLOCK|PARAGRAPH|LINE` — this is the "Line" contract) → `Word` (`word.py`) → `Character` (`character.py`).
- Geometry: `BoundingBox` in `pdomain_book_tools/geometry/bounding_box.py` (`top_left`/`bottom_right` `Point`s, `minX/minY/maxX/maxY/width/height/area/center`, `from_points/from_float/from_ltrb/from_ltwh`). Region-detection layer is separate: `LayoutRegion`, `PageLayout`, `RegionType` in `pdomain_book_tools/layout/types.py`.

**Existing style/formatting fields, two generations coexist on `Word`:**
- Legacy, coarse: `text_style_labels: list[str]`, `text_style_label_scopes: dict[str,str]` (scope = `"whole"` or `"part"` — no offsets), `word_components: list[str]`, validated against a controlled vocabulary in `pdomain_book_tools/ocr/label_normalization.py` (`regular, all caps, small caps, italics, bold, blackletter, underline, strikethrough, monospace, handwritten`; components: `superscript, subscript, footnote marker, drop cap, drop cap unrecovered`). `Character` has the same flat `text_style_labels`/`word_components` lists per-character (no span structure — each `Character` is already atomic with its own bbox).
- **New, precise — this is the attachment point for the new model's output**: `Word.typography_annotations: TypographyAnnotations | None` from `pdomain_book_tools.typography.annotations`.

**`pdomain_book_tools/typography/` — already the canonical inline-style span contract:**

- `labels.py`: `StyleLabel(StrEnum)` = `ITALIC, BOLD, SMALL_CAPS, LETTER_SPACED, SUPERSCRIPT, SUBSCRIPT, UNDERLINE, FONT_BLACKLETTER, FONT_ANTIQUA, FONT_UPRIGHT_IN_ITALIC, FONT_OTHER_REVIEWED`. Also `KnowledgeState` (`POSITIVE/VERIFIED_NEGATIVE/UNKNOWN/CONFLICT`), `LabelSource` (`F2/GUTENBERG_HTML/SE_COMPUTED_CSS/HUMAN/SYNTHETIC`), `ConfidenceTier` (`GOLD/SILVER/BRONZE/QUARANTINE`).
- `spans.py`: grapheme-indexed (extended Unicode grapheme clusters via `regex`, versioned as `GRAPHEME_SEGMENTATION_VERSION`), not raw `str` indices.
  ```python
  class StyleSpan(CanonicalModel):
      label: StyleLabel
      start: int; end: int          # half-open grapheme indices
      state: KnowledgeState
      label_source: LabelSource
      confidence_tier: ConfidenceTier
      source_slices: tuple[SourceSlice, ...]
      rule_ref: str | None
      semantic_reason: str | None
      warnings: tuple[str, ...]

  class TypographySpans(CanonicalModel):
      grapheme_count: int
      spans: tuple[StyleSpan, ...]
      def labels_at(self, index: int) -> set[StyleLabel]: ...
  ```
  Multiple `StyleSpan`s are independent list entries — a grapheme can carry italic + bold + small_caps at once; `labels_at()` returning a `set` confirms multi-label overlap is a tested, first-class behavior, not bolted on.
- `annotations.py`: `TypographyAnnotations(CanonicalModel)` — word-level bundle: `grapheme_count`, `spans`, derived `whole_word_labels` (full-coverage positive labels), `source`, `model_version`, `confidence`, `calibration_version`, `reviewer_id`, `reviewed_at`, `warnings`. This is exactly the shape a trained model's inference output should populate.
- `records.py` (922 lines): `TypographyPageRecord(CanonicalModel)` — page-level container: `identity: TextIdentity`, `parsed_text`, `graphemes: tuple[Grapheme,...]`, `ocr_tokens: tuple[OcrTokenRef,...]` (`bbox`, `line_id`, `grapheme_start/end`, `alignment_id`), `style_spans`, `structural_context`, `parser_warnings`, `training_eligible: bool`, `alignments`.
- `alignment.py` (812 lines): `align_tokens()` DP alignment from a normalized "comparison view" of source text to OCR tokens → `TokenAlignmentResult`; `project_style_span()` projects a source-text style span onto OCR token coordinate space → `ProjectedStyleSpan` (source span + `crop_bbox` + optional `character_boxes` in image pixels). **This is the label-to-crop projection machinery a training pipeline needs.**
- `normalization.py`: `ComparisonView`, `build_comparison_view`, `small_caps_ranges_from_spans()`.
- `review.py` (633 lines, `REVIEW_CONTRACT_VERSION = "0.25.0"`): a portable human-review/correction contract — `TypographyTaxonomy`, `WordTypography`, `TypographyCorrection` (immutable revision chain, UUIDv5 stable word IDs surviving re-segmentation).
- `exchange.py` (999 lines): `WordGeometry`, `PageGeometry`, `CoordinateTransform`, `ModelRun`, `LabelingBundle`, `CorrectionBundle` — a ready-made training/export bundle schema.
- `book_manifest.py`: `BookLabelingManifest`/`BookLabelingPage` — book-level page-index, not span data.

**`pdomain_book_tools/pgdp/f2/` — F2 parser, already extracting all six target styles with grapheme offsets:**
- `tokens.py` (708 lines): `tokenize_f2(page_bytes) -> F2PageTokens` (byte-preserving lexer; `F2TokenKind`: `TEXT, OPEN_TAG, CLOSE_TAG, NOTE, BLOCK_OPEN, BLOCK_CLOSE, SUPERSCRIPT, SUBSCRIPT, NORMALIZATION, UNKNOWN`).
- `parser.py` (490 lines): `F2Parser.parse_page(...) -> TypographyPageRecord`. Direct tag → label map:
  ```python
  _STANDARD_TAG_LABELS = {"i": StyleLabel.ITALIC, "b": StyleLabel.BOLD,
                           "sc": StyleLabel.SMALL_CAPS, "g": StyleLabel.LETTER_SPACED}
  ```
  `f` (font-change) and `u` (underline) route through `ProjectRuleRegistry` (`project_rules.py`, evidence-bound to a project's Project-Comments SHA-256) or fall to `UNKNOWN`/`QUARANTINE`. Superscript/subscript come directly from `F2TokenKind.SUPERSCRIPT`/`SUBSCRIPT` tokens (parser.py:266-286).
- `offsets.py` (400 lines): lossless lexical JSON extraction (`read_lexical_f2_page`, `DecodedF2Character`) without reserializing `F2.json`.
- `warnings.py`: `F2ParseWarning` + `warning_blocks_training(code)` — an explicit training-eligibility gate on malformed/ambiguous markup.

**Test maturity**: `tests/typography/` = 3,629 lines / 8 files; `tests/pgdp/f2/` = 871 lines / 4 files; `pytest --collect-only` over both = 373 tests. This is shipped, released (tags through v0.26.2), and stable — not a prototype. It has no dedicated architecture/spec doc inside `pdomain-book-tools` itself yet (only `CHANGELOG.md`'s `[Unreleased]` section documents it in prose, though the code is in fact released past v0.25.0) — a docgraph gap worth flagging back to that repo separately.

**`Word.glyph_annotations: GlyphAnnotations | None`** (`ocr/glyph_annotations.py`) is a **different, adjacent** concern: ligature/long-s/swash substitution provenance (`LigatureMark.char_span` uses plain `str` character indices, not graphemes — a second, inconsistent indexing convention). It is the type `pdomain-ocr-training`'s `GlyphFeatureSet` derives from (see §5). Do not conflate it with `typography_annotations`.

**Verdict**: canonical span types and F2 parsing already live in `pdomain-book-tools`, are complete for all six target styles, are grapheme-indexed with tested multi-label overlap, and already have an OCR-geometry alignment/projection layer. There is no gap here worth re-litigating — reuse `StyleLabel`, `StyleSpan`, `TypographySpans`, `TypographyAnnotations`, `TypographyPageRecord`, `align_tokens`/`project_style_span` directly.

---

## 3. `pdomain-ocr-training` task structure — hard-wired, not a plugin system

No `Task` ABC, no registry, no entry-points dispatch. "Detect" and "recognition" are two **hardcoded method pairs** on two sibling `Protocol` classes in `pdomain_ocr_training/protocols.py`:

```python
class ITrainingRunner(Protocol):
    def train_detection(self, profile: str, config: DetectionConfig) -> Iterator[TrainingEvent]: ...
    def train_recognition(self, profile: str, config: RecognitionConfig) -> Iterator[TrainingEvent]: ...

class IEvalRunner(Protocol):
    def evaluate_detection(self, profile: str, config: DetectionEvalConfig) -> DetectionEvalResult: ...
    def evaluate_recognition(self, profile: str, config: RecognitionEvalConfig) -> RecognitionEvalResult: ...
```

`LocalTrainingRunner` (`local.py`) and `LocalEvalRunner` (`local_eval.py`) mirror this 1:1, each delegating to module-level functions via a hardcoded thread+queue bridge. No `TaskConfig` base class — `DetectionConfig`/`RecognitionConfig` are independent `BaseModel`s. `pyproject.toml` has `[project.scripts]` only, no entry-points group. The only "task" as *data* is `DATASET_TASKS = ("detection", "recognition")`, a literal tuple in `datasets.py`'s `ExportManager` (scoped to the labeler-export path; the plan does not route formatting data through it).

**A third task requires touching the same shared files, not dropping in a module and registering it:**
1. New subpackage `pdomain_ocr_training/formatting/` (does not exist): `config.py`, `dataset.py`, `model.py`, `losses.py`, `train.py`, `evaluate.py`, `calibration.py`, `export.py` (per the plan's Task 14 / design's recommended layout).
2. `protocols.py` — add `train_formatting(profile, config) -> Iterator[TrainingEvent]` to `ITrainingRunner`; add `evaluate_formatting(profile, config) -> FormattingEvalResult` to `IEvalRunner`; add `FormattingConfig`, `FormattingEvalConfig`, `FormattingEvalResult` models. Existing detect/recog signatures stay untouched.
3. `local.py` — add `train_formatting` to `LocalTrainingRunner`, same thread+queue pattern.
4. `local_eval.py` — add `evaluate_formatting` to `LocalEvalRunner`.
5. `__init__.py` — export the new public names; preserve the lazy `__getattr__` torch-free base-import contract.
6. `pyproject.toml` — new console scripts, e.g. `pdomain-ocr-training-formatting`.
7. Tests — new `tests/formatting/` mirroring the existing per-concern test files, plus an addition to `tests/test_torch_free_import.py`.

**Verdict**: pluggable only in the loose sense that a third task can be added without breaking the first two; every addition is hand-copied into the same shared Protocol/runner files. This is already fully specified by the plan's Task 14 (`docs/plans/2026-08-21-fine-grained-typography-model.md`, lines 792-820) — nothing further to design here, only to implement under approval.

### The glyph-feature sidecar is the wrong carrier — a sibling mechanism, not an extension point

`GlyphFeatureSet` (`protocols.py`) and `EvalSlice` are **diagnostic tooling for the existing recognition task**, not a training-label carrier for a new model:

```python
class GlyphFeatureSet(BaseModel):
    """Per-word glyph feature presence, decoupled from pdomain-book-tools."""
    ligatures: list[str] = []
    long_s: bool = False
    swash: bool = False
```

A JSON sidecar (`dict[crop_id, GlyphFeatureSet]`) is joined to `RecognitionEvalResult` samples **by basename crop ID** (threaded through in commit `fccc594`), purely to slice CER/WER by whether a recognition crop has `long_s`, `swash`, or a distinct `ligature:<kind>` present (commit `ad904c3`; `EvalSlice` fields: `feature, n_pos, n_neg, n_excluded, cer_pos/neg, wer_pos/neg, delta_cer, delta_wer, low_support`). It:
- carries **boolean/list presence flags per whole crop**, not character-span ranges;
- has **no multi-label overlap model** — it's evaluation bucketing, not a prediction target;
- exists to answer "does the recognizer do worse on words with X," not "where exactly is X in this word."

**This does not extend to typography spans; it sits beside the new work.** The new `formatting` task needs its own dataset/label path (per the design: `TypographyPageRecord`/`StyleSpan` from `pdomain-book-tools`, materialized into training manifests by `pdomain-source-data`), not the `GlyphFeatureSet` sidecar mechanism. `EvalSlice`'s own docstring even lists `"italic"`/`"drop_cap"` as *example* feature names, which is coincidental — it's a generic binary-slice mechanism for any existing task's eval, not typography-specific.

### The blocked "classifier runner contract" does not yet define the extension point — but a concrete answer already exists in draft

`docs/context/intent-map.md`'s blocked item ("Typeface and glyph training need typed configuration and runner methods before trainer SPA can expose them... Confirm the exact classifier scope before implementation") predates or is independent of the exact resolution: **Task 14 of the 2026-08-21 plan is precisely that missing contract** — it specifies `train_formatting`/`evaluate_formatting` Protocol methods and `FormattingConfig`/`FormattingEvalConfig`/`FormattingEvalResult` models, as detailed above. But as of today **none of it is implemented** (no `formatting/` subpackage, no new Protocol methods in the current `protocols.py`), and the plan explicitly withholds authorization ("does not authorize implementation... begin each task only after explicit approval"). So: the extension point is **designed but not built and not yet approved for building** — the blocked item is not resolved by existing code, only by an existing unapproved draft plan that directly answers it.

### Sidecar-writer ownership does not block this work

The undecided "glyph sidecar writer ownership" item (dataset export vs. trainer SPA writing the `GlyphFeatureSet` JSON) is scoped entirely to the **existing recognition-eval slicing feature** — a diagnostic for `evaluate_recognition`, unrelated to typography spans. It has no bearing on the new formatting task's data path, which routes through `pdomain-book-tools` types and `pdomain-source-data` manifests instead. The only real risk is naming/conceptual confusion — both mechanisms use the word "glyph"/"feature" and both eventually join per-crop side data by basename ID — so implementers should keep them explicitly separate in code and docs, but no decision here gates the new work.

---

## 4. `pdomain-pgdp-api-client` — corpus layout and F2 handling

**Purpose**: mirrors DP (PGDP) projects to disk before archival (`pgdp-fetch` CLI). Explicitly, repeatedly out of scope: parsing F2 markup. AGENTS.md states directly: "Parsing or normalizing proofread text belongs in `pdomain-book-tools`. That includes the F2 formatting markup for italics and poetry... This repo fetches bytes and does not interpret them."

**Corpus layout** (`ProjectLayout` in `pdomain_pgdp_api_client/layout.py`):
```
<root>/<projectid>/
    001.png ...              # page images, flat, beside pages.json
    pages.json                # primary round, {image: text}
    rounds/P3.json             # additional rounds, same shape
    rounds/F2.json              # raw, unparsed F2 markup text
    rounds/<CHAIN>.sources.json  # fallback provenance, only if a chain fell back
    project.json               # full Project metadata dump
    inventory.json             # pagedetails snapshot (page_size, per-round username, etc.)
    images/                    # illustrations only, never page images
```
This shape is locked by `tests/test_booktools_compat.py` ("the most important test in the repo"), which dynamically imports `pdomain_book_tools/pgdp/pgdp_results.py` from the sibling source tree to assert `PGDPExport.from_json_file` resolves images/text correctly. **No runtime package dependency on `pdomain-book-tools`** exists — only this test-time sibling-source-tree import (with a `regex` dev-only dependency to avoid pulling torch/doctr/opencv for one pure-Python test).

**F2 handling**: none beyond opaque round-name bookkeeping (fetch planning, fallback-chain resolution, byte-size verification). No tag content is ever inspected here — confirmed both by AGENTS.md's explicit statement and by the design spec's Scope section. **Book-tools' `pgdp/f2/` parser (§2) is the only F2-content parser in the workspace**, and this repo's design doc's own Open Question #2 ("should F2 normalization live in `PGDPResults` or a new module?") was still unresolved as of 2026-08-20 — since resolved in practice by the new `pgdp/f2/` package built under the Aug-21 plan.

**Metadata captured**: per-project (`Project` model: title, author, languages, character_suites, genre, difficulty, comments/scan-URL extraction), per-page/round (`PageDetail`/`PageRoundDetail`: image, page_size, per-round proofreader `username`), local SQLite `ProjectRecord` index. **No geometry and no per-span typography metadata anywhere** — this repo only ever produces bytes + round bookkeeping for `pdomain-book-tools` to parse downstream.

---

## 5. Existing inline-style/formatting code inventory (workspace-wide grep)

| Location | What it is | Relevant? |
|---|---|---|
| `pdomain-book-tools/pdomain_book_tools/typography/*` | Canonical span/label/annotation/alignment/review contract | **Yes — reuse directly** (§2) |
| `pdomain-book-tools/pdomain_book_tools/pgdp/f2/*` | F2 markup parser producing `StyleSpan`s | **Yes — reuse directly** (§2) |
| `pdomain-book-tools/pdomain_book_tools/ocr/glyph_annotations.py` | Ligature/long-s/swash side channel on `Word` | Adjacent, not the same thing — different indexing (`str` chars, not graphemes) |
| `pdomain-book-tools/pdomain_book_tools/ocr/label_normalization.py` | Legacy whole/part-scope style vocabulary on `Word`/`Character` | Legacy; superseded by `typography_annotations`, still read by some downstream consumers |
| `pdomain-ocr-training/pdomain_ocr_training/protocols.py` (`GlyphFeatureSet`, `EvalSlice`) | Recognition-eval CER/WER slicing by binary crop feature | Wrong shape for training labels — sits beside, not under, the new work (§3) |
| `pdomain-source-data/pdomain_source_data/tasks/typography/*` | CSS-cascade typography-evidence extraction from XHTML (Gutenberg/Standard Ebooks side) + labeler-bundle prep | **Yes — this is the corpus-matching/manifest layer already being built** (§6) |
| `pdomain-ocr-synth/docs/specs/2026-08-22-pgdp-typography-structure-synthesis-design.md` + M14/M15a/M15b specs | **Different workstream**: measuring book-level typography/page-structure *from scans* to drive synthetic-page *generation* (the reverse direction — synthesis, not prediction). Explicitly states "The synth should extend the shared `pdomain-book-tools` page model" and defers exact changes to "a separate cross-repository plan" — i.e. it already defers to the same Aug-21 design. | Adjacent; do not conflate with the new prediction model, but it independently validates book-tools as the shared-type owner |
| `pdomain-ocr-synth/docs/specs/12-glyph-annotations-emission.md` (M12) | Synth-side emission of `GlyphAnnotations`/`LigatureMark` (ligatures, long-s, swash) — **unbuilt** ("M12 is unbuilt... no annotation recipe block") | Same naming collision as book-tools' `glyph_annotations.py`; not inline style |
| `pd-ocr-trainer/src/pd_ocr_trainer/{ui,dataset_ui}.py` | UI copy mentioning "italics" as an example training-profile filter | Cosmetic; no span logic |
| `pdomain-ocr-cli` | none found | Not relevant |

`pdomain-ocr-synth`'s own `CLAUDE.md` milestone list ("M11 preview UI and M12 glyph annotations are the remaining milestones") is **stale** — the repo has since shipped M14 and M15a, and has an active M15b design, all PGDP-scan-measurement work unrelated to M11/M12. Worth a note back to that repo's docgraph, out of scope for this survey.

---

## 6. `pdomain-source-data` — the corpus-matching/manifest layer, already under construction

Confirms exactly the design's Task 6 intent (`docs/architecture/00-overview.md`, Created 2026-08-22): "prepares public-domain source data for recognition, detection, typography, glyph forms, and page regions. It is not a typography-only package... does not own model training, OCR inference, or source-corpus acquisition."

- Pins `pdomain-book-tools==0.26.1` exactly (current tag: v0.26.2 — one release behind), with wheel SHA-256 recorded in `configs/release-manifest.json`. Explicitly notes book-tools brings **Torch and DocTR as transitive dependencies**; this package does not import Torch itself.
- Package layout matches the design's recommended tree almost exactly: `pdomain_source_data/{audit,corrections,identity,manifests,matching,sources,splits,tasks/typography}/` — only `tasks/typography/` is built among the five planned task modules (`detection/recognition/typography/glyph_forms/page_regions`).
- `tasks/typography/css_styles.py`: a deterministic XHTML CSS cascade (`cssselect2`/`tinycss2`/`defusedxml`) computing `font-style, font-weight, font-variant, text-transform, letter-spacing, vertical-align, font-family` per element with inheritance/specificity, into `ComputedStyle` — this is the Gutenberg/Standard-Ebooks-side typography evidence extractor (the F2 side is covered by book-tools' `pgdp/f2/` instead).
- CLI reserves stable workflow names: `ingest, inventory, audit, match, align-books, materialize-labeler, import-corrections, promote, export-training, split` — directly matching plan Tasks 7-9 (`inventory and audit all three corpora`, `match editions and align books globally`, `materialize canonical records and immutable splits`).
- `ingest` currently handles pgdp/gutenberg/standard-ebooks read-only mounted inventories; "the typography audit emits canonical JSON and Parquet with live counts."
- No dependency edge exists (either direction) between `pdomain-source-data` and `pdomain-ocr-training` or `pdomain-ocr-synth` yet — it currently has no downstream consumers in this workspace.

**Exact file contents, now confirmed:**
- `css_styles.py` (370 lines): `computed_styles(css, xhtml) -> dict[str, ComputedStyle]` — full cascade over the 7 tracked properties. **Orphaned**: called only from its own test file; not wired into `sources/standard_ebooks.py` or any fusion path yet.
- `page_ground_truth.py` (527 lines): `GroundTruthCandidate`/`fuse_page_ground_truth`/`PageGroundTruth` — **whole-field** fusion (one value per named field — `"text"`, `"typography"`, `"geometry"` — per page, priority-ranked across `scan/human/pgdp_f2/gutenberg/standard_ebooks/spa_ocr/synthetic`, flagging disagreement as `requires_review`). Character-span granularity is not computed here — it is carried through opaquely inside the `"typography"` field as a `WordTypography` payload (a book-tools type, see below).
- `materialize.py` (835 lines): validates a promotion-receipt chain and emits `MaterializedTypography` (JSONL + Parquet, content-addressed) via `materialize_typography(...)`. Treats `WordTypography.spans` as an opaque validated blob for split/leakage bookkeeping; does not construct spans itself.
- `prepare_labeler.py` (620 lines) / `prepare_labeler_book.py` (1046 lines): build **human-labeler UI input**, not training data — module docstring literally says *"geometry-absent Task 9 labeler inputs."* PNG bytes are only `Image.open(...).verify()`-checked (format validity), never cropped. Evidence note written into every bundle: `"OCR alignment and geometry are unavailable."` Output literally sets `"geometry": "absent"`.
- `manifests/labeling_bundle.py`: `materialize_labeling_bundle`/`publish_labeling_bundle` — snapshots and hash-verifies whatever `LabelingBundle` (book-tools type) is handed to it; genuinely geometry-*optional* at the schema level, but nothing in this repo populates geometry today.

**The critical gap this deep dive surfaces**: `pdomain-book-tools`'s own `typography/alignment.py` already has the exact machinery to close this — `align_tokens()` (DP alignment of source text to OCR tokens) and `project_style_span()` (splits one `StyleSpan` at OCR word boxes → `ProjectedStyleSpan` with `crop_bbox`, optional `character_boxes`) — **but nothing in `pdomain-source-data` calls either function.** A workspace-wide grep for `align_tokens|project_style_span|project_token_ranges|ProjectedStyleSpan|OcrTokenRef` inside `pdomain_source_data/` returns nothing. And no image-cropping code (cutting pixels from a page raster given a bounding box) exists anywhere in `pdomain-source-data` — `PIL` is used only for PNG-decode verification and one unrelated audit histogram sampler. So: **the span↔geometry projection function already exists in `pdomain-book-tools`, but the "call it, then crop the image" glue that would turn it into actual (crop, spans) training pairs does not exist in any repo yet.** This is real, additional greenfield work beyond Tasks 10-14 as originally scoped — it most naturally belongs wherever real OCR geometry first becomes available for a page, which per the Aug-21 design is `pdomain-ocr-labeler-spa` (Task 9A: "the SPA runs the existing recognition and page-region models... and creates page, line, word, and optional character geometry") — a repo outside this survey's required list, but the one the design already assigns this exact responsibility to.

No downstream labeler-UI consumer of `prepare_labeler`/`LabelingBundle` output was found in `pd-ocr-labeler` or `pdomain-ocr-labeler-spa` in this workspace snapshot — the contract may not yet be connected to a running tool.

---

## 7. Recommendation

**Do not choose one of the brief's four options — the workspace already committed to combining three of them**, and two of the three are done. The only real decision left is whether to proceed with the two undone slices (`pdomain-ocr-training` Tasks 10-14, `pdomain-ocr-synth` Tasks 9B-9E) under the existing design, or to re-litigate the split. I recommend **proceeding under the existing design as-is** — it is not a proposal to evaluate, it is the current, tested, released state of two of the four repositories, and reopening the split now would strand already-shipped, already-released code in `pdomain-book-tools` and `pdomain-source-data`.

**Strongest justification**: `pdomain-book-tools` v0.25.0+ (tags exist through v0.26.2) already ships `StyleLabel`/`StyleSpan`/`TypographySpans`/`TypographyAnnotations`/`TypographyPageRecord` plus a working F2 parser that extracts all six target styles with grapheme-exact offsets and 373 passing tests, and `pdomain-source-data` already exists with a `tasks/typography/` module and a corpus-matching CLI pinned to that exact book-tools release. Recommending a different split now would mean discarding shipped, released, tested code — the "propose a repo split" question was already answered and executed for the harder two-thirds of the problem.

**Exact next steps, in dependency order:**

1. **`pdomain-ocr-training`** (Task 14, unblocks the flagged intent-map item): add `pdomain_ocr_training/formatting/{config,dataset,model,losses,train,evaluate,calibration,export}.py`; extend `protocols.py` with `train_formatting`/`evaluate_formatting` + `FormattingConfig`/`FormattingEvalConfig`/`FormattingEvalResult`; extend `local.py`/`local_eval.py`; add `tests/formatting/`; run `make ci`. Depends on `pdomain-source-data` emitting the training manifests (Task 9) and `pdomain-book-tools`'s released contract (already available).
2. **`pdomain-ocr-synth`** (Tasks 9B-9E): add `src/pdomain_ocr_synth/typography/{spans,font_manifest,feature_runs,mixed_renderer,physical_print,output}.py` and `recipes/typography/`. **New constraint to resolve first**: `pdomain-ocr-synth` currently has **zero dependency on `pdomain-book-tools`**, and adding one to reuse `StyleLabel`/`StyleSpan` directly would pull in book-tools' hard (non-extra) `torch`/`torchaudio`/`torchvision`/`python-doctr`/`transformers` dependencies into an otherwise lightweight (`pydantic`/`pillow`/`numpy`/`freetype-py`/`uharfbuzz`) package — a real install-size regression for a synthetic-data generator that has no other reason to need torch. `pdomain-ocr-training` already solved the identical problem for `GlyphFeatureSet` by defining a small, independent, torch-free Pydantic model rather than importing book-tools' `GlyphAnnotations` ("that would add a heavy foundation-lib dependency edge" — direct quote from that model's docstring). `pdomain-ocr-synth` should do the same: mirror `StyleLabel`/`StyleSpan`'s field shape locally rather than adding the book-tools dependency, or push for book-tools to split typography/pgdp/geometry into a torch-free extra first.
3. **Close the geometry-projection gap before Task 10 can train on real (non-synthetic) data**: `pdomain-book-tools/pdomain_book_tools/typography/alignment.py` already implements `align_tokens()` and `project_style_span()` — the exact function that turns a text-derived `StyleSpan` into an OCR-word-box-aligned `ProjectedStyleSpan.crop_bbox`. Nothing in `pdomain-source-data` calls it yet, and no repo in the workspace crops pixels from a page image given a bounding box for this purpose. Per the design, real OCR geometry is meant to come from `pdomain-ocr-labeler-spa` (Task 9A — outside this survey's repo list but the design's assigned owner), which would populate `OcrTokenRef`, call `project_style_span`, and hand `pdomain-source-data` genuinely geometry-present bundles for `materialize.py` to export. Until that wiring exists, `pdomain-ocr-training`'s `formatting/dataset.py` (Task 10-14) can only train on synthetic crops from `pdomain-ocr-synth` (item 2) — real-scan training data is blocked on this gap, not on anything in `pdomain-ocr-training` itself.
4. All of 1-3 remain gated behind explicit owner approval per the plan's own text — this survey does not recommend starting any of them without that approval step being taken first.

**File paths for follow-up**, in dependency order: `pdomain-book-tools/pdomain_book_tools/typography/`, `pdomain-book-tools/pdomain_book_tools/pgdp/f2/`, `pdomain-source-data/pdomain_source_data/tasks/typography/`, `pdomain-ocr-synth/docs/specs/2026-08-21` (does not exist — the ocr-synth-side design lives in `pdomain-ocr-training/docs/specs/2026-08-21-fine-grained-typography-model-design.md` §"Repository boundaries"), `pdomain-ocr-training/docs/plans/2026-08-21-fine-grained-typography-model.md` (Tasks 14, 9B-9E), `pdomain-ocr-training/pdomain_ocr_training/protocols.py`, `pdomain-ocr-training/pdomain_ocr_training/local.py`, `pdomain-ocr-training/pdomain_ocr_training/local_eval.py`.

---

## 8. Cross-repo dependency and versioning constraints

- **Version-pin inconsistency across consumers of `pdomain-book-tools`**: `pdomain-ocr-training` uses an open range (`>=0.14.1`); `pdomain-ocr-cli` uses an open range (`>=0.21.0`); `pdomain-source-data` pins exact (`==0.26.1`); `pdomain-ocr-synth` has **no dependency at all**; `pd-ocr-trainer` depends on **unpinned git HEAD** (`{ git = "https://github.com/ConcaveTrillion/pdomain-book-tools.git" }`, no tag/rev pin) — the riskiest of the five, though that repo is legacy and being superseded by `pdomain-ocr-training`. Any new consumer of the typography types should pin exactly, following `pdomain-source-data`'s pattern, not `pd-ocr-trainer`'s.
- **Torch is a hard dependency of `pdomain-book-tools`** (`torch>=2.6`, `torchaudio`, `torchvision`, `python-doctr`, `transformers` — all unconditional, not behind an extra). Any repo that adds a `pdomain-book-tools` dependency inherits this at install time regardless of which submodule it imports. `pdomain-ocr-training` solved this at the *import* level (lazy `__getattr__`, `[train]` extra) but that only defers torch import, not install — book-tools itself has no torch-free install mode. This is the single biggest constraint on giving `pdomain-ocr-synth` a direct book-tools dependency (see §7 step 2).
- **`pdomain-source-data` has no downstream consumers yet** — `pdomain-ocr-training` and `pdomain-ocr-synth` do not depend on it. The plan assumes `pdomain-ocr-training`'s `formatting/dataset.py` will consume `pdomain-source-data`'s exported training manifests (Task 9's `export-training`/`split` CLI verbs), but that dependency edge does not exist in any `pyproject.toml` today — it will need to be added as part of Task 10-14 work, not assumed already wired.
- **`pdomain-pgdp-api-client` has zero runtime coupling to `pdomain-book-tools`** — only a test-time sibling-source-tree import guarded by `pytest.skip` if the path is absent. This is intentional (keeps the fetch-only repo light) but means CI in that repo cannot catch a book-tools contract break unless both repos are checked out side by side, which is the current workspace layout but not guaranteed in isolated CI runners.
- **`CHANGELOG.md` documentation lag in `pdomain-book-tools`**: the typography/F2 work is filed under a `[Unreleased — next minor]` heading, but git tags (`v0.25.0`...`v0.26.2`) show it has in fact been released three-plus versions past that point — the changelog heading was not moved forward on release. Not a blocker, but a reason to trust `git tag`/`pyproject.toml` pins over `CHANGELOG.md` section headers when checking what's actually released.
