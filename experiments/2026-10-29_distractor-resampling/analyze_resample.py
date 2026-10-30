import argparse
import configparser
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

import build_requests as br

M = br.M
HERE = Path(__file__).resolve().parent
ARMS = ["Q", "P", "M", "P1"]
CONTRASTS = [
    ("Q - P", "distractor in the question", lambda t: t["p"]["Q"] - t["p"]["P"], lambda t: True),
    ("M - P", "the written mention", lambda t: t["p"]["M"] - t["p"]["P"], lambda t: True),
    ("P - P1", "an ordinary sentence (baseline)", lambda t: t["p"]["P"] - t["p"]["P1"], lambda t: "P1" in t["p"]),
    ("(M - P) - (P - P1)", "mention beyond an ordinary sentence", lambda t: (t["p"]["M"] - t["p"]["P"]) - (t["p"]["P"] - t["p"]["P1"]), lambda t: "P1" in t["p"]),
]


def mentions(text, strict, rare):
    return any(len(br.content_words(s) & strict) >= br.MIN_SHARED or br.content_words(s) & rare for s in br.SENTENCE.findall(text or ""))


def score(rec, meta):
    answer = M.extract_answer(rec.get("content") or "")
    answered = answer is not None and rec.get("finish_reason") != "length"
    return {"correct": bool(answered and M.is_correct({"content": rec["content"], "meta": meta})), "answered": answered,
            "mention": bool(mentions(rec.get("content"), set(meta["distractor_words_strict"]), set(meta["distractor_words_rare"])))}


def load(out, requests, partial):
    meta = {r["id"]: r["meta"] for r in requests}
    rounds = []
    for d in sorted(out.glob("round_*")):
        f = d / "results.json"
        res = {r["id"]: r for r in json.load(open(f, encoding="utf-8"))} if f.exists() else {}
        complete = set(meta) <= set(res)
        rounds.append({"name": d.name, "n": len(res), "complete": complete})
        if complete or partial:
            for i, r in res.items():
                meta[i].setdefault("_samples", []).append(score(r, meta[i]))
    traces = defaultdict(lambda: {"samples": {}})
    for i, m in meta.items():
        t = traces[m["source_id"]]
        t["meta"] = m
        t["samples"][m["arm"]] = m.pop("_samples", [])
    for t in traces.values():
        t["p"] = {a: sum(s["correct"] for s in v) / len(v) for a, v in t["samples"].items() if v}
    usable = [t for t in traces.values() if all(a in t["p"] for a in t["samples"])]
    return usable, rounds


def mean(xs):
    return sum(xs) / len(xs) if xs else None


def test(values, rng, boot, perms):
    n = len(values)
    if n < 2:
        return {"n": n, "mean": mean(values), "ci95": None, "p": None}
    v = np.array(values, dtype=float)
    m = v.mean()
    bs = v[rng.integers(0, n, size=(boot, n))].mean(axis=1)
    flips = (v * rng.choice([-1.0, 1.0], size=(perms, n))).mean(axis=1)
    extreme = int((np.abs(flips) >= abs(m) - 1e-12).sum())
    lo, hi = np.quantile(bs, [0.025, 0.975])
    return {"n": n, "mean": float(m), "ci95": [float(lo), float(hi)], "p": (extreme + 1) / (perms + 1)}


def group_report(traces, rng, boot, perms):
    rep = {"n": len(traces), "accuracy": {}, "contrasts": {}, "mention_rate": {}, "unanswered": {}}
    for a in ARMS:
        ts = [t for t in traces if a in t["p"]]
        if ts:
            rep["accuracy"][a] = mean([t["p"][a] for t in ts])
            rep["mention_rate"][a] = mean([mean([s["mention"] for s in t["samples"][a]]) for t in ts])
            rep["unanswered"][a] = mean([mean([not s["answered"] for s in t["samples"][a]]) for t in ts])
    for name, _, f, keep in CONTRASTS:
        rep["contrasts"][name] = test([f(t) for t in traces if keep(t)], rng, boot, perms)
    answered = {id(t): [s for s in t["samples"]["P"] if s["answered"]] for t in traces}
    pooled = [s for v in answered.values() for s in v]
    yes, no = [s["correct"] for s in pooled if s["mention"]], [s["correct"] for s in pooled if not s["mention"]]
    both = [v for v in answered.values() if any(s["mention"] for s in v) and not all(s["mention"] for s in v)]
    rep["P_by_mention"] = {"rollouts_mentioning": len(yes), "rollouts_not": len(no), "acc_mentioning": mean(yes), "acc_not": mean(no),
                           "within_trace": test([mean([s["correct"] for s in v if s["mention"]]) - mean([s["correct"] for s in v if not s["mention"]]) for v in both], rng, boot, perms)}
    flips = [mean([s["correct"] for s in t["samples"]["P"]]) for t in traces]
    rep["noise_P"] = {"traces_always_right": sum(f == 1 for f in flips), "traces_always_wrong": sum(f == 0 for f in flips), "traces_mixed": sum(0 < f < 1 for f in flips)}
    return rep


def pct(x, signed=False):
    return "–" if x is None else (f"{100 * x:+.1f}" if signed else f"{100 * x:.1f}")


def ci(c):
    return "–" if not c["ci95"] else f"{pct(c['mean'], True)} [{pct(c['ci95'][0], True)}, {pct(c['ci95'][1], True)}]"


def markdown(report):
    md = ["# Distractor resampling results", "",
          f"Rounds used: {report['rounds_used']} ({'complete rounds only' if not report['partial'] else 'including partial rounds'}). Each trace has one sample per arm per round. Accuracy in %, averaged per trace over rounds, then over traces.", "",
          "Primary contrasts (fixed before the run): Q - P, M - P and (M - P) - (P - P1), for Hindi and for English. Everything else is exploratory.", ""]
    groups = report["groups"]
    md += ["## Accuracy by arm", "", "| group | traces | Q (no distractor) | P (before mention) | M (after mention) | P1 (one sentence earlier) |", "|---|---|---|---|---|---|"]
    for g, r in groups.items():
        md.append(f"| {g} | {r['n']} | " + " | ".join(pct(r["accuracy"].get(a)) for a in ARMS) + " |")
    md += ["", "## Contrasts (percentage points, paired by trace, bootstrap 95% CI, sign-flip permutation p)", "",
           "| group | " + " | ".join(f"{n}: {d}" for n, d, _, _ in CONTRASTS) + " |", "|---|" + "---|" * len(CONTRASTS)]
    for g, r in groups.items():
        md.append(f"| {g} | " + " | ".join(f"{ci(r['contrasts'][n])}, p={r['contrasts'][n]['p']:.3g} (n={r['contrasts'][n]['n']})" if r["contrasts"][n]["p"] is not None else "–" for n, _, _, _ in CONTRASTS) + " |")
    md += ["", "## Distractor mentioned in the continuation (% of rollouts)", "", "Q's question has no distractor, so Q's rate is the detector's false-positive rate.", "",
           "| group | Q | P | M | P1 | P, answered rollouts: accuracy when mentioning / not (n) | P, answered: within-trace difference |", "|---|---|---|---|---|---|---|"]
    for g, r in groups.items():
        b = r["P_by_mention"]
        md.append(f"| {g} | " + " | ".join(pct(r["mention_rate"].get(a)) for a in ARMS) + f" | {pct(b['acc_mentioning'])} ({b['rollouts_mentioning']}) / {pct(b['acc_not'])} ({b['rollouts_not']}) | {ci(b['within_trace'])} (n={b['within_trace']['n']}) |")
    md += ["", "## Unanswered or cut off (% of rollouts) and noise in P", "", "| group | Q | P | M | P1 | P traces always right / always wrong / mixed |", "|---|---|---|---|---|---|"]
    for g, r in groups.items():
        z = r["noise_P"]
        md.append(f"| {g} | " + " | ".join(pct(r["unanswered"].get(a)) for a in ARMS) + f" | {z['traces_always_right']} / {z['traces_always_wrong']} / {z['traces_mixed']} |")
    md += ["", "## Rounds", "", "| round | results | complete |", "|---|---|---|"] + [f"| {x['name']} | {x['n']} | {x['complete']} |" for x in report["rounds"]]
    return "\n".join(md) + "\n"


def main(args):
    cfg = configparser.ConfigParser()
    cfg.read(HERE / "config" / "resample.cfg")
    a = cfg["analysis"]
    requests = json.load(open(HERE / "outputs" / "requests_resample.json", encoding="utf-8"))
    traces, rounds = load(Path(args.output), requests, args.partial)
    rng = np.random.default_rng(a.getint("seed"))
    boot, perms = a.getint("bootstrap"), a.getint("permutations")
    lang = lambda t: t["meta"]["language"]
    groups = {}
    for name, keep in [("hi_IN", lambda t: lang(t) == "hi_IN"), ("en_US", lambda t: lang(t) == "en_US"),
                       ("hi_IN, mention in opening sentence", lambda t: lang(t) == "hi_IN" and t["meta"]["opening_mention"]),
                       ("hi_IN, mention later", lambda t: lang(t) == "hi_IN" and not t["meta"]["opening_mention"]),
                       ("en_US, mention in opening sentence", lambda t: lang(t) == "en_US" and t["meta"]["opening_mention"]),
                       ("en_US, mention later", lambda t: lang(t) == "en_US" and not t["meta"]["opening_mention"]),
                       ("hi_IN, in trace-deletion set (234)", lambda t: lang(t) == "hi_IN" and t["meta"]["in_trace_deletion"])]:
        ts = [t for t in traces if keep(t)]
        if ts:
            groups[name] = group_report(ts, rng, boot, perms)
    for key in ["task", "difficulty"]:
        for v in sorted({t["meta"][key] for t in traces}):
            ts = [t for t in traces if lang(t) == "hi_IN" and t["meta"][key] == v]
            if ts:
                groups[f"hi_IN, {key} {v} (exploratory)"] = group_report(ts, rng, boot, perms)
    report = {"rounds": rounds, "rounds_used": sum(r["complete"] or args.partial for r in rounds), "partial": args.partial, "traces": len(traces), "groups": groups}
    out = Path(args.output)
    json.dump(report, open(out / "analysis.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    text = markdown(report)
    open(out / "analysis.md", "w", encoding="utf-8").write(text)
    print(text)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default=str(HERE / "outputs" / "resample"))
    ap.add_argument("--partial", action="store_true")
    main(ap.parse_args())
