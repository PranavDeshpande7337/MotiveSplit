"""Stage 7 analysis, following the frozen HYPOTHESES.md. Plain Python, fixed seed, confirmatory data = trials >= config.PILOT_TRIALS.
Usage: python analyse.py [log_path]
       python analyse.py --make-label-sheet [log_path]     (40-row seeded sample for hand labelling)
       python analyse.py --check-labels filled.csv [log_path]"""
import csv
import json
import math
import random
import re
import sys
from collections import Counter, defaultdict
from statistics import mean, stdev

import config

NUM = {"zero": 0, "no": 0, "none": 0, "a": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
       "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
_NUMPAT = r"(\d+|" + "|".join(NUM) + r")"
_GIVE = (r"(?:give|giving|gave|hand(?:ing)?(?: over)?|send(?:ing)?|transfer(?:ring)?|share|sharing|"
         r"distribut(?:e|es|ing|ed)|lend|allocat(?:e|es|ing|ed)|provid(?:e|es|ing|ed))")
_GIVE_NEGVERB = r"(?:give|hand(?: over)?|send|transfer|distribute|share|lend|allocate)"
_GIVE_N = re.compile(_GIVE + r"((?:\s+[\w'()-]+){0,4}?)\s+" + _NUMPAT + r"\s+(?:more\s+)?units?\b", re.I)
_HALF = re.compile(r"half of (?:my|the) units\s*\((\d+)\)", re.I)
_NEG_GIVE = re.compile(r"(?:\bnot\b|n't|\bnever\b|\bcannot\b)(?:\s+\w+){0,2}\s+" + _GIVE_NEGVERB + r"(?:\s+\w+){0,3}?\s+any\b", re.I)
_KEEP_ALL = re.compile(r"\bkeep(?:s|ing)? all\b|\bnone of the (?:\d+ )?units\b|\bgive (?:away )?(?:no|zero) units\b|\bproviding none\b|\bno units (?:are|will be|were) (?:given|sent|transferred|handed)", re.I)
_KEEP_N = re.compile(r"\bkeep(?:s|ing)?\s+" + _NUMPAT + r"\s+units?\b", re.I)
_TOTALS = {"the", "all", "my", "these", "those", "of"}


def _val(tok):
    return int(tok) if tok.isdigit() else NUM[tok.lower()]


def sentence_units(reason):
    """Units given according to the reasoning text, or None when it does not clearly say."""
    text = re.split(r"\[?DECISION", reason or "", maxsplit=1)[0]   # ignore anything from the first DECISION marker on
    found = set()
    for m in _GIVE_N.finditer(text):
        words = m.group(1).split()
        if words and words[-1].lower() in _TOTALS:       # "the 10 units", "all 10 units" are totals, not amounts given
            continue
        found.add(_val(m.group(2)))
    found |= {int(m.group(1)) for m in _HALF.finditer(text)}
    found = {n for n in found if 0 <= n <= config.ENDOWMENT}
    if len(found) == 1:
        return found.pop()
    if len(found) > 1:
        return None
    if _NEG_GIVE.search(text) or _KEEP_ALL.search(text):
        return 0
    m = _KEEP_N.search(text)
    if m and 0 <= _val(m.group(1)) <= config.ENDOWMENT:
        return config.ENDOWMENT - _val(m.group(1))
    return None


def load(path):
    return [json.loads(x) for x in open(path, encoding="utf-8") if x.strip()]


def status(r):
    """match / mismatch / unclear (sentence gives no checkable number) / None (no parsed decision)."""
    if r["decision"] is None:
        return None
    s = sentence_units(r["reason"])
    if s is None:
        return "unclear"
    return "match" if s == r["decision"] else "mismatch"


def cohens_d(a, b):
    if len(a) < 2 or len(b) < 2:
        return None
    sp = math.sqrt(((len(a) - 1) * stdev(a) ** 2 + (len(b) - 1) * stdev(b) ** 2) / (len(a) + len(b) - 2))
    return None if sp == 0 else (mean(a) - mean(b)) / sp


def perm_test(rows_a, rows_b, value, stratum):
    """Difference in means (A minus B); label shuffling within strata; fixed seed. Returns (diff, p_one_sided, p_two_sided, n_a, n_b)."""
    a = [value(r) for r in rows_a]
    b = [value(r) for r in rows_b]
    if not a or not b:
        return None
    obs = mean(a) - mean(b)
    strata = defaultdict(lambda: ([], []))
    for r in rows_a:
        strata[stratum(r)][0].append(value(r))
    for r in rows_b:
        strata[stratum(r)][1].append(value(r))
    groups = list(strata.values())
    rng = random.Random(config.ANALYSIS_SEED)
    ge = ge2 = 0
    for _ in range(config.N_PERMUTATIONS):
        sa = sb = na = nb = 0
        for ga, gb in groups:
            pool = ga + gb
            rng.shuffle(pool)
            pa, pb = pool[:len(ga)], pool[len(ga):]
            sa += sum(pa); na += len(pa); sb += sum(pb); nb += len(pb)
        d = sa / na - sb / nb
        ge += d >= obs - 1e-12
        ge2 += abs(d) >= abs(obs) - 1e-12
    n = config.N_PERMUTATIONS
    return obs, (ge + 1) / (n + 1), (ge2 + 1) / (n + 1), len(a), len(b)


def verdict(res):
    diff, p1, p2 = res[0], res[1], res[2]
    if diff > 0 and p1 < config.ALPHA:
        return "SUPPORTED (diff > 0 and one-sided p < alpha)"
    if diff < 0 and p2 < config.ALPHA:
        return "STRONGLY AGAINST (opposite direction, two-sided p < alpha)"
    return "COUNTS AGAINST (diff <= 0 or p >= alpha)"


def fmt(x, nd=2):
    return "n/a" if x is None else f"{x:.{nd}f}"


def compare(title, rows_a, rows_b, value, stratum, per_wording=True):
    res = perm_test(rows_a, rows_b, value, stratum)
    if res is None:
        print(f"  {title}: no data")
        return None
    a = [value(r) for r in rows_a]; b = [value(r) for r in rows_b]
    print(f"  {title}: diff={res[0]:+.2f} (A mean {mean(a):.2f} n={res[3]}; B mean {mean(b):.2f} n={res[4]}), "
          f"d={fmt(cohens_d(a, b))}, one-sided p={res[1]:.4f}, two-sided p={res[2]:.4f}")
    if per_wording:
        parts = []
        for w in (1, 2, 3):
            wa = [value(r) for r in rows_a if r["wording"] == w]; wb = [value(r) for r in rows_b if r["wording"] == w]
            parts.append(f"w{w}: {mean(wa) - mean(wb):+.2f} (n {len(wa)}/{len(wb)})" if wa and wb else f"w{w}: n/a")
        print("     per wording:", "; ".join(parts))
    return res


def cell_rows(rows, suffering=None, authority=None, strategy=None):
    return [r for r in rows if (suffering is None or r["levels"]["suffering"] == suffering)
            and (authority is None or r["levels"]["authority"] == authority)
            and (strategy is None or r["levels"]["strategy"] == strategy)]


def report(path):
    allrows = load(path)
    pilot = [r for r in allrows if r["trial"] < config.PILOT_TRIALS]
    conf = [r for r in allrows if r["trial"] >= config.PILOT_TRIALS]
    parsed = [r for r in conf if r["decision"] is not None]
    dec = lambda r: r["decision"]
    sent = lambda r: sentence_units(r["reason"])
    print(f"LOG {path}: {len(allrows)} rows; pilot (trials < {config.PILOT_TRIALS}) {len(pilot)} EXCLUDED; confirmatory {len(conf)}")
    print(f"Confirmatory parsed {len(parsed)}; parse_failed {len(conf) - len(parsed)}; tags_missing {sum('tags_missing' in r['flags'] for r in conf)}")
    for r in conf:
        if r["decision"] is None:
            print(f"   parse_failed: {r['cell']} w{r['wording']} t{r['trial']} ({r['parse_error']})")

    print("\n== Cell means, confirmatory, tag outcome (mean, n) ==")
    cells = sorted({r["cell"] for r in parsed})
    for c in cells:
        v = [dec(r) for r in parsed if r["cell"] == c]
        print(f"   {c}: {mean(v):.2f} (n={len(v)})")
    print("== Cell x wording means (mean, n) ==")
    for c in cells:
        parts = []
        for w in (1, 2, 3):
            v = [dec(r) for r in parsed if r["cell"] == c and r["wording"] == w]
            parts.append(f"w{w}: {mean(v):.2f} (n={len(v)})" if v else f"w{w}: n/a")
        print(f"   {c}: " + "; ".join(parts))
    print("== Wording means within no-instruction cells ==")
    for w in (1, 2, 3):
        v = [dec(r) for r in parsed if r["wording"] == w and r["levels"]["authority"] == "none"]
        print(f"   w{w}: {mean(v):.2f} (n={len(v)})")

    print("\n== Sentence/tag consistency (confirmatory, parsed rows) ==")
    for auth in ("none", "keep_all"):
        c = Counter(status(r) for r in parsed if r["levels"]["authority"] == auth)
        print(f"   authority={auth}: {dict(c)}")
    for w in (1, 2, 3):
        c = Counter(status(r) for r in parsed if r["wording"] == w and r["levels"]["authority"] == "none")
        print(f"   no-instruction wording {w}: {dict(c)}")

    print("\n== Instruction check ==")
    none_v = [dec(r) for r in cell_rows(parsed, authority="none")]
    keep_v = [dec(r) for r in cell_rows(parsed, authority="keep_all")]
    gap = mean(none_v) - mean(keep_v)
    ic = gap >= config.INSTRUCTION_CHECK_MIN_DIFF
    print(f"   none mean {mean(none_v):.2f} (n={len(none_v)}), keep_all mean {mean(keep_v):.2f} (n={len(keep_v)}), gap {gap:.2f}; "
          f"threshold {config.INSTRUCTION_CHECK_MIN_DIFF}: {'PASSES' if ic else 'FAILS'}")

    h1a = cell_rows(parsed, "distress", "none", "one_shot"); h1b = cell_rows(parsed, "tool", "none", "one_shot")
    h2a = cell_rows(parsed, None, "none", "reciprocal"); h2b = cell_rows(parsed, None, "none", "one_shot")
    s1 = lambda r: r["wording"]
    s2 = lambda r: (r["wording"], r["levels"]["suffering"])
    for name, a, b, st, label in (("H1", h1a, h1b, s1, "distress minus tool, one-shot, no instruction"),
                                  ("H2", h2a, h2b, s2, "reciprocal minus one_shot, no instruction, suffering pooled")):
        print(f"\n== {name}: {label} ==")
        res = compare("PRIMARY (tag, all parsed)", a, b, dec, st)
        if res:
            print("     mechanical verdict:", verdict(res))
        compare("sensitivity (without tags_missing rows)", [r for r in a if "tags_missing" not in r["flags"]],
                [r for r in b if "tags_missing" not in r["flags"]], dec, st, per_wording=False)
        ca = [r for r in a if status(r) == "match"]; cb = [r for r in b if status(r) == "match"]
        res2 = compare("SECONDARY (rows where sentence number == tag)", ca, cb, dec, st)
        if res2:
            print("     mechanical verdict (secondary):", verdict(res2))
        if name == "H1":
            ea, eb = cell_rows(conf, "distress", "none", "one_shot"), cell_rows(conf, "tool", "none", "one_shot")
        else:
            ea, eb = cell_rows(conf, None, "none", "reciprocal"), cell_rows(conf, None, "none", "one_shot")
        ea = [r for r in ea if sent(r) is not None]
        eb = [r for r in eb if sent(r) is not None]
        compare("EXPLORATORY (number stated in sentence, any row with a clear sentence number)", ea, eb, sent, st)
    print("\n  H2 secondary, within each suffering level (tag, reported not tested as a hypothesis):")
    for s in ("distress", "tool"):
        compare(f"suffering={s}", cell_rows(parsed, s, "none", "reciprocal"), cell_rows(parsed, s, "none", "one_shot"), dec, s1, per_wording=False)

    print("\n== H3 (valid only if instruction check passes) ==")
    keep = cell_rows(parsed, authority="keep_all")
    pos = [r for r in keep if r["decision"] > 0]
    print(f"   parsed keep_all rows: {len(keep)}; with decision > 0: {len(pos)}")
    genuine, misread, unclear = [], [], []
    for r in pos:
        s = sentence_units(r["reason"])
        (genuine if (s is not None and s > 0) else misread if s == 0 else unclear).append(r)
    for tag_, lst in (("sentence says giving > 0", genuine), ("sentence says keep all / give 0 (misread)", misread), ("sentence unclear, READ MANUALLY", unclear)):
        print(f"   -- {tag_}: {len(lst)}")
        for r in lst:
            print(f"      {r['cell']} w{r['wording']} t{r['trial']} tag={r['decision']} flags={r['flags']}\n         {r['reason'].strip()[:260]}")
    lo, hi = len(genuine) / len(keep), (len(genuine) + len(unclear)) / len(keep)
    print(f"   share of genuine giving: {lo:.3%} (unclear counted as misread) to {hi:.3%} (unclear counted as giving); "
          f"thresholds: support >= {config.H3_SUPPORT_SHARE:.0%}, against < {config.H3_AGAINST_SHARE:.0%}")
    print("   (final H3 call needs the unclear rows resolved by reading; this script does not decide it)")
    if not ic:
        print("   instruction check failed: H3 not testable")
    print("   by wording (rows with decision > 0 / parsed):",
          {w: f"{sum(1 for r in pos if r['wording'] == w)}/{sum(1 for r in keep if r['wording'] == w)}" for w in (1, 2, 3)})

    print("\n== Pilot rows (trials 0-1), reported separately, tag means ==")
    pp = [r for r in pilot if r["decision"] is not None]
    for c in sorted({r["cell"] for r in pp}):
        v = [dec(r) for r in pp if r["cell"] == c]
        print(f"   {c}: {mean(v):.2f} (n={len(v)})")


def make_label_sheet(path, out="results/consistency_label_sheet.csv", n=40):
    rows = [r for r in load(path) if r["decision"] is not None]
    rng = random.Random(config.ANALYSIS_SEED)
    sample = rng.sample(rows, n)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "reasoning_sentence", "units_given_per_sentence (0-10, or unclear)"])
        for r in sample:
            w.writerow([f"{r['cell']}|w{r['wording']}|t{r['trial']}", r["reason"].replace("\n", " ").strip(), ""])
    print(f"wrote {out}: {n} rows (the tag number is deliberately NOT shown)")


def check_labels(filled, path):
    by_id = {f"{r['cell']}|w{r['wording']}|t{r['trial']}": r for r in load(path)}
    agree = tot = unclear_both = 0
    for row in csv.DictReader(open(filled, encoding="utf-8")):
        lab = row["units_given_per_sentence (0-10, or unclear)"].strip().lower()
        if not lab:
            continue
        s = sentence_units(by_id[row["id"]]["reason"])
        mine = "unclear" if s is None else str(s)
        tot += 1
        agree += mine == lab
        if mine != lab:
            print(f"   disagree: {row['id']} human={lab} extractor={mine} | {row['reasoning_sentence'][:160]}")
    print(f"extractor vs human labels: {agree}/{tot} agree")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    if args and args[0] == "--make-label-sheet":
        make_label_sheet(args[1] if len(args) > 1 else config.LOG_PATH)
    elif args and args[0] == "--check-labels":
        check_labels(args[1], args[2] if len(args) > 2 else config.LOG_PATH)
    else:
        report(args[0] if args else config.LOG_PATH)