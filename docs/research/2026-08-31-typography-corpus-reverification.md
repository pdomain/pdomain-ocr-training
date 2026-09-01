---
Status: active
Owner: CT
Created: 2026-08-31
Last verified: 2026-08-31
Kind: research
---

# Typography corpus re-verification

The 2026-08-21 typography research still holds as a method. But its corpus counts have aged by a
factor of three, and six of its findings now point the design somewhere different.

## Agent Index

- **Kind:** research
- **Status:** active
- **Owner:** CT
- **Last verified:** 2026-08-31
- **Read when:** acting on the 2026-08-21 typography research, design, or plan, or before starting
  phase two.
- **Search terms:** typography re-verification, corpus growth, mixed-style words, F2 tag counts,
  Gutenberg HTML, guideline history, monotonic alignment.

## Goal

Re-verify the [2026-08-21 research](2026-08-21-fine-grained-typography-model-research.md) against
the corpora as they stand on 2026-08-31 UTC, and record every finding that changes a design
decision.

This corrects facts. It does not redesign the system. The
[design](../specs/2026-08-21-fine-grained-typography-model-design.md) and
[plan](../plans/2026-08-21-fine-grained-typography-model.md) remain the authorities, amended by the
corrections listed here.

## Method

Six independent research tracks measured the three corpora, the upstream PGDP documentation, the
shipped repositories, and the model literature. None of them saw the 2026-08-21 work, so their
agreement and disagreement with it are both meaningful. Corpus counts were then re-measured directly
against the live mounts. All counts describe the 2026-08-31 UTC snapshot.

## Evidence

## The earlier method reproduces; only the snapshot aged

Scaling the earlier mixed-style count by corpus growth predicts 80,677 mixed-style tokens. Direct
measurement today finds 80,738. The 2026-08-21 audit was sound. Its numbers simply describe a
corpus that has since more than tripled.

| Measure | 2026-08-21 | 2026-08-31 |
| --- | ---: | ---: |
| PGDP projects | 80 | 286 |
| PGDP F2 files | 79 | 285 |
| PGDP pages with F2 text | 21,353 | 73,103 |
| PGDP page images | 21,353 | 73,241 |
| PGDP snapshot size | 3.3 GiB | 11 GiB |
| Gutenberg book directories | 61,679 | 61,750 |
| Standard Ebooks repositories | 1,504 | 1,511 |

Two of the 288 top-level PGDP entries are cover images rather than projects. All 286 projects carry
a Project Gutenberg ebook number.

## Every inline tag count moved, and two moved enough to matter

Raw opening-tag counts over all 285 F2 files, measured the same way as the earlier audit and
saved in `tag-counts.txt` beside this work:

| Tag | 2026-08-21 | 2026-08-31 | Projects |
| --- | ---: | ---: | ---: |
| `<i>` | 27,460 | 102,393 | 283 |
| `<sc>` | 10,090 | 30,008 | 252 |
| `<b>` | 1,958 | 20,734 | 66 |
| `<f>` | 35 | 1,138 | 11 |
| `<g>` | 0 | 9 | 5 |
| `<u>` | not reported | 0 | 0 |

An independent audit parser counted 102,350, 29,988, and 20,733 for the first three tags. The
difference is under 0.05 percent and comes from how each parser treats markup inside bracketed
content such as `[Illustration: ...]`. Either count supports the conclusions below.

Bold is no longer a weak label. At 1,958 examples concentrated in 11 projects, a bold classifier
risked learning eleven particular books. At 20,734 across 66 projects that concern is much reduced.

Ambiguous font changes are no longer negligible. The design quarantines `<f>` unless Project
Comments resolve it, which cost almost nothing at 35 instances. At 1,138 across 11 projects, the
project-rule resolver now carries real weight, and deferring the controlled font-change vocabulary
has a measurable price.

Letter spacing has its first positives. The research states that the snapshot holds no `<g>`
positives, and the taxonomy defers `letter_spaced` on that basis. Nine instances across five
projects are enough for parser fixtures and not enough to train, so the deferral stands but its
stated reason no longer does.

## Only 3,999 words change style with no punctuation at the seam

This is the most consequential correction, because mixed-style words are the reason the model
predicts spans rather than word labels. The count depends entirely on where the boundary is allowed
to fall.

| Definition | Count | Share of tokens |
| --- | ---: | ---: |
| Whitespace tokens | 17,541,544 | |
| Tokens carrying any style | 399,260 | 2.3% |
| Uniformly styled whole words | 318,522 | 1.8% |
| Any label change within the token | 80,738 | 0.46% |
| Label differs among the word characters | 14,639 | 0.083% |
| Boundary falls between two adjacent letters | 3,999 | 0.023% |

Each row removes a class of case that needs no visual judgement. Of the 80,738 tokens with any
label change, 66,099 differ only because unstyled punctuation sits against a styled word. Of the
14,639 that remain, 10,640 place the boundary on interior punctuation such as the hyphen in
`<i>klong</i>-tree`. Only 3,999 words change style between two adjacent letters with no punctuation
to mark the seam.

That last row is what a word-level model plus a punctuation rule cannot reach, and it is the entire
case for predicting spans over graphemes.

Within those 3,999, the largest groups are italic against roman at 2,235 and superscript against
baseline at 1,364. Typical examples are the abbreviation `y^e` and a handwritten inscription
transcribed with letter-by-letter alternation.

Two consequences follow. First, the Phase 4 acceptance gate names "mixed-style exact accuracy"
without saying which of these definitions it means, and they span a factor of 20.

Second, the whole-word baseline should report the share of ground-truth spans it structurally
cannot represent, because that share is the quantified case for building anything more complex.

The counts remain parser-dependent and must not become release gates before acceptance fixtures
exist. An independent audit parser counted 1,541 core-mixed words under a stricter rule than the one
above, mostly by treating bracketed content and superscript shorthand differently. The design
already forbids promoting audit counts to gates for this reason, and that rule should stand.

## Project Gutenberg now carries typography and page anchors

The earlier research found no HTML in the matched Gutenberg directories and cast Gutenberg as a
text-only verification source. That is no longer true.

Across the 286 matched books, 93 percent contain `<i>` at about 90,000 occurrences, and 87 percent
contain small-caps spans at about 29,800 occurrences with real CSS behind them. Another 28 percent
carry letter-spacing CSS.

Page-boundary anchors of the form `id="Page_N"` appear in 89 percent of books, averaging roughly
204 per book.

Gutenberg may therefore become a supervision source rather than only a wording check. But the
anchors have not been tested against actual scan-image page boundaries, so page-level alignment is a
prospect and not a demonstrated capability.

Three further obstacles limit it. The mirror records no artifact version or hash, so a text
revised after PGDP produced it cannot be detected. The same typographic concept appears under
inconsistent class names, so extraction needs a normalization layer rather than a fixed selector
list. Most importantly, the 11 percent of books without page anchors cluster in modern fiction
reprints and multi-volume sets, so the pages that cannot be aligned differ systematically from
those that can.

The match rate is 286 of 286, but it describes a curated recent snapshot rather than a general
rate. The ebook numbers run from 78600 to 79400 and were all issued in mid-2026. Direct text
comparison confirmed 14 of 15 sampled books exactly.

## The edition-identity gate has lost one of its five signals

The design admits an external match only when the identifier relationship is joined by at least two
independent signals. The five candidate signals are edition matter, Distributed Proofreaders
credit, scan source, distinctive-text anchors, and high-margin global alignment.

Distributed Proofreaders credit is unavailable for this corpus. None of the 285 matched books
carries a "Produced by ... Distributed Proofreaders" line, because the modern Project Gutenberg
template omits the credit boilerplate entirely. The gate must reach its two signals from the
remaining four.

## Standard Ebooks confirms the warning and sharpens it

The design warns that a direct tag-to-label map would be wrong, and the catalogue proves it. The
`core.css` file is byte-identical across all 1,511 books and renders `b, strong` as
`font-variant: small-caps; font-weight: normal`, so a Standard Ebooks `<b>` never means bold.

Two further constructs carry no visible typography at all. Roman-numeral semantics appear 87,047
times and footnote reference markers 51,620 times, both with no rendered styling. Only `<em>`, which
is 99.9 percent free of semantic annotation, is a dependable visual-italic signal.

Three-way overlap remains too small to use. One book matches across all three corpora: Project
Gutenberg 79055, *The Place Called Dagon*, corroborated by a shared HathiTrust record. The earlier
conclusion that three-way matched-book evaluation is unsupported still stands.

One finding is more favourable than expected. Compared against its Gutenberg source, that book is
99.87 percent character-identical and 99.28 percent word-identical, with differences confined to
hyphenation, dash typography, and markup. On this single-book evidence, "editorially transformed"
overstates the distance.

Standard Ebooks contributions are CC0, so licensing does not restrict their use as supervision.

## Three guideline rules inject label noise the design does not yet handle

These come from the current official Formatting Guidelines v2.0a of 3 October 2023 and Proofreading
Guidelines v2.0e, with archived captures of the 2003, 2004, and 2006 editions.

Headings are deliberately left unmarked. Bold, gesperrt, and all-small-caps appearance in chapter
and section headings must not be tagged. The surrounding blank lines already separate them, and
the Format Preview tool treats an all-bold heading as a hard error. Visually bold heading text
is therefore systematically recorded as not bold. Headings must be excluded from bold negatives
rather than merely reported as an evaluation slice.

The italic tag means three different things depending on when the project ran. It covers true
italics and underlining under the current rule, and before the March 2007 introduction of `<g>` it
also covered letter-spaced text.

The shipped parser requires a guideline version and rejects an empty one, so the field is enforced.
Its only callers pass `task9-labeler-producer-v1` and `task9-labeler-book-producer-v1`, which name
the producing pipeline rather than a PGDP guideline revision. The era needed to read an older `<i>`
correctly is therefore not recorded anywhere, even though the field that should hold it is
mandatory.

Small capitals destroy letter case by design. An all-small-caps run is written in uppercase and is
indistinguishable from tagged full capitals, and a chapter's first word is re-cased away from the
image. Proofreaders are instructed to leave recognized case alone. Case inside a small-caps tag is a
formatter's classification, never an observation of the page.

Two further rules bear on the schema. The documented uses of `<f>` are mutually inverse, covering
antiqua within fraktur in one project and blackletter within roman in another, resolvable only
through free-text Project Comments.

Punctuation placement at a tag boundary is enforced only as a soft warning, so span edges vary by
one character, which bounds how precisely exact-span-match and boundary-distance metrics can ever
be measured.

## The corpus cannot show whether F2 reviewed anything

The design treats F2 as the strongest page-local evidence because it reviews and corrects F1. Since
June 2005 a project needs only one formatting round, so F2 is sometimes the sole formatting pass
rather than a second-pass review.

The corpus cannot distinguish the two cases. It stores 286 P3 rounds, 285 F2 rounds, and two PP
rounds, and no F1 round at all. The quality premise behind F2 is therefore unverified locally, and
the parsed record should carry the round history as evidence rather than assume a review occurred.

## Alignment should be monotonic rather than free attention

The recommended architecture survives. A text-conditioned visual encoder with a grapheme-level
multi-label head and a whole-word auxiliary head remains the right first production experiment.

One element should change. The design specifies two to four cross-attention layers binding grapheme
queries to image features. Independent review recommends making that alignment explicitly monotonic
and warm-starting it from forced alignment off the existing recognizer. Attention drift on
degraded images is a measured effect, and every part-of-word span depends on the alignment holding.

The closest published precedent runs this exact task. The ICDAR 2024 Competition on Multi Font Group
Recognition and OCR works on early modern prints and represents ground truth as one font label per
character, parallel to the transcription. Its best track-one result reports 0.82 percent text
character error against 2.96 percent font character error. Style error running about three and a
half times text error supports keeping a separate head rather than folding style into transcription.
The scheme needs extending to a per-character bit vector, because it allows only one label.

Two ideas from TexTAR are worth adopting: grouped heads for correlated attributes, and neighbour
context. TexTAR is an ICDAR 2025 attribute recogniser released under MIT with an average F1 of
0.94. Neighbour context matters because bold, small caps, and letter spacing are judgements
relative to surrounding text.

Markup-generating vision-language models were considered and rejected. They replace the recognizer
rather than complement it, and expose no per-span probability to calibrate. Font style detection
remains poor across fifteen current models.

## Nothing produces training crops yet

Phase two cannot begin with the model. No repository crops pixels from a page image, nothing calls
the shipped `align_tokens` or `project_style_span` functions, and the labeler preparation stage
emits geometry as absent. The alignment code exists and has never run against real geometry.

The shared contract is further along than the phase-one handoff records. `pdomain-book-tools` is
released through tag v0.26.2 with 373 passing tests, and `pdomain-source-data` exists and pins it.
The model package and the synthetic typography package are both absent.

## Two shipped facts contradict the design

The design states that routing model inference through a provider protocol preserves torch-free
boundaries in `pdomain-book-tools`. That package requires torch, torchvision, torchaudio,
transformers, and python-doctr as hard dependencies, with optional extras only for GPU support and
dewarping. It is not torch-free and never was. Torch-free public contracts are a property of
`pdomain-ocr-training`.

That matters for the synthetic renderer. The design asks `pdomain-ocr-synth` to implement the
canonical labels from `pdomain-book-tools`. That would pull a full training stack into a package
whose dependencies are currently confined to shaping, imaging, and validation libraries. A
torch-free mirror of the label and span types is the better route.

## Conclusions

The system design survives re-verification. The recommended architecture, the canonical schema, the
confidence tiers, and the repository boundaries all still hold. What changed is the evidence beneath
them.

Three changes matter most:

- Bold is now well supported where it was thin.
- The genuinely hard mixed-style case is far smaller than the earlier loose count suggested, which
  sharpens what the grapheme model must justify.
- Nothing yet produces a training crop, which makes crop production the first work of phase two
  rather than the model.

## Next steps

Amend the 2026-08-21 documents with the corrections below, then begin phase two at crop production.
The [phase two plan](../plans/2026-08-31-fine-grained-typography-phase-two.md) sequences that work.

### Corrections the 2026-08-21 documents need

- Replace every corpus count in the research with the 2026-08-31 figures above.
- Record that Gutenberg HTML is available, carries typography, and supplies page anchors for 89
  percent of matched books.
- Remove Distributed Proofreaders credit from the edition-identity signal list for this corpus.
- State which mixed-style definition the Phase 4 gate measures; they span a factor of 20.
- Add heading exclusion to the bold label's exclusions, beside the existing small-caps exclusions.
- Record that `<i>` before March 2007 may mean letter spacing, and treat guideline era as a
  required field rather than an optional one.
- Correct the claim that `pdomain-book-tools` is torch-free.
- Change the recommended alignment from free cross-attention to monotonic alignment warm-started
  from forced alignment.
- Record that `<g>` now has nine positives, so the `letter_spaced` deferral rests on volume rather
  than absence.
- Record the round history on each parsed page, because the corpus stores no F1 round and cannot show
  whether F2 reviewed anything.
- State that `pdomain-ocr-synth` carries a torch-free mirror of the label and span types rather than
  depending on `pdomain-book-tools`.

## What this does NOT establish

It does not set quality, calibration, or latency thresholds. It does not resolve the tenfold
disagreement between the two audit parsers, which requires the production parser and locked
acceptance fixtures. It does not confirm edition identity beyond the sampled books. It does not
authorize implementation, commits, or model training.
