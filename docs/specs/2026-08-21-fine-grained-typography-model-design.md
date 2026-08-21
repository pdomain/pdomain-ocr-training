---
Status: draft
Owner: CT
Created: 2026-08-21
Last verified: 2026-08-21
Kind: spec
---

# Fine-grained typography model design

The system should add a typography task beside OCR recognition and page-region labeling, with shared canonical spans in `pdomain-book-tools`, training in `pdomain-ocr-training`, and shared source-data preparation in `pdomain-source-data`.

## Agent Index

- **Kind:** spec
- **Status:** draft
- **Owner:** CT
- **Last verified:** 2026-08-21
- **Read when:** implementing fine-grained typography parsing, datasets, training, inference, or evaluation.
- **Search terms:** typography model, grapheme styles, F2 parser, alignment, split manifest, weak supervision.

## Goals and exclusions

The model accepts an OCR word crop or short-line crop, recognized text, and available geometry. It returns whole-word labels for uniform words and exact grapheme spans for mixed words. Labels can overlap. The supporting evidence is in [fine-grained typography model research](../research/2026-08-21-fine-grained-typography-model-research.md).

The model does not recognize text. It does not classify poetry, block quotations, tables, headings, captions, or other page regions. Those structures remain inputs, context, exclusions, or evaluation slices from the existing page-region model.

Drop caps remain structural `word_components` evidence. The initial model uses them as context and hard negatives. A later short-line auxiliary `drop_cap_initial` output can associate the initial grapheme with the existing structural result. It does not enter the core inline-style score.

## Three viable systems

### Text-conditioned grapheme queries are the recommended system

A compact visual encoder produces patch features from a word or short-line crop. Grapheme identity, position, OCR confidence, word geometry, and optional neighbor context form queries. Two to four cross-attention layers bind the queries to image features.

Independent sigmoid heads predict each style at each grapheme. A pooled head predicts whole-word labels. An optional boundary head predicts begin, inside, and end evidence per label. Attention summaries are audit evidence, not character boxes.

This design supports overlaps without a combinatorial output vocabulary. It uses recognized text without duplicating recognition. Its main risks are OCR-conditioned errors, lexical shortcuts, crop truncation, and soft alignment drift.

### Image-only grapheme queries are the smallest sequence baseline

This variant supplies only grapheme count and position to the visual decoder. It is faster and simpler. However, repeated characters and small-cap distinctions lose useful identity context. It should be the first sequence ablation, not the production recommendation.

### CTC latent alignment is the challenger

A left-to-right visual feature sequence aligns to recognized graphemes with a CTC-style forward-backward objective. Style loss is marginalized over the alignment. This avoids character boxes and can handle variable glyph widths.

Vanilla CTC does not model overlapping styles directly. A joint grapheme-style alphabet would grow rapidly. The implementation must keep grapheme alignment and independent style emissions separate. This extra complexity makes CTC a second experiment if cross-attention boundary errors dominate.

### Short-line context is part of the recommended system

The recommended system accepts a high-resolution target-word crop and a short-line crop containing nearby words. It also accepts the target box in line coordinates, full-line recognized text, word and grapheme boundaries, and available geometry. The line view establishes the local norm for height, weight, slant, spacing, and face. The word view preserves punctuation and mixed-span detail.

This contextual-first choice supersedes the earlier word-first experiment sequence. Typography such as small caps is often defined by contrast with surrounding text. The word-only model remains the smallest baseline, ablation, and missing-context fallback. It does not gate contextual training.

## Canonical labels separate visible style from structure and semantics

The first production taxonomy uses independent labels. `regular` is the absence of positive style labels, not a competing class.

| Canonical label | Kind | Initial training status | Strong sources | Important exclusions |
| --- | --- | --- | --- | --- |
| `italic` | visible style | active | resolved F2 `<i>` | underlining is indistinguishable in default F2 |
| `bold` | visible style | active | F2 `<b>` | Standard Ebooks `<b>` often means small caps |
| `small_caps` | visible style | active | F2 `<sc>` with rule-aware case handling | chapter-opening normalization and relative-size headings |
| `letter_spaced` | visible style | deferred until real positives | F2 `<g>`, computed CSS, manual audit | no positives in current F2 snapshot |
| `superscript` | position/style | active after syntax audit | validated F2 caret syntax, matched HTML | footnote semantics stored separately |
| `subscript` | position/style | active after syntax audit | validated F2 underscore syntax, matched HTML | formula ambiguity |
| `underline` | visible style | weak/manual only | explicit project `<u>`, matched CSS | default F2 maps underline to `<i>` |
| `font_blackletter` | visible family class | later | resolved Project Comments, computed CSS, manual | unexplained `<f>` |
| `font_antiqua` | visible family class | later | resolved Project Comments, computed CSS, manual | relative labels without page context |
| `font_upright_in_italic` | relative visible style | later | resolved `<f>` plus enclosing italic | ordinary roman text |
| `font_other_reviewed` | visible change | audit only | human label with definition | never train unresolved `<f>` |

Semantic reasons use a separate vocabulary such as `emphasis`, `foreign_phrase`, `work_title`, `vessel_name`, `acronym`, and `initialism`. They never replace visible style labels.

Structural context uses existing or extended page and word components: `heading`, `caption`, `table`, `poetry`, `block_quote`, `drop_cap`, `drop_cap_unrecovered`, `footnote_marker`, and `decorative_initial`. These fields drive context, hard-negative sampling, and slices.

Every label has one of four knowledge states: `positive`, `verified_negative`, `unknown`, or `conflict`. Missing markup defaults to `unknown` when the source rules intentionally omit the feature.

## The canonical record preserves bytes, spans, evidence, and versions

The interchange format is JSON Lines for inspection and Parquet for training. All string offsets are half-open Unicode grapheme indices. Raw source offsets are half-open byte offsets into the exact stored artifact.

```python
type Sha256 = str
type GraphemeIndex = int

class ArtifactRef(BaseModel):
    source: Literal["pgdp_f2", "gutenberg", "standard_ebooks", "human", "synthetic"]
    source_url: str | None
    local_path: str
    retrieved_at: datetime
    sha256: Sha256
    version: str
    license_ref: str | None

class TextIdentity(BaseModel):
    work_id: str
    edition_id: str
    book_id: str
    project_id: str | None
    pg_ebook_id: int | None
    se_repository: str | None
    page_id: str
    image_artifact: ArtifactRef
    text_artifacts: list[ArtifactRef]

class SourceSlice(BaseModel):
    artifact_sha256: Sha256
    byte_start: int
    byte_end: int

class Grapheme(BaseModel):
    index: GraphemeIndex
    text: str
    source_slices: list[SourceSlice]
    normalized_from: str | None

class StyleSpan(BaseModel):
    label: str
    start: GraphemeIndex
    end: GraphemeIndex
    state: Literal["positive", "verified_negative", "unknown", "conflict"]
    label_source: Literal["f2", "gutenberg_html", "se_computed_css", "human", "synthetic"]
    confidence_tier: Literal["gold", "silver", "bronze", "quarantine"]
    source_slices: list[SourceSlice]
    rule_ref: str | None
    semantic_reason: str | None
    warnings: list[str]

class OcrTokenRef(BaseModel):
    token_id: str
    text: str
    confidence: float | None
    bbox: BoundingBox
    line_id: str
    grapheme_start: GraphemeIndex
    grapheme_end: GraphemeIndex
    alignment_id: str

class AlignmentEvidence(BaseModel):
    alignment_id: str
    method: str
    source_artifact_sha256: Sha256
    target_artifact_sha256: Sha256
    source_coordinate_space: Literal["raw_bytes", "source_graphemes", "source_pages"]
    target_coordinate_space: Literal["ocr_graphemes", "ocr_tokens", "target_pages"]
    source_range: tuple[int, int]
    target_range: tuple[int, int]
    operations: list[str]
    score: float
    margin: float | None
    alternatives: list[dict[str, object]]
    accepted: bool

class TypographyPageRecord(BaseModel):
    schema_version: Literal["1.0"]
    identity: TextIdentity
    original_f2_artifact_base64: str | None
    original_f2_artifact_sha256: Sha256 | None
    f2_page_key: str | None
    f2_page_value_lexical_byte_range: tuple[int, int] | None
    f2_decoded_page_utf8_sha256: Sha256 | None
    parsed_text: str
    graphemes: list[Grapheme]
    ocr_tokens: list[OcrTokenRef]
    style_spans: list[StyleSpan]
    structural_context: list[str]
    parser_warnings: list[str]
    alignments: list[AlignmentEvidence]
    project_comments_artifact: ArtifactRef | None
    guideline_version: str
```

The production types belong in `pdomain-book-tools`. The raw corpus record should not be embedded into `Word`. Inference projects final trusted spans into a new typed `TypographyAnnotations` side channel. `Character.text_style_labels` remains a compatibility projection when character boxes exist.

`TypographyAnnotations` preserves `None` for unknown or unrun inference and an empty object for reviewed regular text. It contains whole-word labels, grapheme spans, source, model version, confidence, calibration version, and review metadata.

## Parsing is deterministic and non-destructive

Parsing begins from the exact `F2.json` artifact bytes. A page value is JSON-escaped inside that file and has no independent original byte stream. A lossless lexical JSON reader records the page key and the value's half-open lexical byte range in `F2.json`. It also records a mapping from decoded page characters back to JSON lexical byte slices. It hashes an explicitly derived UTF-8 page value for convenient comparison. Raw offsets always name their coordinate space and artifact hash.

The parser never calls the current `PGDPResults.process()` first because that method removes notes and normalizes punctuation and diacritics without an offset map.

The parser performs these ordered steps:

1. Read the complete `F2.json` bytes, retain their SHA-256, and locate each page key and value lexically without reserializing JSON.
2. Decode each JSON string escape while retaining a map from decoded characters to lexical byte slices in the full artifact.
3. Scan page-local tokens for known inline tags, block markers, notes, superscript syntax, subscript syntax, and unknown controls.
4. Build visible text and a many-to-many map from every visible grapheme to raw artifact byte slices.
5. Maintain an independent active-label stack. Convert nesting to overlapping spans without flattening labels.
6. Close no tag implicitly at page end. Emit `unclosed_tag` and quarantine affected spans.
7. Keep punctuation exactly where the markup places it. Do not extend a style across neighboring punctuation.
8. Convert `<sc>` source case under the recorded PGDP rule while retaining raw source text and a `small_caps_case_normalized` warning.
9. Remove spaces inside validated `<g>` from visible alignment text while mapping each resulting grapheme to all source slices that contributed.
10. Parse `^x`, `^{...}`, `_x`, and `_{...}` only outside notes and escaped or quarantined constructs.
11. Remove `[** ...]` notes from visible text but retain note objects, offsets, question status, and page review state.
12. Resolve `<f>` and `<u>` only through a versioned project-rule table derived from Project Comments. Otherwise mark the span `unknown` and quarantine it.
13. Emit block structure as context without turning it into inline labels.

The parser rejects a training example with a mismatched close, an unclosed style affecting the crop, an unknown control inside the crop, ambiguous `<f>`, invalid grapheme boundaries, or a note whose removal leaves uncertain adjacency. It retains the page record for audit.

## Alignment preserves exact evidence at three levels

Page-local F2 text first aligns to OCR lines and words. Alignment uses normalized comparison views but always projects through the original grapheme map.

The comparison view may normalize Unicode canonically, case for small-cap comparison, quote variants, dash variants, soft hyphens, and spaces introduced by `<g>`. Each transformation writes an operation to `AlignmentEvidence`. Comparison normalization never changes stored source text.

Line alignment uses dynamic programming with word-box reading order, line breaks, and region context. Token alignment then permits one-to-many and many-to-one transitions for split words, joined punctuation, ligatures, OCR deletions, and page-break fragments. A style span crossing OCR words is split only in the final crop projection. Its canonical source span remains whole.

Gutenberg and Standard Ebooks use global monotonic sequence alignment across the full book. The state machine permits `1:0`, `0:1`, `1:1`, `1:N`, and `N:1` page or section transitions. Costs explicitly allow blank pages, plates, moved footnotes, merged or split pages, and joined page-break words.

No external label is projected until edition identity passes a separate gate. The gate requires the identifier relationship and at least two independent signals among edition matter, DP credit, scan source, distinctive-text anchors, and high-margin global alignment. A low-margin alternate alignment forces `conflict` or `unknown`.

Every projected span records the exact source range, target range, operations, score, runner-up margin, artifact hashes, and confidence tier. Rebuilding with unchanged inputs must produce byte-identical records.

## Confidence tiers control supervision

- `gold`: human-reviewed image and span, or deterministic F2 parse with high-confidence OCR alignment and no warnings.
- `silver`: deterministic source span projected through a verified edition with high-margin alignment.
- `bronze`: editorially transformed or computed-style weak supervision with strong text alignment.
- `quarantine`: malformed, ambiguous, conflicting, unresolved, or low-margin evidence.

Training masks quarantine and unknown labels. It never converts them to negatives. Confidence weights begin at 1.0, 0.7, and 0.3 for gold, silver, and bronze, then become tunable only through validation experiments.

## Splits group works, editions, scans, and derivatives

An immutable split manifest assigns a `leakage_group_id`, not a page. The group joins the source work, physical edition, all volumes, duplicate scans, PG variants, PGDP projects, and Standard Ebooks derivatives.

Grouping evidence includes bibliographic identifiers, normalized title and author, source-scan identifiers, perceptual page hashes, text fingerprints, Gutenberg sources, and Standard Ebooks `dc:source`. Ambiguous groups merge before splitting.

The first manifest uses deterministic hash allocation after grouping. It targets 80 percent train, 10 percent validation, and 10 percent test by book while checking page and rare-label support. A separate calibration subset comes only from validation groups. The manifest stores its schema, seed, grouping algorithm version, input hashes, and every reason that joined two records.

Controlled challenge sets remain outside the random allocation. They cover non-English material once acquired, poetry, tables, headings, captions, pre-1800 printing, blackletter, poor scans, slanted roman, decorative type, mathematical notation, and drop caps. The current all-English snapshot cannot satisfy the language challenge requirement.

## Training uses strong labels first and weak labels later

The visual encoder starts from an ImageNet or permitted scene-text checkpoint. The text encoder is small and learned for grapheme identity, not a general language model.

Training examples mix:

- strong positives for every active label and overlap combination;
- ordinary body-text verified negatives;
- hard negatives: slanted roman, naturally heavy fonts, all caps, headings, drop caps, punctuation, formulas, degraded scans, crop truncation, and decorative faces;
- rare-label oversampling capped to avoid memorizing books;
- confidence-weighted gold, silver, and bronze labels;
- synthetic styles as a supplement, always in distinct source and evaluation slices.

Synthetic examples come from an extension to `pdomain-ocr-synth`. They do not come from a second renderer in the data-preparation repository. The generator creates the canonical grapheme labels first. It shapes complete context with HarfBuzz, rasterizes with FreeType, builds a high-resolution page, applies print and scan effects, and only then extracts word and short-line crops.

The font catalog starts with a pinned OFL core spanning Garamond, Fell, Caslon, Baskerville, transitional, Didone, Goudy, broad multilingual book serif, and Fraktur lineages. Every exact font file has a hash, upstream version, license, axes, character coverage, and a supported GSUB or GPOS feature manifest. All related faces and forks share one `font_lineage_id` for splitting.

Kerning stays enabled through HarfBuzz GPOS in the normal case. `kern=0` is a controlled variant. Letter spacing adds advance only between safe shaped clusters. It never separates marks from bases or divides a ligature unless ligatures are disabled for that sample.

True font features and simulated fallbacks remain separate provenance values. The generator prefers real italic or `ital`, real bold or `wght`, `smcp` and `c2sc`, and `sups`, `subs`, or `sinf`. Sheared roman, emboldening, scaled capitals, and scaled baseline-shifted glyphs are hard or lower-confidence variants.

The clean render runs at four or eight times target resolution in linear grayscale. Physical effects follow a fixed order: ink gain or loss, uneven impression, paper and show-through, page geometry, optical blur, one downsample, then sensor noise and codec effects. Parameter distributions come from real PGDP scan strata, not unconstrained random ranges.

Every grapheme retains its source range, style bitset, HarfBuzz cluster, contributing glyph IDs, clean ink geometry, transformed geometry, clipping fraction, and word or line membership. Ligature graphemes share one cluster polygon and carry `shared_ligature_cluster`; the generator never invents separate character boxes.

The curriculum keeps both visual views from the first grapheme-model stage. First train the contextual model on strong whole-word uniform labels while retaining the word-only fallback. Next add mixed-style words. Then add OCR text corruption, misleading or masked neighbors, and overlap cases. Finally, add silver and bronze weak supervision one source at a time.

Synthetic training has its own tested curriculum. Compare real-only, synthetic-only, and synthetic pretraining followed by real fine-tuning. Also compare mixed real:synthetic ratios of `1:0.5`, `1:1`, `1:2`, and `1:3`, plus synthetic pretraining followed by mixed training and a final real-only stage. The last is the leading candidate. Compare it with self-supervised encoder pretraining on unlabeled real scans.

Loss is masked asymmetric binary cross-entropy or focal loss per grapheme and label, plus whole-word binary cross-entropy. A small boundary-consistency loss encourages stable starts and ends. A cross-head consistency loss requires a whole-word positive when all known graphemes share the label. Unknown labels have zero loss.

Text corruption includes substitutions, deletions, insertions, Unicode normalization variants, and punctuation movement sampled from actual OCR errors. Text dropout and the image-only ablation measure lexical shortcuts.

## Evaluation centers on spans and abstention

Report these metrics on immutable test groups:

- grapheme precision, recall, and F1 for every label;
- micro, macro, and support-weighted summaries;
- exact span match and intersection-over-union;
- absolute start and end boundary distance in graphemes;
- whole-word exact multi-label accuracy;
- mixed-style word exact accuracy;
- multi-label overlap exact accuracy and Jaccard score;
- per-label expected calibration error and Brier score;
- selective risk and coverage under abstention;
- book-level bootstrap 95 percent confidence intervals.

Every metric is sliced by language, period, genre, source, scan-quality band, font-family class, confidence tier, whole versus mixed word, OCR correctness, punctuation boundary, and structural context. Unsupported slices are reported as unavailable, not zero.

Baselines are a rule-based F2 projection, a whole-word logistic or small-CNN classifier, a ResNet-18 multi-label word classifier, approximate equal-width grapheme slicing, and the image-only sequence model.

Each error artifact contains crop, page thumbnail, OCR text, source text, ground truth, prediction, per-label confidence, abstention result, grapheme alignment, provenance, artifact hashes, and parser warnings. Review corrections append a new human evidence record and never overwrite source evidence.

## Repository boundaries keep responsibilities clear

`pdomain-book-tools` owns durable parsing and interchange contracts because it already owns `PGDPExport`, OCR words, characters, geometry, review metadata, and glyph side channels.

Recommended additions:

```text
pdomain-book-tools/
  pdomain_book_tools/pgdp/f2/
    tokens.py
    parser.py
    offsets.py
    project_rules.py
    warnings.py
  pdomain_book_tools/typography/
    labels.py
    spans.py
    annotations.py
    records.py
    alignment.py
  tests/pgdp/f2/
  tests/typography/
```

`pdomain-ocr-training` owns the model, datasets, losses, training runner, evaluation, and export. It adds a distinct `FormattingConfig` and `train_formatting()` path. It does not modify `RecognitionConfig` or `train_recognition()`.

```text
pdomain-ocr-training/
  pdomain_ocr_training/formatting/
    config.py
    dataset.py
    model.py
    losses.py
    train.py
    evaluate.py
    calibration.py
    export.py
  tests/formatting/
```

A new `pdomain-source-data` repository should own shared corpus inventory, artifact hashing, identity, cross-source matching, canonical record materialization, corrections, audits, split manifests, and task exports. Typography, recognition, detection, glyph forms, and page regions share these concerns. Task modules retain separate taxonomies, validation, and materializers. These jobs are neither an OCR runtime concern nor source acquisition. `pdomain-pgdp-api-client` remains PGDP byte acquisition only.

```text
pdomain-source-data/
  pdomain_source_data/
    cli.py
    artifacts/
    provenance/
    identity/
    geometry/
    corrections/
    review/
    splits/
    audit/
    manifests/
    sources/
      pgdp.py
      gutenberg.py
      standard_ebooks.py
    matching/
      edition_graph.py
      book_align.py
      page_align.py
    tasks/
      detection/
      recognition/
      typography/
      glyph_forms/
      page_regions/
  tests/
  schemas/
  manifests/
```

Acquisition remains outside `pdomain-source-data`. The repository consumes pinned source artifacts and emits immutable source, labeling, correction, and training manifests. Training packages and the labeler never depend on its internal database or private Python models.

### Cross-source evidence forms a work and edition graph

PGDP, Project Gutenberg, and Standard Ebooks often represent the same work or a derivation of the same edition. The source-data package records `Work`, `Edition`, `SourceArtifact`, and page or segment identities separately. Edges retain PG ebook numbers, DP credit, edition matter, scan provenance, Standard Ebooks source metadata, distinctive text fingerprints, global alignment scores, manual confirmation, artifact hashes, tool versions, and rejection reasons.

The PG ebook number starts candidate generation but does not prove physical-edition identity. Global monotonic alignment permits page splits and merges, blank pages, plates, moved notes, joined page-break words, and post-processing drift.

Ground truth is fused per field and grapheme rather than selected from one preferred corpus. The scan image is authoritative for visible typography. Reviewed SPA corrections are authoritative for text, geometry, and typography. PGDP F2 provides the strongest initial page-local typography evidence. Gutenberg can improve final wording and post-processed formatting. Standard Ebooks remains weak evidence because its editors can normalize or reinterpret the source. Every selected value retains its evidence and conflicts.

### The labeler creates OCR geometry when sources cannot supply it

Inbound labeling bundles may contain images and matched source evidence without OCR geometry. The SPA runs the existing recognition and page-region models, records their versions and configurations, and creates page, line, word, and optional character geometry. It then aligns source evidence to those OCR anchors and lets a human correct text, geometry, and typography.

The SPA returns an immutable correction bundle tied to the inbound bundle ID and artifact hashes. `pdomain-source-data` validates and imports it, then materializes a new versioned `PageGroundTruth`. The source-data repository may cache reviewed OCR output, but it does not run OCR itself.

`pdomain-ocr-synth` owns synthetic typography generation because it already owns HarfBuzz and FreeType shaping, font recipes, glyph-cluster geometry, deterministic sampling, degradations, and OCR dataset output.

```text
pdomain-ocr-synth/
  src/pdomain_ocr_synth/typography/
    spans.py
    font_manifest.py
    feature_runs.py
    mixed_renderer.py
    physical_print.py
    output.py
  recipes/typography/
  tests/typography/
```

The synthetic output implements the same canonical labels and grapheme indexing from `pdomain-book-tools`. It adds `render_method`, `font_lineage_id`, axes, feature ranges, stage seeds, clean-render hash, and final-image hash. Font binaries remain user-provided or separately fetched under reviewed licenses. The repository never bundles an unreviewed font.

Model inference should later enter `pdomain-book-tools` through a provider protocol. The heavy Torch implementation remains in a deployment package or optional adapter. This preserves the existing torch-free base boundaries.

## Failure handling and rollback preserve source truth

Each pipeline stage writes a content-addressed output directory and a manifest only after validation. A failed stage leaves its prior immutable version active. Promotion updates one manifest pointer. Rollback restores the previous pointer.

Parser and schema versions never mutate stored F2 bytes. Reprocessing creates a new derived record version. Model rollout is shadow-only first, then review-assisted, then opt-in. Existing OCR recognition and page-region outputs remain authoritative until the typography acceptance gate passes.

## Acceptance criteria define readiness

Phase 0, corpus audit, passes when all mounted inputs have hashes and versions; every F2 page has a parse status; published counts reproduce from one command; and unsupported distributions are marked unavailable.

Phase 1, parser and schema, passes when golden fixtures cover every supported syntax, nesting combination, punctuation boundary, malformed case, and normalization map; property tests prove deterministic round trips; and no rejected span enters training output.

Phase 2, matching and splits, passes when every candidate match has evidence; no leakage-group edge crosses splits; the manifest is byte-identical on rerun; and manual review accepts a stratified sample at the agreed precision threshold.

Phase 3, whole-word baseline, is a required comparison. It passes when it beats majority and rule-only baselines on book-grouped test data, emits calibrated probabilities, and produces complete error artifacts. It does not gate contextual training. A human must set the numeric quality and latency thresholds after Phase 0 establishes support.

Phase 4, contextual grapheme model, is the first production experiment. It passes when the two-view target-word and short-line model improves mixed-style exact accuracy and per-label grapheme F1 over the image-only, word-only, and equal-slice baselines, while whole-word performance does not regress beyond the agreed margin.

Phase 5, weak supervision and contextual stress testing, passes only when each source addition improves a locked target metric or a declared rare-label slice without worsening calibration, leakage checks, or strong-label performance beyond agreed margins. Full, masked, misleading, and missing context are reported separately.

Synthetic data passes its own gate on immutable real-scan validation. Macro grapheme F1 must improve by at least 1.0 absolute point and mixed-style exact-word accuracy by at least 2.0. No common label may lose more than 1.0 F1 point. No audited stratum may lose more than 2.0. Calibration and abstention risk must not worsen after recalibration. The result must persist across at least three seeds or edition-group bootstrap resamples and after excluding evaluation words found in synthetic text.

Phase 6, integration, passes when typed contracts remain torch-free, old OCR payloads round-trip unchanged, shadow inference meets local p50 and p95 limits, abstention reaches the chosen risk target, and rollback restores the prior output manifest.

## Human decisions still required

- Choose numeric quality, calibration, abstention, and latency gates after the audited dataset exists.
- Decide whether underlining remains a separate weak/manual label or folds into italic for the first release.
- Approve the controlled font-change vocabulary and every project-specific `<f>` rule.
- Decide whether `letter_spaced` waits for real scanned positives or enters only as an experimental synthetic label.
- Choose the minimum human-audit precision for edition matches and projected labels.
- Approve the initial gold, silver, and bronze loss weights.
- Choose the source-data ingestion policy for Gutenberg and Standard Ebooks acquisition packages; `pdomain-source-data` consumes pinned artifacts and does not crawl public sites itself.
- Decide the owner of model inference packaging and deployment hardware targets.
- Decide whether a later `drop_cap_initial` auxiliary output adds value beyond the existing structural detector.
- Confirm jurisdictions and artifact licenses allowed for model training and redistribution.
- Approve the phase-one OFL font lineages and the legal interpretation for raster datasets and trained weights.
- Choose whether font acquisition remains interactive in `pdomain-ocr-synth` or uses a reviewed hash-pinned manifest fetcher.

## Adversarial Review

Two independent reviewers checked the research, design, and plan through the findings-report, spec-design, and implementation-plan lenses. The review covered source grounding, schema consistency, dependency order, repository boundaries, synthetic data, licensing, executable detail, acceptance criteria, and rollback.

Accepted findings fixed task ordering, release and exact dependency pinning, alignment coordinate provenance, project-authorized `<u>` handling, per-repository Python versions, the current heavy `pdomain-book-tools` dependency cost, lexical byte mapping inside `F2.json`, and the missing fontTools dependency and lockfile step.

One proposed duplicate grouping paragraph was rejected because the current design contains it once. One claim that `Character.text_style_labels` was absent was rejected against `pdomain_book_tools/ocr/character.py`, which defines, normalizes, serializes, deserializes, and exposes that field through its Pydantic schema. Both focused rechecks returned `No actionable findings.`
