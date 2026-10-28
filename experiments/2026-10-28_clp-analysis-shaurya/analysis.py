import json
import sys
from pathlib import Path

import pandas as pd
from scipy.stats import binomtest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))

import metrics as M

BASELINES = [ROOT / "experiments" / p / "results.json" for p in [
    "2026-10-17_run-short-leftover-rahul/outputs",
    "2026-10-17_run-medium-leftover-rahul/output",
    "2026-10-16_finish-run-long-adi/outputs/long",
    "2026-10-18_run-very-long-leftover-aayush/output",
    "2026-10-18-very_very_long-aayush/output",
]]
CLP = ROOT / "experiments" / "2026-10-28_run-clp-shaurya" / "outputs"
DIFFS = ["short", "medium", "long", "very_long", "very_very_long"]
N = 50
OUT = HERE / "outputs"
OUT.mkdir(exist_ok=True)

keep = set()
for d in DIFFS:
    for path in (ROOT / "Dataset" / d).glob("*.json"):
        task, lang = path.stem.rsplit("_", 2)[0], "_".join(path.stem.rsplit("_", 2)[1:])
        keep |= {(d, task, lang, qid) for qid in list(json.load(open(path, encoding="utf-8")))[:N]}

records = [r for p in BASELINES for r in json.load(open(p, encoding="utf-8"))]
for d in DIFFS:
    records += json.load(open(CLP / d / "results.json", encoding="utf-8"))

rows = []
for r in records:
    m = r["meta"]
    if (m["difficulty"], m["task"], m["language"], m["question_id"]) not in keep:
        continue
    answer = M.extract_answer(r["content"])
    target, total = M.target_words(r)
    hindi = total - target if m["language"] == "en_US" else target
    rows.append({
        "cell": f"{m['language'][:2]}/{r['condition']}",
        "qid": f"{m['difficulty']}/{m['task']}/{m['question_id']}",
        "difficulty": m["difficulty"],
        "task": m["task"],
        "insertion": m["insertion"],
        "scored": answer is not None,
        "correct": answer is not None and M.is_correct(r),
        "cutoff": r["finish_reason"] == "length",
        "completion_tokens": r["usage"].get("completion_tokens"),
        "english_ratio": (total - hindi) / total if total else None,
    })
df = pd.DataFrame(rows)
df.to_csv(OUT / "responses.csv", index=False)
CELLS = ["en/direct", "en/cot", "hi/direct", "hi/cot", "hi/clp"]


matched = df.groupby(["qid", "insertion"])["cell"].transform("nunique") == len(CELLS)


def table(by):
    t = df[matched].groupby(by + ["cell"]).agg(acc=("correct", "mean")).unstack("cell")["acc"][CELLS] * 100
    return t.round(1)


def mcnemar(a, b):
    w = df[df["cell"].isin([a, b])].pivot_table(index=["qid", "insertion"], columns="cell", values="correct").dropna()
    x, y = int((w[a] > w[b]).sum()), int((w[a] < w[b]).sum())
    return {"pair": f"{a} vs {b}", "n": len(w), "acc_a": round(100 * w[a].mean(), 1), "acc_b": round(100 * w[b].mean(), 1),
            "a_only": x, "b_only": y, "p": binomtest(x, x + y).pvalue if x + y else 1.0}


summary = {
    "responses": df.groupby("cell").size()[CELLS].to_dict(),
    "accuracy_strict": (df.groupby("cell")["correct"].mean()[CELLS] * 100).round(1).to_dict(),
    "accuracy_scored": (df[df["scored"]].groupby("cell")["correct"].mean()[CELLS] * 100).round(1).to_dict(),
    "unscored_pct": ((1 - df.groupby("cell")["scored"].mean()[CELLS]) * 100).round(2).to_dict(),
    "completion_tokens_mean": df.groupby("cell")["completion_tokens"].mean()[CELLS].round(0).to_dict(),
    "english_ratio_mean": df.groupby("cell")["english_ratio"].mean()[CELLS].round(3).to_dict(),
    "mcnemar": [mcnemar(a, b) for a, b in [("hi/clp", "hi/cot"), ("hi/clp", "hi/direct"), ("hi/clp", "en/cot")]],
}
with open(OUT / "summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)
for name, by in [("by_difficulty", ["difficulty"]), ("by_task", ["task"]), ("by_insertion", ["insertion"])]:
    t = table(by)
    t.to_csv(OUT / f"{name}.csv")
    print(t.reindex(DIFFS) if name == "by_difficulty" else t, "\n")
print(json.dumps(summary, indent=2, ensure_ascii=False))
