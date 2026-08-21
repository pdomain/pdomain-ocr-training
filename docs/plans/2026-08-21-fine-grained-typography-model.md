---
Status: draft
Owner: CT
Created: 2026-08-21
Last verified: 2026-08-21
Kind: plan
---

# Fine-Grained Typography Model Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a separate typography pipeline that predicts overlapping whole-word and grapheme-span styles from OCR crops, recognized text, and geometry.

**Architecture:** `pdomain-book-tools` owns F2 parsing and canonical span contracts. A new `pdomain-source-data` repository owns shared ingestion, cross-source evidence, correction exchange, audit, materialization, and leakage-safe manifests. `pdomain-ocr-labeler-spa` creates and corrects OCR geometry. `pdomain-ocr-training` owns a contextual text-conditioned visual model and a separate formatting runner.

**Tech Stack:** Python 3.11 through 3.13 by repository, Pydantic v2, `regex`, PyArrow, RapidFuzz or Edlib, HarfBuzz, FreeType, fontTools, Pillow/OpenCV, PyTorch, torchvision, pytest, Ruff, basedpyright, Docgraph.

---

This plan does not authorize implementation. Begin each task only after explicit approval. Commit steps are future checkpoints and must not run in this research session.

## Goal

Deliver a separately versioned typography data, training, and inference path without changing OCR recognition or page-region behavior.

## Architecture

Shared lossless parsing and annotations live in `pdomain-book-tools`. Cross-corpus preparation lives in a new owner-approved data repository. Synthetic rendering extends `pdomain-ocr-synth`. Model training and evaluation live in `pdomain-ocr-training`.

## Tech Stack

Use each repository's supported interpreter: Python `>=3.11,<3.14` for `pdomain-book-tools` and `pdomain-ocr-training`, and Python `>=3.13,<3.14` for `pdomain-ocr-synth`. The new data repository should support `>=3.11,<3.14`. Use Pydantic v2, `regex`, PyArrow, a reviewed edit-distance library, HarfBuzz, FreeType, fontTools, Pillow or OpenCV, PyTorch, torchvision, pytest, Ruff, basedpyright, and Docgraph.

## Global Constraints

Do not implement, create a repository, download fonts, train a model, commit, or deploy without explicit owner approval. Preserve all raw source bytes and unrelated working-tree changes. Keep synthetic assets out of real validation and test partitions. Before any future checkpoint, run each repository's own CI and Docgraph gate.

## File map and dependency order

Work proceeds in this order:

1. `pdomain-book-tools` adds lossless source, label, span, and annotation types.
2. `pdomain-book-tools` adds the F2 tokenizer, parser, offset map, rules, and local OCR alignment.
3. `pdomain-source-data` is created and pins the released `pdomain-book-tools` contract.
4. The data repository adds shared inventories, source artifact identity, a work and edition evidence graph, global alignment, geometry-optional labeler bundles, audits, and splits.
5. The inbound bundle schema is released and pinned in `pdomain-ocr-labeler-spa`. The separately approved SPA plan implements OCR/version capture, reviewed geometry, durable corrections, and correction-bundle export.
6. `pdomain-source-data` imports the returned correction bundle, fuses `PageGroundTruth`, and promotes reviewed task manifests.
7. `pdomain-ocr-synth` adds font manifests, mixed-span shaping, physical print simulation, and canonical typography output.
8. `pdomain-ocr-training` adds a separate formatting dataset, baselines, contextual model, runner, evaluation, calibration, and export.
9. Inference integration begins only after offline acceptance.

Every repository uses its own branch and CI gate. Never combine cross-repository changes in one commit. Every generated dataset lives outside Git. A content-addressed manifest references it.

### Task 1: Add canonical typography labels and span types

**Files:**

- Create: `/workspaces/pdomain/pdomain-book-tools/pdomain_book_tools/typography/__init__.py`
- Create: `/workspaces/pdomain/pdomain-book-tools/pdomain_book_tools/typography/labels.py`
- Create: `/workspaces/pdomain/pdomain-book-tools/pdomain_book_tools/typography/spans.py`
- Create: `/workspaces/pdomain/pdomain-book-tools/tests/typography/test_labels.py`
- Create: `/workspaces/pdomain/pdomain-book-tools/tests/typography/test_spans.py`

- [ ] **Step 1: Write failing normalization and overlap tests**

```python
def test_overlapping_spans_remain_independent() -> None:
    spans = TypographySpans(
        grapheme_count=5,
        spans=[
            StyleSpan(label=StyleLabel.ITALIC, start=0, end=5),
            StyleSpan(label=StyleLabel.BOLD, start=1, end=4),
        ],
    )
    assert spans.labels_at(2) == {StyleLabel.ITALIC, StyleLabel.BOLD}
```

- [ ] **Step 2: Run focused tests and confirm missing imports**

Run: `cd /workspaces/pdomain/pdomain-book-tools && uv run pytest -n auto tests/typography/test_labels.py tests/typography/test_spans.py -v`

Expected: collection fails because `pdomain_book_tools.typography` does not exist.

- [ ] **Step 3: Implement strict enums and half-open spans**

Define `StyleLabel`, `KnowledgeState`, `LabelSource`, `ConfidenceTier`, `SourceSlice`, `StyleSpan`, and `TypographySpans`. Validate `0 <= start < end <= grapheme_count`. Do not add `regular` as a positive span.

- [ ] **Step 4: Verify types and serialization**

Run: `cd /workspaces/pdomain/pdomain-book-tools && uv run pytest -n auto tests/typography/test_labels.py tests/typography/test_spans.py -v`

Expected: all new tests pass, including overlapping labels, unknown enum rejection, empty spans, and JSON round trips.

- [ ] **Step 5: Run the repository gate and checkpoint**

Run: `cd /workspaces/pdomain/pdomain-book-tools && make ci AI=1`

Expected: the existing suite and new tests pass. Rollback: revert only the Task 1 commit; no serialized production payload depends on it yet.

### Task 2: Add provenance-rich page records and inference annotations

**Files:**

- Create: `/workspaces/pdomain/pdomain-book-tools/pdomain_book_tools/typography/records.py`
- Create: `/workspaces/pdomain/pdomain-book-tools/pdomain_book_tools/typography/annotations.py`
- Modify: `/workspaces/pdomain/pdomain-book-tools/pdomain_book_tools/ocr/word.py`
- Modify: `/workspaces/pdomain/pdomain-book-tools/pdomain_book_tools/ocr/__init__.py`
- Test: `/workspaces/pdomain/pdomain-book-tools/tests/typography/test_records.py`
- Test: `/workspaces/pdomain/pdomain-book-tools/tests/typography/test_annotations.py`
- Test: `/workspaces/pdomain/pdomain-book-tools/tests/ocr/test_word_pydantic_schema.py`

- [ ] **Step 1: Write failing record and backward-compatibility tests**

Test exact full `F2.json` base64 round-trip, page-key and lexical-value ranges, decoded-page hash validation, grapheme source slices, artifact versions, parser warnings, alignment evidence, and `None` versus reviewed-empty annotations. Load an old `Word` fixture without the new field and assert byte-equivalent output except for intentionally omitted optional keys.

```python
def test_empty_and_unknown_annotations_are_distinct(pixel_bbox: BoundingBox) -> None:
    unknown = Word(text="word", bounding_box=pixel_bbox)
    reviewed = Word(
        text="word",
        bounding_box=pixel_bbox,
        typography_annotations=TypographyAnnotations(spans=[]),
    )
    assert unknown.typography_annotations is None
    assert reviewed.typography_annotations is not None
    assert reviewed.typography_annotations.spans == []
```

- [ ] **Step 2: Run the focused tests**

Run: `cd /workspaces/pdomain/pdomain-book-tools && uv run pytest -n auto tests/typography tests/ocr/test_word_pydantic_schema.py -v`

Expected: failures identify missing record and annotation types.

- [ ] **Step 3: Implement schema version `1.0`**

Add `ArtifactRef`, `TextIdentity`, `Grapheme`, `OcrTokenRef`, `AlignmentEvidence`, and `TypographyPageRecord`. Add optional `typography_annotations` to `Word`. Omit it from serialization when `None`, following `glyph_annotations` precedent.

- [ ] **Step 4: Verify the torch-free public contract**

Run: `cd /workspaces/pdomain/pdomain-book-tools && uv run pytest -n auto tests/typography tests/ocr/test_word_pydantic_schema.py -v && make ci AI=1`

Expected: all tests pass and no Torch import appears. Rollback: revert Task 2 while retaining Task 1 types if downstream work has not started.

### Task 3: Tokenize F2 without losing byte offsets

**Files:**

- Create: `/workspaces/pdomain/pdomain-book-tools/pdomain_book_tools/pgdp/f2/__init__.py`
- Create: `/workspaces/pdomain/pdomain-book-tools/pdomain_book_tools/pgdp/f2/tokens.py`
- Create: `/workspaces/pdomain/pdomain-book-tools/pdomain_book_tools/pgdp/f2/offsets.py`
- Create: `/workspaces/pdomain/pdomain-book-tools/tests/pgdp/f2/test_tokens.py`
- Create: `/workspaces/pdomain/pdomain-book-tools/tests/pgdp/f2/test_offsets.py`
- Create fixtures: `/workspaces/pdomain/pdomain-book-tools/tests/pgdp/f2/fixtures/*.txt`

- [ ] **Step 1: Copy minimal licensed fixtures from audited pages**

Fixtures must cover `<i>`, `<b>`, `<sc>`, `<g>`, `<f>`, project-authorized `<u>`, unapproved `<u>`, the four observed nesting orders, punctuation inside and outside tags, paragraph reopening, block markers, `[** ...]`, caret and underscore forms, Unicode combining marks, and the unclosed `<sc>` page fragment.

- [ ] **Step 2: Write failing token and source-map tests**

```python
def test_visible_grapheme_maps_to_raw_bytes() -> None:
    parsed = tokenize_f2("<i>e\u0301</i>,".encode())
    assert parsed.visible_text == "e\u0301,"
    assert parsed.graphemes[0].source_slices == [SourceSlice(byte_start=3, byte_end=6)]
    assert parsed.graphemes[1].source_slices == [SourceSlice(byte_start=10, byte_end=11)]
```

- [ ] **Step 3: Implement a lexical JSON and byte-oriented scanner**

Read the full `F2.json` bytes. Locate page keys and string values without JSON reserialization. Decode JSON escapes with a mapping back to lexical artifact byte slices. Then recognize controls without regular-expression replacement, segment visible runs with `regex` `\X`, and retain exact artifact slices. Unknown or invalid constructs become tokens and warnings.

- [ ] **Step 4: Add deterministic and property tests**

For each fixture, parse twice and compare serialized bytes. Reconstruct every visible grapheme from its raw slices or a declared normalization operation. Fuzz arbitrary tag truncation and assert no crash and no cross-page state.

- [ ] **Step 5: Run gates and checkpoint**

Run: `cd /workspaces/pdomain/pdomain-book-tools && uv run pytest -n auto tests/pgdp/f2 -v && make ci AI=1`

Expected: all fixtures pass; the unclosed `<sc>` produces `unclosed_tag` and no style leaks to a second parse. Rollback: revert Task 3; raw corpora remain untouched.

### Task 4: Resolve F2 spans, notes, and project rules

**Files:**

- Create: `/workspaces/pdomain/pdomain-book-tools/pdomain_book_tools/pgdp/f2/parser.py`
- Create: `/workspaces/pdomain/pdomain-book-tools/pdomain_book_tools/pgdp/f2/project_rules.py`
- Create: `/workspaces/pdomain/pdomain-book-tools/pdomain_book_tools/pgdp/f2/warnings.py`
- Test: `/workspaces/pdomain/pdomain-book-tools/tests/pgdp/f2/test_parser.py`
- Test: `/workspaces/pdomain/pdomain-book-tools/tests/pgdp/f2/test_project_rules.py`

- [ ] **Step 1: Write failing semantic tests**

Assert maximal grapheme spans, independent nested labels, exact punctuation boundaries, small-cap normalization evidence, letter-space removal maps, note quarantine, superscript and subscript parsing, block context, unresolved `<f>`, project-authorized `<u>` mapped to `underline`, and unapproved `<u>` mapped to `unknown` with quarantine.

- [ ] **Step 2: Implement `F2Parser.parse_page()`**

The method accepts bytes, page identity, Project Comments bytes, and a guideline version. It returns `TypographyPageRecord`. It must not call `PGDPResults.process()`.

- [ ] **Step 3: Add a versioned rule registry**

Rules are keyed by project ID plus comments SHA-256. An undefined `<f>` returns `unknown` with `ambiguous_font_change`. No heuristic can silently promote it.

- [ ] **Step 4: Test the mounted audit fixture set**

Run: `cd /workspaces/pdomain/pdomain-book-tools && uv run pytest -n auto tests/pgdp/f2/test_parser.py tests/pgdp/f2/test_project_rules.py -v`

Expected: every supported fixture passes; malformed fixtures remain serializable but `training_eligible` is false.

- [ ] **Step 5: Run full CI and checkpoint**

Run: `cd /workspaces/pdomain/pdomain-book-tools && make ci AI=1`

Expected: no changes to existing `PGDPResults` behavior. Rollback: revert Task 4 while keeping the lossless tokenizer for later repair.

### Task 5: Align parsed graphemes to OCR geometry

**Files:**

- Create: `/workspaces/pdomain/pdomain-book-tools/pdomain_book_tools/typography/alignment.py`
- Create: `/workspaces/pdomain/pdomain-book-tools/pdomain_book_tools/typography/normalization.py`
- Test: `/workspaces/pdomain/pdomain-book-tools/tests/typography/test_alignment.py`
- Test: `/workspaces/pdomain/pdomain-book-tools/tests/typography/test_normalization.py`

- [ ] **Step 1: Write failing one-to-many and many-to-one tests**

Cover punctuation, split and merged OCR words, page-break fragments, ligatures, deleted characters, combining marks, small-cap case comparison, letter spacing, and a style crossing two word boxes.

- [ ] **Step 2: Implement explicit comparison views**

Each normalization returns transformed graphemes plus an operation map. Allowed operations are Unicode canonical equivalence, approved quote and dash equivalence, case-insensitive small-cap comparison, soft-hyphen removal, and validated letter-space removal.

- [ ] **Step 3: Implement monotonic token alignment**

Return the best path, runner-up margin, edit operations, and accepted flag. Reject low-margin paths through a configurable threshold recorded in the output manifest.

- [ ] **Step 4: Project spans without changing canonical source spans**

Create crop projections that split a source span at OCR word boundaries while retaining one source-span identifier. Character boxes remain optional.

- [ ] **Step 5: Verify and checkpoint**

Run: `cd /workspaces/pdomain/pdomain-book-tools && uv run pytest -n auto tests/typography -v && make ci AI=1`

Expected: deterministic alignments and explicit rejection for ambiguous examples. Rollback: revert Task 5; parsed source records remain usable.

### Task 5A: Release and pin the shared book-tools contract

**Files:**

- Modify: `/workspaces/pdomain/pdomain-book-tools/pyproject.toml` only if the repository's version workflow requires it
- Modify: `/workspaces/pdomain/pdomain-book-tools/CHANGELOG.md` only if present and required by repository guidance
- Modify after release: `/workspaces/pdomain/pdomain-source-data/pyproject.toml`

- [ ] **Step 1: Verify the release candidate**

Run: `cd /workspaces/pdomain/pdomain-book-tools && make ci AI=1 && make build AI=1`

Expected: CI passes and the built wheel exposes the typography schema and F2 parser without Torch.

- [ ] **Step 2: Obtain explicit publish approval**

Publishing is an external write. Stop unless the owner approves the exact version and package index. Follow the repository's release runbook rather than inventing a command.

- [ ] **Step 3: Publish and verify the exact version**

After approval, publish the immutable version through the supported release workflow. Install it into a clean temporary environment and run a smoke parse plus schema round trip.

Expected: the installed package version and wheel SHA-256 match the release record.

- [ ] **Step 4: Pin the data repository**

Set `pdomain-book-tools==<approved-version>` and record the wheel SHA-256 in the data repository lockfile and environment manifest. Replace `<approved-version>` with the owner-approved immutable version during execution; do not use a range.

Rollback: yank or deprecate only through the package-index policy, publish a corrective version, and keep the data repository on the last verified pin.

### Task 6: Create the shared source-data repository

**Files:**

- Create repository: `/workspaces/pdomain/pdomain-source-data`
- Create: `pyproject.toml`, `Makefile`, `AGENTS.md`, `DOCGRAPH.md`, `docgraph.toml`
- Create: `pdomain_source_data/__init__.py`, `cli.py`, `paths.py`, `hashing.py`
- Create: `tests/test_cli.py`, `tests/test_hashing.py`, `docs/architecture/00-overview.md`

- [ ] **Step 1: Confirm the repository boundary with the owner**

The owner approved `pdomain-source-data` as the shared preparation boundary for recognition, detection, typography, glyph forms, and page regions. Do not create a typography-only replacement.

- [ ] **Step 2: Scaffold a strict data package**

Depend on the released `pdomain-book-tools` version containing Tasks 1 through 5. Its current transitive installation includes Torch and DocTR, so do not describe this first version as lightweight or torch-free. The data package itself must not import or call Torch. Add `pydantic`, `pyarrow`, `regex`, and the chosen edit-distance library. A later packaging project may make book-tools OCR dependencies optional. This plan does not hide that current cost.

- [ ] **Step 3: Write failing CLI tests**

Commands are `ingest`, `inventory`, `audit`, `match`, `align-books`, `materialize-labeler`, `import-corrections`, `promote`, `export-training`, and `split`. Task-specific commands require `--task`. Every command accepts `--output`, `--config`, and `--dry-run`; generated outputs require an explicit non-root path.

- [ ] **Step 4: Implement content-addressed output helpers**

Reject `/`, a workspace root, and unresolved environment variables. Write to a temporary sibling directory, validate, then atomically rename and update a manifest pointer.

- [ ] **Step 5: Run the new repository gate**

Run: `cd /workspaces/pdomain/pdomain-source-data && make ci AI=1`

Expected: Ruff, basedpyright, pytest, and Docgraph strict check pass. Rollback: remove only the unregistered new repository after confirming no generated corpus points to it.

### Task 7: Inventory and audit all three corpora

**Files:**

- Create: `/workspaces/pdomain/pdomain-source-data/pdomain_source_data/inventory.py`
- Create: `/workspaces/pdomain/pdomain-source-data/pdomain_source_data/sources/pgdp.py`
- Create: `/workspaces/pdomain/pdomain-source-data/pdomain_source_data/sources/gutenberg.py`
- Create: `/workspaces/pdomain/pdomain-source-data/pdomain_source_data/sources/standard_ebooks.py`
- Create: `/workspaces/pdomain/pdomain-source-data/pdomain_source_data/audit/corpus.py`
- Test: `/workspaces/pdomain/pdomain-source-data/tests/test_inventory.py`
- Test: `/workspaces/pdomain/pdomain-source-data/tests/audit/test_corpus.py`

- [ ] **Step 1: Freeze a tiny manifest fixture**

Use three PGDP pages, two Gutenberg artifacts, and one Standard Ebooks repository fixture. Record source URLs, retrieval UTC, paths, sizes, SHA-256, Git commits, artifact kinds, and licenses.

- [ ] **Step 2: Implement streaming inventory readers**

PGDP reads `project.json` and `rounds/F2.json`. Gutenberg prefers curated HTML then plain text and reads `.pull-complete.json`. Standard Ebooks reads `content.opf`, XHTML, CSS, `LICENSE.md`, origin URL, and commit SHA.

Run the explicit inbound commands:

```bash
uv run pdomain-source-data ingest pgdp --corpus /workspaces/pdomain-data/pgdp-corpus --output /workspaces/pdomain-data/source-data/pgdp-v1
uv run pdomain-source-data ingest gutenberg --corpus /workspaces/gutenberg-corpus --output /workspaces/pdomain-data/source-data/gutenberg-v1
uv run pdomain-source-data ingest standard-ebooks --corpus /workspaces/standardebooks-corpus --output /workspaces/pdomain-data/source-data/standard-ebooks-v1
```

Expected: each command reads the mounted corpus without modifying it and emits a content-addressed source manifest. Acquisition remains in source-specific clients or mounted mirrors.

- [ ] **Step 3: Implement the reproducible audit**

Run: `uv run pdomain-source-data audit --task typography --config configs/local.toml --output /workspaces/pdomain-data/typography/audits/2026-08-21`

Expected: JSON and Parquet summaries reproduce 80 projects, 79 F2 files, 21,353 F2 pages, tag counts `i=27460`, `sc=10090`, `b=1958`, `f=35`, `g=0`, 57 nested opens, and one known unclosed `<sc>`. If canonical grapheme rules change candidate counts, include an explicit parser-version migration note.

- [ ] **Step 4: Add distribution enrichers**

Compute image resolution, contrast, blur, skew, and foreground density from source images. Compute OCR confidence and alignment error only when an optional reviewed SPA result has been imported. Do not require source corpora to provide OCR geometry. Keep `difficulty` and `image_source` separate from scan quality. Mark publication period, font family, and language unavailable until sourced.

- [ ] **Step 5: Verify and checkpoint**

Run: `cd /workspaces/pdomain/pdomain-source-data && make ci AI=1`

Expected: the fixture and mounted read-only smoke audit pass. Rollback: repoint `audits/current.json` to the prior manifest; never alter source corpora.

### Task 8: Match editions and align books globally

**Files:**

- Create: `/workspaces/pdomain/pdomain-source-data/pdomain_source_data/identity/entities.py`
- Create: `/workspaces/pdomain/pdomain-source-data/pdomain_source_data/matching/edition_graph.py`
- Create: `/workspaces/pdomain/pdomain-source-data/pdomain_source_data/matching/page_align.py`
- Create: `/workspaces/pdomain/pdomain-source-data/pdomain_source_data/tasks/typography/css_styles.py`
- Test: `/workspaces/pdomain/pdomain-source-data/tests/matching/test_edition_graph.py`
- Test: `/workspaces/pdomain/pdomain-source-data/tests/matching/test_page_align.py`
- Test: `/workspaces/pdomain/pdomain-source-data/tests/tasks/typography/test_css_styles.py`

- [ ] **Step 1: Write rejection-first tests**

Reject same title with different edition matter, PG ID without distinctive-text support, SE `dc:source` without physical-edition evidence, low-margin alignment, generated Gutenberg derivatives when curated artifacts exist, and CSS tags whose computed style contradicts naive element mapping.

- [ ] **Step 2: Implement candidate generation**

Start with PG ebook number, then title, author, source URL, repository sources, and text fingerprints. Preserve every rejected candidate and reason.

- [ ] **Step 3: Implement the edition gate**

Require identifier lineage plus two independent signals from edition matter, DP credit, scan source, distinctive text, and high-margin alignment. Make thresholds configuration fields stored in the run manifest.

- [ ] **Step 4: Implement global monotonic alignment**

Allow `1:0`, `0:1`, `1:1`, `1:N`, and `N:1` transitions. Add fixtures for blank pages, plates, moved footnotes, merged pages, split pages, and page-break word joining.

- [ ] **Step 5: Resolve Standard Ebooks computed styles**

Parse inherited CSS for `font-style`, `font-weight`, `font-variant`, `text-transform`, `letter-spacing`, `vertical-align`, and `font-family`. Record semantic markup separately. Do not map `<b>` to bold.

- [ ] **Step 6: Run audit and manual checkpoint**

Run: `uv run pdomain-source-data match --task typography --config configs/local.toml --output /workspaces/pdomain-data/typography/matches/pg-v1 --dry-run`

Expected: 80 PG candidates, 80 local text artifacts, zero local HTML artifacts for this cohort, and no automatic edition acceptance without evidence. The SE exact-ID join reports zero for the current 80 PGDP projects. A stratified human audit must approve precision before projection.

Rollback: retain candidate evidence, withdraw the promoted match manifest, and lower no threshold without a new version.

### Task 9: Materialize canonical records and immutable splits

**Files:**

- Create: `/workspaces/pdomain/pdomain-source-data/pdomain_source_data/tasks/typography/materialize.py`
- Create: `/workspaces/pdomain/pdomain-source-data/pdomain_source_data/splits/manifest.py`
- Create: `/workspaces/pdomain/pdomain-source-data/schemas/typography-page-record-1.0.json`
- Test: `/workspaces/pdomain/pdomain-source-data/tests/tasks/typography/test_materialize.py`
- Test: `/workspaces/pdomain/pdomain-source-data/tests/splits/test_manifest.py`

- [ ] **Step 1: Write byte-reproducibility tests**

Identical input hashes, config, and tool version must produce identical JSONL, Parquet, audit, and split-manifest hashes.

- [ ] **Step 2: Implement leakage grouping**

Group work, edition, volumes, duplicate scans, perceptual page hashes, PG variants, PGDP projects, and SE derivatives. Store every edge and evidence. Resolve ambiguity by merging, not splitting.

- [ ] **Step 3: Allocate train, validation, calibration, test, and challenges**

Use a stored seed and group hash. Target 80/10/10 by book for train, validation, and test. Draw calibration only from validation groups. Keep controlled challenge groups separate.

- [ ] **Step 4: Add a leakage gate**

Run: `uv run pdomain-source-data split --task typography --config configs/local.toml --output /workspaces/pdomain-data/typography/splits/v1`

Expected: zero scan, work, edition, text-fingerprint, or derivative edges cross partitions. Rerunning produces the same manifest hash.

- [ ] **Step 5: Promote only audited outputs**

Materialization reports eligible, masked, and quarantined examples per label and source. Rollback repoints `datasets/current.json` and `splits/current.json` to prior content hashes.

### Task 9A: Exchange source evidence and reviewed pages with the labeler

**Files:**

- Create: `/workspaces/pdomain/pdomain-source-data/pdomain_source_data/manifests/labeling_bundle.py`
- Create: `/workspaces/pdomain/pdomain-source-data/pdomain_source_data/corrections/importer.py`
- Create: `/workspaces/pdomain/pdomain-source-data/pdomain_source_data/tasks/typography/page_ground_truth.py`
- Create: `/workspaces/pdomain/pdomain-source-data/schemas/labeling-bundle-1.0.json`
- Create: `/workspaces/pdomain/pdomain-source-data/schemas/correction-bundle-1.0.json`
- Test: `/workspaces/pdomain/pdomain-source-data/tests/manifests/test_labeling_bundle.py`
- Test: `/workspaces/pdomain/pdomain-source-data/tests/corrections/test_importer.py`
- Test: `/workspaces/pdomain/pdomain-source-data/tests/tasks/typography/test_page_ground_truth.py`
- Integrate under the separately approved SPA plan: `/workspaces/pdomain/pdomain-ocr-labeler-spa/docs/specs/2026-08-21-typography-review-and-training-export-design.md`

- [ ] **Step 1: Write geometry-optional inbound bundle tests**

Assert a bundle can contain a page image, PGDP F2, Gutenberg and Standard Ebooks evidence, match edges, conflicts, hashes, and no OCR geometry. Optional cached OCR must carry model, configuration, preprocessing, and artifact hashes.

- [ ] **Step 2: Materialize the work and edition evidence graph**

Represent work, physical edition, source artifact, and page or segment separately. Preserve PG ebook numbers, DP credit, scan provenance, edition matter, source metadata, text fingerprints, accepted and rejected alignments, thresholds, runner-up margins, and manual confirmations.

- [ ] **Step 3: Export a labeling bundle**

Run: `uv run pdomain-source-data materialize-labeler --task typography --config configs/local.toml --output /workspaces/pdomain-data/typography/labeler/input-v1`

Expected: the bundle is immutable, content-addressed, geometry-optional, and readable without importing source-data internals. Acquisition remains outside this command.

- [ ] **Step 4: Release and pin the inbound contract in the SPA**

Release the shared labeling-bundle types through `pdomain-book-tools` or the approved portable schema package. Pin the immutable version and schema hash in the SPA. Do not import `pdomain-source-data` internals.

- [ ] **Step 5: Complete the SPA round-trip checkpoint**

Follow the separately approved SPA implementation plan. Prove that a geometry-optional bundle loads, the configured OCR and page-region models record their versions and preprocessing, the reviewer corrects text, geometry, and typography, the event store reloads the exact state, and the SPA emits an immutable correction bundle. Source-data correction import remains blocked until this checkpoint passes.

- [ ] **Step 6: Import a reviewed correction bundle**

Require the inbound bundle ID, page and image hashes, OCR and page-region model metadata, taxonomy version, explicit positive, negative, and unknown label states, corrected text, typography spans, correction revisions, reviewer provenance, and event-store page heads. Geometry must include named coordinate spaces, source orientation, source-to-oriented-page transforms, crop transforms, crop-recipe version, padding, resampling, and preprocessing hashes. Reject stale, unknown, incomplete, cross-split, contradictory, and unsupported records.

- [ ] **Step 7: Fuse page ground truth by field**

Treat the scan as visual authority, SPA corrections as reviewed authority, PGDP F2 as the strongest initial page-local typography evidence, Gutenberg as final-text and post-processing evidence, and Standard Ebooks as weak editorial evidence. Never select one corpus as the unexplained authority for the whole page. Round-trip taxonomy-versioned label states and every geometry coordinate and transform field into `PageGroundTruth`.

- [ ] **Step 8: Verify deterministic round trip**

Run: `cd /workspaces/pdomain/pdomain-source-data && make ci AI=1`

Expected: source bundle to reviewed correction import produces a versioned `PageGroundTruth` with exact field-level evidence. Repeating identical inputs produces identical canonical manifest hashes. Rollback restores the prior promoted source-data pointer and retains the rejected correction bundle for audit.

### Task 9B: Add a licensed historical-font manifest to the existing synthesizer

**Files:**

- Create: `/workspaces/pdomain/pdomain-ocr-synth/src/pdomain_ocr_synth/typography/__init__.py`
- Create: `/workspaces/pdomain/pdomain-ocr-synth/src/pdomain_ocr_synth/typography/font_manifest.py`
- Create: `/workspaces/pdomain/pdomain-ocr-synth/recipes/typography/fonts.yaml`
- Create: `/workspaces/pdomain/pdomain-ocr-synth/tests/typography/test_font_manifest.py`
- Modify: `/workspaces/pdomain/pdomain-ocr-synth/src/pdomain_ocr_synth/recipe/models.py`
- Modify: `/workspaces/pdomain/pdomain-ocr-synth/pyproject.toml`
- Regenerate: `/workspaces/pdomain/pdomain-ocr-synth/uv.lock`
- Regenerate: `/workspaces/pdomain/pdomain-ocr-synth/docs/specs/recipe.schema.json`

- [ ] **Step 1: Approve the initial font and licensing policy**

Begin with reviewed OFL builds from EB Garamond 12, Junicode 2, IM FELL text families, Old Standard TT, Sorts Mill Goudy, Source Serif 4, Libertinus Serif, Cormorant, UnifrakturMaguntia or Cook, Baskervville, Libre Caslon Text, and one Bodoni family. The owner must approve raster-generation and trained-model use before download automation.

- [ ] **Step 2: Write failing manifest-validation tests**

```python
def test_font_manifest_rejects_hash_mismatch(tmp_path: Path) -> None:
    font = tmp_path / "face.otf"
    font.write_bytes(b"not-the-declared-font")
    with pytest.raises(FontManifestError, match="sha256"):
        load_font_entry(_entry(path=font, sha256="0" * 64))


def test_related_faces_share_lineage() -> None:
    entries = load_catalog(FONT_FIXTURE)
    assert entries["family-roman"].lineage_id == entries["family-italic"].lineage_id
```

- [ ] **Step 3: Inspect pinned binaries with fontTools**

Record exact file SHA-256, family and PostScript names, version, upstream URL and commit, SPDX license, license-file hash, Reserved Font Names, `cmap`, GSUB, GPOS, `fvar`, `STAT`, `OS/2`, and supported scripts, languages, and features.

Add `fonttools` to runtime dependencies because manifest validation uses it. Run `uv lock` through the repository's supported dependency workflow and review the full lockfile diff.

- [ ] **Step 4: Preserve the no-bundled-font rule**

The catalog references user-provided or cache paths. An optional interactive fetch command verifies hashes and writes license files beside the cache. It never runs during tests or CI.

- [ ] **Step 5: Regenerate schema and verify**

Run: `cd /workspaces/pdomain/pdomain-ocr-synth && make schema AI=1 && make ci AI=1`

Expected: manifest fixtures pass, hash or license failures stop validation, missing optional fonts warn, and no font binary enters Git. Rollback: restore the prior recipe schema and omit the typography catalog.

### Task 9C: Render exact mixed grapheme spans with HarfBuzz and FreeType

**Files:**

- Create: `/workspaces/pdomain/pdomain-ocr-synth/src/pdomain_ocr_synth/typography/spans.py`
- Create: `/workspaces/pdomain/pdomain-ocr-synth/src/pdomain_ocr_synth/typography/feature_runs.py`
- Create: `/workspaces/pdomain/pdomain-ocr-synth/src/pdomain_ocr_synth/typography/mixed_renderer.py`
- Modify: `/workspaces/pdomain/pdomain-ocr-synth/src/pdomain_ocr_synth/render/sample.py`
- Test: `/workspaces/pdomain/pdomain-ocr-synth/tests/typography/test_feature_runs.py`
- Test: `/workspaces/pdomain/pdomain-ocr-synth/tests/typography/test_mixed_renderer.py`

- [ ] **Step 1: Write failing shaping fixtures**

Pin glyph IDs, clusters, advances, and offsets for `AV`, `To`, supported ligatures, combining marks, Turkish, Greek, Cyrillic, blackletter historical forms, `smcp`, `c2sc`, `sups`, `subs`, and punctuation inside or outside style spans.

- [ ] **Step 2: Add grapheme-first label generation**

Generate independent style bitsets over extended graphemes. Include whole-word, one boundary, two boundaries, overlaps, stem-only style with regular punctuation, font changes, and structural drop-cap context.

- [ ] **Step 3: Shape maximal compatible runs with safe context**

Run boundaries occur only when face, axes, size, baseline, script, language, direction, or features change. Use HarfBuzz monotone-character clusters. Preserve extended-grapheme boundaries independently.

- [ ] **Step 4: Implement kerning and tracking correctly**

Normal samples keep HarfBuzz `kern=1`; controlled negatives use `kern=0`. Tracking adds advance only between safe clusters and records font-unit and pixel deltas. Tests prove it never separates marks or splits active ligatures.

- [ ] **Step 5: Separate real features from fallbacks**

Prefer real italic, bold, `smcp`, `c2sc`, `sups`, `subs`, and variable axes. Record simulated shear, emboldening, scaled capitals, and baseline-shifted glyphs as distinct `render_method` values.

- [ ] **Step 6: Verify geometry truth**

Every ink pixel lies within a glyph or shared-cluster polygon. Ligature graphemes share geometry and carry `shared_ligature_cluster`. No test invents independent boxes for inseparable glyphs.

- [ ] **Step 7: Run the synthesizer gate**

Run: `cd /workspaces/pdomain/pdomain-ocr-synth && uv run pytest -n auto tests/typography -v && make ci AI=1`

Expected: exact style spans and deterministic cluster truth pass across pinned fixtures. Rollback: keep font manifests and disable the mixed renderer in recipe validation.

### Task 9D: Add calibrated historical print and scan simulation

**Files:**

- Create: `/workspaces/pdomain/pdomain-ocr-synth/src/pdomain_ocr_synth/typography/physical_print.py`
- Create: `/workspaces/pdomain/pdomain-ocr-synth/src/pdomain_ocr_synth/typography/output.py`
- Modify: `/workspaces/pdomain/pdomain-ocr-synth/src/pdomain_ocr_synth/degradation/builtins.py`
- Modify: `/workspaces/pdomain/pdomain-ocr-synth/src/pdomain_ocr_synth/degradation/pipeline.py`
- Create: `/workspaces/pdomain/pdomain-ocr-synth/tests/typography/test_physical_print.py`
- Create: `/workspaces/pdomain/pdomain-ocr-synth/tests/typography/test_output.py`

- [ ] **Step 1: Write stage-isolation tests**

Each stage derives its seed from dataset seed, sample ID, stage name, and stage version. Adding a later paper effect must not change font choice, labels, shaping, or ink simulation.

- [ ] **Step 2: Add high-resolution clean rendering**

Render linear grayscale at four or eight times target resolution. Record hinting, render mode, clean image hash, and exact clean geometry.

- [ ] **Step 3: Apply effects in physical order**

Implement ink gain or erosion, uneven impression and broken strokes, paper tone and fibers, mirrored reverse-side show-through, page geometry, optical blur, one downsample, sensor noise, and codec output. Halftone applies only to suitable source strata.

- [ ] **Step 4: Fit parameter profiles from training scans**

Consume aggregate distributions from the data audit for foreground and background histograms, stroke width, edge softness, blur, skew, contrast, blocking, bleed-through, and crop margins. Do not read validation or test pages.

- [ ] **Step 5: Transform truth with the image**

Affine, homography, and dense-warp stages update cluster polygons, word boxes, line boxes, clipping, and occlusion. Pixel-only stages leave geometry unchanged.

- [ ] **Step 6: Emit canonical synthetic records**

Record generator and container versions, library versions, font and text hashes or licenses, feature ranges, axes, all stage parameters and seeds, clean and final hashes, and canonical grapheme spans from `pdomain-book-tools`.

- [ ] **Step 7: Verify and checkpoint**

Run: `cd /workspaces/pdomain/pdomain-ocr-synth && uv run pytest -n auto tests/typography tests/test_degradation.py -v && make schema AI=1 && make ci AI=1`

Expected: identity degradation reproduces the clean image, stage seeds isolate changes, all geometry stays valid or explicitly clipped, and font files remain unbundled. Rollback: select the prior degradation schema and renderer version in recipes.

### Task 9E: Prepare leakage-safe synthetic experiment manifests

**Files:**

- Create: `/workspaces/pdomain/pdomain-ocr-training/tests/formatting/test_synthetic_sampling.py`
- Create: `/workspaces/pdomain/pdomain-source-data/pdomain_source_data/tasks/typography/synthetic_manifest.py`
- Test: `/workspaces/pdomain/pdomain-source-data/tests/tasks/typography/test_synthetic_manifest.py`

- [ ] **Step 1: Lock text and font leakage controls**

Synthetic text comes only from training groups or separate public-domain works. All files in one font lineage stay together. Hold out several complete font lineages. Validation and test contain real scans only.

- [ ] **Step 2: Validate synthetic manifests without training**

Validate taxonomy versions, font lineage groups, text-source groups, stage seeds, renderer hashes, licenses, and separation from real validation and test manifests. Do not run effectiveness experiments before Tasks 10 through 12 provide the dataset, contextual model, evaluator, calibration, and abstention path.

- [ ] **Step 3: Verify and checkpoint**

Run the focused source-data and training sampling tests. Expected: deterministic manifests and no synthetic asset in a real validation or test partition. Rollback withdraws the synthetic manifest pointer without deleting rendered audit artifacts.

### Task 10: Add the smallest whole-word formatting baseline

**Files:**

- Create: `/workspaces/pdomain/pdomain-ocr-training/pdomain_ocr_training/formatting/__init__.py`
- Create: `/workspaces/pdomain/pdomain-ocr-training/pdomain_ocr_training/formatting/config.py`
- Create: `/workspaces/pdomain/pdomain-ocr-training/pdomain_ocr_training/formatting/dataset.py`
- Create: `/workspaces/pdomain/pdomain-ocr-training/pdomain_ocr_training/formatting/baseline.py`
- Create: `/workspaces/pdomain/pdomain-ocr-training/pdomain_ocr_training/formatting/evaluate.py`
- Create: `/workspaces/pdomain/pdomain-ocr-training/tests/formatting/test_config.py`
- Create: `/workspaces/pdomain/pdomain-ocr-training/tests/formatting/test_dataset.py`
- Create: `/workspaces/pdomain/pdomain-ocr-training/tests/formatting/test_baseline.py`

- [ ] **Step 1: Write torch-free config tests**

`FormattingConfig` includes manifest paths, active labels, encoder, crop size, batch size, learning rate, confidence weights, sampling caps, seed, calibration split, and output directory. Importing config and public protocols must not import Torch.

- [ ] **Step 2: Write dataset masking and sampling tests**

Assert unknown labels have zero loss mask, quarantine never loads for training, rare labels sample by book cap, confidence tiers apply weights, and no test group enters the training loader.

- [ ] **Step 3: Implement a whole-word multi-label baseline**

Use torchvision ResNet-18 or MobileNetV3 with independent logits. Report majority, rule-only, and neural results. Do not add formatting fields to `RecognitionConfig`.

- [ ] **Step 4: Train the smallest experiment**

Run: `uv run pdomain-ocr-training-formatting --config experiments/formatting/word-baseline.toml`

Expected: a checkpoint, frozen config, input manifest hashes, per-label metrics, calibration inputs, latency measurements, and error-review bundle. No acceptance claim uses random-page splits.

- [ ] **Step 5: Gate and rollback**

Run: `cd /workspaces/pdomain/pdomain-ocr-training && make ci AI=1`

Expected: existing recognition and detection tests remain unchanged. Rollback removes the baseline registry pointer; OCR tasks continue normally.

### Task 11: Add the contextual text-conditioned grapheme model

**Files:**

- Create: `/workspaces/pdomain/pdomain-ocr-training/pdomain_ocr_training/formatting/model.py`
- Create: `/workspaces/pdomain/pdomain-ocr-training/pdomain_ocr_training/formatting/losses.py`
- Create: `/workspaces/pdomain/pdomain-ocr-training/pdomain_ocr_training/formatting/train.py`
- Test: `/workspaces/pdomain/pdomain-ocr-training/tests/formatting/test_model.py`
- Test: `/workspaces/pdomain/pdomain-ocr-training/tests/formatting/test_losses.py`
- Test: `/workspaces/pdomain/pdomain-ocr-training/tests/formatting/test_train_step.py`

- [ ] **Step 1: Write shape and overlap tests**

For batch `B`, graphemes `G`, and labels `L`, assert grapheme logits `[B,G,L]`, word logits `[B,L]`, and valid masks `[B,G,L]`. Two labels can be positive at one grapheme. Assert the target-word mask selects exact scored graphemes within the contextual line.

- [ ] **Step 2: Write invariance and corruption tests**

Padding must not change valid logits. Unknown labels contribute zero loss. Text dropout produces an image-only path. OCR substitutions change only the intended grapheme queries. Masked neighbors and missing line context must use the recorded word-only fallback.

- [ ] **Step 3: Implement the model**

Use a compact CNN or ViT encoder with a high-resolution target-word view and a short-line context view. Add learned grapheme and position embeddings, target-box and word-boundary embeddings, geometry and OCR-confidence projections, and two to four cross-attention blocks. Use independent sigmoid logits, a target-word mask, and a pooled whole-word head that compares target and neighbor features. Keep text decoding absent.

- [ ] **Step 4: Implement confidence-weighted losses**

Add masked asymmetric BCE or focal loss, word BCE, boundary consistency, and cross-head consistency. Unit tests compute small tensors by hand.

- [ ] **Step 5: Train three locked comparisons**

Run whole-word baseline, word-only image queries, word-only text-conditioned queries, and two-view contextual queries with the same groups and seed set. Keep the contextual model as the primary experiment. Expected: complete comparable manifests and no claim until book-level confidence intervals exist.

- [ ] **Step 6: Gate and rollback**

Run: `cd /workspaces/pdomain/pdomain-ocr-training && make ci AI=1`

Expected: all formatting and existing OCR tests pass. Rollback repoints the experiment registry to the word baseline.

### Task 12: Add calibration, abstention, and complete evaluation

**Files:**

- Create: `/workspaces/pdomain/pdomain-ocr-training/pdomain_ocr_training/formatting/calibration.py`
- Extend: `/workspaces/pdomain/pdomain-ocr-training/pdomain_ocr_training/formatting/evaluate.py`
- Create: `/workspaces/pdomain/pdomain-ocr-training/pdomain_ocr_training/formatting/review_artifacts.py`
- Test: `/workspaces/pdomain/pdomain-ocr-training/tests/formatting/test_calibration.py`
- Test: `/workspaces/pdomain/pdomain-ocr-training/tests/formatting/test_metrics.py`
- Test: `/workspaces/pdomain/pdomain-ocr-training/tests/formatting/test_review_artifacts.py`

- [ ] **Step 1: Write exact metric fixtures**

Cover per-label grapheme precision, recall, F1, exact span match, span IoU, boundary distance, whole-word exact accuracy, mixed-style exact accuracy, overlap Jaccard, ECE, Brier score, selective risk, and book bootstrap intervals.

- [ ] **Step 2: Implement per-label temperature scaling**

Fit only on calibration groups. Store temperatures, support, ECE before and after, tool version, and calibration manifest hash. Fall back to an approved pooled or isotonic method only through a new config version.

- [ ] **Step 3: Implement abstention and review bundles**

Abstain on low calibrated confidence, high entropy, OCR mismatch, low alignment margin, crop truncation, or parser conflict. Emit crop, page thumbnail, texts, spans, confidence, provenance, warnings, and hashes.

- [ ] **Step 4: Run locked evaluation**

Run: `uv run pdomain-ocr-training-formatting-eval --config experiments/formatting/grapheme-v1-eval.toml`

Expected: overall and slice metrics, book-level 95 percent intervals, p50 and p95 CPU/GPU latency at batch 1 and production batch, calibration plots, risk-coverage curves, and review artifacts.

- [ ] **Step 5: Human acceptance checkpoint**

The owner supplies numeric gates for quality, regression margin, calibration, abstention, and latency. Without them, the phase remains experimental.

### Task 12A: Measure whether synthetic data helps real scans

**Depends on:** Tasks 10, 11, and 12.

**Files:**

- Create: `/workspaces/pdomain/pdomain-ocr-training/experiments/formatting/synthetic-real-only.toml`
- Create: `/workspaces/pdomain/pdomain-ocr-training/experiments/formatting/synthetic-only.toml`
- Create: `/workspaces/pdomain/pdomain-ocr-training/experiments/formatting/synthetic-pretrain-real-finetune.toml`
- Create: `/workspaces/pdomain/pdomain-ocr-training/experiments/formatting/synthetic-mixed-*.toml`

- [ ] **Step 1: Run the real-only and synthetic-only controls**

Synthetic-only exposes the domain gap and cannot be promoted. Both runs use the Task 11 contextual model and the same optimizer settings as later comparisons.

- [ ] **Step 2: Run the curriculum matrix**

Compare synthetic pretraining then real fine-tuning; mixed real:synthetic ratios `1:0.5`, `1:1`, `1:2`, and `1:3`; and synthetic pretraining, mixed training, then real-only final fine-tuning. Compare encoder freezing for zero, one, and five epochs.

- [ ] **Step 3: Run data-quality ablations**

Compare clean rendering, generic degradation, corpus-calibrated degradation, rare-label-only supplementation, held-out font lineages, and self-supervised pretraining on unlabeled real scans.

- [ ] **Step 4: Apply the real-validation gate**

Expected: at least 1.0 absolute macro grapheme F1 and 2.0 mixed-style exact-word improvement over real-only; no common label loses more than 1.0 F1; no audited stratum loses more than 2.0; calibration and abstention do not worsen after recalibration; gains survive three seeds or edition-group bootstrap resamples and removal of evaluation words present in synthetic text.

Rollback: retain synthetic artifacts for stress tests but remove their manifest from production training.

### Task 13: Add contextual stress tests and weak supervision separately

**Files:**

- Create: `/workspaces/pdomain/pdomain-ocr-training/pdomain_ocr_training/formatting/line_dataset.py`
- Extend: `/workspaces/pdomain/pdomain-ocr-training/pdomain_ocr_training/formatting/model.py`
- Test: `/workspaces/pdomain/pdomain-ocr-training/tests/formatting/test_line_dataset.py`
- Test: `/workspaces/pdomain/pdomain-ocr-training/tests/formatting/test_line_model.py`

- [ ] **Step 1: Add word-box and separator fixtures**

Test styles crossing word boundaries, relative superscript baselines, letter spacing, punctuation crops, joined page-break words, drop-cap context, and incorrect reading order.

- [ ] **Step 2: Verify shared word and line paths**

Verify the Task 11 contextual encoder keeps word-local output indices, caps pixel width and grapheme count rather than downscaling beyond readable resolution, and uses the word-only fallback when context is missing or masked.

- [ ] **Step 3: Run source-isolated experiments**

Add Gutenberg silver labels, Standard Ebooks bronze labels, and synthetic data one at a time. Compare full, masked, misleading, and missing context separately. Each run changes one source or context condition and keeps test groups fixed.

- [ ] **Step 4: Apply the no-harm gate**

Expected: the addition improves a declared locked metric or rare-label slice and stays within owner-set regression and calibration margins on gold data. Otherwise withdraw that source manifest.

### Task 14: Add a separate formatting runner and export contract

**Files:**

- Modify: `/workspaces/pdomain/pdomain-ocr-training/pdomain_ocr_training/protocols.py`
- Modify: `/workspaces/pdomain/pdomain-ocr-training/pdomain_ocr_training/local.py`
- Modify: `/workspaces/pdomain/pdomain-ocr-training/pdomain_ocr_training/__init__.py`
- Create: `/workspaces/pdomain/pdomain-ocr-training/pdomain_ocr_training/formatting/export.py`
- Test: `/workspaces/pdomain/pdomain-ocr-training/tests/formatting/test_protocol.py`
- Test: `/workspaces/pdomain/pdomain-ocr-training/tests/formatting/test_export.py`
- Extend: `/workspaces/pdomain/pdomain-ocr-training/tests/test_torch_free_import.py`

- [ ] **Step 1: Write a separate protocol test**

Add `train_formatting(profile, config) -> Iterator[TrainingEvent]` and `evaluate_formatting(profile, config) -> FormattingEvalResult`. Existing detection and recognition signatures remain exact.

- [ ] **Step 2: Preserve the optional-heavy boundary**

Public Pydantic models and protocols import without Torch. Concrete formatting training and inference load lazily through the `train` extra.

- [ ] **Step 3: Export a versioned portable model**

Export TorchScript or ONNX only after an equivalence test compares logits, masks, grapheme spans, and calibrated decisions within recorded tolerances.

- [ ] **Step 4: Run full CI and package checks**

Run: `cd /workspaces/pdomain/pdomain-ocr-training && make ci AI=1 && make build`

Expected: old and new public contracts pass, the base import remains torch-free, and the wheel contains formatting config but no bundled corpus.

Rollback: remove the formatting registry entry and lazy export. Detection and recognition runners remain deployed.

### Task 15: Integrate through shadow inference only

**Files:**

- Create after owner decision: `/workspaces/pdomain/pdomain-book-tools/pdomain_book_tools/typography/provider.py`
- Create after owner decision: `/workspaces/pdomain/pdomain-book-tools/tests/typography/test_provider.py`
- Deployment adapter path: choose the existing OCR service repository only after its AGENTS and Docgraph review.

- [ ] **Step 1: Define a torch-free provider protocol**

The protocol accepts crop bytes or arrays, recognized graphemes, OCR confidence, normalized geometry, and optional line context. It returns `TypographyAnnotations` with model and calibration versions.

- [ ] **Step 2: Run shadow inference**

Store predictions beside existing OCR output. Do not mutate `ground_truth_text`, recognition confidence, page-region labels, or existing style labels.

- [ ] **Step 3: Compare shadow output to reviewed samples**

Expected: owner-set quality, calibration, abstention, and latency gates pass on immutable groups. Error bundles include every abstained or conflicting example selected for audit.

- [ ] **Step 4: Promote through one reversible manifest pointer**

Promotion selects a model, schema, calibration, and label-taxonomy version together. Rollback restores the prior pointer without changing OCR or page-region models.

## Final verification checklist

- [ ] All three source inventories record URLs, times, hashes, versions, and license evidence.
- [ ] Corpus counts reproduce from one versioned command.
- [ ] F2 parsing precedes normalization and retains byte-to-grapheme maps.
- [ ] Unknown and conflicting labels never become negatives.
- [ ] Exact edition evidence exists for every external label projection.
- [ ] No leakage edge crosses an immutable split.
- [ ] Whole-word, mixed-span, overlap, calibration, abstention, and slice metrics exist.
- [ ] Baseline and production candidates use the same locked test groups.
- [ ] The formatting task remains separate from OCR recognition and page-region labeling.
- [ ] Drop caps remain structural context unless a later human-approved auxiliary task is added.
- [ ] Every repository passes its own CI and Docgraph strict gate.
- [ ] Rollback has been exercised on generated data and model registry pointers.
