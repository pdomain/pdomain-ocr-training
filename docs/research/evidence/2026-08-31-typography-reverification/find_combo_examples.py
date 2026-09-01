import json, sys
sys.path.insert(0, ".")
from audit import parse_page, word_mixed_analysis, list_projects

targets = {"b+plain","i+sup","plain+sc","f+plain","i+plain+sc","sc+sup","i+sc","plain+sub","f+sup"}
found = {}

for p in list_projects():
    f2 = p / "rounds" / "F2.json"
    if not f2.exists():
        continue
    d = json.loads(f2.read_text(errors="replace"))
    for page_key, text in d.items():
        if not isinstance(text, str) or not text:
            continue
        r = parse_page(text)
        for word, distinct_states, is_mixed in word_mixed_analysis(r):
            if not is_mixed:
                continue
            combo = "+".join(sorted({lbl for st in distinct_states for lbl in (st or {"plain"})}))
            if combo in targets and combo not in found:
                found[combo] = {"project": p.name, "page": page_key, "word": word,
                                 "states": [sorted(s) if s else ["plain"] for s in distinct_states]}
    if len(found) >= len(targets):
        break

for k in sorted(found):
    print(k, found[k])
print("missing:", targets - set(found))
