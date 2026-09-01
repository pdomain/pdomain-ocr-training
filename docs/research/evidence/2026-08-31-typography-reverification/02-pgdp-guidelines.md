# PGDP formatting guidelines: what the F2 markup actually means

Research note for the fine-grained typography model. All external claims carry a source URL and a
retrieval date. Retrieval date for every source below is **2026-08-31** unless stated otherwise.

**Authoritative source.** The current official document is *Formatting Guidelines*, "Version 2.0a,
revised 3 October 2023", on the DP wiki:
<https://www.pgdp.net/wiki/DP_Official_Documentation:Formatting/Formatting_Guidelines> (retrieved
2026-08-31; raw wikitext fetched via `?action=raw`, which is what the quotations below come from).
The companion *Proofreading Guidelines* (version 2.0e, 14 October 2025) is at
<https://www.pgdp.net/wiki/DP_Official_Documentation:Proofreading/Proofreading_Guidelines>.

**Source tiers used here.**

- *Official*: the two Guidelines documents and pages in the `DP Official Documentation:` namespace.
- *Community wiki*: `Formatting Guidelines Explanation`, `Formatting`, `Gesperrt`, `Format Preview`,
  `Diffs That Don't Matter`. Useful, explicitly non-normative, occasionally quoting older wording.
- *Archived official*: Wayback captures of the pre-wiki guidelines at `pgdp.net/c/faq/document.php`.
- *Forum*: **not usable.** `www.pgdp.net/phpBB3/` returns "The board requires you to be registered
  and logged in to view this forum" for anonymous fetches (checked 2026-08-31 on `p=819261` and
  `p=177278`). Every forum thread the wiki cites is therefore uncited here.

Marking convention below: **[FIRM]** = stated as a rule in the official Guidelines.
**[CONVENTION]** = real but with documented or structural variation. **[SILENT]** = the Guidelines
do not say.

---

## 1. Italics and underlining

**[FIRM]** "Format *italicized* text with `<i>` inserted at the start and `</i>` inserted at the end
of the italics." — Formatting Guidelines, *Italics*
(<https://www.pgdp.net/wiki/DP_Official_Documentation:Formatting/Formatting_Guidelines#italics>).

**[FIRM]** Underlining in the scan maps to `<i>`, not to a separate tag: "Format underlined text as
Italics, with `<i>` and `</i>`. … Underlining was often used to indicate emphasis when the
typesetter was unable to actually italicize the text, for example in a typewritten document." —
*Underlined Text*, same page (`#underl`).

**[CONVENTION] Exception, project-level:** "Some Project Managers may specify in the Project
Comments that underlined text be marked up with the `<u>` and `</u>` tags." — same section. The
Format Preview tool has an explicit opt-in for this: "Allow `<u>` for underline … This should only
be used where it is requested in the Project Comments. (The guidelines say that underlined text
should normally be marked as italic)." — <https://www.pgdp.net/wiki/Format_Preview>.

**Consequence for labels:** `<i>` is a *two-source* label — true italic glyphs and underlined
upright glyphs both land in it. A vision model trained on `<i>` sees a mixed class unless the corpus
is filtered. There is no way to tell the two apart from the text alone; `<u>` appears only in the
minority of projects whose PM asked for it.

**[FIRM] Exception, numerals:** "Many typefaces found in older books used the same design for
numbers in both regular text and italics or bold. For dates and similar phrases, format the entire
phrase with one set of markup, rather than marking the words as italics (or bold) and not the
numbers." — *Placement of Inline Formatting Markup* (`#inline`). Worked example given there:
image `Enacted 4 July, 1776` (with "Enacted" and "July" italic, digits upright) → `<i>Enacted 4
July, 1776</i>`. **So `<i>` spans deliberately include upright-looking digits.** This is a
guideline-mandated label/pixel mismatch, not proofreader error.

**[FIRM] Exception, lists:** "If there is a series/list of words or phrases (such as names, titles,
etc.), mark each item of the list individually." — same section. So a run of italics broken by
upright commas becomes several `<i>` spans, and the comma between them is outside.

---

## 2. Bold

**[FIRM]** "Format **bold text** (text printed in a heavier typeface) with `<b>` inserted before the
bold text and `</b>` after it." — *Bold Text* (`#bold`). The trigger is a heavier typeface, nothing
else.

**[FIRM] Large exception — headings are never bolded:** "While chapter headings may appear to be
bold or spaced out, these are usually the result of font or font size changes and **should not be
marked**. The extra blank lines separate the heading, so do not mark the font change as well." —
*Chapter Headings* (`#chap_head`). The identical sentence appears under *Section Headings*
(`#sect_head`). Enforced by tooling: Format Preview lists "Heading should not be entirely bold" as a
**definite issue** (<https://www.pgdp.net/wiki/Format_Preview>).

**Consequence for labels:** heading text that is visually bold in the scan is systematically
labelled *not bold*. Any bold-detection model trained on F2 text must exclude heading regions or it
learns a contradiction. This is the single largest deliberate false-negative source for `<b>`.

*Rationale (community wiki, non-normative):* "We don't mark bold in headings because there is
already a different markup that sets it apart: 4 blank lines before and 2 after. In fact, usually
it's actually just a difference in the font or font size (which we don't mark), not actually bold."
— <https://www.pgdp.net/wiki/Formatting_Guidelines_Explanation>.

---

## 3. Small capitals and mixed capitals

**[FIRM] The rule has two branches:** "Format words that are printed in Mixed Small Caps as Mixed
Upper and Lowercase. Format words that are printed in all small caps as ALL-CAPS. For both mixed
case and all small caps, surround the text with `<sc>` and `</sc>` markup." — *Words in Small
Capitals* (`#small_caps`). Official examples on that page:

| printed | formatted |
|---|---|
| `This is Small Caps` (mixed small caps) | `<sc>This is Small Caps</sc>` |
| `aardvarks` (all small caps) | `You cannot be serious about <sc>AARDVARKS</sc>!` |

**How original case is (and is not) recorded.** The `<sc>` span's *internal case pattern* is the
only record of the printed case, and it is lossy in one direction:

- Mixed small caps: the capitalisation pattern of the printed line survives (`This is Small Caps`).
  The information that the lowercase-shaped letters were *small capitals* rather than lowercase is
  carried by the tag, not by the letters.
- All small caps: **the printed letterforms were lowercase-height, and the text records them as
  uppercase.** `<sc>AARDVARKS</sc>` and a genuinely all-cap `AARDVARKS` differ only by the tag.
- Therefore an all-small-caps span cannot be distinguished, from the text alone, from a full-caps
  span that a formatter tagged; and the per-letter printed case of an all-small-caps span is
  destroyed by the guideline itself, before any post-processing.

**[FIRM] Lowercase inside `<sc>` is invalid.** The DP post-processing guide calls the older form
out: "You may also see the old-DP-style `<sc>a.d.</sc>` — this is plain wrong according to the
formatting guidelines. Uppercase these before going any further." —
<https://www.pgdp.net/wiki/DP_Official_Documentation:PP_and_PPV/Guide_to_smallcaps>. Format Preview
flags "Small caps must contain at least one upper case character" as a **definite issue**
(<https://www.pgdp.net/wiki/Format_Preview>). So all-lowercase `<sc>` spans in a corpus are either
pre-2005 residue or unfixed errors.

**[FIRM] Headings are excluded again:** "Headings (Chapter Headings, Section Headings, Captions,
etc.) may appear to be in all small caps, but this is usually the result of a change in font size
and should not be marked as small caps. The first word of a chapter that is in small caps should be
changed to mixed case without the tags." — `#small_caps`. And: "Mark any italics or **mixed case**
small caps that appear in the image" in *Chapter Headings* / *Section Headings* — i.e. in headings,
mixed-case small caps **are** tagged but all-small-caps are **not**. The community explanation adds
the operative test: "In headings, small caps are only marked up if there is a change in size within
a single line." — <https://www.pgdp.net/wiki/Formatting_Guidelines_Explanation>.

**[FIRM] All caps, no tag:** "Format words that are printed in all capital letters as all capital
letters" — *Words in All Capitals* (`#word_caps`) — with the exception that a chapter's first word
printed in all caps "should be changed to upper and lower case, so 'ONCE upon a time,' becomes
'Once upon a time,'". So the first word of a chapter is *deliberately* re-cased away from the image.

**Upstream case is noise, not signal.** Proofreaders are told: "Please proofread only the characters
in Small Caps … **Do not worry about case changes.** If the OCR'd text is already ALL-CAPPED,
Mixed-Cased, or lower-cased, leave it ALL-CAPPED, Mixed-Cased, or lower-cased." — Proofreading
Guidelines, *Words in Small Capitals*
(<https://www.pgdp.net/wiki/DP_Official_Documentation:Proofreading/Proofreading_Guidelines#small_caps>).
The case seen by F1 is therefore whatever the OCR produced; the formatter's job is to *overwrite* it
per the rule above. Case inside `<sc>` is a formatter classification decision, not an observation.

---

## 4. Letter spacing / gesperrt

**[FIRM]** "Format s p a c e d o u t text with `<g>` inserted before the text and `</g>` after it.
… **Remove the extra spaces between letters in each word.** This was a typesetting technique used
for emphasis in some older books, especially in German." — *Spaced Out Text (gesperrt)* (`#spaced`).

So the spacing characters are **deleted**; the tag is the only trace. Worked example from
*Placement of Inline Formatting Markup*: image `for Erlebnis Geschichte Deutschland seit 1845.`
(letter-spaced) → `for <g>Erlebnis Geschichte Deutschland seit 1845</g>.` — note the final period
falls outside.

**[FIRM] Headings excluded:** the Chapter/Section Heading sections say headings that "appear to be
bold or spaced out … should not be marked".

Definition, community wiki: "*Gesperrt* is the term used to refer to s p a c e d o u t text. This
was a typesetting technique used to emphasize a piece of text in older German (and some Italian and
other languages) books." — <https://www.pgdp.net/wiki/Gesperrt>.

**[SILENT]** The Guidelines give no threshold distinguishing gesperrt from ordinary loose word
spacing or from a wide-tracked title line, and no instruction on inter-word gaps *inside* a gesperrt
run beyond "remove the extra spaces between letters in each word". Judgment call.

---

## 5. Font changes — `<f>`

**[FIRM, but conditional]** "**Some Project Managers may request** that you mark a change of font
within a paragraph or line of normal text by inserting `<f>` before the change in font and `</f>`
after it. This markup may be used to identify a special font or other formatting that does not
already have its own markup (such as italics and bold)." — *Font Changes* (`#font_ch`).

Listed possible uses, verbatim from that section:

- antiqua (a variant of roman font) inside fraktur
- blackletter ("gothic" or "Old English" font) within a section of regular font
- smaller or larger font only if it is **within** a paragraph in regular font (a whole paragraph in
  a different font or size goes to block-quote markup instead)
- upright font inside of a paragraph of italicized text

"The particular use or uses of this markup in a project will usually be spelled out in the Project
Comments. Formatters should post in the Project Discussion if the markup appears to be needed and
has not yet been requested." — same section.

The jargon page states the residual definition: `<f>` is "Used to indicate a change of font within a
paragraph or line of normal text. Use this markup to identify any special font or other formatting,
except bold, italic, small capped, and spaced out text, which have their own tags." —
<https://www.pgdp.net/wiki/Formatting>.

**Why `<f>` is ambiguous for a consumer.** It is a *project-defined* label with no global semantics:
in one project it means "antiqua inside fraktur", in another "blackletter inside roman" (the exact
opposite pixel pattern), in another "upright inside italic", in another "size change inside a
paragraph". Two of the listed uses are mutually inverse. Nothing in the page text records which
meaning applies; only the free-text Project Comments do. `<f>` should be treated as an unlabelled
"something else changed here" marker unless the project's Project Comments have been read.

Related term: "*Antiqua* generally refers to a non-Fraktur font used in a work printed predominantly
in Fraktur. This is seen mostly in older German texts on the characters in proper names or
non-German words." — <https://www.pgdp.net/wiki/Antiqua>.

---

## 6. Superscript and subscript

**[FIRM] Superscript:** "Format these by inserting a single caret (`^`) followed by the
superscripted text. If the superscript continues for more than one character, then surround the text
with curly braces `{` and `}` as well." Official example: image `Gen^rl Washington defeated L^d
Cornwallis's army.` → `Gen^{rl} Washington defeated L^d Cornwallis's army.` — *Superscripts*
(`#supers`). So: one character → `^d`; two or more → `^{rl}`.

**[FIRM] Subscript:** "Format subscripted text by inserting an underline character `_` and
surrounding the text with curly braces `{` and `}`." Example: `H_{2}O.` — *Subscripts* (`#subscr`).
Braces are shown for the single-character case, i.e. subscripts are **always** braced.

**[CONVENTION] Two documented deviations:**

- "The Project Manager may specify in the Project Comments that superscripted text be marked
  differently." — `#supers`.
- The jargon page carries an older scientific-works rule that is *not* in the current Guidelines:
  "`^` … Used to mark superscripts. In scientific & technical works, format superscripted characters
  with curly braces `{` and `}` surrounding them, even if there is only one character
  superscripted." — <https://www.pgdp.net/wiki/Formatting>. This was the official rule until 2009
  (see §12), so both `^d` and `^{d}` occur in the corpus and neither is wrong for its era.

**Round ownership note.** Superscripts and subscripts are now the **proofreaders'** job — the same
text appears verbatim in the Proofreading Guidelines (`#supers`, `#subscr`), and the Formatting
Guidelines wikitext still carries the HTML comment `<!-- Remove this section after some transition,
since it's now all handled in proofreading -->` above both sections (visible in the raw wikitext of
the Formatting Guidelines page, retrieved 2026-08-31). So these two markers reflect P-round work,
not F-round work, and their quality does not track the F1→F2 improvement.

---

## 7. Tag boundaries and punctuation

**[FIRM as stated, [CONVENTION] in practice]** "Place punctuation **outside** the tags unless the
markup is around an entire sentence or paragraph, or the punctuation is itself part of the phrase,
title, or abbreviation that you are marking." — *Placement of Inline Formatting Markup* (`#inline`).
This is stated for `<i>`, `<b>`, `<sc>`, `<f>` and `<g>` together — the section opens by naming all
five.

Official worked examples (`#inline`), all retrieved 2026-08-31:

| image | correct text | what it shows |
|---|---|---|
| *Studies*, and | `these <i>Studies</i>, and` | comma outside |
| (*Psychological Review*, 1898, p. 160) | `(<i>Psychological Review</i>, 1898, p. 160)` | comma outside, parens outside |
| *Phil. Trans.* | `<i>Phil. Trans.</i>` | abbreviation periods inside |
| It cost 9*l.* 4*s.* 1*d.* | `9<i>l.</i> 4<i>s.</i> 1<i>d.</i>` | abbreviation period inside |
| **God knows what she saw in me!** I spoke | `<b>God knows what she saw in me!</b> I spoke` | full sentence, `!` inside |
| "*That's the idea!*" exclaimed | `"<i>That's the idea!</i>" exclaimed` | quotes outside, `!` inside |
| art. "Ticklishness," (small caps) | `art. "<sc>Ticklishness</sc>,"` | comma outside the sc tag |
| gesperrt run ending a sentence | `<g>… seit 1845</g>.` | period outside |

**How consistent is it?** The rule requires a semantic judgment ("is this punctuation part of the
phrase?"), and the tooling treats violations as *soft*. Format Preview classes "Punctuation after
start tag", "Character or punctuation before inline start tag" (user-suppressible), "Character after
inline end tag" and "comma, semicolon or colon before end tag" as **possible issues**, not definite
issues — <https://www.pgdp.net/wiki/Format_Preview>. Only structural faults (unmatched, nested,
empty, space/newline adjacent to a tag) are definite issues. Expect real corpus variation of a
character or two at span edges, concentrated on `.` `,` `!` `?` `"` and closing parens.

**[FIRM] Whitespace never sits inside a tag boundary:** "Space after start tag", "Newline after
start tag", "Newline before end tag", "Space before end tag" are all definite issues (Format
Preview). Spans are tight against non-space characters.

**[FIRM] Tables:** "If inline formatting (italics, bold, etc.) is needed in the table, mark up each
table cell separately." — *Tables* (`#tables`). Also, in the plain-text conversion "`<i>`italics
markup`</i>` normally becomes `_`underscores`_` … On the other hand, `<sc>`Small Caps Markup`</sc>`
is removed completely" — same section, which is why span edges matter to DP at all.

*Rationale (community wiki):* "we also produce text versions of all our projects, and for those,
italics is marked with _underscores_. The placement of the markup during formatting determines where
the underscores appear in the final version." —
<https://www.pgdp.net/wiki/Formatting_Guidelines_Explanation>.

---

## 8. Tags spanning paragraphs and pages

**[FIRM] Page-local closure.** "Since each project is distributed among many formatters, each of
whom is working on different pages, there is no guarantee that you will see the next page of the
project. With this in mind, **be sure to open and close all markup tags on each page.**" —
*Each Page is a Separate Unit* (`#separate_pg`).

**[FIRM] Paragraph-local closure.** "If the formatting goes on for multiple paragraphs, put the
markup around each paragraph." — `#inline`. Enforced: Format Preview lists "No corresponding end tag
in paragraph" as a definite issue. A tag may, however, cross a *line* break inside a paragraph —
only a newline immediately after the start tag or before the end tag is an error.

**[SILENT] Reopening.** The current Guidelines never say in so many words "reopen the tag at the top
of the next page"; that is the necessary consequence of page-local closure plus "the proofreaders
matched the image's content, and now as a formatter you match the image's look" (`#prime`). There is
**no continuation marker for inline tags** in the current rules. Contrast the out-of-line and
footnote machinery, which does have explicit continuation syntax: continued footnotes use
`*[Footnote: *tinued onto the next page.]` and continued sidenotes `*[Sidenote: …]` (`#footnotes`,
`#para_side`), and out-of-line `/* */` `/# #/` must also be closed on the page where opened
(`#outofline`).

**Historically there *was* an inline continuation marker** (see §12): the 2003 guidelines told
proofreaders to "place a `*` in front of the `<i>`" when italics started at the top of a page and "a
`*` after the `</i>`" when they ran to the bottom. A parser meeting `*<i>` or `</i>*` in old text is
seeing that convention, not a typo.

**Consequence for labels:** a single printed italic passage crossing a page break yields two
independent spans in two independently-formatted pages. Cross-page ground truth must be stitched,
and the stitch is unmarked. Page-final and page-initial spans are also where formatter disagreement
concentrates, because neither formatter saw the other page.

---

## 9. F1 versus F2

**[FIRM, official]** "After all of the pages of a project are completed in F1, the project moves
into F2 for **review and any needed corrections**. F2 is the final round of formatting before
Post-Processing." —
<https://www.pgdp.net/wiki/DP_Official_Documentation:Formatting/Welcome_Email_to_new_F1s>.

Definitions: "**F1** refers to Formatting round 1, the first round of formatting, in which markup
for *italics*, **boldface**, SMALL CAPITALS, chapter and section headers, footnotes, etc., is added
to individual pages" (<https://www.pgdp.net/wiki/F1>); "**F2** refers to Formatting round 2, the
second round of formatting, in which **F1 markup is checked and corrected**"
(<https://www.pgdp.net/wiki/F2>).

**Access bar, F1 vs F2** (official, retrieved 2026-08-31):

- F1: 300 P1 pages, pass the formatting quiz (results expire after six months), 21 days since
  registration —
  <https://www.pgdp.net/wiki/DP_Official_Documentation:Formatting/Access_Requirements_--_F1>.
- F2: "volunteers may apply to work in F2 after they have completed 400 F1 pages, provided it is at
  least 91 days since registration and 60 days since their most recent F2 application, there is a
  great deal more required in terms of formatting skill and experience." Access is granted by
  evaluation, and "DP may remove that access if a volunteer has not worked in that area for an
  extended period." —
  <https://www.pgdp.net/wiki/DP_Official_Documentation:Formatting/Access_Requirements_--_F2>.

**What this implies about label quality.** F2 text is F1 text plus a second, more experienced pass
whose entire job is the markup — so F2 is strictly the better label source, and F1→F2 diffs are a
ready-made noise estimate (DP itself points volunteers at a Review Work tool comparing F1 to F2
pages: `review_work.php?work_round_id=F1&review_round_id=F2`, cited in the F1 welcome email above).
Three caveats:

1. **F2 is not universal.** "Since June 2005, each project goes through a *minimum* of two proofing
   rounds and **one** formatting round." — <https://www.pgdp.net/wiki/Round>. Some projects skip F2;
   for those, "F2 text" does not exist and the final pre-PP text is F1 output.
2. **F2 is still one pass by one human**, and it is the last formatting checkpoint — nothing
   downstream re-verifies markup except post-processing, which is a different job.
3. **Some inline markers are not F-round work at all.** Superscripts and subscripts are proofreading
   responsibilities (§6), so their quality is set in P1–P3 and F2 review does not target them.
4. **Not every F1→F2 diff is an error.** DP maintains an explicit list of "Diffs That Don't Matter"
   — for the formatting round it covers blank-line placement around poetry, illustration markup and
   "THE END", i.e. layout preferences, *not* inline markup —
   <https://www.pgdp.net/wiki/Diffs_That_Don't_Matter>. Inline-markup diffs are therefore mostly
   real corrections.

---

## 10. Project Comments and project-specific overrides

**[FIRM] Overrides are total and free-text.** "On this page there is a section called 'Project
Comments' containing information specific to that project (book). **Read these before you start
formatting pages!** If the Project Manager wants you to format something in this book differently
from the way specified in these Guidelines, that will be noted here. **Instructions in the Project
Comments *override* the rules in these Guidelines**, so follow them." — Formatting Guidelines,
*Project Comments* (`#comments`). Restated in the jargon page: "instructions in the Project Comments
*override* the rules contained in the Guidelines" — <https://www.pgdp.net/wiki/Project_Comments>.

**A second, weaker override channel:** the project's forum thread. "The Project Manager may clarify
project-specific guidelines here" — `#comments`. That thread is login-gated (verified 2026-08-31),
so it is invisible to an anonymous consumer *and* its clarifications never appear in the Project
Comments text.

**Overrides the Guidelines themselves anticipate** (each cited above): `<u>` instead of `<i>` for
underlining (`#underl`); `<f>` used at all, and with a project-specific meaning (`#font_ch`);
alternative superscript markup (`#supers`); special handling of page references (`#page_ref`); table
layout conventions settled in the thread (`#tables`); music handling (`#music`); section-heading
blank-line counts "unless the Project Manager has requested otherwise" (`#sect_head`).

**How a consumer detects an override: badly.** There is no structured or machine-readable override
field — Project Comments are free prose on the project page, and the Guidelines describe them only
as "a section … containing information specific to that project". Practical detection signals:

- Presence of `<u>` anywhere in a project ⇒ the PM requested `<u>`, so `<i>` in that project means
  italics only.
- Presence of `<f>` ⇒ the PM defined it; its meaning must be read out of the Project Comments prose.
- `^{d}` single-character braced superscripts ⇒ scientific/technical convention or a pre-2009
  project.
- `{FFT}` in the project title marks a Formatting Fast Track project (released to F2 immediately
  after F1, used for F2 qualification) — <https://www.pgdp.net/wiki/Formatting_Fast_Track>. Not an
  override, but a signal that the F2 pass was done by candidates under evaluation.

Recommendation: treat Project Comments as a required per-project input, and treat any project whose
comments cannot be retrieved as unlabelled for `<f>` and `<u>`.

---

## 11. Cases the Guidelines say to leave alone, flag, or escalate

**Leave alone / do not mark [FIRM]:**

- Font size changes: "Normally we do not do anything to mark changes in font size", except when they
  signal a block quotation or when the size changes within a single paragraph or line (`#font_sz`).
- Bold and spacing in chapter and section headings (`#chap_head`, `#sect_head`).
- All-small-caps appearance in headings (`#small_caps`).
- Printer's errors and archaic spellings: "do not correct what may appear to you to be misspellings
  or printer errors that occur on the page image. Many of the older texts have words spelled
  differently from modern usage and we retain these older spellings" (`#p_errors`).
- Factual errors: "Do not correct factual errors in the author's book" (`#f_errors`).
- The Primary Rule generally: "Don't change what the author wrote!" (`#prime`).
- Previous volunteers' notes: "Any notes or comments put in by a previous volunteer **must** be left
  in place … even if you know the answer, you absolutely must not remove the comment" (`#prev_notes`).

**Flag in the text [FIRM]:** anything uncertain gets an in-text note "Start your note with a square
bracket and two asterisks `[**` and end it with another square bracket `]` … This clearly separates
it from the author's text and signals the post-processor to stop and carefully examine this part of
the text" (`#anything`). Printer's errors get `[**typo for error?]`, and a made change gets
`[**typo "erorr" fixed]` (`#p_errors`). **These bracketed notes are inserted text that is not in the
image** — a consumer must strip `[**…]` before aligning text to pixels. Format Preview confirms
"Tags inside proofreader's notes are ignored" (<https://www.pgdp.net/wiki/Format_Preview>).

**Escalate to humans [FIRM]:** post in the Project Discussion for anything not covered
(`#anything`), for a bad or illegible image (`#bad_image`), for the wrong image attached to the text
(`#bad_text`), when unsure whether a heading is a chapter or a section (`#sect_head`), and when `<f>`
appears needed but has not been requested (`#font_ch`). There is no "reject the page" instruction in
the Guidelines — the escalation path is a forum post plus a `[**` note, and the page is still saved.

**[SILENT]** Nothing in the Guidelines tells a formatter to leave a page unformatted, and nothing
defines a quality floor below which a page is withheld. So an unreadable scan still produces an F2
page with markup on it.

---

## 12. Historical changes — the label-noise and leakage risk

The DP guidelines have changed materially over ~23 years, and **a project carries the conventions of
the era in which its rounds ran, not the era in which it was posted.** Source for the dated table
below unless otherwise noted: *Proofreading and Formatting Guidelines Revision History*,
<https://www.pgdp.net/wiki/DP_Official_Documentation:Proofreading/Proofreading_and_Formatting_Guidelines_Revision_History>
(retrieved 2026-08-31).

| date | version | change (verbatim or close) | why it matters |
|---|---|---|---|
| 2003-01-13 | 1.3 | Sections added incl. Superscripts, Font Size changes, Word in all Caps | first structured markup era |
| 2003-02-20 | 1.4 | "Underlined Text: added this section to the Guidelines"; "Italics: added note & example for numerals in italics" | before this, no underline rule at all |
| 2003-06-19 | 1.5 | "Bold text: default is now html-style markup instead of all-caps" | **pre-2003 bold is ALL CAPS text, not `<b>`** |
| 2004-09-01 | 1.7 | "We now mark-up all italics, including scholarly abbreviations"; "We now mark superscripts with `^`"; "A section has been added for subscripts - they are marked with `_{}`" | **pre-2004 superscripts use an apostrophe, `Gen'rl`** (confirmed below); pre-2004 italics on scholarly abbreviations were *not* marked |
| 2005-06-01 | 1.8 | "Guidelines split into separate Proofreading and Formatting documents" | start of the P/F split |
| 2005-06 | — | "The Change": DP moved "from two rounds (R1 & R2 …), which each involved both proofing and formatting, to four rounds, two for proofing and two for formatting" — <https://www.pgdp.net/wiki/The_Change> | **pre-June-2005 projects have no F1/F2 at all** |
| 2005-11-01 | 1.9 | "**Small caps are now completely handled by the Formatters**"; "The five-star thought break is now indicated by `<tb>`"; "Proofreader notes are now to be indicated by `[**Note]`" | **pre-Nov-2005 `<sc>` usage is inconsistent or absent**; older note syntax differs |
| 2006-06 | — | optional third proofing round added — <https://www.pgdp.net/wiki/The_Change> | P3 exists only after this |
| 2007-03-10 | 1.9d | "**Change spaced text markup to `<g>`.** Add new section for font changes, to be marked with `<f>`." | **pre-March-2007 gesperrt was tagged `<i>`, and `<f>` did not exist** (confirmed below) |
| 2009-06-07 | 2.0 | "Braces for superscripts and subscripts are now handled in proofreading not formatting"; "**For superscripts, use braces any time more than one character is superscripted**"; "Removed `[/x]` and `[\x]`"; "New sections about the placement of inline and out-of-line markup"; "Use the `/# #/` markup for a block of text that's printed differently … regardless of whether it's quoted material"; "Mark right-aligned text with `/* */`" | **the modern `^{rl}` rule starts here**; the current inline-punctuation section dates from here |
| 2019-11-08 | 2.0a | character-picker wording | cosmetic |
| 2020-06-15 | 2.0b | "Updated Proofreading Guidelines to reflect our move to Unicode" | **pre-2020 projects are Latin-1 era**; non-ASCII handling differs |
| 2023-10-03 | 2.0a (F) / 2.0c (P) | Music Guidelines added | narrow |
| 2025-03-08 / 2025-10-14 | 2.0d / 2.0e | diacritical marks; transliteration | proofreading only |

**Archive confirmations** (Wayback captures of the then-official `pgdp.net/c/faq/document.php`,
retrieved 2026-08-31):

- **2003 (v1.53, "released Sep 13, 2003"),**
  <https://web.archive.org/web/20040209025447/http://www.pgdp.net/c/faq/document.php>:
  - Superscripts: "insert a single quote (apostrophe) to identify this as an
    abbreviation/contraction, like this: `Gen'rl Washington defeated L'd Cornwall's army.`"
  - Inline page-continuation markers, since removed: "If the italics start at the top of a page,
    place a `*` in front of the `<i>` … If the italics go to the bottom of a page, place a `*` after
    the `</i>`."
  - Case-insensitive tags allowed: "either lower-case `<i>` or upper-case `<I>` is OK, whichever you
    prefer" (same for `<b>`/`<B>`). **A tag parser must be case-insensitive for old projects.**
  - Bold: "Previously, we used to change bold text into all capitals. We no longer do it that way,
    unless the Project Manager specifies that method in the Project Comments."
  - Small caps: "If a word or words in the text are printed in all capital letters (**including small
    caps**), leave it that way" — i.e. **no `<sc>` tag at all**.
- **2004 (v1.7, "generated August 31, 2004"),**
  <https://web.archive.org/web/20050320022038/http://www.pgdp.net/c/faq/document.php>: still one
  combined document; small caps still untagged; superscripts now `^`, with braces only "in
  scientific & technical works … even if there is only one character superscripted".
- **2006 (v1.9.c, "generated January 1, 2006"),**
  <https://web.archive.org/web/20060605142428/http://www.pgdp.net/c/faq/document.php>:
  - Gesperrt: "**Format s p a c e d o u t text as Italics, with `<i>` and `</i>`**, and remove the
    extra spaces between letters in each word. … Italics serve that purpose for modern readers."
    This is the single most damaging historical change for a typography model: **for projects
    formatted before March 2007, `<i>` silently contains gesperrt runs.**
  - `<sc>` now in use with the modern two-branch mixed/all rule.
  - Bold: "Some Project Managers may specify in the Project Comments that bold text be rendered as
    all caps" — a permitted override that has since disappeared from the Guidelines.
  - Superscripts: still the pre-2009 rule (`Gen^rl`, unbraced multi-character outside scientific
    works).
  - Font size: "The exception to this is when the font size changes to indicate a block quotation" —
    no `<f>`.

**Leakage angle.** Era is inferable from the text itself (`Gen'rl` vs `Gen^rl` vs `Gen^{rl}`;
presence of `<sc>`; `<I>`/`<B>`; `*<i>`; `<g>`/`<f>`), and era correlates with book language,
subject and scan source. A model or an evaluation split that mixes eras will both learn era artefacts
and leak project identity across the split. Split by project, and record each project's era.

---

## Open questions the Guidelines do not answer

- **[SILENT]** No visual threshold is given for any tag: how heavy is "a heavier typeface", how wide
  is gesperrt, how small is a small capital versus a size change. Every inline label is a human
  judgment against an unstated threshold.
- **[SILENT]** No rule covers italic *punctuation* glyphs as such — only whether punctuation falls
  inside a span, which is decided semantically rather than by how the mark was printed.
- **[SILENT]** No guidance on tag *nesting* semantics (Format Preview forbids a tag nested within
  the same tag, but the Guidelines say nothing about, e.g., `<i>` inside `<sc>`).
- **Contradiction, minor:** `Formatting Guidelines Explanation` quotes older heading wording
  ("Chapter Headers are usually printed in a larger font which may appear to be bold") that no
  longer matches the current text of the Guidelines. It is a community page and explicitly "not the
  guidelines".
- **Unverifiable here:** every forum thread the wiki cites for historical rationale (the F2
  self-evaluation checklist, the "New Rounds, New Workflow" threads, the Gallery of Table Layouts) is
  behind a login wall. Any claim from those threads would need an authenticated retrieval.

---

## Markup inventory (quick reference)

Consolidated from the Formatting Guidelines character-level sections and the tag list at
<https://www.pgdp.net/wiki/Formatting> (both retrieved 2026-08-31).

| markup | meaning | trigger | notes |
|---|---|---|---|
| `<i>…</i>` | italics | italic type **or** underlining | numerals inside a date phrase included; list items tagged separately |
| `<b>…</b>` | bold | heavier typeface | **never in chapter/section headings** |
| `<sc>…</sc>` | small capitals | small-cap glyphs | mixed → keep Mixed Case; all-small → UPPERCASE; not in all-cap headings; must contain ≥1 uppercase |
| `<g>…</g>` | gesperrt | letter-spaced emphasis | inter-letter spaces deleted; not in headings; `<i>` before 2007-03 |
| `<f>…</f>` | font change | project-defined | only when the PM asks; meaning varies per project |
| `<u>…</u>` | underline | underlining | only when the PM asks; otherwise `<i>` |
| `^x`, `^{xx}` | superscript | raised type | brace when >1 char (since 2009); apostrophe form before 2004 |
| `_{x}` | subscript | lowered type | always braced |
| `<tb>` | thought break | decorated break between paragraphs | since 2005-11 |
| `[**…]` | volunteer note | uncertainty, typo query | inserted text, not in the image |
| `/* */`, `/# #/` | no-wrap / rewrapped block | tables, poetry, lists / block quotes | out-of-line; page-local |
| `[Illustration: …]`, `[Footnote N: …]`, `[Sidenote: …]`, `[Blank Page]` | structural | — | continuation forms use a leading `*` |
