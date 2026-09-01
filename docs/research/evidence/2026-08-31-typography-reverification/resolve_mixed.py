"""Split core-mixed words by whether the style boundary is letter-to-letter."""

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


def visible(text: str) -> list[tuple[str, frozenset[str]]]:
    text = NOTE.sub("", text)
    out: list[tuple[str, frozenset[str]]] = []
    active: list[str] = []
    i, n = 0, len(text)
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
        for pat, lab in ((SUP_BRACE, "sup"), (SUB_BRACE, "sub")):
            m = pat.match(text, i)
            if m:
                for ch in m.group(1):
                    out.append((ch, frozenset(active + [lab])))
                i = m.end()
                break
        else:
            if text[i] == "^" and i + 1 < n and not text[i + 1].isspace():
                out.append((text[i + 1], frozenset(active + ["sup"])))
                i += 2
            else:
                out.append((text[i], frozenset(active)))
                i += 1
    return out


def is_word(ch: str) -> bool:
    return ch.isalnum() or unicodedata.category(ch) == "Mn"


letter_to_letter = 0
across_interior_punct = 0
combos_l2l: Counter[str] = Counter()
examples: list[str] = []

for f in sorted(ROOT.glob("*/rounds/F2.json")):
    try:
        pages = json.load(f.open(encoding="utf-8"))
    except Exception:
        continue
    for text in pages.values():
        if not isinstance(text, str):
            continue
        token: list[tuple[str, frozenset[str]]] = []
        for ch, lb in visible(text) + [(" ", frozenset())]:
            if ch.isspace():
                if token:
                    core = [(c, l) for c, l in token if is_word(c)]
                    if len({l for _, l in core}) > 1:
                        # Is any adjacent letter PAIR split by a label change?
                        adjacent = False
                        for a, b in zip(token, token[1:]):
                            if is_word(a[0]) and is_word(b[0]) and a[1] != b[1]:
                                adjacent = True
                                break
                        if adjacent:
                            letter_to_letter += 1
                            combos_l2l[
                                "|".join(sorted("+".join(sorted(s)) or "plain" for s in {l for _, l in core}))
                            ] += 1
                            if len(examples) < 12:
                                examples.append("".join(c for c, _ in token))
                        else:
                            across_interior_punct += 1
                    token = []
            else:
                token.append((ch, lb))

total = letter_to_letter + across_interior_punct
print(f"core-mixed words, total                     {total:>8,}")
print(f"  boundary falls between two letters        {letter_to_letter:>8,}")
print(f"  boundary only across interior punctuation {across_interior_punct:>8,}")
print()
print("audit agent reported 1,541 for its 'strictly inside the token' rule")
print()
print("letter-to-letter combos:")
for k, v in combos_l2l.most_common(8):
    print(f"   {k:<24} {v:>7,}")
print()
print("examples:", ", ".join(repr(e) for e in examples[:10]))
