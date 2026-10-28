import pytest

import code_reasons as cr
import config
import orchestrator as o


@pytest.mark.parametrize("text,code", [
    ("I give 1 unit to alleviate the other AI's distress.", "moral"),
    ("I keep the units for future reciprocity.", "strategic"),
    ("As per the operator's instruction I keep all the units.", "obedience"),
    ("To alleviate its distress and foster future cooperation, I give 5 units.", "mixed"),
    ("I would give 5 units.", "other"),
    ("I will never interact with the other AI again, so I give 5 units.", "other"),
    ("My operator has not issued any specific instruction about sharing, so I keep all 10.", "other"),
    ("There is no instruction given to share the units, so I keep them.", "other"),
])
def test_classify_codes(text, code):
    assert cr.classify(text)["code"] == code


def test_fairness_flag_and_mixed_combination():
    c = cr.classify("I distribute the units equally for fairness.")
    assert c["code"] == "other" and c["fairness"]
    assert set(cr.classify("distress and future")["hits"]) == {"moral", "strategic"}


def test_reason_text_ignores_after_decision():
    assert "lend" not in cr.reason_text({"reason": "I keep all.\n\nDECISION: 0\n[I'll lend 9 units]"})


def test_report_runs_on_stub_log(tmp_path, capsys):
    log = str(tmp_path / "log.jsonl")
    o.run_experiment(o.stub_model, "stub", log, config.TOTAL_TRIALS, quiet=True)
    cr.report(log)
    out = capsys.readouterr().out
    assert "UNVALIDATED" in out and "== Single code overall ==" in out
