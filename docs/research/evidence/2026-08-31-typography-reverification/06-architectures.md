# 06 — Model architectures for fine-grained typography prediction

**Scope.** Given an OCR word crop or short text-line crop, the recognized text for that crop, and
whatever geometry is available, predict typography over exact character or grapheme spans:
italic, bold, small caps, letter spacing, font change, superscript, subscript. Labels are
multi-label and may overlap. Spans may cover part of a word. Training data has no reliable
character bounding boxes. Images are historical scanned book pages of variable quality. The model
must complement, not replace, an existing text recognizer and an existing page-region model.

**Retrieval date for every citation in this document: 2026-08-31.** Anything I could not verify
from a primary source is listed in "Verification gaps" at the end and marked inline.

---

## Verdict first

**Keep the stated preference, with one change to how it is trained.** Build a text-conditioned
visual encoder with a grapheme-level multi-label sequence head and a word-level auxiliary head —
but make the text-to-image alignment *explicitly monotonic* rather than free cross-attention, and
warm-start it from CTC forced alignment produced by the existing recognizer.

The single strongest piece of supporting evidence is the ICDAR 2024 Competition on Multi Font
Group Recognition and OCR: it runs exactly this task shape on exactly this material (early modern
prints), represents ground truth as *one font label per character* in a parallel `.font` string
aligned to the transcription, and scores it with character-level edit distance. The best team
reached **0.82% text CER and 2.96% font CER** in the restricted track and **0.81% / 2.78%** in the
open track
([competition page](https://lme.tf.fau.de/competitions/icdar2024-competition-on-multi-font-group-recognition-and-ocr/);
[chapter DOI 10.1007/978-3-031-70552-6_23](https://link.springer.com/chapter/10.1007/978-3-031-70552-6_23)).
That result establishes three things at once: the parallel per-character label string is a proven
representation, character-level typography on historical print is achievable at single-digit error,
and font error is roughly 3–4x the text error, so typography deserves its own head rather than
being folded into transcription.

**Smallest useful baseline to build first:** a whole-word multi-label classifier on word crops
(sigmoid per label), with character spans filled in by copying the word label to every character.
This is the BIR / TexTAR setup, it needs no alignment machinery, and it gives you the numbers that
justify anything more complex.

---

## What the literature actually does

### 1. How modern document-understanding and recognition models handle style alongside transcription

Two families, and neither gives you calibrated span-level typography today.

**Markup-generating sequence models.** The dominant modern pattern is to fold style into the
*output string* as markup, not into a separate label channel.

- KOSMOS-2.5 is trained on two cooperative transcription tasks: spatially-aware text blocks with
  coordinates, and "producing structured text output that captures styles and structures into the
  markdown format," from a shared decoder-only transformer with task-specific prompts
  ([arXiv:2309.11419](https://arxiv.org/abs/2309.11419)). It is 1B parameters, MIT licensed, and its
  own model card warns of hallucination risk and states it "CAN NOT guarantee the accuracy of all
  OCR/Markdown results" ([model card](https://huggingface.co/microsoft/kosmos-2.5)).
- Nougat outputs a lightweight markup (`.mmd`, Mathpix-Markdown-compatible) for academic PDFs
  ([arXiv:2308.13418](https://arxiv.org/abs/2308.13418)). Code is MIT, **model weights are CC-BY-NC**
  ([repo](https://github.com/facebookresearch/nougat)) — non-commercial weights are a licensing
  constraint worth noting before any dependency.
- GOT-OCR2.0 (580M) "can generate plain or formatted results (markdown/tikz/smiles/kern) via an
  easy prompt" ([arXiv:2409.01704](https://arxiv.org/abs/2409.01704);
  [repo](https://github.com/Ucas-HaoranWei/GOT-OCR2.0)).
- olmOCR emits Markdown from PDFs with a `--markdown` flag
  ([repo](https://github.com/allenai/olmocr)).

The limitation is structural: markup interleaved with text has no separable confidence, no
guaranteed alignment to the transcription you already trust, and no way to express overlapping
styles beyond nesting. A dropped `*` is indistinguishable from a style prediction of "roman."

**General VLMs are measurably bad at this specific axis.** "Reading ≠ Seeing: Diagnosing and
Closing the Typography Gap in Vision-Language Models" evaluates 15 state-of-the-art models and
reports that "color recognition is near-perfect, yet font style detection remains universally
poor," that model scale fails to predict performance, and that the gap looks like training-data
omission rather than a capacity ceiling; LoRA on a small synthetic set helps substantially but font
style stays the most resistant attribute ([arXiv:2603.08497](https://arxiv.org/abs/2603.08497)).
This is a direct argument against "just prompt a VLM" for the production path, and a direct
argument *for* synthetic supervision — which this repository generates.

**Dedicated attribute heads.** The counter-tradition treats attributes as their own classification
problem. TexTAR (ICDAR 2025) is the current state of the art for word-level textual attribute
recognition and is the closest published system to the requested task
([arXiv:2509.13151](https://arxiv.org/abs/2509.13151)). Details in Option D below.

### 2. Does anyone do span-level typography on historical print, and what do they report?

Yes — four relevant efforts, in increasing order of closeness to the target task.

| Work | Granularity | Material | Reported |
|---|---|---|---|
| Chaudhuri & Garain, ICPR 1998 | word | printed docs | first "detect italic, bold, all-capital without recognition" method ([IEEE](https://ieeexplore.ieee.org/document/711217/)) |
| BIR database, HIP 2021 | word | 285 pages, 19th–20th c. catalogues, French/Latin | "near-human performance for isolated word classification, but also demonstrating limitations for the task at hand" ([DOI](https://doi.org/10.1145/3476887.3476913); [data, MIT](https://github.com/asciusb/BIR-database)) |
| COCR / EMoFoG, ICDAR 2023 | **pixel column**, fused into CTC | 2,506 pages, 849 books, 15th–18th c. | COCR 1.81% CER overall; **1.95% vs SelOCR 2.61% on multi-font lines** ([arXiv:2305.07131](https://arxiv.org/abs/2305.07131)) |
| ICDAR 2024 Multi Font Group Recognition + OCR | **character** | early modern prints, expert-transcribed | **0.82% text CER / 2.96% font CER** (track 1); 0.81% / 2.78% (track 2) ([competition](https://lme.tf.fau.de/competitions/icdar2024-competition-on-multi-font-group-recognition-and-ocr/)) |

Two details from these matter a great deal for the design.

**The ICDAR 2024 label format is the representation to copy.** Font labels are stored in a `.font`
file holding "ASCII text with one label per character," parallel to the transcription, with the
organizers explicitly warning that multi-byte handling must be correct because "using string
iterators in Python, for example, does not deal with them properly" — i.e. the alignment is per
*grapheme*, not per byte. The class alphabet is single characters: `a` Antiqua, `b` Bastarda,
`f` Fraktur, `G` Gotico-Antiqua, `i` Italic, `r` Rotunda, `s` Schwabacher, `t` Textura. Scoring is
CER against that string, and a missing file scores as fully wrong
([competition page](https://lme.tf.fau.de/competitions/icdar2024-competition-on-multi-font-group-recognition-and-ocr/)).
Note the consequence: this scheme is **single-label per character**. It has no way to express
"italic AND small caps," which the target task requires. The extension needed is a per-character
*bit vector* rather than a per-character symbol, and CER is then the wrong metric (see Losses and
Metrics below).

**COCR proves the mid-line style change case is the one that separates approaches.** COCR estimates
"the font group of every pixel column of the text line to process," then uses "the classification
scores as weights to make a weighted sum of the OCR outputs, before the decoding step." Its overall
gain over selecting one model per line is small (1.81% vs 1.82% CER), but on *multi-font lines* the
gap is large: 1.95% vs 2.61% ([arXiv:2305.07131](https://arxiv.org/abs/2305.07131)). The requested
task is entirely about the part-of-word and mid-line case, so column-resolution style posteriors
are demonstrably the right internal representation, and word-level accuracy is a misleading
headline metric.

**Related but page/region-level, not span-level.** The Seuret et al. font-group dataset (35,623
images, 12 classes including Antiqua, Italic, Textura, Rotunda, Gotico-Antiqua, Bastarda,
Schwabacher, Fraktur, Greek, Hebrew, other, not-a-font; multi-label pages; highly imbalanced)
([DOI](https://dl.acm.org/doi/10.1145/3352631.3352640); [Zenodo](https://zenodo.org/record/3366686)),
its ICDAR 2021 competition successor ([test set](https://zenodo.org/records/4836551);
[chapter](https://link.springer.com/chapter/10.1007/978-3-030-86337-1_41)), and the OCR-D
`ocrd_typegroups_classifier` (DenseNet-121 at page/region level plus a column-wise RNN/CNN
classifier at line level, 12 classes, Apache-2.0, **archived read-only since 2024-02-19**)
([repo](https://github.com/OCR-D/ocrd_typegroups_classifier)). The archived column-wise variant is
the closest open implementation of a per-column style head on historical print.

### 3. Monotonic alignment between a known text string and an image without character boxes

This is a solved problem class, with three usable mechanisms and one well-documented failure mode.

**Forced alignment through a CTC trellis.** CTC-segmentation derives alignments from the frame-level
token posteriors of a CTC network trained only on unaligned pairs, and is robust to unknown extra
content at the ends of the signal
([arXiv:2007.09127](https://arxiv.org/abs/2007.09127)). The identical mechanism is already exposed
in an OCR engine you can use directly: kraken's `ForcedAlignmentTaskModel` performs "the process of
aligning a given transcription to the output of a text recognition model, producing approximate
character locations," reachable through the record's `cuts` attribute
([kraken API guide](https://kraken.re/main/user_guide/api.html)). This is the cheapest possible way
to get character spans out of an existing recognizer with zero new supervision.

**The caveat is that CTC alignments are peaky and therefore imprecise at fine granularity.** Zeyer,
Schlüter and Ney give a formal analysis: "only a few paths, which are dominated by blank labels,
contribute meaningfully to the marginalization," and they prove a case where a network trained with
CTC from uniform initialization converges to peaky behaviour with 100% error
([arXiv:2105.14849](https://arxiv.org/abs/2105.14849)). Huang et al. state the practical
consequence directly — peakiness "can cause inaccurate forced alignments (FA), especially at finer
granularity, e.g., phoneme level" — and fix it with label priors that boost paths containing fewer
blanks, reporting **12–40% improvement in phoneme and word boundary errors**
([arXiv:2406.02560](https://arxiv.org/abs/2406.02560)). Read across to this task: raw CTC peaks tell
you *where a character was decided*, not *how wide the glyph is*. For a style that is defined by
stroke weight or slant over the whole glyph body, boundary error matters, so a label-prior or
prior-smoothed alignment is worth the small extra cost.

**Learned hard monotonic alignment.** Raffel et al. give an end-to-end differentiable method for
learning monotonic alignments, trained by computing the expected alignment in closed form and
decoded as a hard left-to-right scan in linear time
([arXiv:1704.00784](https://arxiv.org/abs/1704.00784); [code](https://github.com/craffel/mad)).
Glow-TTS's Monotonic Alignment Search "searches for the most probable monotonic alignment between
text and the latent representation of speech on its own" by dynamic programming, with no external
aligner, and the authors report that enforcing hard monotonic alignment is what makes the model
robust and generalizable to long inputs ([arXiv:2005.11129](https://arxiv.org/abs/2005.11129)).
Printed Latin-script text lines are strictly left-to-right monotonic, so this assumption is *more*
valid here than in speech.

**Text-conditioned segmentation exists specifically for CTC recognizers.** TCSeg "segments
characters differently according to each text candidate prediction by segmentation-free text
recognition without affecting recognition accuracy," paired with Overlap and Skip Error Suppression
that uses the estimated segmentation to suppress unintuitive errors
([DOI 10.1007/978-3-030-86334-0_10](https://doi.org/10.1007/978-3-030-86334-0_10)). This is the
precedent for conditioning a segmentation on a *hypothesised text string* — the exact conditioning
the recommended architecture uses.

**Free (non-monotonic) attention is the thing to avoid.** Cheng et al. named and measured "attention
drift": attention-based recognizers "perform poorly on complicated and/or low-quality images because
they cannot get accurate alignments between feature areas and targets," and needed a second focusing
network to pull attention back ([arXiv:1709.02054](https://arxiv.org/abs/1709.02054)). Historical
scans of variable quality are precisely the regime where drift was reported. Unconstrained
cross-attention from text tokens to image columns will silently mis-assign spans on the hardest
pages — the pages whose labels you most want to trust.

**Pseudo-character-boxes from word-level labels are also a proven trick.** CRAFT trains a
character-level detector without character annotations: an interim model predicts a region score on
a cropped word image, the watershed algorithm splits it into character boxes, and a confidence
weight is set "proportional to the number of detected characters divided by the number of ground
truth characters" — using the transcription only for its *length*
([arXiv:1904.01941](https://arxiv.org/abs/1904.01941)). DTLR generalises the synthetic-to-real
route: pre-train a transformer detector on synthetic data *with* character boxes, then "fine-tuned
using line-level annotations on real data, even with different alphabets," covering printed,
handwritten, Latin, Chinese, and ciphered text
([arXiv:2409.17095](https://arxiv.org/abs/2409.17095); [code](https://github.com/raphael-baena/DTLR)).

That last result is unusually well matched to this repository, which is a synthetic generator with
perfect glyph placement knowledge: spec `docs/specs/12-glyph-annotations-emission.md` states the
synth "has *perfect* knowledge of which glyphs it placed for each word, so it is the gold-standard
source for any classifier learning to detect ligatures, long-s, or swash forms from word crops."
**You have character boxes on synthetic data even though you have none on real data.** Every
architecture below should be scored on how well it exploits that asymmetry.

---

## The options

Common notation: the crop image is `I`; the recognized text is `y = y_1..y_N` (graphemes, after
NFC + grapheme-cluster segmentation, so that combining marks and ligature clusters count once);
the label set is `L` (italic, bold, small-caps, tracking/letter-spaced, font-change, superscript,
subscript) and the target is a binary matrix `S ∈ {0,1}^(N×|L|)`.

### Option A — Visual encoder + character-sequence tagging head (no text conditioning)

**Inputs / outputs.** `I` → a length-`T` sequence of column features → `T×|L|` logits, then a
reduction to `N×|L|`. The recognized text is used only to know `N`.

**Character spans.** Implicit. You must map `T` feature columns onto `N` graphemes, either by
uniform division (wrong under variable advance widths, and *systematically* wrong for the
letter-spacing label you are trying to detect), by ink-gap heuristics (fragile on Fraktur, on
touching type, and on bleed-through), or by external alignment — at which point you have rebuilt
Option C.

**Multi-label / overlap.** Native and clean: independent sigmoid per label per column.

**Character boxes required?** No.

**Losses.** Per-column BCE with positives sparse; asymmetric loss (ASL) is the standard fix for
"few positive labels, many negative ones" dominating optimisation
([arXiv:2009.14119](https://arxiv.org/abs/2009.14119)).

**Calibration.** Easy case — per-label temperature or Platt scaling on a held-out split. Per-class
temperature scaling is reported to beat a single global temperature for multi-label problems, with
per-class Platt typically better still ([arXiv:2511.08261](https://arxiv.org/abs/2511.08261)),
building on the standard temperature-scaling recipe
([arXiv:1706.04599](https://arxiv.org/abs/1706.04599)).

**Data / compute.** Lowest of the sequence options. A CRNN-scale backbone is adequate; COCR's
column classifier is a CNN + 3-layer 128-unit BiLSTM ([arXiv:2305.07131](https://arxiv.org/abs/2305.07131)).

**Failure cases.** Span boundaries land in the wrong place whenever advance widths vary — italic
stem plus roman punctuation is the canonical example and is a stated requirement. Letter-spacing
labels are self-confounding, since the same geometry drives both the label and the column-to-
grapheme mapping. Bleed-through and ink spread shift column posteriors.

**OCR compatibility.** Perfect: fully independent, no shared weights, no retraining.

**Latency.** Cheapest sequence model. (Engineering estimate, not a cited figure: single-digit
milliseconds per word crop on GPU, tens on CPU.)

**Code / license.** No single reference implementation for the styled variant; the closest is the
archived column-wise classifier in `ocrd_typegroups_classifier`, Apache-2.0
([repo](https://github.com/OCR-D/ocrd_typegroups_classifier)).

**Verdict.** Good internal representation, incomplete as a system. Its column head is worth keeping
as a *component* of Option B or C.

### Option B — Text-conditioned visual encoder + grapheme multi-label head (+ word auxiliary head)

**Inputs / outputs.** `(I, y)` → `N×|L|` logits directly, plus one `|L|` word-level vector from an
auxiliary head. Grapheme embeddings of `y` act as queries over image column features.

**Character spans.** Explicit and exact by construction: output row `i` *is* grapheme `y_i`. No
post-hoc mapping, no CER-style edit distance in the metric — because the label sequence and the
text sequence have the same length by definition, evaluation reduces to per-position multi-label
scores. This is the property the ICDAR 2024 parallel `.font` format buys, extended from one symbol
per character to one bit vector per character
([competition page](https://lme.tf.fau.de/competitions/icdar2024-competition-on-multi-font-group-recognition-and-ocr/)).

**Multi-label / overlap.** Native. Overlapping italic + small-caps + superscript are independent
bits on the same grapheme. Grouping correlated labels into separate heads is a proven refinement:
TexTAR splits attributes into `T₁ = {normal, bold, italic, bold&italic}` and
`T₂ = {normal, underline, strikeout, both}` because "attributes like bold, italic are primarily
characterized by their effect on text, whereas other attributes like underline, strikeout have a
prominent visual feature independent of the text"
([arXiv:2509.13151](https://arxiv.org/abs/2509.13151)). The analogous split here is
{italic, bold, small-caps, font-change} — glyph-shape properties — versus
{letter-spacing, superscript, subscript} — position-and-metrics properties.

**Character boxes required?** No. But alignment is the whole risk: text tokens must find their own
columns. Do this with an explicit monotonic mechanism, not free attention. Three concrete choices,
all with primary-source backing: hard monotonic attention
([arXiv:1704.00784](https://arxiv.org/abs/1704.00784)), Monotonic Alignment Search by dynamic
programming with no external aligner ([arXiv:2005.11129](https://arxiv.org/abs/2005.11129)), or
CTC forced alignment from the frozen existing recognizer as a fixed teacher
([arXiv:2007.09127](https://arxiv.org/abs/2007.09127); ready-made in kraken via
`ForcedAlignmentTaskModel` and `cuts`, [API guide](https://kraken.re/main/user_guide/api.html)).
Free cross-attention invites attention drift on exactly the low-quality images this corpus is full
of ([arXiv:1709.02054](https://arxiv.org/abs/1709.02054)).

**Losses.** Per-grapheme ASL or weighted BCE ([arXiv:2009.14119](https://arxiv.org/abs/2009.14119));
word-level auxiliary BCE, which is what lets you train on cheap word-level labels such as BIR
([DOI](https://doi.org/10.1145/3476887.3476913)) and PGDP word markup; and, on synthetic data only,
an alignment loss against the known glyph boxes from spec 12. That third term is the
synthetic-to-real recipe DTLR validates: character-box supervision on synthetic, line-level only on
real ([arXiv:2409.17095](https://arxiv.org/abs/2409.17095)).

**Calibration.** Two levels, both needed. Per-label temperature/Platt on grapheme logits
([arXiv:2511.08261](https://arxiv.org/abs/2511.08261)), and a separate *alignment* confidence — the
entropy or margin of the monotonic alignment posterior — surfaced as an abstain signal. CRAFT's
confidence weight, "proportional to the number of detected characters divided by the number of
ground truth characters," is the precedent for weighting by alignment plausibility
([arXiv:1904.01941](https://arxiv.org/abs/1904.01941)).

**Data / compute.** Moderate. Synthetic pretraining is free here and, per Reading ≠ Seeing, small
synthetic sets are what close typography gaps by LoRA on existing models
([arXiv:2603.08497](https://arxiv.org/abs/2603.08497)). Real data needs only span-level markup,
which PGDP F2 already carries.

**Failure cases.** Alignment error dominates: a one-grapheme drift moves an italic boundary onto the
adjacent roman comma, which is exactly the requirement being tested. Recognizer errors propagate —
if `y` has an insertion, every downstream span shifts, so the model must be trained with corrupted
`y` (random substitutions/insertions/deletions) or it will be brittle in production. Small caps
versus true caps at a size ratio close to 1 is intrinsically ambiguous. Font-change is only
well-defined relative to a context, which argues for the line-level variant in Option D.

**OCR compatibility.** Excellent, and it is the *only* option that turns the existing recognizer
into an asset rather than a constraint: the recognizer supplies `y` and, optionally, the alignment
teacher. No shared weights, no retraining of the recognizer, no risk to CER.

**Latency.** One extra forward pass per crop, `N` decoder queries with a small cross-attention.
(Engineering estimate: same order as Option A, plus alignment. If CTC forced alignment is reused
from the recognizer's existing logits, the marginal cost is near zero.)

**Code / license.** No drop-in implementation. Reusable parts: TexTAR, MIT
([repo](https://github.com/tex-tar/tex-tar)); DTLR ([repo](https://github.com/raphael-baena/DTLR),
license unverified); monotonic attention reference code
([repo](https://github.com/craffel/mad), license unverified); kraken forced alignment
([API](https://kraken.re/main/user_guide/api.html)).

### Option C — CTC-style / monotonic latent-alignment model with no character boxes

**Inputs / outputs.** `I` → `T×|L|` column posteriors; the training loss marginalises over all
monotonic alignments between the `T` columns and the `N` known graphemes. At inference, take the
Viterbi alignment and pool columns per grapheme.

**Character spans.** Latent during training, explicit at inference from the alignment path. This is
COCR's structure taken one step further: COCR already estimates "the font group of every pixel
column" and fuses those scores into the CTC decode
([arXiv:2305.07131](https://arxiv.org/abs/2305.07131)).

**Multi-label / overlap.** Awkward in *classic* CTC, which needs a categorical alphabet — the
cross-product of 7 binary labels is 128 symbols and the ICDAR 2024 `.font` scheme is single-label
for exactly this reason. Workable if you keep the alignment latent variable but make the emission
model a product of per-label Bernoullis instead of a softmax. That is a small, defensible change,
but it is a change: you inherit the alignment machinery without inheriting an off-the-shelf loss.

**Character boxes required?** No — that is the entire point of the family
([arXiv:2007.09127](https://arxiv.org/abs/2007.09127)).

**Losses.** Marginal likelihood over monotonic paths (CTC-like, or MAS-style DP as in Glow-TTS,
[arXiv:2005.11129](https://arxiv.org/abs/2005.11129)). Add a label prior to fight peakiness
([arXiv:2406.02560](https://arxiv.org/abs/2406.02560)).

**Calibration.** Hardest of the options. Peaky posteriors are known to be poorly localized
([arXiv:2105.14849](https://arxiv.org/abs/2105.14849)), so per-grapheme probabilities inherit both
label uncertainty and boundary uncertainty in an entangled way. Post-hoc temperature scaling on the
*pooled* per-grapheme score is still applicable
([arXiv:1706.04599](https://arxiv.org/abs/1706.04599)).

**Data / compute.** Similar to B; the DP adds training cost.

**Failure cases.** Peaky alignments mis-set boundaries; letter-spacing detection is again partly
confounded with the alignment itself; blank-dominated paths can collapse rare labels.

**OCR compatibility.** Very good — it is architecturally sibling to the recognizer, and COCR shows a
column-wise font posterior can be fused into a CTC decode without harming CER (1.81% vs 1.92%
baseline) ([arXiv:2305.07131](https://arxiv.org/abs/2305.07131)).

**Latency.** Training-side DP cost; inference is a single pass plus a Viterbi backtrace, cheap.

**Code / license.** Column-wise classifier precedent in `ocrd_typegroups_classifier` (Apache-2.0,
archived) ([repo](https://github.com/OCR-D/ocrd_typegroups_classifier)); CTC-segmentation is in
SpeechBrain and in kraken's forced aligner ([kraken API](https://kraken.re/main/user_guide/api.html)).

**Verdict.** This is Option B with the alignment made latent instead of supervised. It is the right
*fallback* if forced alignment from the existing recognizer turns out to be too imprecise, and it is
a strictly larger research risk for the first production experiment.

### Option D — Short-line model, styles predicted jointly across several words

**Inputs / outputs.** A line crop or a word plus a context window of neighbours → per-word (or
per-grapheme) attributes for all of them at once.

**Character spans.** In TexTAR's realisation, none — it is word-level, on crops resized to 128×96 at
a fixed 3:4 aspect ratio ([arXiv:2509.13151](https://arxiv.org/abs/2509.13151)). To get spans you
must combine this with A, B, or C. Its value is the *context*, not the granularity.

**Multi-label / overlap.** Handled by dual grouped heads (`T₁`, `T₂` above), which is the cleanest
published treatment of correlated typography labels.

**Character boxes required?** No; word boxes are required.

**Losses.** "Weighted cross-entropy loss is employed, with empirically determined class weights of
0.25 and 0.75 for the T₁ and T₂ groups" ([arXiv:2509.13151](https://arxiv.org/abs/2509.13151)).

**Calibration.** TexTAR's post-processing already averages logits across overlapping context windows
(CAvg), which is a variance-reduction step that generally helps calibration; the paper reports F₁
only, not calibration.

**Data / compute.** MMTAD: "1,162 real multilingual and multidomain document images" with
"1,117,716 comprehensive word-level annotations," of which "87,867 annotated (except 'normal')
words overall"; splits 1,005 / 137 / 481; domains include notices, circulars, legislative documents,
land records, textbooks, notary documents; Hindi 67.35%, Telugu 8.23%, Marathi 7.95%, Punjabi
5.90%, Bengali 5.35% ([arXiv:2509.13151](https://arxiv.org/abs/2509.13151)). Context window is
S=125 neighbouring words per anchor, selected by weighted Chebyshev distance. Training is two-stage
(train encoder+heads, then freeze and fine-tune the RoPE-mixed attention blocks), 100 epochs, Adam,
lr 1e-4.

**Results.** 0.94 average F₁; bold 0.92 (vs CONSENT 0.86), italic 0.95 (vs 0.93), underline 0.87
(vs 0.81), bold&italic 0.90 (vs 0.84), against baselines including ResNet variants, DeepFont,
DropRegion, MTL, TaCo and CONSENT ([arXiv:2509.13151](https://arxiv.org/abs/2509.13151)).

**Failure cases.** Word granularity cannot express part-of-word spans at all — a hard blocker for
the stated requirement. Their italic augmentation is a shear transform, which is a weak proxy for
real italic typefaces with different letterforms, and weaker still for the Fraktur/Gaelic families
here.

**OCR compatibility.** Good; needs word boxes, which the page-region model presumably supplies.

**Latency.** Not reported in the paper. Context windows of 125 words amortise cost across a page.

**Code / license.** Code and pretrained weights released; **repo is MIT**
([repo](https://github.com/tex-tar/tex-tar); [project page](https://tex-tar.github.io/)). MMTAD test
set is on Hugging Face; the full dataset requires contacting the authors, and no dataset license is
stated on the project page.

**Verdict.** The best *evidence base* of any option and the source of two design elements worth
stealing — grouped heads and neighbour context — but wrong granularity as a whole system.

### Option E — Font-attribute / style-classification baselines

**DeepFont.** CNN with domain adaptation via a stacked convolutional autoencoder, plus learned model
compression; "achieves an accuracy of higher than 80% (top-5) on our collected dataset" and about 6x
compression without visible accuracy loss ([arXiv:1507.03196](https://arxiv.org/abs/1507.03196)).
Note the framing: top-5 over a large font inventory. That is *font identification*, not typography
attribution, and TexTAR uses it as a beaten baseline
([arXiv:2509.13151](https://arxiv.org/abs/2509.13151)).

**The modern successor is a ViT with parameter-efficient fine-tuning.** "Parameter-Efficient
Fine-Tuning of DINOv2 for Large-Scale Font Classification" reports **99.0% top-1 while training only
1% of the model's 87.2M parameters**, on GoogleFontsBench: 32 families, 394 variants, ~226,000
synthetic images (~575 per variant) ([arXiv:2602.13889](https://arxiv.org/abs/2602.13889)). The
transferable lesson for this project is not the number — it is a closed-set synthetic benchmark —
but the *recipe*: a frozen self-supervised ViT plus LoRA plus a synthetic corpus gets very far on
glyph-shape discrimination for very little training compute. This repository generates exactly that
kind of synthetic corpus.

**Attribute vocabularies.** O'Donovan et al. established the crowdsourced font-attribute paradigm —
high-level descriptors like "dramatic" or "legible," with models trained to predict attribute values
for new fonts ([ACM DOI](https://dl.acm.org/doi/10.1145/2601097.2601110);
[project page](https://www.dgp.toronto.edu/~donovan/font/)). Relevant as vocabulary design, not as
architecture.

**Historical-print classifiers.** `ocrd_typegroups_classifier`: DenseNet-121 over pages/regions and a
column-wise CNN/RNN over lines, 12 classes, per-class precision/recall in the 94–99% band,
Apache-2.0, archived 2024-02-19 ([repo](https://github.com/OCR-D/ocrd_typegroups_classifier)).

**Across all of E:** inputs are crops, outputs are a single categorical (or attribute vector) per
crop; there are no character spans; overlap is handled only if you replace softmax with sigmoids;
no character boxes needed; standard CE or BCE; calibration is the easy single-vector case; compute
is low; failure cases are all forms of *mixed-style crops*, which is the target regime. Compatibility
with the recognizer is total (they ignore it). These are baselines and feature extractors, not
candidate production architectures — but a DeepFont-class or DINOv2-LoRA-class encoder is a
perfectly good backbone to put underneath Option B.

### Option F (added) — Markup-generating seq2seq / VLM

**Inputs / outputs.** `I` (optionally plus a prompt or a text hint) → a single string with inline
style markup.

**Character spans.** Implicit in markup nesting; recoverable only by parsing, and only if the model
reproduces the transcription exactly. It usually will not.

**Multi-label / overlap.** Expressible by nesting, but no independent probability per label.

**Character boxes required?** No.

**Losses.** Token-level cross-entropy over the markup string.

**Calibration.** Poor and hard to fix. Token probabilities are over markup symbols, not over
typography events; there is no per-span probability to calibrate. KOSMOS-2.5's own card states it
"CAN NOT guarantee the accuracy of all OCR/Markdown results"
([model card](https://huggingface.co/microsoft/kosmos-2.5)).

**Data / compute.** Highest of all options — these are 0.6–1B+ parameter models
([GOT 580M, arXiv:2409.01704](https://arxiv.org/abs/2409.01704);
[KOSMOS-2.5 1B](https://huggingface.co/microsoft/kosmos-2.5)).

**Failure cases.** Hallucination; transcription drift that breaks the contract with the existing
recognizer; and the measured weakness of VLMs on precisely this attribute — "font style detection
remains universally poor" across 15 models, with font style the attribute most resistant to
fine-tuning ([arXiv:2603.08497](https://arxiv.org/abs/2603.08497)).

**OCR compatibility.** Worst of all options — it *replaces* the recognizer rather than complementing
it, violating a stated requirement.

**Latency.** Autoregressive over the whole output string; orders of magnitude above a per-crop head.

**Code / license.** Nougat: code MIT, **weights CC-BY-NC**
([repo](https://github.com/facebookresearch/nougat)). KOSMOS-2.5: MIT
([model card](https://huggingface.co/microsoft/kosmos-2.5)). GOT-OCR2.0
([repo](https://github.com/Ucas-HaoranWei/GOT-OCR2.0), license unverified). olmOCR
([repo](https://github.com/allenai/olmocr), license unverified).

**Verdict.** Rejected for production. Worth keeping for one purpose only: bulk *label bootstrapping*
on unlabelled pages, which the repository's own design already anticipates — the PGDP typography
design lists "Use multimodal language models to bootstrap tools and labels without making them a
runtime dependency" as a goal and "will not treat LLM output as verified ground truth" as a
non-goal (`docs/specs/2026-08-22-pgdp-typography-structure-synthesis-design.md`).

### Option G (added) — Detection-based character localisation, then per-character classification

**Inputs / outputs.** `I` → character detections (boxes) → per-character crops → per-character
multi-label head; the recognized text supplies the character count and identities for matching.

**Character spans.** The most explicit of all — actual boxes, which also gives you free geometry for
superscript/subscript (relative vertical offset) and letter spacing (inter-box gaps). Those two
labels are *geometric*, and a classic result is that discriminating baseline vs subscript vs
superscript "can be carried out almost perfectly (approximately 99.89%) by using the relative size
and position of adjacent characters" in mathematical OCR (see Verification gaps — this figure comes
from a secondary summary of Identifying Subscripts and Superscripts in Mathematical Documents and I
could not confirm it against the source).

**Multi-label / overlap.** Native per character.

**Character boxes required?** On synthetic data yes, on real data no. DTLR pre-trains on synthetic
character boxes then fine-tunes "using line-level annotations on real data, even with different
alphabets," and releases code and models
([arXiv:2409.17095](https://arxiv.org/abs/2409.17095); [code](https://github.com/raphael-baena/DTLR)).
CRAFT gets there without any character boxes at all, via watershed pseudo-labels weighted by
predicted-vs-expected character count ([arXiv:1904.01941](https://arxiv.org/abs/1904.01941)).

**Losses.** Detection loss (set prediction / Hungarian matching in DTLR) plus per-character BCE.

**Calibration.** Two-stage and therefore honest: detection confidence and classification confidence
are separately calibratable, and their conjunction is a natural abstain rule.

**Data / compute.** Higher than B — a detector plus a classifier — but the synthetic side is free
here given spec 12.

**Failure cases.** Touching type and ligatures in Fraktur and Gaelic break the one-box-per-grapheme
assumption; heavy ink spread merges characters; detection-count mismatch against `y` needs a
reconciliation policy.

**OCR compatibility.** Good, though DTLR is itself a recognizer, so using it purely as a localiser
means discarding half of what it does.

**Latency.** Highest of the non-VLM options.

**Code / license.** DTLR code and models public ([repo](https://github.com/raphael-baena/DTLR),
license unverified); CRAFT is widely reimplemented (license unverified).

**Verdict.** The strongest *alternative* to B, and the better choice if letter-spacing and
superscript/subscript turn out to dominate the error budget, because those labels are geometric and
this is the only option that measures geometry directly. It is more machinery than the first
experiment needs.

---

## Side-by-side

| | A: column tagger | **B: text-conditioned** | C: latent monotonic | D: line/context (TexTAR) | E: font classifiers | F: markup VLM | G: detect-then-classify |
|---|---|---|---|---|---|---|---|
| Exact grapheme spans | derived | **yes, by construction** | via Viterbi | no (word) | no | parse-dependent | yes, with boxes |
| Part-of-word spans | weak | **yes** | yes | **no** | no | nesting only | yes |
| Overlapping labels | yes | **yes** | needs Bernoulli emissions | yes (grouped) | if sigmoid | nesting only | yes |
| Needs char boxes | no | no (synthetic only) | no | no | no | no | synthetic only |
| Uses recognized text | length only | **fully** | length + order | no | no | no | count + identity |
| Calibration | easy | **easy + alignment conf.** | hard (peaky) | easy | easy | very hard | two-stage |
| Complements OCR | yes | **yes, uses it** | yes | yes | yes | **no, replaces** | yes |
| Published precedent for this exact task | partial (COCR columns) | TCSeg conditioning; ICDAR24 format | COCR, ICDAR24 | word-level only | none | none | none |
| Relative cost | low | low–moderate | moderate | moderate | low | high | high |

---

## Losses and metrics, specifically

**Do not use CER.** ICDAR 2024 uses font CER because its labels are one symbol per character and a
submission may be misaligned ([competition page](https://lme.tf.fau.de/competitions/icdar2024-competition-on-multi-font-group-recognition-and-ocr/)).
Under Option B the prediction is length-locked to the transcription, so edit distance is
meaningless. Score instead:

1. Per-label per-grapheme F₁ and precision/recall, the TexTAR convention
   ([arXiv:2509.13151](https://arxiv.org/abs/2509.13151)).
2. **Span-boundary error in graphemes**, reported separately for spans that start or end
   mid-word. This is the requirement, so it must be a headline metric, not a footnote. COCR's
   result — a small overall gain but a large gain restricted to multi-font lines
   ([arXiv:2305.07131](https://arxiv.org/abs/2305.07131)) — is the warning about what an aggregate
   number hides.
3. Expected calibration error per label, plus a reliability curve
   ([arXiv:1706.04599](https://arxiv.org/abs/1706.04599)).
4. Coverage at a fixed precision, since the downstream use is training-data generation and abstaining
   is cheap.

**Loss stack for Option B:** per-grapheme ASL ([arXiv:2009.14119](https://arxiv.org/abs/2009.14119))
for the main head; BCE for the word auxiliary head; on synthetic samples only, a cross-entropy
between the alignment posterior and the true glyph boxes from spec 12; optionally a label-prior term
on the alignment to counter peakiness ([arXiv:2406.02560](https://arxiv.org/abs/2406.02560)).

**Calibration procedure:** per-label temperature or Platt scaling fitted on a held-out real split,
not a synthetic one ([arXiv:2511.08261](https://arxiv.org/abs/2511.08261)); report separately for
in-profile and out-of-profile books, since the domain gap is the thing that breaks calibration.

---

## Recommendation

**Adopt the stated preference — a text-conditioned visual encoder with a grapheme-level multi-label
sequence head plus a word-level auxiliary head — with the alignment made explicitly monotonic and
warm-started from the existing recognizer's CTC forced alignment.**

Why this and not the alternatives:

- It is the only option that produces exact grapheme spans *and* uses the recognized text *and*
  handles overlapping labels natively, which is the intersection of the three hard requirements.
- Its output representation is the one the field already validated on this material: a label
  sequence parallel to the transcription, one entry per character, on early modern prints, at
  2.78–2.96% font CER ([ICDAR 2024](https://lme.tf.fau.de/competitions/icdar2024-competition-on-multi-font-group-recognition-and-ocr/)).
- Conditioning a per-character analysis on a hypothesised text string is published and works
  (TCSeg, [DOI 10.1007/978-3-030-86334-0_10](https://doi.org/10.1007/978-3-030-86334-0_10)).
- The alignment it needs is available for free from the recognizer you already have
  ([kraken forced alignment](https://kraken.re/main/user_guide/api.html);
  [CTC-segmentation, arXiv:2007.09127](https://arxiv.org/abs/2007.09127)).
- The one asymmetry in your data — perfect glyph boxes on synthetic, none on real
  (`docs/specs/12-glyph-annotations-emission.md`) — is exactly the asymmetry DTLR shows how to
  exploit ([arXiv:2409.17095](https://arxiv.org/abs/2409.17095)).

**The one change I would make to the stated preference:** do not use unconstrained cross-attention
from grapheme queries to image columns. Constrain it to be monotonic — MAS-style DP
([arXiv:2005.11129](https://arxiv.org/abs/2005.11129)) or hard monotonic attention
([arXiv:1704.00784](https://arxiv.org/abs/1704.00784)) — or supervise it from forced alignment.
Attention drift on low-quality images is a measured phenomenon, not a hypothetical
([arXiv:1709.02054](https://arxiv.org/abs/1709.02054)), and every part-of-word span you care about
depends on the alignment being right.

**Also steal two things from TexTAR:** grouped output heads for correlated attributes, and a
neighbour-context window. Split the heads into glyph-shape labels {italic, bold, small-caps,
font-change} and metric/position labels {letter-spacing, superscript, subscript} — the same logic
TexTAR used to separate `T₁` from `T₂` ([arXiv:2509.13151](https://arxiv.org/abs/2509.13151)).
Bold, small caps, letter spacing and font change are all *relative* judgements; a crop seen in
isolation has no reference weight, x-height or advance width to compare against. Feed the line's
own statistics, or the book profile the repository already computes, as conditioning.

### What would change this recommendation

Concrete, falsifiable triggers, in the order they would show up:

1. **Forced alignment turns out to be too coarse.** If, measured on synthetic data with known glyph
   boxes, CTC forced alignment from the existing recognizer has a median boundary error worse than
   roughly half an average advance width, the warm start is worthless. Fix in place first with label
   priors ([arXiv:2406.02560](https://arxiv.org/abs/2406.02560)); if that fails, switch to **Option
   G**, which measures geometry directly.
2. **Letter spacing, superscript and subscript dominate the error budget.** These are geometric, not
   appearance, labels. If they are more than half of the residual error after the glyph-shape labels
   are solved, **Option G** is the better architecture, because inter-box gaps and vertical offsets
   are direct features rather than things an encoder must infer.
3. **The baseline is already good enough.** If the whole-word baseline (below) reaches acceptable
   precision and part-of-word spans turn out to be rarer in PGDP than assumed, stop at **Option D/E**
   and spend the effort elsewhere. Measure the frequency of part-of-word spans in the corpus before
   building anything sequential — that single number is the strongest argument for or against this
   entire line of work.
4. **Transcription is unreliable on the hardest pages.** Option B assumes `y` is trustworthy enough
   to condition on. If recognizer CER on the target books is high enough that conditioning injects
   more error than it removes — test by ablating with corrupted `y` — fall back to **Option C**,
   which uses only the text's length and order.
5. **Overlapping labels turn out to be vanishingly rare.** If so, the whole design simplifies to a
   single categorical per grapheme and the ICDAR 2024 scheme applies unmodified, off the shelf,
   including its metric.

---

## Smallest useful baseline to build first

**A whole-word multi-label classifier: word crop in, one sigmoid vector out, character spans filled
by copying the word label to every grapheme.**

Specifics:

- Backbone: any small pretrained vision encoder, fine-tuned. The DINOv2 + LoRA result — 99.0% top-1
  training 1% of 87.2M parameters ([arXiv:2602.13889](https://arxiv.org/abs/2602.13889)) — suggests
  the cheapest viable configuration. A ResNet or DeepFont-class CNN is a fine alternative and is what
  TexTAR benchmarks against ([arXiv:2509.13151](https://arxiv.org/abs/2509.13151)).
- Labels: sigmoid per label, ASL or weighted BCE ([arXiv:2009.14119](https://arxiv.org/abs/2009.14119)).
- Calibration: per-label temperature scaling from day one
  ([arXiv:1706.04599](https://arxiv.org/abs/1706.04599);
  [arXiv:2511.08261](https://arxiv.org/abs/2511.08261)).
- Training data: synthetic pages from this repository, plus PGDP word-level markup; optionally the
  BIR database, 285 pages of list-like historical prints annotated at word level with bold and
  italic, MIT-licensed data ([DOI](https://doi.org/10.1145/3476887.3476913);
  [repo](https://github.com/asciusb/BIR-database)).
- Evaluation: per-label F₁ *and*, separately, the fraction of ground-truth spans that this baseline
  cannot represent at all — the part-of-word spans. That second number is the quantified case for
  building Option B, and it costs almost nothing to produce.

Why this baseline and not something smaller: it is the published state of the art's own granularity
(TexTAR reaches 0.94 average F₁ at word level,
[arXiv:2509.13151](https://arxiv.org/abs/2509.13151)), the BIR paper reports "near-human performance
for isolated word classification" ([DOI](https://doi.org/10.1145/3476887.3476913)), and it shares its
label vocabulary, its loss, its calibration procedure, its evaluation harness and most of its data
pipeline with the recommended architecture. Nothing built for it is thrown away.

---

## Verification gaps

Stated plainly, because the recommendation partly rests on sources I could not open.

1. **ICDAR 2024 competition per-team methods.** The chapter is closed access
   ([DOI](https://doi.org/10.1007/978-3-031-70552-6_23); Semantic Scholar confirms
   `openAccessPdf: CLOSED` and elides the abstract). I have the task definition, label format and
   headline CERs from the organizers' own competition page, but **not** the winning architectures.
   That is the single highest-value follow-up: knowing whether the winner used a cross-product
   alphabet, a second CTC head, or a column classifier would directly de-risk the design.
2. **BIR numeric baselines.** The ACM full text and the HAL PDF are both behind bot protection. I
   have the abstract verbatim via Semantic Scholar (openAccessPdf status GREEN, CC-BY-NC), which
   gives the "near-human performance" claim but no per-class F₁.
3. **TCSeg method detail.** Springer-paywalled; I have the method summary from the publisher's
   abstract page and secondary indexes, not the paper. Whether TCSeg needs character-box supervision
   anywhere is *not* confirmed.
4. **TexTAR inference latency and parameter count.** Not reported in the paper and not in the repo.
5. **Licenses I did not verify:** DTLR, CRAFT reimplementations, GOT-OCR2.0, olmOCR, PARSeq,
   `craffel/mad`. **Verified:** Nougat code MIT / weights CC-BY-NC; KOSMOS-2.5 MIT;
   `ocrd_typegroups_classifier` Apache-2.0 (archived 2024-02-19); `tex-tar/tex-tar` MIT;
   `asciusb/BIR-database` MIT.
6. **The 99.89% superscript/subscript figure** in Option G comes from a search-engine summary of
   "Identifying Subscripts and Superscripts in Mathematical Documents," not from the paper itself.
   Treat it as indicative only.
7. **All latency statements are my engineering estimates**, explicitly labelled as such. No source in
   this document reports inference latency for a typography head.
8. **Two cited papers post-date my training data** (arXiv:2602.13889, arXiv:2603.08497). I verified
   both exist by fetching their arXiv abstract pages, and I have reported only what those pages say.

---

## Source list

Retrieved 2026-08-31.

- DeepFont — <https://arxiv.org/abs/1507.03196>
- DINOv2 + LoRA font classification — <https://arxiv.org/abs/2602.13889>
- O'Donovan et al., crowdsourced font attributes — <https://dl.acm.org/doi/10.1145/2601097.2601110>, <https://www.dgp.toronto.edu/~donovan/font/>
- Chaudhuri & Garain, italic/bold/all-capital detection — <https://ieeexplore.ieee.org/document/711217/>
- TexTAR + MMTAD — <https://arxiv.org/abs/2509.13151>, <https://tex-tar.github.io/>, <https://github.com/tex-tar/tex-tar>
- BIR database — <https://doi.org/10.1145/3476887.3476913>, <https://github.com/asciusb/BIR-database>
- ICDAR 2024 Multi Font Group Recognition and OCR — <https://lme.tf.fau.de/competitions/icdar2024-competition-on-multi-font-group-recognition-and-ocr/>, <https://link.springer.com/chapter/10.1007/978-3-031-70552-6_23>
- Combining OCR Models for Reading Early Modern Printed Books (COCR / EMoFoG) — <https://arxiv.org/abs/2305.07131>
- Seuret et al., early printed books font groups dataset — <https://dl.acm.org/doi/10.1145/3352631.3352640>, <https://zenodo.org/record/3366686>
- ICDAR 2021 Historical Document Classification — <https://link.springer.com/chapter/10.1007/978-3-030-86337-1_41>, <https://zenodo.org/records/4836551>
- OCR-D typegroups classifier — <https://github.com/OCR-D/ocrd_typegroups_classifier>
- Nougat — <https://arxiv.org/abs/2308.13418>, <https://github.com/facebookresearch/nougat>
- KOSMOS-2.5 — <https://arxiv.org/abs/2309.11419>, <https://huggingface.co/microsoft/kosmos-2.5>
- GOT-OCR2.0 — <https://arxiv.org/abs/2409.01704>, <https://github.com/Ucas-HaoranWei/GOT-OCR2.0>
- olmOCR — <https://github.com/allenai/olmocr>
- Reading ≠ Seeing (typography gap in VLMs) — <https://arxiv.org/abs/2603.08497>
- CRAFT — <https://arxiv.org/abs/1904.01941>
- DTLR (general detection-based text line recognition) — <https://arxiv.org/abs/2409.17095>, <https://github.com/raphael-baena/DTLR>
- TCSeg (text-conditioned character segmentation) — <https://doi.org/10.1007/978-3-030-86334-0_10>
- Raffel et al., monotonic alignments — <https://arxiv.org/abs/1704.00784>, <https://github.com/craffel/mad>
- Glow-TTS / Monotonic Alignment Search — <https://arxiv.org/abs/2005.11129>
- CTC-segmentation (Kürzinger et al.) — <https://arxiv.org/abs/2007.09127>
- Why does CTC result in peaky behavior? — <https://arxiv.org/abs/2105.14849>
- Less Peaky and More Accurate CTC Forced Alignment by Label Priors — <https://arxiv.org/abs/2406.02560>
- Focusing Attention Network (attention drift) — <https://arxiv.org/abs/1709.02054>
- Asymmetric Loss for Multi-Label Classification — <https://arxiv.org/abs/2009.14119>
- On Calibration of Modern Neural Networks — <https://arxiv.org/abs/1706.04599>
- Uncertainty Calibration of Multi-Label Classifiers (per-class temperature/Platt) — <https://arxiv.org/abs/2511.08261>
- kraken forced alignment API — <https://kraken.re/main/user_guide/api.html>
- PARSeq (recognizer reference point) — <https://arxiv.org/abs/2207.06966>
- Calamari OCR — <https://github.com/Calamari-OCR/calamari>
