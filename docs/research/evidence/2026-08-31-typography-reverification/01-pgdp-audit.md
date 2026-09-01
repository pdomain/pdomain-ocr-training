# PGDP corpus audit: supervision for inline style-span prediction

Read-only audit of `/workspaces/pdomain-data/pgdp-corpus` (286 project
directories, ~11G). Goal: quantify what supervision this corpus can provide
for a model predicting inline style spans (italic, bold, small caps,
letter-spaced, font change, superscript, subscript) over exact character
spans within OCR word/line crops.

Reproducibility: all counts below come from
`/tmp/claude-1000/-workspaces-pdomain-pdomain-ocr-synth/a13105ad-089e-4e25-9c73-3e8b3a784c8f/scratchpad/typo-research/audit.py`,
run as:

```
uv run --project /workspaces/pdomain/pdomain-ocr-synth python audit.py
```

which writes the full machine-readable backing data (all per-page
histograms, per-project tag counts, and example pools) to `report.json` in
the same directory. Everything reported here is either read directly from
`report.json` or from a small number of one-off verification commands shown
inline (also read-only, all `cat`/`python3 -c` against the corpus). No file
under `/workspaces/pdomain-data/pgdp-corpus` or any git repository was
modified.

**Nothing in this repo, `pd-ocr-trainer`, or `pdomain-book-tools` currently
reads this corpus or these markup conventions** — this is corpus-only
groundwork for a not-yet-scoped future milestone. `make ci` was not run;
no code was added to the repo.

## 1. Structure

- **286 project directories** (`projectID*`), not the ~288 estimated in the
  brief — verified exact count via `ls -d .../pgdp-corpus/projectID* | wc -l`.
  The corpus root also holds 2 unrelated cover-art PNGs, not projects.
- Every project has `project.json`, `pages.json`, `inventory.json`,
  `.mirror-state.json`, and a `rounds/` directory (286/286 each).
- `rounds/P3.json` exists for **286/286** projects. `rounds/F2.json` exists
  for **285/286** — the sole exception is `projectID408c1dd9b9318`
  (138 pages, state `proj_submit_pgposted`). That project has *no* markup
  source at all and must be excluded from any style-span training set.
- **Declared `pages_total` sums to 73,241** (from `project.json`). Top-level
  page-image PNG count sums to **73,241** — an exact match, confirming every
  declared page has a scan.
- `pages.json` key count sums to **73,229** (12 short, spread across 6
  projects, each off by 1–3 pages — a minor bookkeeping gap not further
  investigated). `rounds/P3.json` matches `pages.json` exactly (73,229).
  `rounds/F2.json` key count sums to **73,103** — short by exactly 138,
  which is entirely explained by the one project with no F2 file at all.
  For every other project, F2 page count equals P3 page count exactly: F2
  (formatting-round) coverage is complete wherever it exists at all.
- **F2 key → image filename check: 0 mismatches across the whole corpus.**
  Every `"NNN.png"` key in every `F2.json` has a matching PNG file at the
  project's top level. Naming is exact and directly usable for image/text
  alignment.
- Page-image filename patterns (73,241 files): numeric (`299.png`)
  58,221; letter+digit prefix (`a003.png`, `p026.png`) 14,245; split-page
  suffix (`_l`/`_r`/`_1..._4`, for two-up or multi-part scans) 139;
  `NNN-NNN.png` 7; other 629. Naming convention is **not uniform across
  projects** — a page-image loader needs to handle at least these four
  shapes.
- `images/` subdirectories (facing plates / illustration scans, distinct
  from page scans — confirmed their keys never appear in F2) hold **6,377
  files** total across the corpus; 4 projects have no `images/` dir (no
  illustration plates, not a defect).
- `project.json` fields, with presence out of 286: `projectid`, `title`,
  `author`, `languages`, `character_suites`, `genre`, `difficulty`, `state`,
  `pages_total`, `pages_available`, `last_state_change_time`,
  `pg_ebook_number` — all **286/286**. `image_source`, `comments`,
  `forum_url` — **285/286** (one project has none of these three; not the
  same project that lacks F2).
- **`pg_ebook_number` is populated for all 286/286 projects**, always a
  plain integer, ranging **78,652–79,400** — a narrow ~750-wide band. This
  means the local corpus is not a broad historical sample; it looks like a
  single recent PGDP processing batch (all `state: proj_submit_pgposted`,
  i.e. all fully posted to Project Gutenberg). Composition claims below
  should be read as "this batch," not "PGDP in general."
- `pages.json` vs `rounds/F2.json` content differs meaningfully: `pages.json`
  is a **rendered/cleaned view** (block markers stripped) while
  `rounds/F2.json` is the **raw markup source** — e.g. `pages.json["308.png"]`
  starts `"39. Conventional figure..."` while `rounds/F2.json["308.png"]`
  starts `"/*\r\n39. Conventional figure..."`. **`rounds/F2.json` is the only
  file carrying inline style tags** — `rounds/P3.json` (the pre-formatting
  proofread text) was checked across a 60-project sample and contains
  **zero** `<...>` tags anywhere. P3 is not usable for style supervision.

## 2. Inline markup counts

Only five paired inline tags occur anywhere in the corpus's F2 text: `<i>`
(italic), `<b>` (bold), `<sc>` (small caps), `<g>` (letter-spaced /
gesperrt), `<f>` (font change, used both for named type styles like
"Black letter." and for otherwise-undescribed font shifts, e.g. a display
word rendered in a different face). No other paired inline tag exists
anywhere in the corpus. (`<tb>`, thought-break, also exists but is a
self-closing block-level paragraph marker, not a word-carrying style — see
below.)

Corrected corpus totals (see §7 on the bracket-recursion bug this figure
already accounts for), across 73,103 F2 pages:

| tag | opens | closes | pages with ≥1 | % of pages |
|---|---:|---:|---:|---:|
| `<i>` italic | 102,350 | 102,350 | 24,814 | 33.9% |
| `<sc>` small caps | 29,988 | 29,985 | 7,150 | 9.8% |
| `<b>` bold | 20,733 | 20,733 | 2,357 | 3.2% |
| `<f>` font change | 1,138 | 1,138 | 471 | 0.64% |
| `<g>` letter-spaced | 9 | 9 | 7 | 0.0096% |

`<tb>` (thought break): 4,685 occurrences — block-level, excluded from
inline style-span counting.

Per-page distribution is heavily skewed toward zero, not a smooth spread —
this is page-local burst behavior, not uniform density:

| tag | pages w/ 0 | pages w/ 1 | pages w/ 2–5 | pages w/ 6–20 | pages w/ 21+ | max on one page |
|---|---:|---:|---:|---:|---:|---:|
| `<i>` | 50,836 (69.5%) | 10,434 | 9,477 | 1,930 | 426 | 254 |
| `<sc>` | 66,779 (91.4%) | 2,849 | 3,168 | 289 | 18 | 91 |
| `<b>` | 70,752 (96.8%) | 419 | 635 | 1,032 | 265 | 53 |
| `<f>` | 72,642 (99.4%) | 64 | 372 | 25 | 0 | 12 |
| `<g>` | 73,098 (99.99%) | 3 | 2 | 0 | 0 | 2 |

The right tail (single pages carrying 50–254 tags of one type) is
front-matter: dramatis-personae lists, tables of contents, and dictionaries
with heavy small-caps/italic use per line. Full histograms (every bucket,
0–254) are in `report.json → markup.per_page_tag_count_histogram`.

Per-project tag totals for all 286 projects are in
`report.json → per_project_tag_counts` (one dict per project; not
reproduced here for length — 286 rows).

## 3. Superscript and subscript

Two distinct plain-text encodings are in use, confirmed by direct
inspection, not by tag search (sup/sub have no wrapping `<...>` tag):

- **Brace form**, both directions: `^{content}` and `_{content}` — applies
  to a run of one or more characters.
- **Single-character shorthand**, superscript only: `^X` where `X` is one
  letter or digit not preceded by `{`. **No single-character subscript
  shorthand exists anywhere in the corpus** (0 instances of a bare `_X`
  form after excluding false positives — see verification below).

Counts (after excluding carets/underscores that fall inside `[**...]`
proofreader notes or bare marker brackets, which are not real markup —
see §7):

| form | count |
|---|---:|
| `^{...}` (superscript, brace) | 227 |
| `^X` (superscript, single-char) | 1,476 |
| `_{...}` (subscript, brace) | 346 |
| `_X` (subscript, single-char) | 0 |

Real examples:

- `y^r` → "your" (legal-document abbreviation): *"you to assure y^{r}selves"*
- `27^{th} April 1870`, `May 2^{nd}. 1820`
- `Sept^r. 1807` (with an embedded proofreader note:
  `Sept^r. 1807</i>[**date unclear]`)
- `H_{2} and O`, `C_{2}H_{5}OH`, `HgCl_{2}`, `HNO_{3}`, `H_{2}O_{2}` —
  chemistry subscripts, always brace form
- `iiij^{li}`, `1^{us}, 2^{us}, 3^{us}` — Latin/legal-document ordinal
  abbreviations, single-char shorthand

**Methodological finding**: a naive whole-page-text regex for `^X` (no
awareness of bracket context) overcounts by ~40% here — 1,504 vs. the
correct 1,476 — because a handful of `^` characters live inside
`[**...]` proofreader notes that are *talking about* markup rather than
applying it (e.g. `[**P3 ^v ?]`, a proofer flagging uncertainty about
whether `^v` should be there), plus one project
(`projectID69a663dbc6925`) whose `[Formula: ...]` bracket blocks contain
**LaTeX math** (`\(a^2 + b^2 = c^2\)`, `\begin{array}...`) with 207 carets
that are exponent notation, not PGDP-convention superscript over prose.
Both must be excluded, and the parser used here excludes them: proofreader
notes are stripped as pure meta-commentary, and this one project's LaTeX
formula content is out-of-scope for prose typography (it's a different
representation of a different content type, not a labeled word span).

## 4. Block markers

Two paired block-level marker types, page-local (no evidence of crossing
pages — see §7):

| marker | opens | closes |
|---|---:|---:|
| `/* ... */` | 24,406 | 24,383 |
| `/# ... #/` | 11,000 | 11,020 |

Empirically (from real samples, not from an external spec lookup):
`/* */` wraps **centered** content — title pages, table-of-contents blocks,
plate/figure captions, and block quotations introduced with a colon, e.g.:

```
/*
PLATES

                                                               Page
76. Various forms of conventionalized...
```

`/# #/` wraps **indented/quoted running prose**, commonly quotation blocks
and illustration-caption bodies:

```
Illustration:

/#
Fig. 54.--Lateral view of bird
with twisted tail and wing
feathers.
#/
```

Open/close counts are not exactly balanced (24,406 vs 24,383; 11,000 vs
11,020) — small page-local discrepancies of the same kind as the unclosed
inline tags in §7, likely proofing slips rather than a systemic issue given
their size relative to totals (<0.2%).

## 5. Mixed-style words (key metric)

**Definition used**, chosen to match how a crop-level model would actually
be supervised: strip all markup from a page's F2 text, and for every
character in the stripped text, track the *set* of active style labels at
that position — italic/bold/small-caps/letter-spaced/font-change from a
proper open/close tag nesting stack, plus superscript/subscript from the
caret/underscore spans in §3. Tokenize the stripped text into word tokens
(runs of Unicode letters, joined across an internal apostrophe or hyphen —
so `Ennus's` and `n-dimensional` are each one token). A word is
**mixed-style** if the active-label state changes anywhere strictly inside
its character span — i.e., a style boundary lands inside the token rather
than at its edges. This catches partial-word italics, an italic stem with a
roman suffix, and a superscripted tail on an otherwise-plain abbreviation,
all with one rule.

**Headline numbers**:

- Total word tokens (whole corpus, all 285 F2-bearing projects): **17,068,296**
- Mixed-style words: **1,541**
- Mixed-style fraction: **0.0090%** (1 in ~11,077 words)

By style combination touching the word (`plain` = the untagged portion):

| combination | count |
|---|---:|
| italic + plain | 897 |
| plain + superscript | 495 |
| bold + plain | 62 |
| italic + superscript | 50 |
| plain + small-caps | 14 |
| font-change + plain | 9 |
| italic + plain + small-caps (3-way) | 5 |
| small-caps + superscript | 4 |
| italic + small-caps | 2 |
| plain + subscript | 2 |
| font-change + superscript | 1 |

Worked examples (verified against raw F2 text):

- **Partial-word italic, roman possessive**: `<i>Ennus</i>'s` → token
  `"Ennus's"` — italic stem, roman `'s`. Same pattern for `Fox's`,
  `Pigeon's`, `Minerva's`, `Tortoise's` (all in one Aesop's-fables project,
  `projectID5fa44b0308ca9`).
- **Italic stem, roman hyphen-suffix**: `<i>n</i>-dimensional` → token
  `"n-dimensional"`.
- **Superscript abbreviation split** (the largest non-italic category —
  historical legal/epistolary abbreviations where only the raised final
  letters are marked): `y^e` → token `"ye"` (= "the"), `w^{th}` → `"wth"`
  (= "with"), `Parliamt`, `Corts`, `Dr`, `Sr` — the plain stem plus a
  superscripted tail on the *same* word.
- **Rare extreme case — near-letter-by-letter alternation**: a child's
  handwritten book inscription, transcribed as
  `"<i>R</i><sc>U</sc>t<i>h</i> S<i>h</i>o<sc>R</sc><i>t</i> | <i>h</i>e<sc>R</sc> <i>b</i>oo<i>k</i> | <i>a</i>ge<i>d</i> <i>s</i>e<i>v</i>e<i>n</i> | <i>y</i>e<i>a</i><sc>R</sc><i>s</i>"`
  (`projectID62e173ee993c7`, page `027.png`) — used by the proofer to
  represent shaky, irregular handwriting. Produces the corpus's only
  4-state word, `"RUth"` (italic → small-caps → plain → italic). This is a
  genuine edge case a crop-level model has to be able to represent
  (single-letter spans), even though it's vanishingly rare.
- **Annotator uncertainty about the label itself**: `<b>V</b>-shaped` in a
  technical manual, immediately followed by the proofreader's own note
  `[**V bold/symbol/different font]` — the human labeler wasn't sure
  whether the source glyph was bold, a symbol, or a different font. This is
  a reminder that even "ground truth" style tags carry some irreducible
  labeling noise at the boundary between categories.
- **False-positive caveat**: one `plain+subscript` hit, token `"Sn"`, comes
  from `S_{n}` inside a LaTeX math formula in the one math-heavy project
  (`projectID69a663dbc6925`), not from prose typography — see §3. A
  production pipeline should probably exclude or separately flag
  `[Formula: ...]` regions before computing this metric.

**Practical implication**: mixed-style words are real but extremely rare —
too rare to rely on this corpus alone for that specific sub-phenomenon
(partial-word/partial-glyph style boundaries). If the model needs strong
supervision for boundary-inside-word cases specifically, this corpus alone
gives well under 2,000 real examples worldwide across all style pairs
combined, and single-digit-to-low-double-digit counts for most pairs other
than italic+plain and superscript+plain.

## 6. Nested and overlapping styles

Nesting is genuinely rare and shallow. **Maximum nesting depth observed:
3** (i.e., a run inside a run inside a run — never deeper) — found by
maintaining a real tag stack while scanning, not by regex.

Nested pairs (outer→inner), all instances:

| outer→inner | count |
|---|---:|
| `<i>` → `<f>` | 69 |
| `<b>` → `<i>` | 50 |
| `<i>` → `<sc>` | 16 |
| `<sc>` → `<i>` | 16 |
| `<i>` → `<b>` | 10 |
| `<i>` → `<i>` | 6 |
| `<sc>` → `<sc>` | 3 |

Real examples, verified by direct search for adjacent open-tag sequences:

- `<i><f>` — `"<i><f>Caput</f> breve, latum, subtriangulare. <f>Aures</f> parvæ..."`
  — italic Latin species description with individual font-changed
  genus/anatomical terms nested inside.
- `<b><i>` — `"<b><i>Diploma</i></b> of\r\n<b><i>Character</i></b>"` (an
  illustration caption; bold+italic combined on the same words).
- `<i><b>` — `'"<i><b>Yes.</b></i>"'` (dialogue emphasis).
- `<sc><i>` — `"<sc><i>Sheweth</i></sc>:"` (legal-document salutation, small
  caps wrapping an italic word).
- `<i><sc>` — `"<i><sc>The</sc> HEALTHY LIFE\r\nBEVERAGE BOOK</i>"` — with
  the proofreader's own note `[**italics for underline]` alongside it,
  i.e. italics here stands in for what was underlining in the original.
- `<i><i>` — `"<i><i>Ass</i></i>"` — a doubly-wrapped identical tag with no
  visual difference from single italic; almost certainly a proofing
  artifact (redundant markup) rather than an intentional third style, worth
  filtering out in any downstream parser.
- `<sc><sc>` (3 instances) — same redundant-wrapping pattern for small caps.

No `<g>`-involving nesting was observed (too rare — only 9 occurrences
total). `<f>` nested inside `<i>` (69 cases) is the single most common
nesting pattern, consistently for embedded technical/Latin terms inside an
italicized descriptive clause.

## 7. Malformed or unbalanced markup

F2 markup is **almost perfectly page-local**, as documented. Out of 73,103
pages:

| defect | instances | pages affected |
|---|---:|---:|
| unclosed open tag at end of page | 3 | 2 |
| unmatched close tag (no open) | 0 | 0 |
| crossed nesting (`<a><b></a></b>`) | 0 | 0 |

The 2 affected pages were checked by hand against the immediately following
page to see whether the "missing" close tag was actually a real
cross-page style continuation (i.e., whether the next page opens with the
matching close tag):

- `projectID62930b71a45bb`, page `p3640.png` — page ends with an unclosed
  `<sc>` inside a footnote-like aside. The next page (`p3650.png`) begins
  `"known. The present case, in which <i>Mantis membranacea</i>..."` — no
  leading `</sc>`. **Not** a real cross-page span; a genuine proofing slip.
- `projectID6644d7736baab`, page `190.png` — 2 unclosed `<sc>` inside what
  looks like a complex ASCII table (`+---+---+` school-statistics table).
  The next page (`191.png`) begins with a fresh `<sc>Table showing Race or
  Creed</sc>` — again no leading close tag. Also a proofing slip, not
  intentional.

**Conclusion: F2 markup's page-local documentation holds in practice** —
0.0027% of pages (2/73,103) have any unclosed tag, and in both checked
cases the style clearly does *not* continue onto the next page's raw text
— confirming per-page markup parsing is safe without needing any
cross-page state.

A related but distinct bug was found and fixed *in this audit's own
parser*, not in the corpus: an early version of `audit.py` treated every
`[...]` bracket note as fully opaque metadata and stripped it, which
silently dropped tags that live *inside* `[Footnote ...]`, `[Illustration:
...]`, and bare stage-direction brackets like `[<i>Laughing</i>]` — see §9.
Before the fix this undercounted `<i>` by 10,414 occurrences (10.2%) and
`<sc>` by 1,755 (5.9%) corpus-wide. All numbers in this report use the
fixed parser.

## 8. Proofreader notes and unresolved questions

Two families of bracketed annotation exist in F2 text:

- **`[**...]` proofreader notes** — the standard PGDP formatting-round
  note, always meta-commentary that was never on the printed page (spot
  checked: only 28 of 13,814 contain a caret/underscore, and those are the
  proofer *talking about* markup, e.g. `[**P3 ^v ?]`, not applying it).
  **Total: 13,814.** Of these, **4,313 (31.2%) end in `?`** — an unresolved
  question the proofreader flagged but did not answer, e.g.
  `[**raised comma?]`, `[**materially?]`, `[**Raphael?]`,
  `[**mark place in <sc>?]`. The remaining ~69% are declarative formatting
  instructions or corrections, e.g. `[**wide indent]`,
  `[**unneeded ']`, `[**responsibilities]` (a correction/expansion).
  **These can be reliably stripped** — they carry no page content and
  never span a bracket boundary that also opens a real tag (spot-checked
  for nested `[` inside `[**...]`: none found in the sampled projects).
- **Other bracketed content, 37,498 total instances**, is a mix of:
  - **Footnote-anchor / diacritic / short markers** (≤4 alnum chars,
    13,646 instances, 341 distinct tokens) — numeric/lettered footnote
    call-outs (`[1]`, `[A]`, `[2]` ... — the 10 most common are single
    digits/letters), roman-numeral-style anchors (`[vj]`, `[vJ]`), and
    diacritic-substitution notation for characters outside the project's
    declared character set (`[=o]`, `[=e]`, `[=a]` — macron/breve marks
    over a base letter). These represent a single glyph or a footnote-call
    symbol that *is* on the page but isn't running text — **not reliably
    strippable without loss**, since discarding them loses the footnote
    anchor position or the diacritic character entirely.
  - **Labeled-content brackets carrying real page text with their own
    style tags**: `[Footnote A: ...<i>...</i>]`, `[Illustration: ...]`,
    `[Sidenote: ...]` — see §9, these total 8,383 and are now recursed into
    rather than stripped.
  - **Pure structural markers**: `[Blank Page]` (2,353), bare
    `[Illustration]` with no caption (1,314), `[Cyrillic]` (346, a
    placeholder where non-Latin script wasn't transcribed, likely because
    the project's `character_suites` doesn't cover it) — safe to strip,
    they carry no recoverable text.

## 9. Project-specific formatting instructions

Formatting/proofing guidance lives in `project.json → comments`, an
HTML-formatted free-text field written per-project by the project's
formatter/post-processor for the human proofreading team on pgdp.net. It is
**not** part of F2 markup and is **not machine-structured** — it must be
read as prose.

- **283/285** F2-bearing projects have a non-empty `comments` field.
- A broad keyword scan (italic/bold/font/superscript/etc.) matches
  **218/285** — but manual inspection shows most of these are false
  positives: boilerplate HTML (`<b>` used for a comment-section heading),
  a passing mention of the book's own title in italics, or a
  content-free `# Formatting\nNothing out of the ordinary.` section.
- A tighter phrase-level heuristic (looking for imperative override
  language — "please treat/mark/format...", "do not mark...", "should be
  ...") matches **94/285** — a better (still approximate) estimate of
  projects carrying an actual project-specific override.
- Real examples of genuine per-project overrides found:
  - *Structural reclassification*: "Please treat everything listed in the
    [TOC] as a major division." / "Where there are roman numeral headers,
    please treat these as chapters."
  - *Explicit non-default punctuation convention*: "the author uses three
    spaced asterisks to show a deleted section. Please proof these as
    `* * *` with a single space between the asterisks."
  - *Telling proofers NOT to over-interpret style tags structurally*:
    "Consider paragraphs beginning with a few bold or small caps words as
    regular paragraphs, not section headers" — directly relevant to this
    project's goal, since it shows PGDP's own proofers are explicitly
    warned that `<b>`/`<sc>` at a paragraph start does **not** reliably
    imply a structural role.
  - *Formatting-guideline override*: "**Do not mark** thought breaks with
    an extra blank line" (overriding the site-wide default convention,
    linked from the official DP formatting-guidelines wiki page) — appears
    verbatim across several projects, suggesting a shared template rather
    than an independently-written note each time.
  - *Retread/legacy-formatting warning*: one project's comments explain it
    was "previously run as a chapter out of a larger volume... you may
    find some formatting markup in the project. Feel free to remove all
    the formatting" — i.e., pre-existing markup in that project may be
    stale/inconsistent with the current round.

Net: **project-specific overrides exist and are non-trivial (roughly a
third of projects), but they're prose instructions to human proofreaders,
not a machine-readable override table** — using them to adjust style-label
semantics per project would require an LLM or manual read of each
project's comments field, not a parser.

## 10. Corpus composition

Measured directly from `project.json` (286 projects):

- **Language**: `languages: ["English"]` for **286/286** — no other value
  appears in the `languages` field. (Inferred, not measured: some English
  books quote or footnote in other scripts — see `character_suites` below
  — so "100% English" describes the primary language field, not every
  character on every page.)
- **`character_suites`** (a project can declare more than one):
  `basic-latin` 286/286; `polytonic-greek` 15; `basic-greek` 8;
  `symbols-collection` 6; `extended-european-latin-b` 4;
  `medievalist-supplement` 3; `extended-european-latin-a` 2;
  `basic-cyrillic` 2; `extended-european-latin-c` 1;
  `semitic-and-indic` 1; `math-symbols` 1. So ~9% of projects contain some
  non-basic-Latin content even though all are tagged English-language.
- **Genre**: 61 distinct values, long-tailed. Top entries: General Fiction
  31, Travel 18, Juvenile 17, Poetry 16, Instructional 15, Mystery 14,
  History 12, Non-Fiction 10, Drama 9, Romance 8. No genre exceeds 11% of
  the corpus.
- **`difficulty`** (PGDP's own proofing-complexity/scan-quality rating —
  the closest thing to a scan-quality signal in the metadata):
  `average` 250 (87.4%), `easy` 29 (10.1%), `hard` 5 (1.7%), `beginner` 2
  (0.7%). Heavily skewed toward "average" — this batch is not weighted
  toward hard-to-scan material.
- **`image_source`**: TIA (Internet Archive) 146 (51%), TIA_AL 48,
  HATHITRUST 41, `_internal` 33, TIA_CAN 6, DL_VILL_U 3, ICE 2, GOOGLE 2,
  BHL 1, NLS 1, AUSTLIB 1, MJP 1. Dominated by two archive.org variants
  plus HathiTrust — i.e. mostly library rescans, not born-digital.
- **`state`**: `proj_submit_pgposted` for **286/286** — every project in
  this local corpus has already been fully posted to Project Gutenberg.
  This is a finished-work sample, not a mix of in-progress projects.
- **Period**: **not derivable from metadata** — there is no
  publication-year or period field in `project.json`. The only
  time-adjacent signal is `last_state_change_time` (when this project's
  processing last changed, in 2025–2026, not the book's publication date)
  and the free-text `title`/`comments` fields, which were not
  systematically parsed for dates here. Reporting a period distribution
  would require either OCR/metadata lookup against the PG ebook number or
  manual title inspection — out of scope for this pass.
- **PG ebook number**: present for **286/286** projects (100%), always
  populated, range 78,652–79,400 (see §1 caveat about batch narrowness).

## 11. Total text volume and per-label word counts

Computed from the markup-stripped F2 text of all 285 F2-bearing projects
(the corrected parser — see §7/§9 — used consistently, including recursing
into labeled-content brackets), 73,103 pages:

- **Total word tokens: 17,068,296**
- **Total visible characters (non-markup, whitespace excluded from the
  character-label breakdown below but included in this total): 102,263,377**

Per-label word counts (a word can appear in more than one row if it's a
mixed-style word from §5 — rows do not sum to the total):

| label | word count | % of all words |
|---|---:|---:|
| plain (no style) | 16,672,688 | 97.68% |
| italic | 281,761 | 1.65% |
| small caps | 64,935 | 0.38% |
| bold | 47,050 | 0.28% |
| font change | 1,388 | 0.0081% |
| superscript | 917 | 0.0054% |
| letter-spaced | 10 | 0.00006% |
| subscript | 2 | 0.00001% |

Per-label character counts (visible, non-whitespace):

| label | char count |
|---|---:|
| plain | 79,158,019 |
| italic | 1,447,358 |
| small caps | 355,362 |
| bold | 251,166 |
| font change | 7,592 |
| superscript | 2,003 |
| subscript | 357 |
| letter-spaced | 79 |

## Honest gaps

- **Period/date composition** is not derivable from the local metadata at
  all (§10) — would need an external PG-ebook-number → year lookup.
- **Per-project override count (§9)** is a heuristic phrase match, not an
  exact count — the field is free-text prose and a fully accurate count
  would need manual reading of all 285 comment blocks.
- **Nested-pair examples in §6** were re-verified by direct adjacent-tag
  search after the first automated example-extraction approach (grabbing
  "the first `<tag>` on the page") produced misleading snippets that
  didn't actually show the nesting event; the counts themselves were
  correct throughout, only the illustrative snippets needed re-derivation.
- **Genre/period/difficulty distributions describe this local batch**, not
  PGDP as a whole or historical printed English generally — see the
  narrow `pg_ebook_number` band in §1.

## Files

- `audit.py` — the full read-only analysis script (structure, tag census,
  sup/sub, block markers, proofreader notes, mixed-word analysis, nesting,
  malformed-tag detection, project comments, visible-text/label counts).
- `report.json` — full machine-readable output, including all per-page
  histograms (every bucket 0–254 for each tag), per-project tag counts for
  all 286 projects, and example pools larger than what's quoted above.
- `find_combo_examples.py` — small follow-up script (imports `audit.py`)
  used to find one real example of each rare mixed-style-word combination
  for §5.
