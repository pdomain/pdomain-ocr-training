"""Count mixed-style words under a strict and a loose definition, one parser."""

import json
import pathlib
import re
import unicodedata
from collections import Counter

ROOT = pathlib.Path("/workspaces/pdomain-data/pgdp-corpus")
TAG = re.compile(r"<(/?)(i|b|sc|g|f|u)>")
NOTE = re.compile(r"\[\*\*[^\]]*\]", re.DOTALL)
SUP_BRACE = re.compile(r"\^\{([^}]*)\}")
SUB_BRACE = re.compile(r"_\{([^}]*)\}")

strict = Counter()
loose = Counter()
uniform_styled = 0
tokens_total = 0
tokens_with_any_style = 0
mixed_strict = 0
mixed_loose = 0
punct_only_boundary = 0


def visible(text: str) -> list[tuple[str, frozenset[str]]]:
    """Return (char, active-label-set) for each visible char."""
    text = NOTE.sub("", text)
    out: list[tuple[str, frozenset[str]]] = []
    active: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        m = TAG.match(text, i)
        if m:
            close, name = m.group(1), m.group(2)
            if close:
                if name in active:
                    active.reverse()
                    active.remove(name)
                    active.reverse()
            else:
                active.append(name)
            i = m.end()
            continue
        m = SUP_BRACE.match(text, i)
        if m:
            for ch in m.group(1):
                out.append((ch, frozenset(active + ["sup"])))
            i = m.end()
            continue
        m = SUB_BRACE.match(text, i)
        if m:
            for ch in m.group(1):
                out.append((ch, frozenset(active + ["sub"])))
            i = m.end()
            continue
        if text[i] == "^" and i + 1 < n and not text[i + 1].isspace():
            out.append((text[i + 1], frozenset(active + ["sup"])))
            i += 2
            continue
        out.append((text[i], frozenset(active)))
        i += 1
    return out


def is_wordchar(ch: str) -> bool:
    return ch.isalnum() or unicodedata.category(ch) == "Mn"


for f in sorted(ROOT.glob("*/rounds/F2.json")):
    try:
        pages = json.load(f.open(encoding="utf-8"))
    except Exception:
        continue
    for text in pages.values():
        if not isinstance(text, str):
            continue
        chars = visible(text)
        token: list[tuple[str, frozenset[str]]] = []
        for ch, labels in chars + [(" ", frozenset())]:
            if ch.isspace():
                if token:
                    tokens_total += 1
                    sets = {lb for _, lb in token}
                    if any(lb for lb in sets):
                        tokens_with_any_style += 1
                    if len(sets) > 1:
                        mixed_loose += 1
                        loose["|".join(sorted("+".join(sorted(s)) or "plain" for s in sets))] += 1
                        core = [(c, lb) for c, lb in token if is_wordchar(c)]
                        core_sets = {lb for _, lb in core}
                        if len(core_sets) > 1:
                            mixed_strict += 1
                            strict[
                                "|".join(sorted("+".join(sorted(s)) or "plain" for s in core_sets))
                            ] += 1
                        else:
                            punct_only_boundary += 1
                    elif sets and next(iter(sets)):
                        uniform_styled += 1
                    token = []
            else:
                token.append((ch, labels))

print(f"whitespace tokens total          {tokens_total:>12,}")
print(f"tokens with any style            {tokens_with_any_style:>12,}")
print(f"uniformly styled whole words     {uniform_styled:>12,}")
print()
print(f"MIXED, loose (incl. punctuation) {mixed_loose:>12,}   research said 22,164 on a 3.4x smaller corpus")
print(f"MIXED, strict (inside word core) {mixed_strict:>12,}   audit agent said 1,507")
print(f"  of which punctuation-only edge {punct_only_boundary:>12,}")
print()
print("top strict combos:")
for k, v in strict.most_common(8):
    print(f"   {k:<28} {v:>8,}")
print("top loose combos:")
for k, v in loose.most_common(6):
    print(f"   {k:<28} {v:>8,}")
