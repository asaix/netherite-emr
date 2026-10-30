import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from cube_sweep import OUT, load
from cube_variants import KEY, META, QUESTION

DIFFS = ["short", "medium", "long", "very_long", "very_very_long"]
VIEWS = ["full", "no_answer", "core", "ops", "ops_no_answer", "ops_core"]


def core_count(seq):
    return sum(t.split(" ")[0] not in META for t in seq)


def paired_ci(d):
    d = np.asarray(d, float)
    se = d.std(ddof=1) / np.sqrt(len(d))
    return round(d.mean(), 3), round(d.mean() - 1.96 * se, 3), round(d.mean() + 1.96 * se, 3), len(d)


if __name__ == "__main__":
    pd.set_option("display.width", 220, "display.max_columns", 40, "display.max_rows", 500)
    variants = pd.read_pickle(OUT / "variants.pkl")
    variants["question_id"] = variants.question_id.astype(int)
    frame = load()
    frame["question_id"] = frame.question_id.astype(int)
    std = frame[frame.set.eq("standard")].copy()
    std = std.merge(variants[variants.set.eq("standard") & variants.kind.eq("en_hi_same_q")][KEY + VIEWS], on=KEY)
    std["en"] = std.en_seq.map(json.loads)
    std["hi"] = std.hi_seq.map(json.loads)
    std["en_core"] = std.en.map(core_count)
    std["hi_core"] = std.hi.map(core_count)

    print("=== 1. all-correct baseline: same question, none vs distractor, all four traces right")
    wide = std.pivot_table(index=QUESTION, columns="insertion", values=["en_correct", "hi_correct"], observed=True)
    rows = []
    for ins in ["similar_insertion", "dissimilar_insertion"]:
        ok = wide[(wide["en_correct"]["no_insertion"].eq(1)) & wide["en_correct"][ins].eq(1) & wide["hi_correct"]["no_insertion"].eq(1) & wide["hi_correct"][ins].eq(1)].index
        v = variants[variants.set.eq("standard")]
        for kind in ["en_self", "hi_self"]:
            sub = v[v.kind.eq(kind) & v.insertion.eq(ins)].set_index(QUESTION).reindex(ok)
            rows.append({"insertion": ins, "kind": kind, "n": len(ok), **sub[VIEWS].mean().to_dict()})
        same = std.set_index(QUESTION)
        for use in ["no_insertion", ins]:
            sub = same[same.insertion.eq(use)].reindex(ok)
            rows.append({"insertion": ins, "kind": f"en_hi@{use}", "n": len(ok), **sub[VIEWS].mean().to_dict()})
    table = pd.DataFrame(rows)
    table.to_csv(OUT / "all_correct_baseline.csv", index=False)
    print(table.round(3).to_string(index=False))

    print("\n=== 2. flip test on stripped tokens: hi self distance (none vs distractor), en right throughout")
    v = variants[variants.set.eq("standard")]
    rows = []
    for ins in ["similar_insertion", "dissimilar_insertion"]:
        base = wide[wide["en_correct"]["no_insertion"].eq(1) & wide["en_correct"][ins].eq(1) & wide["hi_correct"]["no_insertion"].eq(1)]
        for label, ix in {"flips": base[base["hi_correct"][ins].eq(0)].index, "stays": base[base["hi_correct"][ins].eq(1)].index}.items():
            sub = v[v.kind.eq("hi_self") & v.insertion.eq(ins)].set_index(QUESTION).reindex(ix)
            rows.append({"insertion": ins, "group": label, "n": len(ix), **sub[VIEWS].mean().round(3).to_dict()})
    print(pd.DataFrame(rows).to_string(index=False))

    print("\n=== 3. same-question en-only minus both-correct on step types, by task")
    rows = []
    d = std[std.outcome.isin(["both correct", "en only"])]
    for task, g in d.groupby("task"):
        row = {"task": task}
        for view in ["full", "no_answer", "ops_no_answer"]:
            w = g.pivot_table(index=QUESTION, columns="outcome", values=view, observed=True).dropna()
            row[view] = paired_ci(w["en only"] - w["both correct"])
        rows.append(row)
    table = pd.DataFrame(rows)
    table.to_csv(OUT / "same_question_by_task.csv", index=False)
    print(table.to_string(index=False))

    print("\n=== 4. trace length vs difficulty (median tokens / computational steps), per task")
    rows = []
    for (task, diff), g in std.groupby(["task", "difficulty"], observed=True):
        rows.append({"task": task, "difficulty": diff, "en_med": g.en_len.median(), "hi_med": g.hi_len.median(), "en_core": g.en_core.median(), "hi_core": g.hi_core.median(),
                     "en_acc": g.en_correct.mean(), "hi_acc": g.hi_correct.mean()})
    lengths = pd.DataFrame(rows)
    lengths.to_csv(OUT / "length_by_difficulty.csv", index=False)
    for col in ["en_core", "hi_core"]:
        print(col, "\n", lengths.pivot(index="task", columns="difficulty", values=col).reindex(columns=DIFFS).to_string())
    print("overall median core by difficulty", std.groupby("difficulty", observed=True)[["en_core", "hi_core"]].median().reindex(DIFFS).to_dict())
    print("overall mean core by difficulty", std.groupby("difficulty", observed=True)[["en_core", "hi_core"]].mean().reindex(DIFFS).round(2).to_dict())

    print("\n=== 5. date arithmetic: hi computational steps by hi right vs wrong")
    for task in ["date_subtraction", "date_addition", "date_recurrence", "time_duration"]:
        g = std[std.task.eq(task) & std.hi_correct.notna()]
        t = g.groupby(["difficulty", "hi_correct"], observed=True).agg(n=("hi_core", "size"), hi_core=("hi_core", "median"), en_core=("en_core", "median"), hi_mean=("hi_core", "mean")).unstack()
        print(task, "\n", t.reindex(DIFFS).round(1).to_string())
        by = g.assign(steps=pd.cut(g.hi_core, [-1, 3, 6, 10, 20, 10000])).groupby("steps", observed=True).hi_correct.agg(["size", "mean"]).round(3)
        print(by.to_string())

    print("\n=== 6. IGNORE tokens per trace by language and insertion")
    print(std.assign(en_i=std.en.map(lambda s: sum(t == "IGNORE" for t in s)), hi_i=std.hi.map(lambda s: sum(t == "IGNORE" for t in s))).groupby("insertion")[["en_i", "hi_i"]].agg(["mean", lambda c: (c > 0).mean()]).round(3).to_string())

    print("\n=== 7. both-correct RDS by difficulty (does RDS rise without failure?)")
    print(std[std.outcome.eq("both correct")].pivot_table(index="task", columns="difficulty", values="ops_no_answer", observed=True).reindex(columns=DIFFS).round(3).to_string())
    print(std[std.outcome.eq("both correct")].pivot_table(index="task", columns="difficulty", values="full", observed=True).reindex(columns=DIFFS).round(3).to_string())
    print(std[std.outcome.eq("both correct")].groupby("difficulty", observed=True)[VIEWS + ["ed_floor"]].mean().reindex(DIFFS).round(3).to_string())

    print("\n=== 8. date_subtraction very_very_long samples")
    g = std[std.task.eq("date_subtraction") & std.difficulty.eq("very_very_long") & std.insertion.eq("no_insertion") & std.en_correct.eq(1)]
    for label, sample in {"hi wrong": g[g.hi_correct.eq(0)].head(4), "hi right": g[g.hi_correct.eq(1)].head(3)}.items():
        for _, r in sample.iterrows():
            print(f"-- {label} q{r.question_id} rds {r.full:.3f} ops {r.ops_no_answer:.3f}\nEN {r.en[:40]}\nHI {r.hi[:40]}")
