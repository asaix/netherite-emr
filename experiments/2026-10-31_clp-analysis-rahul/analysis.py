import json
from pathlib import Path

import matplotlib

matplotlib.use("pdf")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import binomtest, fisher_exact
from statsmodels.stats.contingency_tables import StratifiedTable
from statsmodels.stats.multitest import multipletests

HERE = Path(__file__).resolve().parent
OUT = HERE / "outputs"
FIG = OUT / "plots"
FIG.mkdir(parents=True, exist_ok=True)

B = 2000
RNG = np.random.default_rng(0)
TASKS = ["date_addition", "date_subtraction", "date_duration", "date_recurrence", "day_of_week",
         "interval_date", "time_addition", "time_subtraction", "time_duration"]
LEVELS = ["short", "medium", "long", "very_long", "very_very_long"]
INS = ["no_insertion", "similar_insertion", "dissimilar_insertion"]
CELLS = ["en_US/direct", "en_US/cot", "hi_IN/direct", "hi_IN/cot", "hi_IN/en-cot", "hi_IN/clp"]
NAME = {"en_US/direct": "English direct", "en_US/cot": "English CoT", "hi_IN/direct": "Hindi direct",
        "hi_IN/cot": "Hindi CoT", "hi_IN/en-cot": "Hindi en-CoT", "hi_IN/clp": "Hindi CLP"}
REASONING = ["en_US/cot", "hi_IN/cot", "hi_IN/en-cot", "hi_IN/clp"]

df = pd.read_pickle(OUT / "data" / "responses.pkl")
df["correct"] = df["correct"].astype(float)
qids = df["qid"].unique()
df["qi"] = df["qid"].map({q: i for i, q in enumerate(qids)})
Q = len(qids)
WEIGHTS = np.stack([np.bincount(RNG.integers(0, Q, Q), minlength=Q) for _ in range(B)])
numbers = {}
md = []


def sel(**kw):
    mask = np.ones(len(df), dtype=bool)
    for k, v in kw.items():
        mask &= df[k].isin(v).to_numpy() if isinstance(v, (list, tuple, set)) else (df[k] == v).to_numpy()
    return mask


def counts(mask, strict=False):
    sub = df[mask] if strict else df[mask & df["scored"].to_numpy()]
    return (np.bincount(sub["qi"], weights=sub["correct"], minlength=Q),
            np.bincount(sub["qi"], minlength=Q).astype(float))


def acc(mask, strict=False):
    c, n = counts(mask, strict)
    return c.sum() / n.sum()


def boot(mask, strict=False):
    c, n = counts(mask, strict)
    return (WEIGHTS @ c) / (WEIGHTS @ n)


def ci(samples):
    lo, hi = np.percentile(samples, [2.5, 97.5])
    return [float(lo), float(hi)]


def paired(a, b, mask):
    sub = df[mask & df["scored"].to_numpy() & df["cell"].isin([a, b]).to_numpy()]
    wide = sub.pivot_table(index=["qid", "insertion"], columns="cell", values="correct").dropna()
    x = int(((wide[a] == 1) & (wide[b] == 0)).sum())
    y = int(((wide[a] == 0) & (wide[b] == 1)).sum())
    return {"pairs": len(wide), "a_only": x, "b_only": y, "p": float(binomtest(x, x + y, 0.5).pvalue) if x + y else 1.0}


def mantel_haenszel(sub, exposure):
    tables = []
    for _, g in sub.groupby(["task", "difficulty"]):
        e, c = g[exposure].astype(bool), g["correct"] == 1
        t = np.array([[(e & c).sum(), (e & ~c).sum()], [(~e & c).sum(), (~e & ~c).sum()]], dtype=float)
        if t[0].sum() and t[1].sum():
            tables.append(t)
    if not tables:
        return {"odds_ratio": None, "or_ci": None, "p": None, "strata": 0}
    st = StratifiedTable(tables)
    lo, hi = st.oddsratio_pooled_confint()
    return {"odds_ratio": float(st.oddsratio_pooled), "or_ci": [float(lo), float(hi)], "p": float(st.test_null_odds().pvalue),
            "strata": len(tables)}


def pct(x):
    return "–" if x is None or x != x else f"{100 * x:.1f}"


def sg(x):
    return "–" if x is None or x != x else f"{100 * x:+.1f}"


def pv(p):
    return "–" if p is None else "<0.001" if p < 0.001 else f"{p:.3f}" if p < 0.01 else f"{p:.2f}"


def table(title, header, rows, note=None):
    md.extend([f"## {title}", "", "| " + " | ".join(header) + " |", "|" + "---|" * len(header)])
    md.extend("| " + " | ".join(map(str, r)) + " |" for r in rows)
    md.extend(["", note, ""] if note else [""])


# 1. Coverage and unscored responses
checks = json.load(open(OUT / "data" / "checks.json", encoding="utf-8"))
numbers["questions"] = Q
numbers["records_per_cell"] = df.groupby("cell").size().to_dict()
uns = {}
for cell in CELLS:
    s = df[df["cell"] == cell]
    uns[cell] = {"unscored": int((~s["scored"]).sum()), "unscored_cutoff": int((~s["scored"] & s["cutoff"]).sum()),
                 "rate": float((~s["scored"]).mean())}
clp = df[df["cell"] == "hi_IN/clp"]
uns["hi_IN/clp"]["stage1_cutoff"] = int(clp["s1_cutoff"].sum())
numbers["unscored"] = uns
table("Data and unscored responses", ["Condition", "Responses", "Questions", "No Answer line", "of which cut off"],
      [[NAME[c], numbers["records_per_cell"][c], Q, uns[c]["unscored"], uns[c]["unscored_cutoff"]] for c in CELLS],
      f"CLP stage 1 was cut off at 4,096 tokens in {uns['hi_IN/clp']['stage1_cutoff']} responses. Checks: CLP and en-CoT question texts and gold answers match the standard runs for every record ({len(checks['clp_question_text_differs_from_standard'])} and {len(checks['clp_gold_differs_from_standard'])} mismatches for CLP, {len(checks['en-cot_question_text_differs_from_standard'])} and {len(checks['en-cot_gold_differs_from_standard'])} for en-CoT).")

# 2. Accuracy by task, with CLP comparisons
COMPARE = [("hi_IN/clp", "hi_IN/cot"), ("hi_IN/clp", "hi_IN/direct"), ("hi_IN/clp", "hi_IN/en-cot"), ("en_US/cot", "hi_IN/clp")]
acc_task, comp = {}, {}
for task in TASKS + ["all"]:
    base = sel(task=task) if task != "all" else np.ones(len(df), dtype=bool)
    for cell in CELLS:
        acc_task[f"{cell}/{task}"] = acc(base & sel(cell=cell))
    for a, b in COMPARE:
        r = paired(a, b, base)
        r["delta"] = acc_task[f"{a}/{task}"] - acc_task[f"{b}/{task}"]
        if task == "all":
            r["ci"] = ci(boot(sel(cell=a)) - boot(sel(cell=b)))
        comp[f"{a} vs {b}/{task}"] = r
for a, b in COMPARE:
    keys = [f"{a} vs {b}/{t}" for t in TASKS]
    reject, ph, _, _ = multipletests([comp[k]["p"] for k in keys], alpha=0.05, method="holm")
    for k, rj, p in zip(keys, reject, ph):
        comp[k]["p_holm"], comp[k]["sig"] = float(p), bool(rj)
    comp[f"{a} vs {b}/all"]["sig"] = comp[f"{a} vs {b}/all"]["p"] < 0.05
numbers["accuracy_by_task"] = acc_task
numbers["comparisons"] = comp
strict = {c: acc(sel(cell=c), strict=True) for c in CELLS}
numbers["strict_accuracy"] = strict


def star(k):
    v = comp[k]
    return sg(v["delta"]) + ("*" if v["sig"] else "")


table("Accuracy by task (% of answered responses)", ["Task"] + [NAME[c] for c in CELLS] + ["CLP − Hindi CoT", "CLP − Hindi direct", "CLP − en-CoT"],
      [[t.replace("_", " ") if t != "all" else "**All tasks**"] + [pct(acc_task[f"{c}/{t}"]) for c in CELLS]
       + [star(f"hi_IN/clp vs hi_IN/cot/{t}"), star(f"hi_IN/clp vs hi_IN/direct/{t}"), star(f"hi_IN/clp vs hi_IN/en-cot/{t}")] for t in TASKS + ["all"]],
      "2,250 questions × 3 distractor conditions per cell. * exact McNemar p < 0.05 on paired responses, Holm-corrected over the 9 tasks within each comparison (the All row is uncorrected). "
      + "Overall CIs (cluster bootstrap over questions): " + "; ".join(f"{NAME[a]} − {NAME[b]} {sg(comp[f'{a} vs {b}/all']['delta'])} [{sg(comp[f'{a} vs {b}/all']['ci'][0])}, {sg(comp[f'{a} vs {b}/all']['ci'][1])}]" for a, b in COMPARE)
      + ". Counting unanswered responses as wrong: " + ", ".join(f"{NAME[c]} {pct(strict[c])}" for c in CELLS) + ".")
table("Paired comparisons, all tasks", ["Comparison", "Pairs", "Only first right", "Only second right", "Δ (points) [95% CI]", "p"],
      [[f"{NAME[a]} vs {NAME[b]}", comp[f"{a} vs {b}/all"]["pairs"], comp[f"{a} vs {b}/all"]["a_only"], comp[f"{a} vs {b}/all"]["b_only"],
        f"{sg(comp[f'{a} vs {b}/all']['delta'])} [{sg(comp[f'{a} vs {b}/all']['ci'][0])}, {sg(comp[f'{a} vs {b}/all']['ci'][1])}]", pv(comp[f"{a} vs {b}/all"]["p"])] for a, b in COMPARE])

# 3. Difficulty and the English-Hindi gap
diff = {}
for lvl in LEVELS:
    for cell in CELLS:
        m = sel(cell=cell, difficulty=lvl)
        diff[f"{cell}/{lvl}"] = {"acc": acc(m), "ci": ci(boot(m))}
    for cell in ["hi_IN/cot", "hi_IN/en-cot", "hi_IN/clp"]:
        a, b = sel(cell="en_US/cot", difficulty=lvl), sel(cell=cell, difficulty=lvl)
        diff[f"gap/{cell}/{lvl}"] = {"gap": acc(a) - acc(b), "ci": ci(boot(a) - boot(b))}
numbers["difficulty"] = diff
table("Accuracy by difficulty (%)", ["Level"] + [NAME[c] for c in CELLS] + ["Gap En CoT − Hi CoT", "Gap En CoT − Hi CLP"],
      [[lvl.replace("_", " ")] + [pct(diff[f"{c}/{lvl}"]["acc"]) for c in CELLS]
       + [f"{sg(diff[f'gap/hi_IN/cot/{lvl}']['gap'])} [{sg(diff[f'gap/hi_IN/cot/{lvl}']['ci'][0])}, {sg(diff[f'gap/hi_IN/cot/{lvl}']['ci'][1])}]",
          f"{sg(diff[f'gap/hi_IN/clp/{lvl}']['gap'])} [{sg(diff[f'gap/hi_IN/clp/{lvl}']['ci'][0])}, {sg(diff[f'gap/hi_IN/clp/{lvl}']['ci'][1])}]"] for lvl in LEVELS],
      "All nine tasks at every level (450 questions per level). Gaps in points with cluster-bootstrap 95% CIs.")

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "pdf.fonttype": 42})
series = [("en_US/cot", "#2a78d6", "s", "-"), ("hi_IN/en-cot", "#1baf7a", "D", "-"), ("hi_IN/clp", "#eb6834", "o", "-"),
          ("hi_IN/cot", "#6b6b66", "s", "--"), ("hi_IN/direct", "#6b6b66", "o", ":")]
fig, ax = plt.subplots(figsize=(6.2, 3.0))
x = np.arange(len(LEVELS))
for cell, color, marker, ls in series:
    ys = np.array([100 * diff[f"{cell}/{l}"]["acc"] for l in LEVELS])
    lo = np.array([100 * diff[f"{cell}/{l}"]["ci"][0] for l in LEVELS])
    hi = np.array([100 * diff[f"{cell}/{l}"]["ci"][1] for l in LEVELS])
    ax.errorbar(x, ys, yerr=[ys - lo, hi - ys], color=color, marker=marker, linestyle=ls, lw=1.6, ms=5, capsize=2.5,
                markerfacecolor=color if ls == "-" else "white", label=NAME[cell])
    ax.text(x[-1] + 0.12, ys[-1], NAME[cell], color=color, va="center", fontsize=8)
ax.set_xticks(x, ["Short", "Medium", "Long", "Very long", "Very very long"])
ax.set_xlim(-0.25, len(LEVELS) + 0.9)
ax.set_ylabel("Accuracy (%)")
ax.set_xlabel("TRD difficulty level")
ax.grid(axis="y", color="#e4e3de", lw=0.8)
fig.tight_layout()
fig.savefig(FIG / "difficulty.pdf")
fig.savefig(FIG / "difficulty.png", dpi=300, facecolor="white")
plt.close(fig)

# 4. Distractors
dist = {}
for cell in CELLS:
    for ins in INS:
        m = sel(cell=cell, insertion=ins)
        dist[f"{cell}/{ins}"] = (acc(m), boot(m))
    for ins in INS[1:]:
        a0, b0 = dist[f"{cell}/no_insertion"]
        a1, b1 = dist[f"{cell}/{ins}"]
        dist[f"drop/{cell}/{ins}"] = (a0 - a1, b0 - b1)
for cell in ["hi_IN/cot", "hi_IN/en-cot", "hi_IN/clp"]:
    for ins in INS[1:]:
        a, b = dist[f"drop/{cell}/{ins}"], dist[f"drop/hi_IN/direct/{ins}"]
        dist[f"penalty/{cell}/{ins}"] = (a[0] - b[0], a[1] - b[1])
for ins in INS[1:]:
    a, b = dist[f"drop/hi_IN/clp/{ins}"], dist[f"drop/hi_IN/cot/{ins}"]
    dist[f"clp_minus_cot_drop/{ins}"] = (a[0] - b[0], a[1] - b[1])
numbers["distractor"] = {k: {"value": float(v[0]), "ci": ci(v[1])} if not isinstance(v[1], float) else {"value": float(v[0])} for k, v in dist.items()}
dv = numbers["distractor"]
fmt_ci = lambda k: f"{sg(dv[k]['value'])} [{sg(dv[k]['ci'][0])}, {sg(dv[k]['ci'][1])}]"
table("Distractors: accuracy (%) and drops (points)", ["Condition", "None", "Time-related", "Unrelated", "Drop, time-related [95% CI]", "Drop, unrelated [95% CI]"],
      [[NAME[c]] + [pct(dv[f"{c}/{i}"]["value"]) for i in INS] + [fmt_ci(f"drop/{c}/similar_insertion"), fmt_ci(f"drop/{c}/dissimilar_insertion")] for c in CELLS],
      "Drop = accuracy without the distractor minus accuracy with it (positive: the distractor hurt).")
table("Distraction penalty relative to Hindi direct answers (points)", ["Reasoning condition", "Time-related [95% CI]", "Unrelated [95% CI]"],
      [[NAME[c], fmt_ci(f"penalty/{c}/similar_insertion"), fmt_ci(f"penalty/{c}/dissimilar_insertion")] for c in ["hi_IN/cot", "hi_IN/en-cot", "hi_IN/clp"]]
      + [["CLP drop − Hindi CoT drop", fmt_ci("clp_minus_cot_drop/similar_insertion"), fmt_ci("clp_minus_cot_drop/dissimilar_insertion")]],
      "Penalty = the condition's distractor drop minus the Hindi direct drop on the same questions (the mid report's CoT distraction penalty, with CLP or en-CoT in place of CoT).")

# 5. Distractor reuse in wrong answers
reuse = {}
for cell in CELLS:
    ins_rows = df[sel(cell=cell, insertion="similar_insertion") & df["reuse_similar"].notna().to_numpy()]
    plc_rows = df[sel(cell=cell, insertion="no_insertion") & df["reuse_similar"].notna().to_numpy()]
    a, n1, b, n2 = int(ins_rows["reuse_similar"].sum()), len(ins_rows), int(plc_rows["reuse_similar"].sum()), len(plc_rows)
    reuse[cell] = {"inserted": a, "inserted_n": n1, "placebo": b, "placebo_n": n2,
                   "p": float(fisher_exact([[a, n1 - a], [b, n2 - b]])[1]) if n1 and n2 else None}
numbers["reuse_similar"] = reuse
table("Wrong answers containing a number, month or weekday from the time-related distractor", ["Condition", "With distractor", "Placebo (no distractor)", "Fisher p"],
      [[NAME[c], f"{pct(reuse[c]['inserted'] / reuse[c]['inserted_n'])}% ({reuse[c]['inserted']}/{reuse[c]['inserted_n']})",
        f"{pct(reuse[c]['placebo'] / reuse[c]['placebo_n'])}% ({reuse[c]['placebo']}/{reuse[c]['placebo_n']})", pv(reuse[c]["p"])] for c in CELLS],
      "Placebo: wrong answers to the same questions without the distractor, checked against the distractor that would have been inserted.")

# 6. Distractor mentions
mention = {}
SOURCES = [("en_US/cot", "mentions"), ("hi_IN/cot", "mentions"), ("hi_IN/en-cot", "mentions"), ("hi_IN/clp", "s1_mentions"), ("hi_IN/clp", "mentions")]
for cell, prefix in SOURCES:
    for kind in ("similar", "dissimilar"):
        col = f"{prefix}_{kind}"
        ins = sel(cell=cell, insertion=f"{kind}_insertion") & df[col].notna().to_numpy()
        plc = sel(cell=cell, insertion="no_insertion") & df[col].notna().to_numpy()
        sub = df[ins].copy()
        sub["mention"] = sub[col].astype(bool)
        mention[f"{cell}/{prefix}/{kind}"] = {"rate": float(df.loc[ins, col].mean()), "placebo": float(df.loc[plc, col].mean()), "n": int(ins.sum()),
                                              "acc_mention": float(sub.loc[sub["mention"], "correct"].mean()) if sub["mention"].any() else None,
                                              "acc_no_mention": float(sub.loc[~sub["mention"], "correct"].mean()) if (~sub["mention"]).any() else None,
                                              **mantel_haenszel(sub, "mention")}
numbers["mention"] = mention
label = {("hi_IN/clp", "s1_mentions"): "Hindi CLP, stage 1", ("hi_IN/clp", "mentions"): "Hindi CLP, stage 2"}
orf = lambda v: "–" if v["odds_ratio"] is None else f"{v['odds_ratio']:.2f} [{v['or_ci'][0]:.2f}, {v['or_ci'][1]:.2f}]"
table("Distractor mentions in the reasoning (% of answered responses; placebo in brackets) and odds ratio of a correct answer when mentioned",
      ["Text", "Time-related", "Unrelated", "OR, time-related", "OR, unrelated"],
      [[label.get((c, p), NAME[c]), f"{pct(mention[f'{c}/{p}/similar']['rate'])} ({pct(mention[f'{c}/{p}/similar']['placebo'])})",
        f"{pct(mention[f'{c}/{p}/dissimilar']['rate'])} ({pct(mention[f'{c}/{p}/dissimilar']['placebo'])})",
        orf(mention[f"{c}/{p}/similar"]), orf(mention[f"{c}/{p}/dissimilar"])] for c, p in SOURCES],
      "A text mentions the distractor if it contains a content word of the distractor that is not in the question (mid-report rule). For CLP and en-CoT, which reason in English about a Hindi question, the words of the matching English distractor also count. Placebo: the same check on responses to the same questions without the distractor. OR: Mantel–Haenszel odds ratio of a correct final answer for responses that mention the distractor versus those that do not, stratified by task and difficulty.")

# 7. Trace properties
props = {}
for cell in REASONING:
    s = df[(df["cell"] == cell) & df["scored"]]
    w = s["hindi_words"] + s["english_words"]
    props[cell] = {"median_words": float(w.median()), "median_tokens": float(s["completion_tokens"].median()),
                   "english_share": float(s["english_words"].sum() / w.sum()), "verification": float(s["verification"].mean()),
                   "answer_in_reasoning": float(s["answer_in_reasoning"].dropna().mean()),
                   "wrong": int((s["correct"] == 0).sum()), "wrong_ends_at_gold": int(((s["correct"] == 0) & (s["reasoning_ends_at_gold"] == True)).sum())}
s1 = df[(df["cell"] == "hi_IN/clp") & df["scored"]]
w1 = s1["s1_hindi_words"] + s1["s1_english_words"]
props["clp_stage1"] = {"median_words": float(w1.median()), "median_tokens": float(s1["s1_tokens"].median()),
                       "english_share": float(s1["s1_english_words"].sum() / w1.sum()), "verification": float(s1["s1_verification"].mean())}
props["clp_total_median_tokens"] = float((s1["s1_tokens"] + s1["completion_tokens"]).median())
numbers["trace"] = props
table("Properties of the reasoning (answered responses)", ["", "English CoT", "Hindi CoT", "Hindi en-CoT", "CLP stage 2", "CLP stage 1"],
      [["Median words"] + [f"{props[c]['median_words']:.0f}" for c in REASONING] + [f"{props['clp_stage1']['median_words']:.0f}"],
       ["Median completion tokens"] + [f"{props[c]['median_tokens']:.0f}" for c in REASONING] + [f"{props['clp_stage1']['median_tokens']:.0f}"],
       ["Share of English words"] + [f"{props[c]['english_share']:.3f}" for c in REASONING] + [f"{props['clp_stage1']['english_share']:.3f}"],
       ["Has a verification step (%)"] + [pct(props[c]["verification"]) for c in REASONING] + [pct(props["clp_stage1"]["verification"])],
       ["Answer value appears in the reasoning (%)"] + [pct(props[c]["answer_in_reasoning"]) for c in REASONING] + ["–"],
       ["Wrong answers whose reasoning ended at the gold value"] + [f"{props[c]['wrong_ends_at_gold']} of {props[c]['wrong']:,}" for c in REASONING] + ["–"]],
      f"CLP uses a median of {props['clp_total_median_tokens']:.0f} completion tokens over both stages. Share of English words = English words / (English + Devanagari words), pooled over responses.")

# 8. From stage 1 to stage 2 (date-answer tasks)
st = df[(df["cell"] == "hi_IN/clp") & df["scored"] & df["s1_has_value"].notna().to_numpy()].copy()
st["s1_gold"] = st["s1_last_is_gold"].astype(bool)
st["s1_same"] = st["s1_last_is_answer"].astype(bool)
stage = {"n": len(st), "s1_has_value": float(st["s1_has_value"].astype(bool).mean()), "s1_ends_at_gold": float(st["s1_gold"].mean()),
         "s2_correct": float(st["correct"].mean()), "s2_equals_s1": float(st["s1_same"].mean())}
for flag in (True, False):
    g = st[st["s1_gold"] == flag]
    stage[f"s1_gold_{flag}"] = {"n": len(g), "s2_correct": float(g["correct"].mean()), "s2_equals_s1": float(g["s1_same"].mean())}
wrong = st[st["correct"] == 0]
stage["wrong_n"] = len(wrong)
stage["wrong_inherited"] = int(wrong["s1_same"].sum())
for cell in ["hi_IN/cot", "hi_IN/en-cot", "en_US/cot"]:
    stage[f"acc_date_tasks/{cell}"] = acc(sel(cell=cell, task=["date_addition", "date_subtraction", "date_recurrence"]))
for task in ["date_addition", "date_subtraction", "date_recurrence"]:
    g = st[st["task"] == task]
    stage[f"task/{task}"] = {"n": len(g), "s1_ends_at_gold": float(g["s1_gold"].mean()), "s2_correct": float(g["correct"].mean()),
                             "en_cot_acc": acc(sel(cell="hi_IN/en-cot", task=task))}
numbers["stage1_to_stage2"] = stage
table("From stage 1 to stage 2 (CLP, date-answer tasks)", ["", "Stage 1 ends at the gold date", "Stage 1 ends elsewhere", "All"],
      [["Responses", stage["s1_gold_True"]["n"], stage["s1_gold_False"]["n"], stage["n"]],
       ["Stage 2 correct (%)", pct(stage["s1_gold_True"]["s2_correct"]), pct(stage["s1_gold_False"]["s2_correct"]), pct(stage["s2_correct"])],
       ["Stage 2 final answer = stage 1's last date (%)", pct(stage["s1_gold_True"]["s2_equals_s1"]), pct(stage["s1_gold_False"]["s2_equals_s1"]), pct(stage["s2_equals_s1"])]],
      f"Date addition, date subtraction and date recurrence only (answers are dates, so stage 1's last date can be read reliably; checked by hand on 12 random responses). Stage 1 contains a date other than the question's in {pct(stage['s1_has_value'])}% of responses. Of {stage['wrong_n']} wrong stage-2 answers, {stage['wrong_inherited']} repeat stage 1's last date. On the same tasks, en-CoT is correct in {pct(stage['acc_date_tasks/hi_IN/en-cot'])}%, Hindi CoT in {pct(stage['acc_date_tasks/hi_IN/cot'])}% and English CoT in {pct(stage['acc_date_tasks/en_US/cot'])}%.")
table("Stage 1 by task", ["Task", "Responses", "Stage 1 ends at gold (%)", "CLP correct (%)", "en-CoT correct (%)"],
      [[t.replace("_", " "), stage[f"task/{t}"]["n"], pct(stage[f"task/{t}"]["s1_ends_at_gold"]), pct(stage[f"task/{t}"]["s2_correct"]), pct(stage[f"task/{t}"]["en_cot_acc"])]
       for t in ["date_addition", "date_subtraction", "date_recurrence"]])

# 9. Agreement with English CoT
agree = {}
for cell in ["hi_IN/direct", "hi_IN/cot", "hi_IN/en-cot", "hi_IN/clp"]:
    ref = "en_US/direct" if cell == "hi_IN/direct" else "en_US/cot"
    sub = df[df["scored"] & df["cell"].isin([ref, cell]).to_numpy()]
    wide = sub.pivot_table(index=["qid", "task", "difficulty", "insertion"], columns="cell", values="correct").dropna().reset_index()
    e, h = wide[ref] == 1, wide[cell] == 1
    phis = []
    for _, g in wide.groupby(["difficulty", "task"]):
        ge, gh = g[ref] == 1, g[cell] == 1
        den = np.sqrt(ge.mean() * (1 - ge.mean()) * gh.mean() * (1 - gh.mean()))
        if den:
            phis.append(((ge & gh).mean() - ge.mean() * gh.mean()) / den)
    eo, ho = int((e & ~h).sum()), int((~e & h).sum())
    agree[cell] = {"reference": ref, "pairs": len(wide), "both_right": int((e & h).sum()), "both_wrong": int((~e & ~h).sum()),
                   "english_only": eo, "hindi_only": ho, "p": float(binomtest(eo, eo + ho, 0.5).pvalue),
                   "median_phi": float(np.median(phis)), "phi_iqr": [float(x) for x in np.percentile(phis, [25, 75])], "cells": len(phis)}
numbers["agreement"] = agree
table("Does the Hindi condition fail on the same questions as English?", ["Hindi condition (vs English)", "Pairs", "Both right", "Both wrong", "Only English right", "Only Hindi right", "Median φ within task × level [IQR]"],
      [[f"{NAME[c]} (vs {NAME[agree[c]['reference']]})", agree[c]["pairs"], agree[c]["both_right"], agree[c]["both_wrong"], agree[c]["english_only"], agree[c]["hindi_only"],
        f"{agree[c]['median_phi']:.2f} [{agree[c]['phi_iqr'][0]:.2f}, {agree[c]['phi_iqr'][1]:.2f}]"] for c in agree],
      "Pairs are the same question and distractor condition in both languages. φ is the correlation of right/wrong between the two, computed within each task × difficulty cell that has both right and wrong answers in both conditions (" + ", ".join(f"{agree[c]['cells']}" for c in agree) + " of 45 cells, in table order), so that differences in difficulty between cells do not inflate it.")

# 10. Day of week, recurrence patterns, error composition
dow = {}
for cell in CELLS:
    s = df[(df["cell"] == cell) & (df["task"] == "day_of_week") & df["scored"]]["weekday_offset"].dropna().astype(int)
    dow[cell] = {str(o): float((s == o).mean()) for o in range(-3, 4)}
    dow[cell]["n"] = int(len(s))
numbers["day_of_week_offsets"] = dow
table("Day of week: predicted minus correct weekday (% of answered)", ["Condition", "n", "−3", "−2", "−1", "0 (correct)", "+1", "+2", "+3"],
      [[NAME[c], dow[c]["n"]] + [pct(dow[c][str(o)]) for o in range(-3, 4)] for c in CELLS])
rec = {}
for cell in CELLS:
    s = df[(df["cell"] == cell) & (df["task"] == "date_recurrence")]["recurrence_pattern"].dropna()
    rec[cell] = {**{k: float(v) for k, v in s.value_counts(normalize=True).items()}, "n": int(len(s))}
numbers["recurrence"] = rec
table("Date recurrence answer patterns (% of answered)", ["Condition", "n", "Correct", "First step only", "Mirror (backwards)", "Other"],
      [[NAME[c], rec[c]["n"], pct(rec[c].get("correct", 0)), pct(rec[c].get("first_step", 0)), pct(rec[c].get("mirror", 0)), pct(rec[c].get("other", 0))] for c in CELLS],
      "First step only: today plus one interval, ignoring which occurrence was asked for. Mirror: the right number of days, counted backwards.")
GROUPS = {"off_by_one": "Off by one", "wrong_direction": "Wrong direction", "month_slip": "Month slip"}
err = {}
for cell in REASONING:
    e = df[(df["cell"] == cell) & df["error_type"].notna()]["error_type"].map(lambda x: GROUPS.get(x, "Other"))
    err[cell] = {**{k: float(e.eq(k).mean()) for k in ["Off by one", "Wrong direction", "Month slip", "Other"]}, "n": int(len(e))}
numbers["error_composition"] = err
table("Composition of wrong answers (%)", ["Condition", "Wrong answers", "Off by one", "Wrong direction", "Month slip", "Other"],
      [[NAME[c], err[c]["n"], pct(err[c]["Off by one"]), pct(err[c]["Wrong direction"]), pct(err[c]["Month slip"]), pct(err[c]["Other"])] for c in REASONING],
      "Mid-report error classes; 'wrong direction' is the mirror image of the correct date or time around the one in the question.")

json.dump(numbers, open(OUT / "numbers.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False, default=float)
(OUT / "analysis.md").write_text("# CLP analysis\n\n" + "\n".join(md), encoding="utf-8")
print("\n".join(md))
