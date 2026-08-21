---
Status: active
Owner: CT
Created: 2026-08-21
Last verified: 2026-08-21
Kind: research
---

# Fine-grained typography model research

The available corpora can support a fine-grained typography model, but F2 must be parsed as noisy, page-local evidence rather than literal ground truth.

## Agent Index

- **Kind:** research
- **Status:** active
- **Owner:** CT
- **Last verified:** 2026-08-21
- **Read when:** designing or auditing typography labels, corpus matching, weak supervision, or model choices.
- **Search terms:** typography, F2, italics, small caps, superscript, grapheme spans, Gutenberg, Standard Ebooks.

## Scope and conclusion

This research covers the live local PGDP, Project Gutenberg, and Standard Ebooks corpora. It also covers official source guidance and primary model literature. The companion [design](../specs/2026-08-21-fine-grained-typography-model-design.md) turns the findings into a system. The [implementation plan](../plans/2026-08-21-fine-grained-typography-model.md) defines test-first work. It does not authorize implementation.

The recommended first production experiment is a text-conditioned visual encoder. Recognized graphemes query word or short-line image features. Independent sigmoid heads predict overlapping style labels per grapheme. A whole-word auxiliary head preserves the simple case.

Drop caps should not enter the initial inline-style label set. They depend on scale and placement across several lines. The existing page and OCR contracts already carry `drop cap` as a structural word component. F2 usually removes that distinction.

## Goal

Determine whether the mounted corpora and current technical evidence support a separate fine-grained typography model, then define the evidence constraints for its design.

## Method

The audit inspected the three mounted corpora, applicable repositories, current OCR contracts, and official upstream documentation. Independent research tracks covered PGDP rules, external artifact semantics, model architecture, historical fonts, shaping, and synthetic-to-real training. All local counts describe the 2026-08-21 UTC snapshot.

## Evidence

## Corpus snapshot is large enough for targeted experiments

All three requested mounts were available on 2026-08-21 UTC.

| Corpus | Mounted path | Snapshot size | Available records |
| --- | --- | ---: | ---: |
| PGDP | `/workspaces/pdomain-data/pgdp-corpus` | 3.3 GiB | 80 projects, 79 F2 files, 21,353 F2 pages and matching root page PNGs |
| Project Gutenberg | `/workspaces/gutenberg-corpus` | 48 GiB | 61,679 ebook directories, 61,482 text files, 56,195 HTML files |
| Standard Ebooks | `/workspaces/standardebooks-corpus` | 34 GiB | 1,504 Git repositories and `content.opf` files, 53,911 XHTML files |

The 79 F2 files contain 30,191,475 Unicode code points and 5,020,667 whitespace-delimited tokens before linguistic tokenization. Removing known inline tags and `[** ...]` notes leaves 29,812,369 visible code points. It leaves 23,712,617 non-whitespace code points. These are parser-audit counts, not final training counts.

Every PGDP metadata record has a Project Gutenberg ebook number. All 80 numbers match a local Gutenberg directory with plain text. None of those 80 directories contains HTML in this snapshot. Standard Ebooks metadata contains 1,786 unique Gutenberg source IDs, but none intersects the 80 PGDP numbers. The current corpora therefore support PGDP-to-Gutenberg text matching for all projects. They do not yet support three-way matched-book evaluation.

## F2 contains useful labels and measurable noise

The live F2 snapshot contains these balanced opening-tag counts before validation:

| F2 tag | Opening tags | Projects | Initial interpretation |
| --- | ---: | ---: | --- |
| `<i>` | 27,460 | 79 | italic or underlining normalized to italic |
| `<sc>` | 10,090 | 73 | PGDP small-cap transcription rule |
| `<b>` | 1,958 | 11 | bold |
| `<f>` | 35 | 2 | project-defined font change; reject unless comments resolve it |
| `<g>` | 0 | 0 | letter spacing label exists in the rules but has no positive examples here |

The audit found 101,618 whitespace tokens with at least one styled visible character. It found 22,164 mixed-style tokens whose active label mask changes within the token. This includes punctuation immediately outside tags. It also found 57 nested opening events, so the representation must permit overlapping labels.

One page has an unclosed `<sc>` at end of page: `projectID62930b71a45bb/p3640.png`. The remaining known inline tags balance globally. The parser must still validate each page independently because PGDP requires page-local closure.

The corpus contains 4,254 `[** ...]` notes on 2,934 pages. Of these notes, 1,441 contain at least one question mark, with 1,482 question marks in total. Notes are review evidence, not visible text or negative labels.

Superscript syntax appears 594 times by raw pattern count: 147 braced spans and 447 single-character forms. Subscript appears 32 times: 23 braced spans and 9 single-character forms. These raw counts need parser validation because a caret or underscore can be ordinary text in malformed or project-specific cases.

Project Comments exist for 79 of 80 projects and contain 96,361 characters. Seven explicitly discuss small caps. None mentions `drop cap`, `drop-cap`, or `letter spacing`. Comments must be retained and versioned because they override default instructions and can define `<f>`.

All 80 projects list English. Difficulty is `average` for 69, `easy` for 10, and `hard` for 1. The largest image-source groups are TIA 43, TIA_AL 15, HathiTrust 10, `_internal` 5, TIA_CAN 2, and DL_VILL_U 2. ICE, NLS, and missing source metadata account for one project each. The leading genres are General Fiction 9, Non-Fiction 6, Mystery 6, Instructional 5, Juvenile 4, Travel 4, Historical Fiction 3, History 3, Cooking 3, and Short Story 3.

This snapshot cannot measure language diversity, reliable publication period, font family, or scan quality from PGDP metadata alone. Those fields need enrichment from title pages, catalog metadata, source scans, and computed image-quality features. Controlled evaluation splits must not claim coverage before that enrichment exists.

## Reproduce the corpus inventory before training

The following shell commands reproduce top-level availability counts without changing data.

```bash
find /workspaces/pdomain-data/pgdp-corpus -mindepth 1 -maxdepth 1 -type d | wc -l
find /workspaces/pdomain-data/pgdp-corpus -path '*/rounds/F2.json' -type f | wc -l
find /workspaces/pdomain-data/pgdp-corpus -mindepth 2 -maxdepth 2 -type f -iname '*.png' | wc -l
find /workspaces/gutenberg-corpus/books -mindepth 1 -maxdepth 1 -type d | wc -l
find /workspaces/standardebooks-corpus/books -mindepth 1 -maxdepth 1 -type d | wc -l
du -sh /workspaces/pdomain-data/pgdp-corpus /workspaces/gutenberg-corpus /workspaces/standardebooks-corpus
```

The implementation must add a versioned audit command instead of relying on one-off regular expressions. The command must stream each F2 JSON mapping and parse markup before normalization. It must segment visible text with Unicode grapheme boundaries and emit both JSON and Parquet summaries. It must include input file hashes and a tool version so later snapshots can be compared exactly.

Required audit outputs are:

- projects, works, editions, pages, graphemes, OCR tokens, and visible-text tokens;
- label spans, label combinations, mixed-style words, and whole-word labels;
- malformed tags, unclosed tags, page-crossing attempts, unknown markup, and ambiguous `<f>`;
- notes, unresolved questions, and applicable Project Comment rules;
- language, genre, publication period, source, image dimensions, and computed scan-quality bands;
- Gutenberg and Standard Ebooks candidate, verified-edition, and rejected match rates;
- SHA-256 hashes, retrieval timestamps, repository commits, and artifact versions.

## Official PGDP rules make F2 strong but selective evidence

F1 adds formatting after proofreading. F2 reviews and corrects F1 and is the final formatting round before post-processing. The [official F1 welcome documentation](https://www.pgdp.net/wiki/DP_Official_Documentation%3AFormatting/Welcome_Email_to_new_F1s) states this division.

Formatting matches printed appearance while proofreading matches content. Each page is a separate unit, so inline tags must open and close on the same page. Project Comments override the defaults, and Project Discussion resolves unclear cases. These rules come from the [official Formatting Guidelines](https://www.pgdp.net/wiki/DP_Official_Documentation%3AFormatting/Formatting_Guidelines).

The official inline tags are `<i>`, `<b>`, `<sc>`, `<g>`, and project-defined `<f>`. Punctuation normally stays outside a tag unless it belongs to the marked phrase or the whole sentence or paragraph has that style. A style continuing across paragraphs closes and reopens around each paragraph. Before applying any normalization, the parser must preserve both tag placement and visible grapheme offsets. [Formatting Guidelines](https://www.pgdp.net/wiki/DP_Official_Documentation%3AFormatting/Formatting_Guidelines)

Underlining normally becomes `<i>` because it historically marks emphasis, though Project Comments can request `<u>`. A model trained from F2 cannot distinguish printed italics from underlining unless another source supplies that distinction. [Formatting Guidelines](https://www.pgdp.net/wiki/DP_Official_Documentation%3AFormatting/Formatting_Guidelines)

Spaced text uses `<g>` after removing inter-letter spaces. The rule describes a historical emphasis practice common in German. This corpus has no `<g>` positives, so letter spacing needs another PGDP snapshot, matched external artifacts, manual labels, or synthetic supplements. [Formatting Guidelines](https://www.pgdp.net/wiki/DP_Official_Documentation%3AFormatting/Formatting_Guidelines)

Small-cap transcription is not a literal case record. Mixed small caps use mixed case within `<sc>`, while all-small-cap text remains all caps within `<sc>`. Headings and captions that only resemble small caps because of relative size are not tagged. Opening chapter words in caps or small caps are normalized to mixed case without tags. Small-cap negatives therefore need context. They cannot be inferred only from missing `<sc>`. [Formatting Guidelines](https://www.pgdp.net/wiki/DP_Official_Documentation%3AFormatting/Formatting_Guidelines)

`<f>` is not one stable style. A project manager can define it for antiqua within fraktur, blackletter within roman, local size changes, or upright text inside italic. An unexplained `<f>` must be quarantined and sent for review. [Formatting Guidelines](https://www.pgdp.net/wiki/DP_Official_Documentation%3AFormatting/Formatting_Guidelines)

One-character superscripts use `^x`; longer superscripts use `^{xy}`. Subscripts use `_{...}`. Footnote markers and Project Comments can change interpretation. The parser must keep the raw syntax and the resolved visible graphemes. [Formatting Guidelines](https://www.pgdp.net/wiki/DP_Official_Documentation%3AFormatting/Formatting_Guidelines)

`/* ... */` preserves line arrangement for poetry and similar material. `/# ... #/` marks blocks printed differently, including block quotations. These are page structures, not inline labels, but they provide context and affect negative sampling. The [official revision history](https://www.pgdp.net/wiki/DP_Official_Documentation%3AProofreading/Proofreading_and_Formatting_Guidelines_Revision_History) records the 2009 generalization of `/# ... #/`.

Proofreader notes use `[** ...]`. Later volunteers retain them for post-processing review, and uncertain text goes to Project Discussion. Bad images and wrong text also require discussion or quarantine. These cases must never become ordinary negative labels. [Proofreading Guidelines](https://www.pgdp.net/wiki/DP_Official_Documentation%3AProofreading/Proofreading_Guidelines)

Guideline history changes label meaning. The official history records `<g>` and `<f>` in 2007, generalized block markup in 2009, small-cap formatting responsibility and `[**Note]` in 2005, and caret or brace notation in 2004. Every parsed record must carry either a guideline revision or an explicit `unknown` value. [Revision history](https://www.pgdp.net/wiki/DP_Official_Documentation%3AProofreading/Proofreading_and_Formatting_Guidelines_Revision_History)

Drop caps receive no reliable F2 marker. Official proofreading says to transcribe a large ornate opening capital as an ordinary letter. Later post-processing tools support `.dc` and `.di`, but that syntax does not make F2 absence a negative. [Proofreading guidance](https://www.pgdp.net/wiki/DP_Official_Documentation%3AProofreading/Proofreading_Guidelines#Large,_Ornate_Opening_Capital_Letter_(Drop_Cap)), [PPGen manual](https://www.pgdp.net/wiki/PPTools/Ppgen/Manual), [Easy Epub drop caps](https://www.pgdp.net/wiki/DP_Official_Documentation%3APP_and_PPV/Easy_Epub/Dropcaps)

## Gutenberg is a transformed verification source

Project Gutenberg separates manually curated main HTML and plain text from automatically generated derivatives. Generated EPUB uses HTML when available and plain text otherwise. Matching should prefer main HTML, then main text, and must record exact bytes. [Official mirroring guide](https://dev.gutenberg.org/help/mirroring.html), [official bibliographic record documentation](https://dev.gutenberg.org/help/bibliographic_record.html)

The local corpus uses mirror access and stores main HTML plus the best text while excluding generated formats, images, and `old/`. This follows Project Gutenberg's request to avoid large-scale public-site crawling. [Project Gutenberg terms](https://www.gutenberg.org/policy/terms_of_use.html)

Gutenberg may modernize spelling, remove line-end hyphenation, and convert formats. It does not promise fidelity to a physical edition. Updated editions can replace current files. Every match must therefore capture the ebook ID, relative artifact path, retrieval time, SHA-256, release or update header, and edition evidence. [Permission guidance](https://gutenberg.org/policy/permission), [Project Gutenberg license](https://www.gutenberg.org/policy/license)

An ebook number is only the first candidate key. Verification must compare title and copyright pages, edition statements, source-scan URLs, Distributed Proofreaders credit, transcriber names, and distinctive text. Global monotonic alignment must allow page merges, splits, moved footnotes, blank pages, plates, and words joined across a page break.

Project Gutenberg licensing is artifact-specific. Some works are distributed with a copyright holder's permission, and non-US law can differ. Preserve the license text or snapshot beside every artifact used for training. [Project Gutenberg license policy](https://gutenberg.org/policy/license.html)

## Standard Ebooks is high-quality but editorially transformed supervision

Standard Ebooks separates semantics from visual presentation imperfectly by design. `<em>` conveys emphasis and renders italic. `<i>` renders italic without inherent emphasis and often carries an `epub:type`. `<b>` renders as small caps in the core stylesheet rather than bold. A direct tag-to-label map would be wrong. [Standard Ebooks semantics manual](https://standardebooks.org/manual/1.8.3/4-semantics)

Current typography guidance uses `<strong>` for strong emphasis rendered in small caps. It also modernizes capitalization and can transform source all caps into `<em>`, `<strong>`, or `<b>`. Acronyms and initialisms have different semantic types and CSS. Supervision must resolve inherited CSS and record the semantic reason separately. It must label only computed visible typography. [Standard Ebooks typography manual](https://standardebooks.org/manual/1.9.0/8-typography)

`content.opf` can record separate transcription and scan sources through repeated `dc:source` entries. These links establish editorial lineage, not physical-edition identity on their own. [Metadata manual](https://standardebooks.org/manual/1.8.7/9-metadata), [section patterns](https://standardebooks.org/manual/1.9.0/6-standard-ebooks-section-patterns)

Standard Ebooks cleans and modernizes source ebooks for current readers. It is therefore a separate weak source, not a correction layer for F2. [What makes Standard Ebooks different](https://standardebooks.org/about/what-makes-standard-ebooks-different)

Standard Ebooks contributions and markup are released under CC0. Underlying text and art can remain restricted outside the United States. Preserve each repository's `LICENSE.md` and commit SHA in the manifest. [Standard Ebooks and the public domain](https://standardebooks.org/about/standard-ebooks-and-the-public-domain)

Local examples confirm the distinction:

- `jack-london_lost-face/src/epub/text/flush-of-gold.xhtml` uses `<em>` for emphasis, `<i>` for a vessel name, and `<i xml:lang="chn">` for a foreign phrase.
- `arthur-conan-doyle_the-adventures-of-sherlock-holmes/src/epub/text/the-redheaded-league.xhtml` uses `<b>`, while `src/epub/css/core.css` renders `b,strong` as small caps.
- `j-j-connington_nordenholts-million/src/epub/text/chapter-9.xhtml` uses `<sub>` inside a formula-like token.
- `h-rider-haggard_she/src/epub/css/local.css` combines blackletter, first-letter, and superscript rules that require computed-style resolution.

## Cross-corpus evidence should be fused per field

PGDP, Project Gutenberg, and Standard Ebooks often describe the same work or derive from related editions. A shared `pdomain-source-data` repository should record these relationships as a work and edition evidence graph. An ebook number or `dc:source` link starts matching but does not prove that two artifacts represent the same physical edition.

No source is authoritative for every page field. The scan image is authoritative for visible typography. Human labeler corrections are authoritative for reviewed text, geometry, and spans. PGDP F2 offers the strongest initial page-local formatting evidence. Gutenberg can improve final wording and explain post-processing changes. Standard Ebooks provides useful but editorially transformed weak evidence.

The fused page record should retain the selected value, every contributing artifact, disagreements, confidence, and derivation version. It can use PGDP for a span boundary, Gutenberg for wording, SPA OCR for word geometry, and a human decision for punctuation on the same page.

The source corpora usually do not provide OCR geometry. `pdomain-source-data` should emit geometry-optional labeling bundles containing images, text, markup, matches, conflicts, hashes, and provenance. The SPA runs the existing recognition and page-region models, creates geometry, aligns source evidence to OCR anchors, and records human corrections. The SPA then returns an immutable correction bundle for source-data import, audit, and versioned promotion.

## Model evidence favors recognized-text conditioning

A fixed-position visual sequence head is the smallest serious neural baseline. ViTSTR shows that a single-stage vision transformer can handle text sequences with parallel computation, and its official implementation is Apache-2.0. It lacks character identity, so repeated letters, punctuation, and small-cap distinctions are likely harder. [ViTSTR paper](https://arxiv.org/abs/2105.08582), [official code](https://github.com/kwon-evan/ViTSTR)

A text-conditioned head uses the known grapheme sequence as queries over visual features. This directly fits the task because OCR already supplies text. PARSeq demonstrates learned position queries and parallel decoding in a compact scene-text model. Its official Apache-2.0 implementation reports a 23.8M-parameter reference model, 3.26 GFLOPs, and a 14.87 ms median benchmark for its documented setup. Those figures establish a plausible scale, not a latency commitment here. [PARSeq paper](https://arxiv.org/abs/2207.06966), [official implementation](https://github.com/baudm/parseq)

ABINet provides supporting evidence for separate visual and language representations on degraded text. Its autonomous visual and language components also motivate text masking and an image-only ablation so the typography model cannot succeed through lexical shortcuts. [ABINet paper](https://arxiv.org/abs/2103.06495), [official code](https://github.com/FangShancheng/ABINet)

CTC is the strongest alignment challenger when character boxes do not exist. It marginalizes monotonic frame-to-symbol alignments, but vanilla CTC emits one symbol per step. Overlapping styles would require a separate alignment-marginalized multi-label loss rather than a combinatorial joint alphabet. [Original CTC paper](https://mlanthology.org/icml/2006/graves2006icml-connectionist/)

A short-line model can use several words and their geometry when style is relative to a baseline or neighbor. LayoutLMv3 shows that image patches, text, and two-dimensional geometry can support document token classification. Its official repository uses CC BY-NC-SA 4.0 and its 133M and 368M variants are larger than this task needs. Use the idea, not the dependency. [LayoutLMv3 paper](https://arxiv.org/abs/2204.08387), [official code and license](https://github.com/microsoft/unilm/tree/master/layoutlmv3)

DeepFont and FontCLIP are useful font-family or domain-shift references, not span models. DeepFont predicts among thousands of typefaces and uses synthetic-to-real adaptation, but it has no clear official reusable implementation and weights license. FontCLIP can mine typography-similarity negatives, but its repository includes CC BY-NC-SA 4.0 material. [DeepFont paper](https://arxiv.org/abs/1507.03196), [Adobe record](https://research.adobe.com/person/hailin-jin/), [FontCLIP implementation](https://github.com/yukistavailable/FontCLIP)

TrOCR and Donut generate text and would duplicate the existing recognizer. TrOCR's released configurations range from 62M to 558M parameters. Donut targets OCR-free document understanding rather than aligned style tagging. [TrOCR official models](https://github.com/microsoft/unilm/tree/master/trocr), [UniLM license](https://github.com/microsoft/unilm), [Donut paper](https://arxiv.org/abs/2111.15664), [Donut code](https://github.com/clovaai/donut)

Per-label temperature scaling is the first calibration method to test. It is simple and effective across many neural classifiers, though rare labels may need pooled or isotonic calibration. [Guo et al., 2017](https://proceedings.mlr.press/v70/guo17a.html)

## Historical-font synthesis can fill rare span gaps

Generated data is most useful for exact mixed boundaries, overlaps, rare superscripts and subscripts, letter spacing, and controlled hard negatives. It should not define production quality. Clean digital rendering cannot reproduce the full distribution of metal type, ink, paper, aging, microfilm, and scanning.

The workspace already has the right foundation in `/workspaces/pdomain/pdomain-ocr-synth`. It uses HarfBuzz with FreeType and emits shaped cluster geometry. It supports OpenType feature switches, deterministic recipes, paper textures, ink spread, erosion, blur, noise, skew, and JPEG degradation. The typography project should extend this repository rather than add another renderer.

HarfBuzz shapes Unicode with explicit direction, script, language, and feature ranges. It returns glyph identifiers, advances, offsets, and input clusters. Its cluster documentation warns that clusters are shaping units rather than Unicode graphemes. The canonical record must retain both. [HarfBuzz getting started](https://harfbuzz.github.io/getting-started.html), [OpenType features](https://harfbuzz.github.io/shaping-opentype-features.html), [cluster model](https://harfbuzz.github.io/clusters.html)

FreeType supplies controlled glyph loading and rasterization. The main generator should use grayscale coverage at four or eight times target resolution. It should then simulate print and scan effects before one final downsample. HarfBuzz should handle kerning because FreeType's direct kerning API does not cover general GPOS positioning. [HarfBuzz-FreeType integration](https://harfbuzz.github.io/integration-freetype.html), [FreeType glyph retrieval](https://freetype.org/freetype2/docs/reference/ft2-glyph_retrieval.html), [OpenType kerning](https://learn.microsoft.com/en-us/typography/opentype/spec/features_ko)

Kerning and letter spacing are separate factors. Normal shaping should leave `kern` enabled. Controlled variants can disable it. Letter spacing should add advance only between safe shaped clusters after shaping. It must not split a base from its marks or a ligature unless that sample also disables the ligature.

True and simulated typography must remain distinct in provenance. Italic should prefer a real italic face or `ital` axis. Bold should prefer a real face or `wght` coordinate. Small caps should prefer `smcp` and `c2sc`. Superscript and subscript should prefer `sups`, `subs`, or `sinf`. Scaled capitals and shifted small glyphs are useful fallback variants. They must be labeled as synthetic implementations. [OpenType variation axes](https://learn.microsoft.com/en-us/typography/opentype/otspec181/fvar), [OpenType small caps](https://learn.microsoft.com/en-us/typography/opentype/spec/features_pt), [registered feature list](https://learn.microsoft.com/en-us/typography/opentype/spec/featurelist)

Variable fonts add useful controlled axes. `wght`, `wdth`, `ital`, `slnt`, and `opsz` should be sampled only when the pinned binary declares them. Optical size is a design axis measured in points, not outline scaling. `fontTools` can inspect names, character maps, GSUB, GPOS, `fvar`, `STAT`, `OS/2`, and glyph sets. [fontTools documentation](https://fonttools.readthedocs.io/en/stable/index.html), [variable-font support](https://fonttools.readthedocs.io/en/latest/varLib/index.html)

Useful open historical revivals exist. A phase-one set should cover design lineages rather than collect near-duplicates:

- EB Garamond 12 for sixteenth-century French oldstyle and extensive small-cap, superior, inferior, and historical features. [Official project](https://github.com/octaviopardo/EBGaramond12), [feature specimen](https://github.com/georgd/EB-Garamond/blob/master/specimen/Specimen.tex)
- Junicode 2 for late-seventeenth and early-eighteenth-century Oxford types, broad historic characters, and variable weight and width. [Official project](https://github.com/psb1558/Junicode-font)
- IM FELL English, Great Primer, DW Pica, Double Pica, and French Canon for direct late-seventeenth-century revivals. [Google Fonts metadata](https://github.com/google/fonts/blob/main/ofl/imfellenglish/METADATA.pb)
- Old Standard TT for late-nineteenth and early-twentieth-century German, Russian, and European academic printing. [Official manual](https://ftp.math.utah.edu/pub/texlive/Contents/live/texmf-dist/doc/fonts/oldstandard/oldstand-manual.pdf)
- Sorts Mill Goudy for early-twentieth-century English and American book work with true small caps and rich figure features. [League of Moveable Type](https://www.theleagueofmoveabletype.com/sorts-mill-goudy)
- Source Serif 4 for Fournier-inspired transitional controls across weight and optical-size axes. [Official project documentation](https://github.com/adobe-fonts/source-serif/wiki/Source-Serif-Readme)
- Libertinus Serif for multilingual book typography and real small caps. [Official design guidance](https://github.com/alerque/libertinus/blob/master/documentation/Design-Guidelines.md)
- Cormorant for display faces and difficult font-change negatives. [Official project](https://github.com/CatharsisFonts/Cormorant)
- UnifrakturMaguntia and UnifrakturCook for text and display Fraktur. [Official project](https://unifraktur.sourceforge.net/de/)
- Baskervville, Libre Caslon Text, and one reviewed Bodoni family for transitional, Caslon, and Didone coverage. [Baskervville project](https://github.com/anrt-type/ANRT-Baskervville), [Libre Caslon project](https://github.com/font-archive/Libre-Caslon), [Bodoni Moda OFL](https://github.com/google/fonts/blob/main/ofl/bodonimoda/OFL.txt)

Every font enters through a manifest with the exact file SHA-256, upstream commit or tag, names, version, license, Reserved Font Names, axes, character coverage, and GSUB or GPOS features. Feature support must come from the pinned binary, not the family reputation.

The SIL Open Font License permits documents and graphics made with OFL fonts without applying the OFL to those outputs. Font-file redistribution still requires the license and copyright, and modified fonts must follow Reserved Font Name rules. This supports raster training-data generation, but the trained-model question still deserves project legal review. [Official OFL FAQ and text](https://software.sil.org/oflt/), [Google Fonts repository](https://github.com/google/fonts)

## Synthetic-to-real evidence requires real-only final evaluation

MJSynth established that millions of rendered word crops can train recognizers, but its corpus license is not clear enough for default reuse. Use the research, not the downloaded corpus, without legal review. [MJSynth paper](https://arxiv.org/abs/1406.2227), [official dataset page](https://www.robots.ox.ac.uk/~vgg/data/scenetext/)

SynthText placed text into scene images and released an Apache-2.0 generator. Its repository disclaims ownership of background images, and its scene pipeline does not match historical scans. [SynthText paper and code](https://github.com/ankush-me/SynthText)

SynthTIGER is the strongest external generator reference. It combines configurable text, fonts, textures, layouts, transformations, and effects under MIT. Its paper reports gains over combined MJSynth and SynthText training. The local renderer already covers much of this space, so SynthTIGER should inform comparison and missing features rather than replace `pdomain-ocr-synth`. [SynthTIGER paper](https://arxiv.org/abs/2107.09313), [official code](https://github.com/clovaai/synthtiger), [official API](https://clovaai.github.io/synthtiger/api_reference/synthtiger/index.html)

DeepFont directly found that clean synthetic font images transfer poorly without domain adaptation to real images. This is the closest typography-specific warning against synthetic-only training. [DeepFont domain adaptation](https://arxiv.org/abs/1412.5758), [system paper](https://arxiv.org/abs/1507.03196)

Real-data studies favor synthetic pretraining followed by real fine-tuning. One study improved CRNN accuracy from 75.8 to 82.1 percent and TRBA from 85.7 to 90.0 percent after fine-tuning large synthetic training on 276,000 real crops. [Baek et al., CVPR 2021](https://openaccess.thecvf.com/content/CVPR2021/papers/Baek_What_if_We_Only_Use_Real_Datasets_for_Scene_Text_CVPR_2021_paper.pdf)

A 2024 scaling study found that mixed real and diverse synthetic data helped PARSeq until synthetic data became too dominant. Its table peaked at a real-to-synthetic ratio of 1:3, then declined at 1:4 and sharply at 1:5. The paper's nearby ratio wording is inconsistent. This project must therefore treat the table as a starting hypothesis and select ratios on its own real validation set. [Rang et al., CVPR 2024](https://openaccess.thecvf.com/content/CVPR2024/papers/Rang_An_Empirical_Study_of_Scaling_Law_for_Scene_Text_Recognition_CVPR_2024_paper.pdf)

Another study found real fine-tuning essential and real unlabeled images better than synthetic data for self-supervised pretraining on its harder benchmark. The experiment program should therefore compare masked-image pretraining on unlabeled PGDP scans with supervised synthetic pretraining. [Jiang et al., ICCV 2023](https://openaccess.thecvf.com/content/ICCV2023/papers/Jiang_Revisiting_Scene_Text_Recognition_A_Data_Perspective_ICCV_2023_paper.pdf)

The leading curriculum is synthetic pretraining, a mixed middle stage, and real-only final fine-tuning. Initial mixed ratios should be real:synthetic `1:0.5`, `1:1`, `1:2`, and `1:3`. Synthetic-only performance must be reported to expose the domain gap, but it can never qualify a production model.

Synthetic text must come only from training groups or separate public-domain works. Rendering held-out transcriptions would leak lexical and punctuation patterns into the text-conditioned model. Font splits group design lineages, all weights, italics, variable instances, forks, and renamed derivatives. Several lineages remain entirely held out for synthetic generalization diagnostics.

Synthetic augmentation is accepted only when immutable real-scan validation shows at least 1.0 absolute macro grapheme F1 improvement and 2.0 absolute mixed-style exact-word improvement. No common label may lose more than 1.0 F1 point, and no audited stratum may lose more than 2.0. Calibration and abstention risk must not worsen after recalibration. The gain must persist across three training seeds or edition-group bootstrap resamples and after removing evaluation words seen in synthetic text.

## Evidence limits

The measured counts describe the mounted snapshot on 2026-08-21 UTC. They are not immutable corpus facts. The final data-preparation command must write its own version, input hashes, and timestamp.

The mixed-style and malformed counts come from an audit parser, not the proposed production parser. Acceptance tests must lock representative pages before any count becomes a release gate.

The official PGDP wiki is current documentation with revision history, not a per-project record of which historical rule version volunteers followed. Guideline revision therefore begins as `unknown` unless project timing and archived instructions justify a stronger value.

External model latency comes from different hardware, inputs, and software. Only local word and line benchmarks can set production limits.

## Conclusions

The mounted PGDP data supports strong initial experiments for italic, bold, small caps, and mixed spans. Superscript and subscript need syntax validation. Letter spacing and resolved font changes need other real sources or audited labels. Historical-font synthesis can cover rare combinations, but only real-scan validation can justify its use.

The first production experiment should remain a text-conditioned visual encoder with grapheme-level independent labels and a whole-word auxiliary head. Synthetic pretraining followed by mixed training and real-only fine-tuning is the leading synthetic curriculum to test.

## Next steps

Implement only after owner approval. Begin with the canonical parser and audit, establish immutable real-data splits, build the real-only whole-word baseline, then add the synthetic renderer extensions and controlled curriculum comparisons.

## What this does NOT establish

This research does not set production quality or latency thresholds. It does not prove edition identity from ebook numbers, infer missing PGDP labels as negatives, approve a trained-model license interpretation, or authorize code, repository creation, font downloads, model training, commits, or deployment.
