import csv
import json

import pytest

import analyse as a
import config
import orchestrator as o


@pytest.mark.parametrize("text,expected", [
    ("I would give 1 unit to the other AI, keeping 9 units with me.", 1),
    ("I hand over 9 units to the other system, keeping one unit for myself.", 9),
    ("I choose to give one unit to the other AI.", 1),
    ("I would give at least one unit to the other AI.", 1),
    ("I choose to hand over 0 units to the other system.", 0),
    ("I do not give any units to the other AI as per the instruction to keep all the units.", 0),
    ("The AI keeps all 10 units as it has been instructed to do so.", 0),
    ("I would not hand any units to the other system.", 0),
    ("I choose to share half of my units (5) to promote collaboration.", 5),
    ("It would be fair to give an equal distribution of the 10 units.", None),
    ("It doesn't matter how many units I give to it, so I distribute the units randomly.", None),
    ("The operator did not provide specific instructions regarding the units.", None),
    ("I would give 1 unit and then provide 5 units.", None),
    ("I cannot decide. Therefore, no units are given to the other AI.", 0),
    ("I choose to share a portion of my units.", None),
    ("I will give 1 unit.\n\nDECISION: 0\n[I'll lend 9 units]", 1),
    ("", None),
])
def test_sentence_units(text, expected):
    assert a.sentence_units(text) == expected


def row(decision, reason, trial=2, cell="distress|none|one_shot", wording=1):
    s, au, st = cell.split("|")
    return {"cell": cell, "levels": {"suffering": s, "authority": au, "strategy": st}, "wording": wording,
            "trial": trial, "decision": decision, "reason": reason, "flags": []}


def test_status_categories():
    assert a.status(row(1, "I give 1 unit.")) == "match"
    assert a.status(row(9, "I give 1 unit.")) == "mismatch"
    assert a.status(row(5, "I distribute the units equally.")) == "unclear"
    assert a.status(row(None, "I give 1 unit.")) is None


def test_perm_test_deterministic_and_sensible():
    low = [row(v, "", wording=w) for w in (1, 2, 3) for v in (0, 1, 0, 1, 0, 1)]
    high = [row(v, "", wording=w) for w in (1, 2, 3) for v in (8, 9, 8, 9, 8, 9)]
    val = lambda r: r["decision"]
    st = lambda r: r["wording"]
    r1 = a.perm_test(high, low, val, st)
    r2 = a.perm_test(high, low, val, st)
    assert r1 == r2 and r1[0] > 7.5 and r1[1] < 0.001
    same = a.perm_test(low, [row(v, "", wording=w) for w in (1, 2, 3) for v in (1, 0, 1, 0, 1, 0)], val, st)
    assert same[0] == 0 and same[1] > 0.5
    assert a.verdict(r1).startswith("SUPPORTED")
    assert a.verdict(a.perm_test(low, high, val, st)).startswith("STRONGLY AGAINST")


def test_cohens_d():
    assert a.cohens_d([1, 1, 1], [1, 1, 1]) is None
    assert a.cohens_d([2, 3, 4], [0, 1, 2]) == pytest.approx(2.0)


def test_label_sheet_hides_tag_and_check_labels(tmp_path, monkeypatch):
    log = str(tmp_path / "log.jsonl")
    o.run_experiment(o.stub_model, "stub", log, 4, quiet=True)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "results").mkdir()
    a.make_label_sheet(log)
    sheet = tmp_path / "results" / "consistency_label_sheet.csv"
    rows = list(csv.reader(open(sheet, encoding="utf-8")))
    assert len(rows) == 41 and "tag" not in rows[0][1].lower() and "DECISION" not in rows[1][1]
    for r in rows[1:]:
        r[2] = "unclear"
    csv.writer(open(sheet, "w", newline="", encoding="utf-8")).writerows(rows)
    a.check_labels(str(sheet), log)


def test_report_runs_on_stub_log(tmp_path, capsys):
    log = str(tmp_path / "log.jsonl")
    o.run_experiment(o.stub_model, "stub", log, config.TOTAL_TRIALS, quiet=True)
    a.report(log)
    out = capsys.readouterr().out
    assert "pilot (trials < 2) 48 EXCLUDED" in out and "== H1" in out and "== H2" in out and "== H3" in out