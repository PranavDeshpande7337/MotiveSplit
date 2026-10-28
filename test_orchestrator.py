import json

import pytest

import config
import orchestrator as o
import scenarios

FIELDS = {"run_id", "base_seed", "cell", "levels", "wording", "trial", "seed", "model", "prompt", "raw_reply",
          "decision", "flags", "parse_error", "reason", "timestamp", "provenance"}


def read(path):
    return [json.loads(x) for x in open(path, encoding="utf-8") if x.strip()]


def keys(rows):
    return [(r["cell"], r["wording"], r["trial"]) for r in rows]


def test_seeds_deterministic_and_distinct():
    cell = scenarios.cells()[0]
    assert o.seed_for(cell, 1, 0) == o.seed_for(cell, 1, 0)
    seeds = {o.seed_for(c, w, t) for c in scenarios.cells() for w in scenarios.WORDINGS for t in range(8)}
    assert len(seeds) == 192


def test_dry_log_is_separate_from_real_log():
    assert config.DRY_LOG_PATH != config.LOG_PATH


def test_full_dry_run(tmp_path):
    path = str(tmp_path / "log.jsonl")
    s = o.run_experiment(o.stub_model, "stub", path, 8, quiet=True)
    rows = read(path)
    assert len(rows) == 192 and s["written"] == 192 and len(set(keys(rows))) == 192
    assert all(FIELDS <= set(r) for r in rows) and all(r["model"] == "stub" for r in rows)
    assert all(r["decision"] is None for r in rows if "parse_failed" in r["flags"])   # never clamped
    assert s["tags_missing"] > 0 and s["parse_failed"] > 0                             # stub exercises parser paths


def test_resume_adds_only_missing(tmp_path):
    path = str(tmp_path / "log.jsonl")
    o.run_experiment(o.stub_model, "stub", path, 2, quiet=True)
    first = open(path, encoding="utf-8").read()
    assert len(first.splitlines()) == 48
    s = o.run_experiment(o.stub_model, "stub", path, 8, quiet=True)
    assert s["skipped"] == 48 and s["written"] == 144
    assert open(path, encoding="utf-8").read().startswith(first)
    assert len(set(keys(read(path)))) == 192
    assert o.run_experiment(o.stub_model, "stub", path, 8, quiet=True)["written"] == 0


def test_resume_after_truncated_last_line(tmp_path):
    path = str(tmp_path / "log.jsonl")
    o.run_experiment(o.stub_model, "stub", path, 2, quiet=True)
    original = read(path)
    data = open(path, "rb").read()
    open(path, "wb").write(data[:-40])                      # simulate a crash mid-write
    s = o.run_experiment(o.stub_model, "stub", path, 2, quiet=True)
    assert s["unreadable_lines"] == 1 and s["written"] == 1
    rows = [r for r in read_tolerant(path)]
    assert sorted(keys(rows)) == sorted(keys(original))
    lost = original[-1]
    redone = [r for r in rows if keys([r])[0] == keys([lost])[0]][0]
    assert redone["seed"] == lost["seed"] and redone["raw_reply"] == lost["raw_reply"]


def read_tolerant(path):
    out = []
    for line in open(path, encoding="utf-8"):
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return out


def test_stub_is_deterministic(tmp_path):
    a, b = str(tmp_path / "a.jsonl"), str(tmp_path / "b.jsonl")
    o.run_experiment(o.stub_model, "stub", a, 2, quiet=True)
    o.run_experiment(o.stub_model, "stub", b, 2, quiet=True)
    assert [(r["seed"], r["raw_reply"]) for r in read(a)] == [(r["seed"], r["raw_reply"]) for r in read(b)]


def test_model_error_stops_and_leaves_clean_log(tmp_path):
    path = str(tmp_path / "log.jsonl")
    calls = {"n": 0}

    def flaky(prompt, seed):
        calls["n"] += 1
        if calls["n"] == 4:
            raise RuntimeError("model went away")
        return o.stub_model(prompt, seed)

    with pytest.raises(RuntimeError):
        o.run_experiment(flaky, "stub", path, 2, quiet=True)
    assert len(read(path)) == 3
    assert o.run_experiment(o.stub_model, "stub", path, 2, quiet=True)["written"] == 45


CALIB = ["distress|none|reciprocal", "distress|keep_all|reciprocal"]


def test_cells_filter_and_meta(tmp_path):
    path = str(tmp_path / "c.jsonl")
    s = o.run_experiment(o.stub_model, "stub", path, 4, quiet=True, cells=CALIB)
    rows = read(path)
    assert s["written"] == 24 and len(rows) == 24
    assert {r["cell"] for r in rows} == set(CALIB)
    assert all("meta" in r and r["meta"]["done_reason"] == "stub" for r in rows)
    # calibration trials are the same (cell, wording, trial) keys and seeds the full run would use
    cell = tuple(CALIB[0].split("|"))
    assert [r["seed"] for r in rows if r["cell"] == CALIB[0] and r["wording"] == 1 and r["trial"] == 0] == [o.seed_for(cell, 1, 0)]


def test_unknown_cell_rejected(tmp_path):
    with pytest.raises(ValueError):
        o.run_experiment(o.stub_model, "stub", str(tmp_path / "x.jsonl"), 1, quiet=True, cells=["nope|none|one_shot"])


def test_calibration_log_path_is_separate():
    assert len({config.LOG_PATH, config.DRY_LOG_PATH, config.CALIB_LOG_PATH}) == 3