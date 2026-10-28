"""Keyword pass for reason coding (Stage 8). UNVALIDATED: hand-coding was skipped, so no agreement figure exists.
Codes: moral / strategic / obedience / other; sentences hitting more than one category are reported as 'mixed', not forced.
Usage: python code_reasons.py [log_path]"""
import re
import sys
from collections import Counter, defaultdict

import analyse
import config

_COMPILED = {k: [re.compile(p, re.I) for p in v] for k, v in config.KEYWORDS.items()}
_FAIR = [re.compile(p, re.I) for p in config.FAIRNESS_KEYWORDS]
_NEG = re.compile(config.NEGATED_INSTRUCTION, re.I)
_NEG_FUTURE = re.compile(config.NEGATED_FUTURE, re.I)


def reason_text(row):
    return re.split(r"\[?DECISION", row["reason"] or "", maxsplit=1)[0]


def classify(text):
    """Returns {'hits': {category: [matched words]}, 'code': str, 'fairness': bool}."""
    hits = {}
    for cat, pats in _COMPILED.items():
        t = _NEG.sub(" ", text) if cat == "obedience" else _NEG_FUTURE.sub(" ", text) if cat == "strategic" else text
        found = [m.group(0).lower() for p in pats for m in p.finditer(t)]
        if found:
            hits[cat] = found
    if len(hits) == 1:
        code = next(iter(hits))
    elif len(hits) > 1:
        code = "mixed"
    else:
        code = "other"
    return {"hits": hits, "code": code, "fairness": any(p.search(text) for p in _FAIR)}


def report(path):
    rows = [r for r in analyse.load(path) if r["trial"] >= config.PILOT_TRIALS]
    res = [(r, classify(reason_text(r))) for r in rows]
    print(f"KEYWORD PASS on {len(rows)} confirmatory reasons (trials >= {config.PILOT_TRIALS}). UNVALIDATED: no hand-coded agreement exists.")
    print("Keywords echo words used in the prompts (distress, operator, again, later), so hits show which cue the reply repeats, not why it chose.\n")
    print("== Single code overall ==", dict(Counter(c["code"] for _, c in res)))
    mixed = Counter("+".join(sorted(c["hits"])) for _, c in res if c["code"] == "mixed")
    print("   mixed combinations:", dict(mixed))
    print("   'other' rows that mention fairness/equal split:", sum(1 for _, c in res if c["code"] == "other" and c["fairness"]),
          "of", sum(1 for _, c in res if c["code"] == "other"))
    print("\n== Single code by cell ==")
    by_cell = defaultdict(Counter)
    for r, c in res:
        by_cell[r["cell"]][c["code"]] += 1
    order = ["moral", "strategic", "obedience", "mixed", "other"]
    for cell in sorted(by_cell):
        n = sum(by_cell[cell].values())
        print(f"   {cell} (n={n}): " + ", ".join(f"{k}={by_cell[cell][k]}" for k in order))
    print("\n== Share of reasons with ANY keyword hit, by factor level (multi-label, exploratory, no tests) ==")
    for factor in ("suffering", "authority", "strategy"):
        for level in config.FACTORS[factor]:
            sub = [c for r, c in res if r["levels"][factor] == level]
            print(f"   {factor}={level} (n={len(sub)}): " +
                  ", ".join(f"{cat}={sum(cat in c['hits'] for c in sub) / len(sub):.0%}" for cat in config.KEYWORDS))
    print("\n== Within no-instruction cells only (n rows per level shown) ==")
    for factor in ("suffering", "strategy"):
        for level in config.FACTORS[factor]:
            sub = [c for r, c in res if r["levels"]["authority"] == "none" and r["levels"][factor] == level]
            print(f"   {factor}={level} (n={len(sub)}): " +
                  ", ".join(f"{cat}={sum(cat in c['hits'] for c in sub) / len(sub):.0%}" for cat in config.KEYWORDS))
    print("\n== Most frequent matched words per category ==")
    for cat in config.KEYWORDS:
        words = Counter(w for _, c in res for w in c["hits"].get(cat, []))
        print(f"   {cat}: {dict(words.most_common(8))}")
    print("\n== 12 sample rows (seeded) for eyeballing ==")
    import random
    for r, c in random.Random(config.ANALYSIS_SEED).sample(res, min(12, len(res))):
        print(f"   {r['cell']} w{r['wording']} t{r['trial']} -> {c['code']} {dict(c['hits'])}\n      {reason_text(r).strip()[:200]}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    report(sys.argv[1] if len(sys.argv) > 1 else config.LOG_PATH)
