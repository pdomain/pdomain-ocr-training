# Standard Ebooks mirror — inspection findings

Mirror root: `/workspaces/standardebooks-corpus` (read-only inspection, no writes/clones/fetches performed).
All counts below are **measured** against this local mirror on 2026-08-31 unless marked **inferred**.

## 0. Mirror identity

- `books/` contains **1511** full git checkouts (README's "~1,450" is stale by comparison to `clone_manifest.json`, whose `summary.repo_count` also reads 1511).
- `clone_manifest.json`: schema_version 1, source = GitHub org `standardebooks`, one entry per repo keyed by slug, each with `clone_url`, `local_head`/`upstream_head` (drift check), `local_sparse_audit`. All checkouts are full clones (not sparse) per the audit fields sampled.
- Reproduce book count: `ls /workspaces/standardebooks-corpus/books | wc -l` → 1511.
- Reproduce manifest count: `python3 -c "import json;d=json.load(open('clone_manifest.json'));print(len(d['repos']))"` → 1511.

## 1. Repository layout (per book)

Example: `books/a-a-milne_winnie-the-pooh/`

```
LICENSE.md                        # CC0 dedication text, identical in all 1511 books (single md5sum)
production-notes.md               # optional; present in 491/1511 books — notes deliberate deviations from source
images/                            # cover art (jpg/svg)
src/META-INF/container.xml
src/mimetype
src/epub/content.opf              # <- METADATA: identifies source(s), transcribers, PG ebook number
src/epub/toc.xhtml
src/epub/css/core.css             # SE's shared boilerplate CSS — byte-identical across all 1511 books (1 md5sum)
src/epub/css/se.css               # SE's shared semantic-vocabulary CSS — also byte-identical across all 1511 books (1 md5sum)
src/epub/css/local.css            # per-book overrides (this is where book-specific typography lives)
src/epub/images/{cover,logo,titlepage}.svg
src/epub/text/*.xhtml             # <- CONTENT: chapter-1.xhtml, imprint.xhtml, colophon.xhtml, dedication.xhtml, etc.
```

Reproduce: `find books/a-a-milne_winnie-the-pooh -not -path '*/.git*'`

- **Content lives in** `src/epub/text/*.xhtml` (one file per chapter/front-/back-matter section). 52,620 `.xhtml` files total in `src/epub/text/` across the corpus (`find . -path '*/src/epub/text/*.xhtml' | wc -l`).
- **CSS lives in** `src/epub/css/{core,se,local}.css`. `core.css` and `se.css` are SE's generated boilerplate and are **byte-identical in all 1511 repos** (verified by md5sum over all copies — 1 unique hash each). `local.css` is the only per-book stylesheet and is where genuine book-specific typographic choices (e.g. letter-spacing, custom small-caps headers) are expressed.
- **Metadata/source identification** is `src/epub/content.opf` (Dublin Core + SE's own `dc:source`, contributor/transcriber fields), reinforced in prose by `src/epub/text/imprint.xhtml` and `colophon.xhtml`.
- **Git history**: every book is a real git repo with substantial commit history — sampled books show 97 (Winnie-the-Pooh), 144 (Anna Karenina), 175 (A Tale of Two Cities), 250 (Pride and Prejudice) commits. The history documents SE's own production pipeline as discrete, named commits — e.g. Winnie-the-Pooh's earliest commits are literally `Initial commit` → `Adjust formatting, CSS` → `Convert italic spans to em, format songs/verse` → `Semanticate` → `Typogrify`. This confirms SE's tooling (`se semanticate`, `se typogrify`) as the mechanism that turns a raw transcription into SE's semantic/typographic markup, and the git history lets you diff any book back to its pre-semantication, pre-typogrify state.

## 2. Typography vocabulary — measured across the whole catalogue

Method: concatenated all 52,620 `src/epub/text/*.xhtml` files (976MB) and ran tag/attribute-token counts. Reproducible with:
```sh
find books -path '*/src/epub/text/*.xhtml' -exec cat {} + > /tmp/all.xhtml
grep -oE '<i[ >]' /tmp/all.xhtml | wc -l   # etc.
```

### Tag counts (opening-tag occurrences)

| tag | count |
|---|---|
| `<i>` | 199,968 |
| `<em>` | 138,675 |
| `<b>` | 39,446 |
| `<strong>` | 2,217 |
| `<abbr>` | 491,850 |
| `<sup>` | 395 |
| `<sub>` | 130 |

### epub:type vocabulary

155 distinct `epub:type` tokens appear catalogue-wide (space-tokenized, counted). Most frequent (top of a 155-line table):
`z3998:name-title` 351,243 (almost entirely on `<abbr>` — honorifics like "Mr.", "Dr.", not book titles), `z3998:persona` 142,392 (speaker-name markup — mostly `<td>` in verse-drama tables and `<b>` in prose dialogue), `z3998:roman` 87,047 (roman numerals — mostly on `<h*>`/`<span>`), `z3998:ordinal` 64,453, `noteref`/`backlink` ~51.5k each (footnote plumbing), `z3998:stage-direction` 39,965, `z3998:fiction` 39,342, `se:name.publication.book` 36,288 (book/work titles — 35,913 of these on `<i>`), `z3998:verse` 32,500, `z3998:given-name` 23,884, `se:name.vessel.ship` 14,376, `z3998:initialism` 12,147.

### class vocabulary

208 distinct `class` token values. Dominated by poetry-indentation levels (`i1`…`i13`, tens of thousands of uses) and the abbreviation-spacing hint `eoc` ("end of clause", on `<abbr class="eoc">etc.</abbr>` etc., 9,221 uses) — these are typographic-technical hints, not semantic-content classes. `class` is used far less systematically than `epub:type`; most book-specific classes (`noun`, `telegram`, `manicule`, `speaker`, `headline`…) are local, book-defined hooks tied to that book's `local.css`, not a fixed shared vocabulary.

### Small caps

SE does not use a `class="small-caps"` convention (0 hits for that literal string). Small caps is applied **via CSS `font-variant: small-caps` / `all-small-caps`**, most importantly:
- `core.css` (identical in all 1511 books): `b, strong { font-variant: small-caps; font-weight: normal; }` — **`<b>`/`<strong>` never render bold in SE**; they render as small caps at normal weight. This is the single largest semantic/visual trap in the corpus.
- `se.css` (identical in all 1511 books): `abbr[epub|type~="se:era"] { font-variant: all-small-caps; }` (AD/BC-type era markers), plus small-caps rules for colophon dates/links.
- 8,216 CSS declarations of `font-variant: small-caps` and 2,116 of `all-small-caps` across all books' CSS files (core+se+local combined) — the great majority inherited from the two identical boilerplate files, not book-specific.

### Letter spacing

Genuinely rare and book-specific: only **7 books** use `letter-spacing` in `local.css` (e.g. `lew-wallace_ben-hur`, `w-e-b-du-bois_dark-princess`), always on a small hand-picked selector (a blockquote header, a specific chapter's closing line) to reproduce a specific spaced-out heading in the source, never a corpus-wide convention.

### Superscript / subscript

Rare and used almost exclusively for genuine mathematical/chemical notation (`<sup>` for exponents like `x`, `10`; `<sub>` for chemical subscripts like `H<sub>2</sub>O`), not for footnote markers. **Footnote references use `<a epub:type="noteref">2</a>` as an inline, non-superscripted link** — no `<sup>` and no CSS rule superscripting `noteref` was found in the shared or per-book stylesheets. This is a clear case where the source page's visible typography (a small superscript digit) is *not* reproduced by SE's semantic markup at all — a plain inline numeral link stands in for it.

## 3. Semantic vs. visual — the core finding

**Verdict: SE's italic-family markup (`<i>`) is overwhelmingly semantic-first; `<em>` is the reliable "true visual emphasis" tag; `<b>`/`<strong>` are a visual trap (they render as small caps, never bold).**

Measured over all 199,968 `<i>` tags, all 138,675 `<em>` tags, and all 39,446 `<b>` tags in the catalogue:

| tag | has `epub:type` | has `xml:lang` | has neither (bare) |
|---|---|---|---|
| `<i>` | 120,209 (60.1%) | 80,356 (40.2%) | 13,299 (6.7%) |
| `<em>` | 10 (0.0%) | — | 138,534 (99.9% bare) |
| `<b>` | 32,059 (81.3%) | — | 7,350 (18.6% bare) |
| `<strong>` | 0 (0.0%) | — | 2,206 (99.5% bare) |

So **93.3% of `<i>` tags carry some semantic annotation** (an `epub:type` value or an `xml:lang` foreign-phrase marker), vs. essentially none of `<em>`'s uses. SE's own style: `<em>` = pure stress emphasis (semantically empty, always renders italic, reliably reproduces visible italics on the source page); `<i>` = a semantic container that *also happens to render italic by default* (core.css does not override `font-style` on `<i>`), used for named categories — book/publication titles, ship/vessel names, foreign-language words, "thought" passages, stage directions, taxonomic names, etc.

### Worked examples

**Reliable italic-on-page correspondence** (`herbert-gorman_the-place-called-dagon/src/epub/text/chapter-1.xhtml`):
```html
<em>was</em> a mystery, for he felt it like two huge dark wings…
```
This is exactly the PG source's underscore-italics convention (`_was_` in `79055-0.txt`) converted 1:1 to `<em>`. Visual and semantic agree.

**Semantic but visually neutral** — roman numerals:
```html
<h3 epub:type="z3998:ordinal z3998:roman">I</h3>
<span epub:type="z3998:roman">XIX</span>
```
No CSS rule anywhere in the shared or per-book stylesheets touches `z3998:roman` — it never triggers italics, small caps, or any distinct rendering. It is pure accessibility/semantic labeling (so assistive tech can expand "IV" as "four" rather than reading letters) with **zero visible typographic signal**.

**Semantic and visually distinct, but not italic** — speaker names in dialogue (`samuel-richardson_clarissa/src/epub/text/letter-325.xhtml`):
```html
<p><b epub:type="z3998:persona">Miss Charlotte.</b> Permit me to make a proposal…</p>
```
Renders as **small caps**, not bold — via the corpus-wide `core.css` rule. This does typically match how printed drama/dialogue speaker labels look on the page (small caps names), so semantic and visual agree — but only because `<b>` secretly means "small caps," a fact invisible from the tag name alone.

**Semantic honorific with no reliable page correspondence**:
```html
<abbr epub:type="z3998:name-title">Mr.</abbr> Westcott's taken something awful.
```
`z3998:name-title` here means "honorific title before a name" (Mr./Dr./Rev.), not "title of a work" — a vocabulary trap for anyone assuming `name-title` means book titles. `<abbr>` has no italic or bold styling in core.css (`border:none; white-space:nowrap`), so it is invisible typographically; on the original page "Mr." was set in ordinary roman type too, so semantic and visual (non-)correspondence agree here.

**Footnote markers** — semantic-only, with no visual correspondence to the source page's superscript numeral (see §2 above).

## 4. Source identification — measured across all 1511 books

`content.opf` `<dc:source>` is the field of record; SE also restates it in prose in `imprint.xhtml`/`colophon.xhtml`.

- **1510 / 1511** books (99.9%) have at least one `<dc:source>` entry; only 1 book has none.
- Domain breakdown of the 4,908 total `<dc:source>` URLs (a book can cite multiple sources — a text transcription plus separate page-scan source):

| domain | `<dc:source>` occurrences |
|---|---|
| archive.org | 1,967 |
| www.gutenberg.org | 1,808 |
| catalog.hathitrust.org | 411 |
| books.google.com | 168 |
| en.wikisource.org | 101 |
| www.fadedpage.com | 84 |
| www.google.com | 81 |
| trove.nla.gov.au | 59 |
| www.gutenberg.net.au | 47 |
| shakespeare.mit.edu | 32 |
| www.pgdp.org | 9 |

- Every `www.gutenberg.org` `<dc:source>` uses the pattern `https://www.gutenberg.org/ebooks/<N>` (no other PG URL shapes observed).
- **1,808** such PG-ebook `<dc:source>` entries, across **1,223 / 1,511 books (81.0%)** that cite at least one PG edition (a book may cite more than one PG number, e.g. multi-volume works, hence 1,808 > 1,223).
- **1,792** distinct PG ebook numbers are referenced catalogue-wide.

Reproduce: `grep -rl 'gutenberg.org' --include=content.opf books | wc -l` type counts; exact commands used are in the scratch worktree (`se_book_pg_pairs.tsv`, book↔PG-number pairs, one per line).

Note: SE's `dc:source` is *not always* PG — Winnie-the-Pooh, for instance, cites Faded Page + Google Books scans, not PG at all, despite both being well-known public-domain texts. PG citation is common but not universal or exclusive.

## 5. Overlap with the local PG and PGDP mirrors — the number that matters

**Matching rule**: exact integer equality of PG ebook number — SE's `dc:source` `.../ebooks/<N>` vs. `gutenberg-corpus/books/<N>/` directory name vs. PGDP `project.json`'s `pg_ebook_number` field. No fuzzy/title matching was used or needed because all three sources key on the same PG numbering scheme.

- **SE → local PG mirror**: all **1,792 / 1,792** distinct PG numbers cited by SE books are present as a directory in `/workspaces/gutenberg-corpus/books/` (61,750 numeric directories total — the local PG mirror is broad enough to cover 100% of SE's PG citations). Correspondingly, **1,223 / 1,511 SE books (81.0%)** have their cited PG edition available locally.
- **PGDP corpus**: `/workspaces/pdomain-data/pgdp-corpus/` contains **286** `projectID*` directories with a `project.json` (the other 2 top-level entries under that path are cover-art PNGs, not projects — the task's "288" figure counts those). All 286 carry a `pg_ebook_number` field (100% coverage of that field within the local PGDP corpus).
- **Three-way overlap (SE ∩ local-PG-mirror ∩ PGDP)**: **1 book.**
  - PG ebook **79055**, *The Place Called Dagon* by Herbert Gorman (1927).
  - SE repo: `books/herbert-gorman_the-place-called-dagon/` — `dc:source` cites `https://www.gutenberg.org/ebooks/79055` and `https://catalog.hathitrust.org/Record/006576101`.
  - PGDP project: `projectID69287386e7f4f` — title "The place called Dagon", author "Gorman, Herbert", `pg_ebook_number: 79055`, `image_source: HATHITRUST`, its comments cite the same HathiTrust record (`catalog.hathitrust.org/Record/006576101`) as the scan source — an independent corroboration beyond just the shared PG number.
  - Present locally at `/workspaces/gutenberg-corpus/books/79055/` (79055-0.txt, 79055-h/).

This is a small, singular overlap: the SE catalogue draws heavily on PG (1,223 books) and the local PGDP mirror is a broad, high-quality sample of PGDP projects (286), but PGDP's projects and SE's chosen PG editions intersect at only this one book in this snapshot. Treat 1 as exact for this snapshot, not as representative of the true SE∩PGDP overlap at large (SE draws from ~20,000+ live PGDP-derived PG books; the local PGDP mirror of 286 is a small sample of PGDP's total output, so a larger PGDP mirror would likely raise this count — this extrapolation is **inferred**, not measured).

## 6. Editorial transformation — worked diff on the one 3-way-matched book

Compared `books/herbert-gorman_the-place-called-dagon/src/epub/text/chapter-1.xhtml` (tags stripped) against the corresponding "Chapter One" span of `/workspaces/gutenberg-corpus/books/79055/79055-0.txt`, after Unicode-normalizing both (NFKC, collapsing SE's word-joiner characters, treating `...` and `…` as equivalent).

- Character-level `difflib.SequenceMatcher` ratio: **0.9987** (31,617 vs 31,650 chars).
- Word-level ratio: **0.9928** (5,495 PG words vs 5,500 SE words; 37 non-equal diff blocks total).
- Every observed word-level diff falls into one of these categories, with **no content words rewritten and no spelling modernized**:
  - **Hyphenation normalization**: `white-washed`→`whitewashed`, `jelly-fish`→`jellyfish`, `side-long`→`sidelong`, `school-house`→`schoolhouse`, `court-house`→`courthouse`, `golden-rod`→`goldenrod`, `farm-yards`→`farmyards`, `for ever`→`forever`.
  - **Dash typography**: ASCII double-hyphen `--` → em dash `—` (`Marlborough--and`→`Marlborough—and`).
  - **Italics markup, not text**: PG's underscore-italics convention (`_was_`) becomes real `<em>was</em>` markup (text unchanged, only representation).
  - **Ellipsis/whitespace tokenization**: PG's literal `...`/`....` at line-wrap boundaries vs. SE's Unicode `…` with word-joiner spacing — cosmetic, not content.
- Structural transformation observed directly in markup: PG's plain-text `Chapter One` / blank-line `I` becomes SE's nested `<section epub:type="chapter">`/`<section epub:type="z3998:subchapter">` hierarchy with `<h2>`/`<h3 epub:type="z3998:ordinal z3998:roman">` headings — a structural/semantic layer added on top, not a rewording.
- This is consistent with SE's documented, git-visible production pipeline (§1): `Semanticate` and `Typogrify` are literal, separately-committed automated passes in every book's history that (a) convert raw HTML/markup conventions into semantic `epub:type` tags and (b) normalize typographic characters (dashes, quotes, ellipses, hyphenation per SE's style manual) — this is not manual rewriting of prose.

**Caveat**: this is one book, one chapter — a sample, not a corpus-wide guarantee. The general SE style guide (external, not in this mirror) explicitly permits normalizing hyphenation, modernizing certain spellings on a case-by-case basis, and silently correcting scanner/typesetting errors, so other books may show larger deltas, especially where the PG source itself was a poor-quality OCR transcription that SE corrected against original page images. `production-notes.md` (present in 491/1511 books) is the per-book record of such deliberate departures where SE editors flagged them.

**Implication for character-level alignment**: because word choice is preserved and only mechanical typography changes (dashes, hyphenation, ellipsis, quote style), SE text is very likely alignable back to the underlying PG plain text (and by extension to a scanned page) with an off-the-shelf sequence aligner — the 99%+ character-level identity in this sample is a good sign. It has not been verified whether SE text aligns as cleanly to the actual *scanned page image* (as opposed to the PG plain-text transcription), which is the harder and more relevant alignment target for OCR training.

## 7. Licensing and provenance constraints

Per this mirror's own files (not fetched externally):

- `LICENSE.md` is **byte-identical across all 1511 books** (1 md5sum): "The source text and artwork in this ebook are believed to be in the United States public domain… The creators of, and contributors to, this ebook dedicate their contributions to the worldwide public domain via the terms in the CC0 1.0 Universal Public Domain Dedication."
- `content.opf`'s `<dc:rights>` restates the same text verbatim in every book (spot-checked, matches `LICENSE.md` content).
- Two distinct rights layers are asserted: (1) the underlying original text/artwork is *believed* to be US-public-domain (a belief, not a warranty — "may still be copyrighted in other countries… check local laws"), and (2) SE's own contribution (the transcription corrections, semantic markup, typography, CSS, cover art) is CC0-dedicated by SE and its named contributors.
- `SOURCE_COLLECTIONS.md` (this repo's own acquisition-policy doc, not SE's) states the broader house rule under which this mirror operates: "prefer official APIs… Do not build adapters around bypassing viewer controls or scraping pages meant for human reading" — SE is mirrored via full git clones of SE's own public GitHub org (the intended distribution channel for SE's source), so acquisition itself is not a licensing concern.
- No mirror-local document asserts anything narrower than CC0 for SE's own editorial layer. **Inferred, not stated anywhere in this mirror**: using SE text as weak-supervision training data is legally unconstrained by SE's license (CC0 imposes no attribution or share-alike burden), but the "believed to be public domain… may be copyrighted elsewhere" caveat on the *underlying* work is SE's own hedge, not a resolved rights determination — worth carrying forward as a caveat rather than a blocker.

## Summary of what could not be derived precisely

- Corpus-wide editorial-transformation statistics (spelling modernization rate, average character-diff-from-PG-source) are based on **one worked example**, not a systematic pass over all 1,223 PG-sourced books — that would require per-book PG-edition disambiguation (many PG numbers have multiple front-matter variants: `-0.txt`, `-h.htm`, `-8.txt`) and is flagged as future work, not computed here.
- Whether SE text aligns to the *scanned page image* (vs. the PG plain-text transcript) was not tested — no page-image-to-text alignment was attempted.
- The true SE∩PGDP overlap at PGDP's full scale (not just this 286-project local sample) is not derivable from this mirror; the measured "1" is exact for the local snapshot only.
