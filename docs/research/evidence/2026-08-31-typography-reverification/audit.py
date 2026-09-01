#!/usr/bin/env python3
"""Read-only audit of the local PGDP corpus for inline-style-span supervision.

Corpus root: /workspaces/pdomain-data/pgdp-corpus
Produces a single JSON report with counts, distributions, and examples for
every phenomenon described in the audit brief. Read-only: never writes into
the corpus itself.

Usage:
    uv run --project /workspaces/pdomain/pdomain-ocr-synth python audit.py \
        > report.json
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

CORPUS = Path("/workspaces/pdomain-data/pgdp-corpus")

STYLE_TAGS = ["i", "b", "sc", "g", "f"]  # inline paired tags carrying style

TAG_RE = re.compile(r"<(/?)([a-zA-Z][a-zA-Z0-9]*)((?:\s[^>]*)?)>")

SUP_BRACE_RE = re.compile(r"\^\{([^{}]*)\}")
SUP_CHAR_RE = re.compile(r"\^(?!\{)([A-Za-z0-9])")
SUB_BRACE_RE = re.compile(r"_\{([^{}]*)\}")
SUB_CHAR_RE = re.compile(r"(?<![A-Za-z0-9_])_(?!\{)([A-Za-z0-9])(?![A-Za-z0-9_])")

# word token: unicode letters, joined by internal apostrophe/hyphen
WORD_RE = re.compile(r"[^\W\d_]+(?:['’\-][^\W\d_]+)*", re.UNICODE)

# recognized editorial-label prefixes inside bracket notes that carry real
# page content after the colon (footnote body text, illustration captions,
# sidenote text) -- the label itself is PGDP metadata, not page text.
LABEL_RE = re.compile(r"^(Footnote[^:]*|Illustration|Sidenote|Decoration|Handwritten)\s*:\s*")


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception as e:  # noqa: BLE001
        return {"__error__": str(e)}


def list_projects():
    return sorted(p for p in CORPUS.iterdir() if p.is_dir() and p.name.startswith("projectID"))


def counter_top(c: Counter, n=None):
    return dict(c.most_common(n))


# --------------------------------------------------------------------------
# 1. Structure
# --------------------------------------------------------------------------

def audit_structure(projects):
    out = {
        "num_projects": len(projects),
        "field_presence": Counter(),
        "field_examples": {},
        "pg_ebook_number_present": 0,
        "pages_total_sum": 0,
        "pages_json_keys_sum": 0,
        "f2_json_keys_sum": 0,
        "p3_json_keys_sum": 0,
        "projects_missing_project_json": [],
        "projects_missing_pages_json": [],
        "projects_missing_rounds_dir": [],
        "projects_missing_f2": [],
        "projects_missing_p3": [],
        "projects_missing_images_dir": [],
        "top_level_png_count_sum": 0,
        "images_subdir_file_count_sum": 0,
        "image_filename_patterns": Counter(),
        "f2_key_image_mismatches": [],
        "languages": Counter(),
        "genres": Counter(),
        "difficulties": Counter(),
        "states": Counter(),
        "image_sources": Counter(),
        "character_suites": Counter(),
    }

    for p in projects:
        pj = p / "project.json"
        pg = p / "pages.json"
        rd = p / "rounds"
        f2 = rd / "F2.json"
        p3 = rd / "P3.json"
        imgd = p / "images"

        if not pj.exists():
            out["projects_missing_project_json"].append(p.name)
        else:
            d = load_json(pj)
            if isinstance(d, dict):
                for k, v in d.items():
                    out["field_presence"][k] += 1
                    if k not in out["field_examples"] and v not in (None, "", []):
                        out["field_examples"][k] = v if not isinstance(v, (dict, list)) else str(v)[:200]
                if d.get("pg_ebook_number") not in (None, ""):
                    out["pg_ebook_number_present"] += 1
                if isinstance(d.get("pages_total"), int):
                    out["pages_total_sum"] += d["pages_total"]
                for lang in d.get("languages") or []:
                    out["languages"][lang] += 1
                if d.get("genre"):
                    out["genres"][d["genre"]] += 1
                if d.get("difficulty"):
                    out["difficulties"][d["difficulty"]] += 1
                if d.get("state"):
                    out["states"][d["state"]] += 1
                if d.get("image_source"):
                    out["image_sources"][d["image_source"]] += 1
                for cs in d.get("character_suites") or []:
                    out["character_suites"][cs] += 1

        if not pg.exists():
            out["projects_missing_pages_json"].append(p.name)
        else:
            d = load_json(pg)
            if isinstance(d, dict):
                out["pages_json_keys_sum"] += len(d)

        if not rd.exists():
            out["projects_missing_rounds_dir"].append(p.name)

        f2_keys = set()
        if not f2.exists():
            out["projects_missing_f2"].append(p.name)
        else:
            d = load_json(f2)
            if isinstance(d, dict):
                out["f2_json_keys_sum"] += len(d)
                f2_keys = set(d.keys())

        if not p3.exists():
            out["projects_missing_p3"].append(p.name)
        else:
            d = load_json(p3)
            if isinstance(d, dict):
                out["p3_json_keys_sum"] += len(d)

        if not imgd.exists():
            out["projects_missing_images_dir"].append(p.name)
        else:
            out["images_subdir_file_count_sum"] += sum(1 for _ in imgd.iterdir())

        top_pngs = set()
        for f in p.iterdir():
            if f.is_file() and f.suffix.lower() == ".png":
                top_pngs.add(f.name)
                stem = f.stem
                if re.fullmatch(r"\d+", stem):
                    pat = "numeric"
                elif re.fullmatch(r"\d{3}-\d{3}", stem):
                    pat = "NNN-NNN"
                elif re.fullmatch(r"[a-zA-Z]\d+", stem):
                    pat = "letter+digits"
                elif re.search(r"_(l|r|\d+)$", stem):
                    pat = "split-suffix (_l/_r/_N)"
                else:
                    pat = "other"
                out["image_filename_patterns"][pat] += 1
        out["top_level_png_count_sum"] += len(top_pngs)

        if f2_keys and not f2_keys.issubset(top_pngs):
            missing = sorted(f2_keys - top_pngs)
            if missing:
                out["f2_key_image_mismatches"].append([p.name, len(missing), missing[:5]])

    for k in list(out.keys()):
        if isinstance(out[k], Counter):
            out[k] = counter_top(out[k])
    return out


# --------------------------------------------------------------------------
# Style-state parser shared by markup-count, mixed-word, nesting, malformed
# --------------------------------------------------------------------------

class ParseResult:
    def __init__(self):
        self.clean_chars = []
        self.style_at = []  # frozenset of active style-names per clean char
        self.tag_open_counts = Counter()
        self.tag_close_counts = Counter()
        self.unclosed_open = []
        self.unmatched_close = []
        self.crossed_nesting_events = []
        self.max_depth = 0
        self.nested_pairs = Counter()
        self.block_open = 0
        self.block_close = 0
        self.paren_block_open = 0  # /#
        self.paren_block_close = 0  # #/
        self.proofer_notes = []
        self.bracket_notes = []  # opaque marker-only brackets (e.g. [1], [Blank Page])
        self.labeled_bracket_events = []  # (category, raw_content) for brackets recursed into
        self.tb_count = 0
        self.sup_brace = 0
        self.sup_char = 0
        self.sub_brace = 0
        self.sub_char = 0


def parse_page(text: str) -> ParseResult:
    r = ParseResult()
    stack = []
    i = 0
    n = len(text)

    while i < n:
        two = text[i:i+2]
        if two in ("/*", "*/", "/#", "#/"):
            if two == "/*":
                r.block_open += 1
            elif two == "*/":
                r.block_close += 1
            elif two == "/#":
                r.paren_block_open += 1
            else:
                r.paren_block_close += 1
            i += 2
            continue

        if text.startswith("[**", i):
            end = text.find("]", i)
            if end == -1:
                r.proofer_notes.append(text[i+3:])
                i = n
            else:
                r.proofer_notes.append(text[i+3:end])
                i = end + 1
            continue

        if text[i] == "[":
            end = text.find("]", i)
            if end != -1 and "[" not in text[i+1:end]:
                content = text[i+1:end]
                has_markup = ("<" in content) or ("^" in content) or ("_" in content)
                if not has_markup:
                    # pure marker/anchor/diacritic bracket: opaque, strip entirely
                    r.bracket_notes.append(content)
                    i = end + 1
                    continue
                # bracket carries real page content (footnote/illustration/
                # sidenote body text, or a bare stage direction) with its own
                # style tags -- do NOT swallow it opaquely. Strip only the
                # "[" delimiter (and a recognized editorial label prefix,
                # which is PGDP metadata rather than page text) and let the
                # main loop parse the remaining content normally, tags and
                # all. The matching "]" later falls through as a harmless
                # non-word character.
                lm = LABEL_RE.match(content)
                if lm:
                    r.labeled_bracket_events.append((lm.group(1).split()[0], content[:60]))
                    i += 1 + lm.end()  # skip "[" + "Label:" prefix
                else:
                    r.labeled_bracket_events.append(("bare", content[:60]))
                    i += 1  # skip just "["
                continue

        m = SUP_BRACE_RE.match(text, i)
        if m:
            r.sup_brace += 1
            for c in m.group(1):
                r.clean_chars.append(c)
                r.style_at.append(frozenset(stack) | {"sup"})
            i = m.end()
            continue

        m = SUB_BRACE_RE.match(text, i)
        if m:
            r.sub_brace += 1
            for c in m.group(1):
                r.clean_chars.append(c)
                r.style_at.append(frozenset(stack) | {"sub"})
            i = m.end()
            continue

        m = SUP_CHAR_RE.match(text, i)
        if m:
            r.sup_char += 1
            r.clean_chars.append(m.group(1))
            r.style_at.append(frozenset(stack) | {"sup"})
            i = m.end()
            continue

        m = SUB_CHAR_RE.match(text, i)
        if m:
            r.sub_char += 1
            r.clean_chars.append(m.group(1))
            r.style_at.append(frozenset(stack) | {"sub"})
            i = m.end()
            continue

        m = TAG_RE.match(text, i)
        if m:
            is_close = m.group(1) == "/"
            name = m.group(2).lower()
            if name == "tb":
                r.tb_count += 1
                i = m.end()
                continue
            if name not in STYLE_TAGS:
                # unknown/rare tag: still track open/close bookkeeping generically
                pass
            if is_close:
                r.tag_close_counts[name] += 1
                if name in stack:
                    if stack[-1] != name:
                        r.crossed_nesting_events.append((list(stack), name))
                        while stack and stack[-1] != name:
                            stack.pop()
                    if stack and stack[-1] == name:
                        stack.pop()
                else:
                    r.unmatched_close.append(name)
            else:
                r.tag_open_counts[name] += 1
                stack.append(name)
                r.max_depth = max(r.max_depth, len(stack))
                if len(stack) >= 2:
                    r.nested_pairs[(stack[-2], stack[-1])] += 1
            i = m.end()
            continue

        r.clean_chars.append(text[i])
        r.style_at.append(frozenset(stack))
        i += 1

    r.unclosed_open = list(stack)
    return r


def word_mixed_analysis(r: ParseResult):
    """Return list of (word, distinct_style_state_sequence, is_mixed)."""
    clean = "".join(r.clean_chars)
    results = []
    for m in WORD_RE.finditer(clean):
        s, e = m.span()
        states = r.style_at[s:e]
        distinct = []
        for st in states:
            if not distinct or distinct[-1] != st:
                distinct.append(st)
        is_mixed = len(distinct) > 1
        results.append((m.group(0), distinct, is_mixed))
    return results


STYLE_LABEL_NAMES = {
    "i": "italic", "b": "bold", "sc": "small_caps", "g": "letter_spaced",
    "f": "font_change", "sup": "superscript", "sub": "subscript",
}


def main():
    projects = list_projects()
    report = {}

    print("[*] structure...", flush=True)
    report["structure"] = audit_structure(projects)

    print("[*] markup + words + nesting + malformed...", flush=True)
    tag_totals = Counter()  # (kind,name) open/close totals across corpus
    per_page_tag_counts = Counter()  # name -> Counter of "tags on this page" histogram bucketed later
    pages_with_tag = Counter()  # name -> num pages containing >=1
    per_project_tag_counts = {}  # project -> Counter(name)
    total_pages_seen = 0

    sup_brace_total = sub_brace_total = sup_char_total = sub_char_total = 0
    sup_sub_examples = []

    block_star_open = block_star_close = block_hash_open = block_hash_close = 0
    block_examples = []

    proofer_note_total = 0
    proofer_note_question_total = 0
    proofer_note_examples = []
    bracket_note_total = 0
    bracket_note_top = Counter()
    labeled_bracket_total = 0
    labeled_bracket_by_category = Counter()
    labeled_bracket_examples = {}

    tb_total = 0

    unclosed_open_total = 0
    unmatched_close_total = 0
    crossed_nesting_total = 0
    crossed_nesting_examples = []
    unclosed_examples = []
    unmatched_examples = []
    max_depth_seen = 0
    nested_pairs_total = Counter()
    nested_examples = {}

    mixed_word_total = 0
    total_word_tokens = 0
    mixed_word_examples = []
    mixed_word_by_style_combo = Counter()

    word_count_visible = 0
    char_count_visible = 0
    label_word_counts = Counter()  # style-name -> word tokens that carry that style (fully or partially)
    label_char_counts = Counter()

    project_comments = []  # (project, comments_text) for formatting-instruction audit

    per_page_tag_histogram = {name: Counter() for name in STYLE_TAGS}

    import random
    rng = random.Random(1234)

    for p in projects:
        f2_path = p / "rounds" / "F2.json"
        if not f2_path.exists():
            continue
        d = load_json(f2_path)
        if not isinstance(d, dict):
            continue

        proj_tag_counter = Counter()

        # project-specific formatting instructions from project.json comments
        pj = load_json(p / "project.json")
        if isinstance(pj, dict) and pj.get("comments"):
            project_comments.append((p.name, pj["comments"]))

        for page_key, text in d.items():
            if not isinstance(text, str) or not text:
                continue
            total_pages_seen += 1
            r = parse_page(text)

            # tag totals
            page_tag_counter = Counter()
            for name, cnt in r.tag_open_counts.items():
                tag_totals[("open", name)] += cnt
                proj_tag_counter[name] += cnt
                page_tag_counter[name] += cnt
            for name, cnt in r.tag_close_counts.items():
                tag_totals[("close", name)] += cnt
            for name in STYLE_TAGS:
                if page_tag_counter.get(name, 0) > 0:
                    pages_with_tag[name] += 1
                per_page_tag_histogram[name][page_tag_counter.get(name, 0)] += 1

            sup_brace_total += r.sup_brace
            sub_brace_total += r.sub_brace
            sup_char_total += r.sup_char
            sub_char_total += r.sub_char
            if (r.sup_brace or r.sup_char or r.sub_brace or r.sub_char) and len(sup_sub_examples) < 20 and rng.random() < 0.4:
                sup_sub_examples.append({
                    "project": p.name, "page": page_key,
                    "snippet": text[:0],  # filled below if needed
                })

            block_star_open += r.block_open
            block_star_close += r.block_close
            block_hash_open += r.paren_block_open
            block_hash_close += r.paren_block_close
            if (r.block_open or r.paren_block_open) and len(block_examples) < 12 and rng.random() < 0.3:
                idx = text.find("/*") if "/*" in text else text.find("/#")
                if idx != -1:
                    block_examples.append({"project": p.name, "page": page_key, "snippet": text[max(0, idx-10):idx+120]})

            proofer_note_total += len(r.proofer_notes)
            for note in r.proofer_notes:
                if note.strip().endswith("?"):
                    proofer_note_question_total += 1
                if len(proofer_note_examples) < 25 and rng.random() < 0.05:
                    proofer_note_examples.append({"project": p.name, "page": page_key, "note": note[:100]})

            bracket_note_total += len(r.bracket_notes)
            for bn in r.bracket_notes:
                bracket_note_top[bn[:20]] += 1

            labeled_bracket_total += len(r.labeled_bracket_events)
            for cat, raw in r.labeled_bracket_events:
                labeled_bracket_by_category[cat] += 1
                if cat not in labeled_bracket_examples:
                    labeled_bracket_examples[cat] = {"project": p.name, "page": page_key, "raw": raw}

            tb_total += r.tb_count

            if r.unclosed_open:
                unclosed_open_total += len(r.unclosed_open)
                if len(unclosed_examples) < 15:
                    unclosed_examples.append({"project": p.name, "page": page_key, "still_open": r.unclosed_open, "tail": text[-120:]})
            if r.unmatched_close:
                unmatched_close_total += len(r.unmatched_close)
                if len(unmatched_examples) < 15:
                    unmatched_examples.append({"project": p.name, "page": page_key, "unmatched": r.unmatched_close})
            if r.crossed_nesting_events:
                crossed_nesting_total += len(r.crossed_nesting_events)
                if len(crossed_nesting_examples) < 15:
                    crossed_nesting_examples.append({"project": p.name, "page": page_key, "events": r.crossed_nesting_events[:3]})
            max_depth_seen = max(max_depth_seen, r.max_depth)
            for pair, cnt in r.nested_pairs.items():
                nested_pairs_total[pair] += cnt
                key = f"{pair[0]}>{pair[1]}"
                if key not in nested_examples and cnt > 0:
                    idx = text.find(f"<{pair[0]}>")
                    nested_examples[key] = {"project": p.name, "page": page_key, "snippet": text[max(0, idx-10):idx+80] if idx != -1 else ""}

            # word / mixed-word / label counts
            word_results = word_mixed_analysis(r)
            clean_text = "".join(r.clean_chars)
            char_count_visible += len(clean_text)
            for word, distinct_states, is_mixed in word_results:
                total_word_tokens += 1
                # union of style labels touching this word (excluding plain)
                touching = set()
                for st in distinct_states:
                    for lbl in st:
                        touching.add(lbl)
                for lbl in touching:
                    label_word_counts[lbl] += 1
                if not touching:
                    label_word_counts["plain"] += 1
                if is_mixed:
                    mixed_word_total += 1
                    combo = "+".join(sorted({lbl for st in distinct_states for lbl in (st or {"plain"})}))
                    mixed_word_by_style_combo[combo] += 1
                    if len(mixed_word_examples) < 40 and rng.random() < 0.08:
                        mixed_word_examples.append({
                            "project": p.name, "page": page_key, "word": word,
                            "states": [sorted(s) if s else ["plain"] for s in distinct_states],
                        })
            word_count_visible += len(word_results)
            for c, st in zip(clean_text, r.style_at):
                if c.strip():
                    for lbl in (st or ()):
                        label_char_counts[lbl] += 1
                    if not st:
                        label_char_counts["plain"] += 1

        per_project_tag_counts[p.name] = dict(proj_tag_counter)

    report["markup"] = {
        "total_pages_with_f2_text": total_pages_seen,
        "tag_totals_open": {k[1]: v for k, v in tag_totals.items() if k[0] == "open"},
        "tag_totals_close": {k[1]: v for k, v in tag_totals.items() if k[0] == "close"},
        "pages_with_tag_gt0": dict(pages_with_tag),
        "per_page_tag_count_histogram": {
            name: {str(k): v for k, v in sorted(hist.items())}
            for name, hist in per_page_tag_histogram.items()
        },
    }

    report["superscript_subscript"] = {
        "sup_brace_total": sup_brace_total,
        "sup_char_shorthand_total": sup_char_total,
        "sub_brace_total": sub_brace_total,
        "sub_char_shorthand_total": sub_char_total,
    }

    report["block_markers"] = {
        "star_open_slash_star": block_star_open,
        "star_close_star_slash": block_star_close,
        "hash_open_slash_hash": block_hash_open,
        "hash_close_hash_slash": block_hash_close,
        "examples": block_examples,
    }

    report["proofreader_notes"] = {
        "double_star_note_total": proofer_note_total,
        "double_star_note_ending_in_question_mark": proofer_note_question_total,
        "examples": proofer_note_examples,
        "other_bracket_notes_total": bracket_note_total,
        "other_bracket_notes_top": dict(bracket_note_top.most_common(30)),
    }

    report["labeled_content_brackets"] = {
        "note": (
            "Brackets whose content carries real page text plus its own style "
            "tags (footnote bodies, illustration captions, sidenotes, bare "
            "stage directions) -- parsed into the main markup/word streams "
            "rather than stripped opaquely."
        ),
        "total_instances": labeled_bracket_total,
        "by_category": dict(labeled_bracket_by_category.most_common()),
        "examples": labeled_bracket_examples,
    }

    report["thought_breaks_tb_tag_total"] = tb_total

    report["malformed"] = {
        "pages_seen": total_pages_seen,
        "unclosed_open_tag_instances": unclosed_open_total,
        "unmatched_close_tag_instances": unmatched_close_total,
        "crossed_nesting_instances": crossed_nesting_total,
        "max_nesting_depth_observed": max_depth_seen,
        "unclosed_examples": unclosed_examples,
        "unmatched_examples": unmatched_examples,
        "crossed_nesting_examples": crossed_nesting_examples,
    }

    report["nesting"] = {
        "nested_pairs_total": {f"{k[0]}>{k[1]}": v for k, v in nested_pairs_total.most_common(30)},
        "examples": nested_examples,
    }

    report["mixed_style_words"] = {
        "total_word_tokens": total_word_tokens,
        "mixed_style_word_count": mixed_word_total,
        "mixed_style_fraction": mixed_word_total / total_word_tokens if total_word_tokens else None,
        "mixed_style_combo_counts": dict(mixed_word_by_style_combo.most_common(30)),
        "examples": mixed_word_examples,
    }

    report["visible_text_totals"] = {
        "word_tokens_total": word_count_visible,
        "char_count_visible_total": char_count_visible,
        "label_word_counts": dict(label_word_counts.most_common()),
        "label_char_counts": dict(label_char_counts.most_common()),
    }

    report["project_formatting_instructions"] = {
        "num_projects_with_comments_field": len(project_comments),
        "num_projects_total_with_f2": sum(1 for p in projects if (p / "rounds" / "F2.json").exists()),
        "examples": [
            {"project": name, "comments": text[:600]}
            for name, text in project_comments[:15]
        ],
    }

    report["per_project_tag_counts"] = per_project_tag_counts

    with open("/tmp/claude-1000/-workspaces-pdomain-pdomain-ocr-synth/a13105ad-089e-4e25-9c73-3e8b3a784c8f/scratchpad/typo-research/report.json", "w") as fh:
        json.dump(report, fh, indent=2, default=str)
    print("[*] wrote report.json", flush=True)


if __name__ == "__main__":
    main()
