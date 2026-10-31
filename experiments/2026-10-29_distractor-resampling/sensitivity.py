import configparser
import json
from pathlib import Path

import numpy as np

import analyze_resample as A

HERE = Path(__file__).resolve().parent
LOOP_TAILS = (60, 150, 300)


def loops(text):
    text = text or ""
    return any(text.count(text[-n:]) >= 3 for n in LOOP_TAILS)


def ci(values, rng, boot):
    v = np.array(values, dtype=float)
    bs = v[rng.integers(0, len(v), size=(boot, len(v)))].mean(axis=1)
    return {"n": len(v), "mean": float(v.mean()), "ci95": [float(x) for x in np.quantile(bs, [0.025, 0.975])]}


cfg = configparser.ConfigParser()
cfg.read(HERE / "config" / "resample.cfg")
rng = np.random.default_rng(cfg["analysis"].getint("seed"))
boot = cfg["analysis"].getint("bootstrap")
requests = json.load(open(HERE / "outputs" / "requests_resample.json", encoding="utf-8"))
meta = {r["id"]: r["meta"] for r in requests}
out = HERE / "outputs" / "resample"
results = [r for d in sorted(out.glob("round_*")) for r in json.load(open(d / "results.json", encoding="utf-8"))]

report = {"rounds": len(list(out.glob("round_*"))), "continuations": len(results)}
cut = [r for r in results if r.get("finish_reason") == "length"]
report["cut_off"] = len(cut)
report["unanswered_not_cut_off"] = sum(not A.score(r, meta[r["id"]])["answered"] and r.get("finish_reason") != "length" for r in results)
for lang in ("hi_IN", "en_US"):
    c = [r for r in cut if meta[r["id"]]["language"] == lang]
    report[f"cut_off_loops/{lang}"] = {"cut_off": len(c), "exact_loop": sum(loops(r["content"]) for r in c)}
tokens = np.array([(r.get("usage") or {}).get("completion_tokens") or 0 for r in results if A.score(r, meta[r["id"]])["answered"]])
report["answered_tokens"] = {"n": int(len(tokens)), "p50": float(np.percentile(tokens, 50)), "p99": float(np.percentile(tokens, 99)),
                             "share_above_3500": float((tokens > 3500).mean())}
per_round = {}
for d in sorted(out.glob("round_*")):
    rr = json.load(open(d / "results.json", encoding="utf-8"))
    per_round[d.name] = sum(r.get("finish_reason") == "length" for r in rr) / len(rr)
report["cut_off_share_per_round"] = per_round

traces = {}
for r in results:
    m = meta[r["id"]]
    t = traces.setdefault(m["source_id"], {"meta": m, "arms": {}})
    t["arms"].setdefault(m["arm"], []).append(A.score(r, m))
answered_acc = lambda xs: np.mean([x["correct"] for x in xs if x["answered"]]) if any(x["answered"] for x in xs) else None
groups = {"hi_IN": lambda m: m["language"] == "hi_IN", "hi_IN, opening": lambda m: m["language"] == "hi_IN" and m["opening_mention"],
          "hi_IN, later": lambda m: m["language"] == "hi_IN" and not m["opening_mention"], "en_US": lambda m: m["language"] == "en_US",
          "en_US, opening": lambda m: m["language"] == "en_US" and m["opening_mention"], "en_US, later": lambda m: m["language"] == "en_US" and not m["opening_mention"]}
for name, keep in groups.items():
    ts = [t for t in traces.values() if keep(t["meta"])]
    for a, b in (("Q", "P"), ("M", "P")):
        diffs = [answered_acc(t["arms"][a]) - answered_acc(t["arms"][b]) for t in ts
                 if answered_acc(t["arms"][a]) is not None and answered_acc(t["arms"][b]) is not None]
        report[f"answered_only/{name}/{a} - {b}"] = ci(diffs, rng, boot)

json.dump(report, open(out / "sensitivity.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print(json.dumps(report, indent=2))
