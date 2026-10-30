import json

import matplotlib

matplotlib.use("agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import binomtest
from statsmodels.stats.contingency_tables import StratifiedTable
from statsmodels.stats.multitest import multipletests

import temporal_answers as T
from temporal_answers import HERE, TOKEN, content_words, distractor_texts, normalise, qid, question_key, question_texts, reasoning_body

M = T.use_parser("current")
DATA = HERE / "outputs" / "data"
OUT = HERE / "outputs" / "report"
OUT.mkdir(parents=True, exist_ok=True)
B = 2000
RNG = np.random.default_rng(0)
TASKS = ["date_addition", "date_subtraction", "date_duration", "date_recurrence", "day_of_week",
         "interval_date", "time_addition", "time_subtraction", "time_duration"]
DIFFS = ["short", "medium", "long", "very_long", "very_very_long"]
CONDS = ["English direct", "English CoT", "Hindi direct", "Hindi CoT", "Hindi CLP", "Hindi en-cot"]

encot = pd.read_pickle(DATA / "responses_encot_current.pkl")
standard = pd.read_pickle(DATA / "responses_current.pkl")
qids = set(encot["qid"])
standard = standard[standard["qid"].isin(qids)]


def label(frame, lang, cond, name):
    sub = frame[(frame["language"] == lang) & (frame["condition"] == cond)].copy()
    sub["cond"] = name
    return sub


clp_rows = []
for d in DIFFS:
    for r in json.load(open(HERE.parents[1] / "responses" / "clp" / f"{d}.json", encoding="utf-8")):
        rec = {"content": r["stage2"]["content"], "meta": r["meta"]}
        answer = M.extract_answer(rec["content"])
        m = r["meta"]
        clp_rows.append({"qid": f"{m['difficulty']}/{m['task']}/{m['question_id']}", "difficulty": m["difficulty"], "task": m["task"],
                         "insertion": m["insertion"], "scored": answer is not None,
                         "correct": answer is not None and M.is_correct(rec), "cond": "Hindi CLP"})
clp = pd.DataFrame(clp_rows)
clp = clp[clp["qid"].isin(qids)]

df = pd.concat([label(standard, "en_US", "direct", "English direct"), label(standard, "en_US", "cot", "English CoT"),
                label(standard, "hi_IN", "direct", "Hindi direct"), label(standard, "hi_IN", "cot", "Hindi CoT"),
                clp, label(encot, "hi_IN", "cot", "Hindi en-cot")], ignore_index=True)
df["correct"] = df["correct"].astype(float)
qlist = sorted(qids)
df["qi"] = df["qid"].map({q: i for i, q in enumerate(qlist)})
Q = len(qlist)
WEIGHTS = np.stack([np.bincount(RNG.integers(0, Q, Q), minlength=Q) for _ in range(B)])
n = {"questions": Q, "responses": df.groupby("cond").size().to_dict()}


def sel(**kw):
    mask = np.ones(len(df), dtype=bool)
    for k, v in kw.items():
        mask &= (df[k] == v).to_numpy()
    return mask


def counts(mask):
    sub = df[mask & df["scored"].to_numpy()]
    return (np.bincount(sub["qi"], weights=sub["correct"], minlength=Q),
            np.bincount(sub["qi"], minlength=Q).astype(float))


def acc(mask):
    c, k = counts(mask)
    return c.sum() / k.sum()


def boot(mask):
    c, k = counts(mask)
    return (WEIGHTS @ c) / (WEIGHTS @ k)


def ci(samples):
    lo, hi = np.percentile(samples, [2.5, 97.5])
    return [round(100 * lo, 1), round(100 * hi, 1)]


def mcnemar(a, b, mask=True):
    sub = df[mask & df["scored"].to_numpy() & df["cond"].isin([a, b]).to_numpy()]
    w = sub.pivot_table(index=["qid", "insertion"], columns="cond", values="correct").dropna()
    x, y = int((w[a] > w[b]).sum()), int((w[a] < w[b]).sum())
    return x, y, binomtest(x, x + y).pvalue if x + y else 1.0


# 1. accuracy by task, with paired tests against Hindi CoT and Hindi direct
rows, tests = [], {}
for task in TASKS + ["all"]:
    base = sel(task=task) if task != "all" else np.ones(len(df), dtype=bool)
    row = {"task": task, **{c: round(100 * acc(base & sel(cond=c)), 1) for c in CONDS}}
    for ref in ("Hindi CoT", "Hindi direct", "Hindi CLP"):
        x, y, p = mcnemar("Hindi en-cot", ref, base)
        row[f"vs {ref}"] = round(100 * (acc(base & sel(cond="Hindi en-cot")) - acc(base & sel(cond=ref))), 1)
        tests.setdefault(ref, []).append(p)
        row[f"only en-cot / only {ref}"] = f"{x} / {y}"
    rows.append(row)
for ref, ps in tests.items():
    holm = multipletests(ps[:-1], method="holm")[1].tolist() + [ps[-1]]
    for row, p in zip(rows, holm):
        row[f"p vs {ref}"] = p
by_task = pd.DataFrame(rows)
by_task.to_csv(OUT / "accuracy_by_task.csv", index=False)
everything = np.ones(len(df), dtype=bool)
n["overall_ci"] = {f"en-cot - {ref}": ci(boot(sel(cond="Hindi en-cot")) - boot(sel(cond=ref)))
                   for ref in ("Hindi CoT", "Hindi direct", "Hindi CLP", "English CoT")}
n["unanswered"] = {c: int((~df[sel(cond=c)]["scored"]).sum()) for c in CONDS}
n["strict_accuracy"] = {c: round(100 * df[sel(cond=c)]["correct"].fillna(0).mean(), 1) for c in CONDS}

# 2. accuracy by difficulty and the gap to English CoT
rows = []
for d in DIFFS:
    base = sel(difficulty=d)
    row = {"difficulty": d, **{c: round(100 * acc(base & sel(cond=c)), 1) for c in CONDS}}
    for c in ("Hindi CoT", "Hindi en-cot"):
        gap = boot(base & sel(cond="English CoT")) - boot(base & sel(cond=c))
        row[f"En CoT - {c}"] = round(100 * (acc(base & sel(cond="English CoT")) - acc(base & sel(cond=c))), 1)
        row[f"En CoT - {c} CI"] = ci(gap)
    row["ci"] = {c: ci(boot(base & sel(cond=c))) for c in CONDS}
    rows.append(row)
by_diff = pd.DataFrame(rows)
by_diff.drop(columns=["ci"]).to_csv(OUT / "accuracy_by_difficulty.csv", index=False)

# 3. distractors: accuracy without and with each distractor
rows = []
for c in CONDS:
    base = sel(cond=c)
    row = {"cond": c}
    for ins in ("no_insertion", "similar_insertion", "dissimilar_insertion"):
        row[ins] = round(100 * acc(base & sel(insertion=ins)), 1)
    for ins in ("similar_insertion", "dissimilar_insertion"):
        drop = boot(base & sel(insertion="no_insertion")) - boot(base & sel(insertion=ins))
        row[f"drop {ins}"] = round(100 * (acc(base & sel(insertion="no_insertion")) - acc(base & sel(insertion=ins))), 1)
        row[f"drop {ins} CI"] = ci(drop)
    rows.append(row)
distractors = pd.DataFrame(rows)
distractors.to_csv(OUT / "distractors.csv", index=False)

# 4. distractor mentions; for en-cot the words of the matching English distractor also count
records, _ = T.load_records("en_cot")
dtexts, qtexts = distractor_texts(records), question_texts(records)
mention = {}
for r in records:
    m = r["meta"]
    if m["language"] != "hi_IN" or r["condition"] != "cot":
        continue
    hi, en = question_key(r), (m["difficulty"], m["task"], "en_US", m["question_id"])
    tokens = set(TOKEN.findall(normalise(reasoning_body(r)).casefold()))
    for ins in ("similar_insertion", "dissimilar_insertion"):
        if m["insertion"] not in ("no_insertion", ins):
            continue
        words = (content_words(dtexts[hi, ins]) | content_words(dtexts[en, ins])) - content_words(qtexts[hi]) - content_words(qtexts[en])
        if words:
            mention[r["id"], ins] = bool(words & tokens)
en_rows = df["cond"] == "Hindi en-cot"
for ins in ("similar", "dissimilar"):
    df.loc[en_rows, f"mentions_{ins}"] = [mention.get((i, f"{ins}_insertion")) for i in df.loc[en_rows, "id"]]


def mantel_haenszel(sub):
    tables = []
    for _, g in sub.groupby(["task", "difficulty"]):
        e, c = g["m"].astype(bool), g["correct"] == 1
        t = np.array([[(e & c).sum(), (e & ~c).sum()], [(~e & c).sum(), (~e & ~c).sum()]], dtype=float)
        if t[0].sum() and t[1].sum():
            tables.append(t)
    st = StratifiedTable(tables)
    lo, hi = st.oddsratio_pooled_confint()
    return [round(float(st.oddsratio_pooled), 2), round(float(lo), 2), round(float(hi), 2)]


rows = []
for c in ("English CoT", "Hindi CoT", "Hindi en-cot"):
    row = {"cond": c}
    for ins in ("similar", "dissimilar"):
        g = df[(df["cond"] == c) & df["scored"]]
        hit = g[g["insertion"] == f"{ins}_insertion"].dropna(subset=[f"mentions_{ins}"])
        plc = g[g["insertion"] == "no_insertion"].dropna(subset=[f"mentions_{ins}"])
        row[f"mention {ins}"] = round(100 * hit[f"mentions_{ins}"].astype(bool).mean(), 1)
        row[f"placebo {ins}"] = round(100 * plc[f"mentions_{ins}"].astype(bool).mean(), 1)
        row[f"OR {ins}"] = mantel_haenszel(hit.assign(m=hit[f"mentions_{ins}"]))
    rows.append(row)
mentions = pd.DataFrame(rows)
mentions.to_csv(OUT / "mentions.csv", index=False)

# 5. agreement with English CoT, and the error profile
rows = []
for c in ("Hindi direct", "Hindi CoT", "Hindi en-cot"):
    ref = "English direct" if c == "Hindi direct" else "English CoT"
    sub = df[df["cond"].isin([c, ref]) & df["scored"]]
    w = sub.pivot_table(index=["qid", "insertion", "task", "difficulty"], columns="cond", values="correct").dropna().reset_index()
    phis = []
    for _, g in w.groupby(["task", "difficulty"]):
        a, b = g[ref], g[c]
        if a.std() > 0 and b.std() > 0:
            phis.append(np.corrcoef(a, b)[0, 1])
    rows.append({"cond": c, "vs": ref, "pairs": len(w), "both right": int(((w[ref] == 1) & (w[c] == 1)).sum()),
                 "both wrong": int(((w[ref] == 0) & (w[c] == 0)).sum()), "only English": int(((w[ref] == 1) & (w[c] == 0)).sum()),
                 "only Hindi": int(((w[ref] == 0) & (w[c] == 1)).sum()), "median phi": round(float(np.median(phis)), 2),
                 "IQR": [round(float(x), 2) for x in np.percentile(phis, [25, 75])], "cells": len(phis)})
agreement = pd.DataFrame(rows)
agreement.to_csv(OUT / "agreement.csv", index=False)

profile = {}
for c in ("English CoT", "Hindi CoT", "Hindi en-cot"):
    g = df[(df["cond"] == c) & df["scored"] & (df["correct"] == 0)]
    dow = df[(df["cond"] == c) & (df["task"] == "day_of_week") & df["weekday_offset"].notna()]
    rec = df[(df["cond"] == c) & (df["task"] == "date_recurrence") & df["recurrence_pattern"].notna()]
    profile[c] = {"off_by_one_share_of_wrong": round(100 * (g["error_type"] == "off_by_one").mean(), 1),
                  "dow_one_day_late": round(100 * (dow["weekday_offset"] == 1).mean(), 1),
                  "recurrence_backwards": round(100 * (rec["recurrence_pattern"] == "mirror").mean(), 1),
                  "median_completion_tokens": float(df[(df["cond"] == c) & df["scored"]]["completion_tokens"].median()),
                  "verification": round(100 * df[(df["cond"] == c) & df["scored"]]["verification"].mean(), 1)}
encot_words = df[(df["cond"] == "Hindi en-cot") & (df["words"] > 0)]
profile["Hindi en-cot"]["english_word_share"] = round(1 - float((encot_words["target_words"] / encot_words["words"]).mean()), 3)
n["profile"] = profile

with open(OUT / "numbers.json", "w", encoding="utf-8") as f:
    json.dump({**n, "by_task": by_task.to_dict(orient="records"), "by_difficulty": by_diff.to_dict(orient="records"),
               "distractors": distractors.to_dict(orient="records"), "mentions": mentions.to_dict(orient="records"),
               "agreement": agreement.to_dict(orient="records")}, f, indent=2, ensure_ascii=False, default=str)

# figures
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
style = {"English CoT": ("#555555", "s", "-"), "Hindi direct": ("#bbbbbb", "o", "--"), "Hindi CoT": ("#e07b39", "o", "-"),
         "Hindi CLP": ("#8c6bb1", "^", "-"), "Hindi en-cot": ("#1f77b4", "D", "-")}
fig, ax = plt.subplots(figsize=(7, 4.2))
x = np.arange(len(DIFFS))
for c, (color, marker, ls) in style.items():
    y = by_diff[c].to_numpy()
    err = np.array([[v - lo, hi - v] for v, (lo, hi) in zip(y, (r[c] for r in by_diff["ci"]))]).T
    ax.errorbar(x, y, yerr=err, color=color, marker=marker, ls=ls, lw=2 if c == "Hindi en-cot" else 1.4, capsize=3, label=c)
ax.set_xticks(x, ["Short", "Medium", "Long", "Very long", "Very very long"])
ax.set_ylabel("Accuracy (%)")
ax.set_ylim(0, 100)
ax.legend(frameon=False, ncol=3, loc="lower left", fontsize=9)
fig.tight_layout()
fig.savefig(OUT / "fig1_accuracy_by_difficulty.png", dpi=200)

fig, ax = plt.subplots(figsize=(8, 4.2))
names = ["Date add.", "Date sub.", "Date dur.", "Recurrence", "Day of week", "Interval", "Time add.", "Time sub.", "Time dur."]
w = 0.2
for i, (c, color) in enumerate([("Hindi CoT", "#e07b39"), ("Hindi CLP", "#8c6bb1"), ("Hindi en-cot", "#1f77b4"), ("English CoT", "#555555")]):
    ax.bar(np.arange(9) + (i - 1.5) * w, by_task[c][:9], w, color=color, label=c)
ax.set_xticks(np.arange(9), names, rotation=20)
ax.set_ylabel("Accuracy (%)")
ax.set_ylim(0, 100)
ax.legend(frameon=False, ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.12), fontsize=9)
fig.tight_layout()
fig.savefig(OUT / "fig2_accuracy_by_task.png", dpi=200)

print(by_task.to_string())
print(by_diff.drop(columns=["ci"]).to_string())
print(distractors.to_string())
print(mentions.to_string())
print(agreement.to_string())
print(json.dumps({k: n[k] for k in ("overall_ci", "unanswered", "strict_accuracy", "profile")}, indent=1))
