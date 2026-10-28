"""Run the sharing game. Resumable: any (cell, wording, trial) already in the log is skipped.
Usage:  python orchestrator.py --dry-run          (stub model, writes to config.DRY_LOG_PATH)
        python orchestrator.py [--trials N]       (Ollama, writes to config.LOG_PATH)
Options: --cells "a|b|c" ...  restrict to named cells (quote them in PowerShell); --log-path P  override the log file."""
import argparse
import hashlib
import json
import os
import urllib.request
from datetime import datetime, timezone

import config
import scenarios
from parser import parse_reply


def seed_for(cell, wording, trial):
    key = f"{config.BASE_SEED}|{scenarios.cell_id(cell)}|{wording}|{trial}"
    return int.from_bytes(hashlib.sha256(key.encode()).digest()[:4], "big") & 0x7FFFFFFF


META_STUB = {"done_reason": "stub", "eval_count": None, "total_duration_s": None}


def stub_model(prompt, seed):
    """Deterministic FAKE replies, independent of the scenario. Occasionally malformed so parser paths are exercised."""
    h = int.from_bytes(hashlib.sha256(f"{seed}|{prompt}".encode()).digest()[:4], "big")
    n, kind = h % 11, (h >> 8) % 20
    if kind == 0:
        return f"I will give {n} units.", META_STUB            # tags missing
    if kind == 1:
        return "Stub reasoning sentence.\n[DECISION]\n11", META_STUB    # out of range
    return f"Stub reasoning sentence.\n[DECISION]\n{n}", META_STUB

def ollama_model(prompt, seed):
    body = json.dumps({
        "model": config.MODEL, "prompt": prompt, "stream": False,
        "options": {"num_ctx": config.NUM_CTX, "num_predict": config.NUM_PREDICT,
                    "temperature": config.TEMPERATURE, "seed": seed},
    }).encode()
    req = urllib.request.Request(config.OLLAMA_HOST + "/api/generate", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        d = json.load(r)
    meta = {"done_reason": d.get("done_reason"), "eval_count": d.get("eval_count"),
            "total_duration_s": round(d.get("total_duration", 0) / 1e9, 2)}
    return d["response"], meta


def load_done(log_path):
    """Return (set of (cell_id, wording, trial) already logged, number of unreadable lines)."""
    done, bad = set(), 0
    if os.path.exists(log_path):
        with open(log_path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    r = json.loads(line)
                    done.add((r["cell"], r["wording"], r["trial"]))
                except (json.JSONDecodeError, KeyError):
                    bad += 1
    return done, bad


def _needs_newline(path):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return False
    with open(path, "rb") as f:
        f.seek(-1, os.SEEK_END)
        return f.read(1) != b"\n"


def run_experiment(model_fn, model_name, log_path, trials, quiet=False, cells=None):
    all_cells = scenarios.cells()
    if cells is None:
        cell_list = all_cells
    else:
        cell_list = [tuple(c.split("|")) for c in cells]
        unknown = [c for c in cell_list if c not in all_cells]
        if unknown:
            raise ValueError(f"unknown cell(s): {['|'.join(u) for u in unknown]}")
    done, bad = load_done(log_path)
    os.makedirs(os.path.dirname(log_path) or ".", exist_ok=True)
    fix_newline = _needs_newline(log_path)
    run_id = "run-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    stats = {"run_id": run_id, "written": 0, "skipped": 0, "parse_failed": 0,
             "tags_missing": 0, "unreadable_lines": bad}
    with open(log_path, "a", encoding="utf-8") as f:
        if fix_newline:
            f.write("\n")
        for trial in range(trials):                      # trial-major, so any prefix is balanced across cells
            for cell in cell_list:
                cid = scenarios.cell_id(cell)
                for w in scenarios.WORDINGS:
                    if (cid, w, trial) in done:
                        stats["skipped"] += 1
                        continue
                    prompt = scenarios.build_prompt(cell, w)
                    seed = seed_for(cell, w, trial)
                    reply, meta = model_fn(prompt, seed)       # an exception stops the run; nothing partial is logged
                    p = parse_reply(reply)
                    record = {
                        "run_id": run_id, "base_seed": config.BASE_SEED,
                        "cell": cid,
                        "levels": dict(zip(("suffering", "authority", "strategy"), cell)),
                        "wording": w, "trial": trial, "seed": seed, "model": model_name,
                        "prompt": prompt, "raw_reply": reply, "meta": meta,
                        "decision": p["decision"], "flags": p["flags"], "parse_error": p["parse_error"],
                        "reason": p["reason"],
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "provenance": {
                            "prompt": "scenarios.py",
                            "raw_reply": f"generated by {model_name}" + (" (deterministic fake, not a real model)" if model_name == "stub" else ""),
                            "reason": "text before the last [DECISION] tag, extracted by parser.py from raw_reply",
                        },
                    }
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                    f.flush()
                    os.fsync(f.fileno())
                    stats["written"] += 1
                    stats["parse_failed"] += "parse_failed" in p["flags"]
                    stats["tags_missing"] += "tags_missing" in p["flags"]
                    if not quiet:
                        print(f"[{stats['written']}] {cid} w{w} t{trial} seed={seed} -> {p['decision']} {p['flags']}")
    return stats


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="use the deterministic stub, log to DRY_LOG_PATH")
    ap.add_argument("--trials", type=int, default=config.TOTAL_TRIALS)
    ap.add_argument("--model", default=config.MODEL)
    ap.add_argument("--cells", nargs="+", help='cell ids such as "distress|none|reciprocal"')
    ap.add_argument("--log-path", default=None)
    a = ap.parse_args()
    if a.dry_run:
        s = run_experiment(stub_model, "stub", a.log_path or config.DRY_LOG_PATH, a.trials, cells=a.cells)
    else:
        config.MODEL = a.model
        s = run_experiment(ollama_model, a.model, a.log_path or config.LOG_PATH, a.trials, cells=a.cells)
    print("SUMMARY (this run):", s)