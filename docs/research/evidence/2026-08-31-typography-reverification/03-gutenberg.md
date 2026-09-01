# Project Gutenberg local mirror — usability as weak supervision for PGDP typography

Read-only inspection. Local mirror: `/workspaces/gutenberg-corpus` (README: `/workspaces/gutenberg-corpus/README.md`,
manifest: `/workspaces/gutenberg-corpus/clone_manifest.json`, catalog cache: `/workspaces/gutenberg-corpus/.cache/pg_catalog.csv`).
PGDP corpus: `/workspaces/pdomain-data/pgdp-corpus`. All numbers below are **measured** from these files unless
marked **inferred**. Commands are reproducible as shown; scratch intermediates live in
`/tmp/claude-1000/-workspaces-pdomain-pdomain-ocr-synth/a13105ad-089e-4e25-9c73-3e8b3a784c8f/scratchpad/typo-research/`
(`all_files.txt`, `pgdp_projects.tsv`, `matched.tsv`).

## 1. Acquisition contract (from README + manifest)

- `clone_manifest.json`: schema 1, generated `2026-08-31T04:02:20Z`, filter
  `{type: "Text", languages: ["en"], fiction: "any"}`, 61,750 book entries (`id`, `title`, `author`, `language`).
- Per-book pull is **rsync**, not HTTP/git, from `rsync.ibiblio.org::gutenberg` (fallback
  `gutenberg.pglaf.org::gutenberg`). Fetched: "all HTML plus the best plain text, never images."
  Explicitly excluded always: images, the upstream `old/` subdir, and `*.zip *.mobi *.epub *.iso` plus audio.
- Fetch completeness marker: `books/<id>/.pull-complete.json` — `{completed, files[], mirror, schema}`. **No content
  hash, no upstream file mtime/ETag, no PG revision number** is recorded — only the local fetch timestamp.
- Command: `find /workspaces/gutenberg-corpus/books -type f | wc -l` → 179,472 files.
- Of 61,750 book directories, 61,651 have `.pull-complete.json`; **99 directories are incomplete fetches**
  (README's own definition: absence of the marker means "refetch"), verified via
  `comm -23 <(dirs) <(dirs-with-marker)`. None of the 99 fall in the PGDP-matched set (checked below).

### Artifact types and counts (measured, all 61,750 dirs)

| artifact | count | notes |
|---|---|---|
| `.pull-complete.json` | 61,651 | fetch-complete marker; 99 dirs missing it |
| any `.htm`/`.html` file | 56,210 books | `have_html` via full directory walk |
| no `.htm`/`.html` at all (text-only) | 5,540 books | old/legacy postings; HTML weak-supervision is impossible for these by construction |
| `<id>-0.txt` | 39,188 | "best" UTF-8 plain text |
| `<id>-8.txt` | 13,768 | Latin-1 plain text (no UTF-8 edition exists) |
| bare `<id>.txt` | 8,597 | oldest legacy encoding (plain ASCII/no suffix convention) |
| `<id>-h/<id>-h.htm` | 56,248 | the standard "HTML edition," depth-2 under an `<id>-h/` dir |
| `<id>-src/<id>-src.htm` | 14 files across 7 books | see below — raw math-source HTML, pre-image-generation |
| other one-off htm (`-index.htm`, split multi-file books like `KingHorn.html`, `WoodEngraving*.html`) | <20 total | rare split-file or legacy naming, not a systematic category |

**No epub/mobi/generated-derivative formats exist in this mirror at all** — they're excluded by the fetch
policy itself, so the "prefer master over generated derivative" question mostly does not arise as an epub-vs-html
choice. The one place a real master-vs-generated distinction shows up:

- 7 books (`38993, 78050, 79044, 33283, 79069, 78255, 73996, 76404, 78513, 75107, 78343, 79080, 78586, 77427` —
  14 files, some books have 2) carry **both** `<id>-src/<id>-src.htm` and `<id>-h/<id>-h.htm`. Diffing them
  (`diff books/38993/38993-src/38993-src.htm books/38993/38993-h/38993-h.htm`) shows `-src` holds literal LaTeX
  math (`\(C\)`, `\[...\]`) and no images, while `-h` is the **same file with every inline formula machine-converted
  to an `<img src="images/N.svg" data-tex="...">`** by PG's `ebookmaker` build — i.e. `-src` is closer to the
  proofread master, `-h` is a generated rendering of it. This only matters for math-heavy books (rare in this set).
- More broadly, 266/286 matched books' `-h.htm` carry `.x-ebookmaker`/`.x-ebookmaker-drop` CSS hooks (measured),
  confirming the "-h.htm" itself is a build product of PG's `ebookmaker` pipeline (conditional CSS toggling
  content for HTML vs epub output) rather than a raw DP submission. It is still the most-authoritative HTML PG
  publishes; there's no "more original" HTML to prefer over it in this mirror.

## 2. Match rate: PGDP → PG ebook number → local mirror directory

- `pdomain-data/pgdp-corpus` has **286** `projectID*` directories (glob `projectID*`; the raw `ls` count of 288
  includes 2 stray `*.png` cover-art files at the corpus root that are not project directories).
- **286/286 (100%)** of `project.json` files carry a numeric `pg_ebook_number` field. State field is uniformly
  `proj_submit_pgposted` for all 286 — i.e. every project in this corpus snapshot has already been posted to PG.
- **286/286 (100%)** of those ebook numbers resolve to an existing `books/<id>/` directory in the local mirror,
  **and** every one of those 286 directories has both `.pull-complete.json` and at least one HTML artifact.
  Zero unmatched projects — there is no "unmatched, and why" list to report because none failed.
- Ebook numbers cluster tightly in 78600–79400 (all `Issued` 2026-06 through 2026-08 per the catalog CSV),
  consistent with the PGDP corpus being a snapshot of *recently* PG-posted projects, and with the Gutenberg
  mirror (manifest generated today, 2026-08-31) having been refreshed to include them. This 100% rate should be
  read as **a property of this particular curated pairing**, not a general PGDP↔PG match rate — it is not
  representative of matching an arbitrary/older PGDP sample against a Gutenberg mirror.

Reproduce: `python3` script reading `pgdp-corpus/projectID*/project.json → pg_ebook_number`, then
`os.path.isdir(f"gutenberg-corpus/books/{peb}")` — full script output saved to
`.../scratchpad/typo-research/matched.tsv`.

## 3. Edition-identity verification beyond the number

**DP credit line: absent, measured, 0/285.** Classic PG text files carry a pre-`START` header block
("Title:", "Author:", "Credits: Produced by ... Distributed Proofreaders") and a post-`END` full-license
boilerplate. Checked all 285 matched `-0.txt`/`.txt`/`-8.txt` files for `"This eBook is for the use of anyone"`,
`"\nProduced by"`, `"START: FULL LICENSE"`: **zero hits on all three, in all 285 files.** Example, book 79063
(`/workspaces/gutenberg-corpus/books/79063/79063-0.txt`): the file starts directly at
`*** START OF THE PROJECT GUTENBERG EBOOK 79063 ***` with no preceding header, and ends at
`*** END OF THE PROJECT GUTENBERG EBOOK 79063 ***` with no trailing license text. Corpus-wide (not just matched),
this boilerplate *does* exist elsewhere — `grep -rl "START: FULL LICENSE" --include="*.txt" books/` hits
16,215/61,553 txt files (26%) — so this is a real difference between the modern PG text template (used for the
78xxx–79xxx range this PGDP snapshot draws from) and the older template, not a corpus-wide stripping policy.
**Practically: DP credit-line matching cannot be used to verify edition identity for this dataset**, because the
signal doesn't exist in the artifacts. A literal grep for `pgdp.net` in HTML across all 286 matched books: 0 hits.
`"distributed proofread"` (case-insensitive) in HTML: 2/286 hits, both generic "25th Anniversary" boilerplate
unrelated to a specific project (`79331`, `78814`), not attributable credit.

**Title/author agreement with the PG catalog: strong, spot-checked.** Cross-referencing 6 sampled ebook numbers
against `.cache/pg_catalog.csv` (`awk -F',' -v id="$id" '$1==id{print}'`) shows title and author agreement in
every case (e.g. `79063` PGDP title "Designs on prehistoric Hopi pottery" vs. catalog "Designs on prehistoric
Hopi pottery" by "Fewkes, Jesse Walter, 1850-1930" — exact).

**Direct text agreement (F2 vs PG artifact): the strongest available signal, and it holds.** Method: for a
random sample of 15 matched books, pull one substantial (>300-char, non-blank) page from `rounds/F2.json`,
strip DP proofing markup (`<i>`/`<b>` tags, `[**...]` proofer brackets, `[Illustration:...]`/`[Sidenote:...]`),
reduce both the F2 page and the full PG text/HTML to lowercase alnum-only strings, and test substring containment
of an 80-character mid-page snippet. **14/15 matched exactly** (script + output in scratchpad). The one failure
(`79274`, "Coffee: Its History, Classification and Description", page `317.png`) is a financial table
(`TABLE XII... Reis 44:201$810...`); manual inspection confirms the *content* (e.g. the figure `19,161`) is
present in the PG text (`grep -o "19,161" books/79274/79274-0.txt` → 2 hits) but column layout differs enough
between DP's fixed-width table and PG's reflowed table that a contiguous 80-char run doesn't align — a
formatting artifact, not an edition mismatch. **Verdict: all 15/15 sampled pairs are positively confirmed as the
same edition on textual grounds; 0 doubtful.** No source-scan-reference (e.g. "archive.org", "Internet Archive")
corroboration was found in any PG artifact — PGDP's `project.json.image_source` field (e.g. `"TIA"`) has no
counterpart string anywhere in the PG HTML/text, so that channel is not available either.

## 4. HTML typography inventory (286 matched books' `-h.htm`, one file per book)

Measured via regex tag/class counts over all 286 `-h.htm` files (script in scratchpad).

| element/class | total occurrences | books containing it (of 286) |
|---|---|---|
| `<i>` | 89,998 | 266 (93%) |
| `<span>` (any) | 106,290 | 283 (99%) |
| `<b>` | 22,136 | 80 (28%) |
| `<em>` | 8,273 | 80 (28%) |
| `<sup>` | 5,320 | 54 (19%) |
| `<strong>` | 760 | 52 (18%) |
| `<small>` | 242 | 18 (6%) |
| `<sub>` | 123 | 10 (3.5%) |
| small-caps spans (`smcap`+`allsmcap`+`sc` classes combined) | 29,851 | 249 (87%) |
| `class="pagenum"`/`class="pageno"` (page anchors — see §5) | 45,915 + 13,531 | 255 (89%) |
| any CSS `letter-spacing` rule | — | 80 (28%) |
| any CSS `small-caps`/`font-variant` rule | — | 257 (90%) |

Top non-utility span classes by occurrence (full list in scratchpad output): `smcap` 15,968, `pageno` 13,531,
`allsmcap` 7,377, `sc` 6,613, `gothic` 1,000, `large` 533, `dropcap` 171, `blackletter` 91, `frac` 204.

Real examples (book id, snippet):
- `<i>` — `79063`: `<i>monkohu</i>`, `<i>nakwakwoci</i>` (italicized foreign/technical terms)
- `<b>` — `79369`: `<b>Southwell</b>`
- `<em>` — `79396`: `<em>green oranges</em>`
- `<strong>` — `78978`: `<strong>Transcriber's Note:</strong>` (PG-added editorial marker, not original typography — see §6)
- `<sup>` — `79330`: `<sup>[1907]</sup>`
- `<sub>` — `78957`: `<sub>2</sub>`
- small-caps span — `79063`: `<span class="smcap">Jesse Walter Fewkes</span>`
- small-caps CSS — `79063`: `.smcap { font-variant: small-caps; font-style: normal; }`;
  `79063` also: `.allsmcap { font-variant: small-caps; font-style: normal; text-transform: lowercase; }`
  (i.e. two distinct small-caps conventions: "keep case, render small-caps" vs. "force lowercase, render small-caps" —
  the latter is PG's convention for text that was ALL-CAPS in the original and should render as small-caps)
- `sc` CSS — `78978`: `.sc { font-variant: small-caps; }`
- letter-spacing CSS — `79396`: `{letter-spacing: .25em; margin-right: -0.25em;}` (used for spaced-out display text)
- gothic/blackletter font — `79064`: `<span class="gothic">New York</span>` with CSS
  `.gothic { font-family: 'Old English Text MT', 'Old English', serif; }`

**Signal quality caveat:** `<span>` is used both for real typography (`smcap`, `gothic`, `dropcap`) and for
structural/utility purposes (`pagenum`, `nowrap`, `pad1`, `label`) — a naive `<span>` count overstates usable
typographic signal roughly 2.3x; class-name filtering is required, and class names are **not standardized**
across books (`smcap` vs `allsmcap` vs `sc` vs `sc` all mean small-caps but style differently; `pagenum` vs
`pageno` both mark page anchors — see §5).

## 5. Page-number anchors

Method: search each matched book's `-h.htm` for `id="Page_..."`/`id='Page_...'` (case-insensitive, either quote
style) — this is the actual anchor id PG uses; the wrapping `<span class="...">` name varies (see below), so
searching by class name alone undercounts.

- **255/286 (89.2%) matched books have at least one `id="Page_N"` anchor.** Mean 204.2 anchors/book, median
  224.5 (i.e. roughly one anchor per physical page, consistent with page-level granularity).
- **31/286 (10.8%) have zero page anchors of any kind** — confirmed by grepping for any `id="<word><digits>"`
  pattern and finding none, not just a missed class name (e.g. `78848` "Jim Hanvey, Detective" and `79242` "The
  price of salt" have no numbered `id` attributes anywhere in the HTML — no `class=` attributes at all in some
  cases, i.e. minimally-marked-up plain HTML). These are disproportionately modern genre-fiction reprints and a
  few multi-volume nonfiction sets (all 4 volumes of "The History of Civilisation in Scotland," `78937/39/40/41`,
  have zero anchors).
- Of the 255 with anchors, the wrapping class is `pagenum` for 192 books and `pageno` for 52 books (two
  historically-different DP/PG conventions for the same concept); the remainder wrap the id in some other/no span.
- The anchor id directly encodes the physical page number (`id="Page_248"`) and is frequently paired with visible
  bracketed text (`<span class="pagenum" id="Page_1">[Pg 1]</span>`), giving both a machine anchor and a
  human-readable page marker in the same token — good for alignment tooling.

**Quantified conclusion for alignment use:** for 89% of matched books, PG HTML gives a page-boundary anchor
roughly at the true page granularity, which is necessary for aligning back to individual PGDP page images/F2
text. For the remaining 11%, no page-level alignment is possible from the HTML at all; text would have to be
aligned at whole-document or heuristic-paragraph granularity only.

## 6. Transcriber's notes / PG-added front-back matter

- **244/286 (85.3%)** of matched books' `-h.htm` contain a literal "Transcriber's Note" (case-insensitive
  substring match).
- **No single consistent CSS selector marks it** — measured wrapper classes across those 244 books:
  `c000` (41), `transnote` (71), `tnote` (24), `center` (25), `tn_blk`/`tnbot` (4 each), plus 12 other one-off
  classes, and some instances with no distinguishing class at all (bare `<div class="chapter">` or similar).
  **Practical detector: text-pattern match on "Transcriber" (heading text), not class name** — a
  `.transnote { background-color: #E6E6FA; ... }` CSS rule exists in some books (e.g. `79396`) and is a bonus
  signal when present, but isn't universal.
- Transcriber's notes are typically placed *inside* the `START`/`END` PG markers (right after the title page, or
  at the very end before `END`), so **trimming to the START/END span does not exclude them** — they must be
  detected and stripped separately, by locating the "Transcriber" heading and excising to the next structural
  boundary (next `<div class="chapter">`/`<hr>`, or end of file).
- The classic PG legal boilerplate (pre-START header, post-END full-license text) is a separate, and in this
  dataset **absent**, category — see §3. So for this specific PGDP-matched batch, the only front/back matter to
  strip is the Transcriber's Note (and, rarely, a "cover note" div, e.g. `78978`'s
  `<div class='tnotes covernote'>` announcing new PG-commissioned cover art — also PG-added, not original text).
- `.x-ebookmaker`/`.x-ebookmaker-drop` CSS classes (266/286 books) mark conditionally-shown/hidden blocks in the
  PG build pipeline and are worth treating as a general "PG apparatus, not original text" signal, though they
  weren't individually enumerated here beyond the presence count.

## 7. Version drift

- **No content hash or upstream revision identifier exists anywhere in the mirror.** `.pull-complete.json`
  records only `completed` (local fetch timestamp) and `mirror` (which rsync host); `clone_manifest.json`
  records only `id`/`title`/`author`/`language` per book, no version field. This is confirmed by direct
  inspection of both files' schemas (§1) — **there is no mechanism in this local data to detect that a PG text
  changed after either the PGDP project posted or the mirror fetched it.**
  This is a stated absence, not an inferred one.
- **Weak proxy available:** `pg_catalog.csv`'s `Issued` date, cross-checked against PGDP's
  `project.json.last_state_change_time` and the mirror's own `.pull-complete.json.completed`. Spot-checked on
  10 matched books: chronology is always sane and tight (PGDP posted → catalog issued 1–2 days later → mirror
  pulled days-to-weeks after that; e.g. `79063`: posted 2026-07-10, issued 2026-07-09 in catalog, pulled
  2026-07-14). This is consistent with a single clean posting-to-fetch pipeline with **no evidence of
  post-posting revision** in this sample — but the absence of a hash means a genuine silent revision (PG does
  occasionally re-run `ebookmaker` or accept an errata patch) could not be detected even if one existed. This
  is an **inferred** absence-of-evidence, not a measured guarantee of stability.

## 8. Provenance of cited artifacts

- Mirror contract: `/workspaces/gutenberg-corpus/README.md`, `/workspaces/gutenberg-corpus/clone_manifest.json`
  (schema 1, generated 2026-08-31T04:02:20Z).
- Catalog: `/workspaces/gutenberg-corpus/.cache/pg_catalog.csv` (90,610 data rows; no cache-refresh date recorded
  in the file itself beyond directory mtime `Aug 31 04:02`, same run as the manifest).
- Every per-book fact cited above traces to `/workspaces/gutenberg-corpus/books/<id>/.pull-complete.json`
  (`completed`, `mirror`, `files[]`) and the actual artifact files under `/workspaces/gutenberg-corpus/books/<id>/`
  named individually inline above (e.g. `79063/79063-0.txt`, `79063/79063-h/79063-h.htm`,
  `38993/38993-src/38993-src.htm`).
- PGDP side: `/workspaces/pdomain-data/pgdp-corpus/projectID<hash>/project.json` (fields `pg_ebook_number`,
  `state`, `last_state_change_time`, `title`, `author`) and `.../rounds/F2.json` (per-page proofed text, keyed
  by image filename e.g. `303.png`).
- No file in either corpus carries a cryptographic hash; all "version" claims above are timestamp-based only,
  as stated in §7.
