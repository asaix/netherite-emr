import argparse
import json
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("pdf")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy.stats import binomtest

ap = argparse.ArgumentParser()
ap.add_argument("--source", choices=["standard", "reasoning_on"], default="standard")
args = ap.parse_args()

HERE = Path(__file__).resolve().parent
OUT = HERE / "outputs" / ("extra" if args.source == "standard" else "extra-ron")
TAB, FIG = OUT / "tables", OUT / "plots"
for d in (TAB, FIG):
    d.mkdir(parents=True, exist_ok=True)

B = 2000
RNG = np.random.default_rng(0)
TASKS = ["date_addition", "date_subtraction", "date_duration", "date_recurrence", "day_of_week",
         "interval_date", "time_addition", "time_subtraction", "time_duration"]
LABEL = {"date_addition": "Date addition", "date_subtraction": "Date subtraction", "date_duration": "Date duration",
         "date_recurrence": "Date recurrence", "day_of_week": "Day of week", "interval_date": "Interval date",
         "time_addition": "Time addition", "time_subtraction": "Time subtraction", "time_duration": "Time duration"}
DIFFS = ["short", "medium", "long", "very_long", "very_very_long"]
DIFF_LABEL = {"short": "Short", "medium": "Medium", "long": "Long", "very_long": "Very long", "very_very_long": "V. v. long"}
LANGS = ["en_US", "hi_IN"]
LANG = {"en_US": "English", "hi_IN": "Hindi"}
INS = ["no_insertion", "similar_insertion", "dissimilar_insertion"]

plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Times New Roman"], "font.size": 9, "axes.titlesize": 9,
    "axes.labelsize": 9, "legend.fontsize": 8, "xtick.labelsize": 8, "ytick.labelsize": 8,
    "pdf.fonttype": 42, "ps.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False,
})

df = pd.read_pickle(HERE / "outputs" / "data" / ("responses_current.pkl" if args.source == "standard" else "responses_on_current.pkl")).reset_index(drop=True)
df["correct"] = df["correct"].astype(float)
df["strict"] = df["correct"].where(df["scored"], 0.0)
qids = df["qid"].unique()
df["qi"] = df["qid"].map({q: i for i, q in enumerate(qids)})
Q = len(qids)
WEIGHTS = np.stack([np.bincount(RNG.integers(0, Q, Q), minlength=Q) for _ in range(B)])
numbers = {}


def sel(**kw):
    mask = np.ones(len(df), dtype=bool)
    for k, v in kw.items():
        mask &= df[k].isin(v).to_numpy() if isinstance(v, (list, tuple, set)) else (df[k] == v).to_numpy()
    return mask


def counts(mask, strict=False):
    sub = df[mask] if strict else df[mask & df["scored"].to_numpy()]
    c = np.bincount(sub["qi"], weights=sub["strict" if strict else "correct"], minlength=Q)
    n = np.bincount(sub["qi"], minlength=Q).astype(float)
    return c, n


def acc(mask, strict=False):
    c, n = counts(mask, strict)
    return c.sum() / n.sum()


def boot(mask, strict=False):
    c, n = counts(mask, strict)
    return (WEIGHTS @ c) / (WEIGHTS @ n)


def ci(samples):
    lo, hi = np.percentile(samples, [2.5, 97.5])
    return [float(lo), float(hi)]


def stat(value, samples):
    lo, hi = ci(samples)
    return {"value": float(value), "ci": [lo, hi], "sig": bool(lo > 0 or hi < 0)}


def mcnemar(mask, strict=False):
    col = "strict" if strict else "correct"
    sub = df[mask] if strict else df[mask & df["scored"].to_numpy()]
    wide = sub.pivot_table(index=["qid", "insertion"], columns="condition", values=col).dropna()
    b = int(((wide["cot"] == 1) & (wide["direct"] == 0)).sum())
    c = int(((wide["cot"] == 0) & (wide["direct"] == 1)).sum())
    return {"cot_wins": b, "direct_wins": c, "p": float(binomtest(b, b + c, 0.5).pvalue) if b + c else 1.0}


def cot_delta(base, strict=False):
    d, c = sel(condition="direct") & base, sel(condition="cot") & base
    return {"direct": float(acc(d, strict)), "cot": float(acc(c, strict)),
            **stat(acc(c, strict) - acc(d, strict), boot(c, strict) - boot(d, strict)), **mcnemar(base, strict)}


def did(base, ins, strict=False):
    drops = {}
    for cond in ("direct", "cot"):
        m0, m1 = base & sel(condition=cond, insertion="no_insertion"), base & sel(condition=cond, insertion=ins)
        drops[cond] = (acc(m0, strict) - acc(m1, strict), boot(m0, strict) - boot(m1, strict))
    return {"drop_direct": stat(*drops["direct"]), "drop_cot": stat(*drops["cot"]),
            **stat(drops["cot"][0] - drops["direct"][0], drops["cot"][1] - drops["direct"][1])}


def signed(x):
    return f"{100 * x:+.1f}".replace("-", "$-$")


def with_ci(s):
    text = f"{signed(s['value'])} [{signed(s['ci'][0])}, {signed(s['ci'][1])}]"
    return r"\textbf{" + text + "}" if s["sig"] else text


# 1. Difficulty profile on all nine tasks
profile = {}
for lang in LANGS:
    for lvl in DIFFS:
        base = sel(language=lang, difficulty=lvl)
        profile[f"{lang}/{lvl}"] = cot_delta(base)
for lvl in DIFFS:
    for cond in ("direct", "cot"):
        m = sel(condition=cond, difficulty=lvl)
        en, hi = m & sel(language="en_US"), m & sel(language="hi_IN")
        profile[f"gap/{lvl}/{cond}"] = stat(acc(en) - acc(hi), boot(en) - boot(hi))
numbers["difficulty_profile"] = profile

lines = [r"\begin{table}[t]", r"\centering", r"\small", r"\setlength{\tabcolsep}{3pt}", r"\begin{tabular}{@{}lrrrrr@{}}",
         r"\toprule", r" & " + " & ".join(DIFF_LABEL[l].replace("V. v.", r"V.\,v.") for l in DIFFS) + r" \\", r"\midrule"]
for lang in LANGS:
    lines.append(r"\multicolumn{6}{@{}l}{\textit{" + LANG[lang] + r"}} \\")
    for cond, name in (("direct", "Direct"), ("cot", "CoT")):
        lines.append(r"\quad " + name + " & " + " & ".join(f"{100 * profile[f'{lang}/{l}'][cond]:.1f}" for l in DIFFS) + r" \\")
    lines.append(r"\quad $\Delta$ & " + " & ".join(
        (r"\textbf{" + signed(profile[f"{lang}/{l}"]["value"]) + "}") if profile[f"{lang}/{l}"]["sig"] else signed(profile[f"{lang}/{l}"]["value"])
        for l in DIFFS) + r" \\")
lines.append(r"\midrule")
for cond, name in (("direct", "Direct"), ("cot", "CoT")):
    lines.append(f"Gap, {name} & " + " & ".join(f"{100 * profile[f'gap/{l}/{cond}']['value']:.1f}" for l in DIFFS) + r" \\")
lines += [r"\bottomrule", r"\end{tabular}",
          r"\caption{Accuracy (\%) on all nine tasks by difficulty level. $\Delta$ is CoT minus direct (points), bold where the 95\% "
          r"cluster-bootstrap interval excludes zero. Gap is English minus Hindi accuracy.}",
          r"\label{tab:difficulty-profile}", r"\end{table}"]
(TAB / "difficulty_profile.tex").write_text("\n".join(lines) + "\n")

# 2. CoT distraction penalty by difficulty and by task
penalty = {}
for lang in LANGS:
    for ins in INS[1:]:
        penalty[f"{lang}/{ins}/all"] = did(sel(language=lang), ins)
        for lvl in DIFFS:
            penalty[f"{lang}/{ins}/{lvl}"] = did(sel(language=lang, difficulty=lvl), ins)
        for task in TASKS:
            penalty[f"{lang}/{ins}/{task}"] = did(sel(language=lang, task=task), ins)
numbers["did"] = penalty

lines = [r"\begin{table}[t]", r"\centering", r"\small", r"\setlength{\tabcolsep}{3pt}", r"\begin{tabular}{@{}lll@{}}",
         r"\toprule", r" & English & Hindi \\", r"\midrule"]
for ins, name in (("similar_insertion", "Time-related"), ("dissimilar_insertion", "Unrelated")):
    lines.append(r"\multicolumn{3}{@{}l}{\textit{" + name + r" distractor}} \\")
    for group in ["all"] + DIFFS:
        label = "All levels" if group == "all" else DIFF_LABEL[group]
        lines.append(r"\quad " + label + " & " + " & ".join(with_ci(penalty[f"{l}/{ins}/{group}"]) for l in LANGS) + r" \\")
lines += [r"\bottomrule", r"\end{tabular}",
          r"\caption{CoT distraction penalty (CoT drop minus direct drop, points) by difficulty level, all nine tasks. "
          r"Brackets are 95\% cluster-bootstrap intervals; bold where they exclude zero.}",
          r"\label{tab:did-difficulty}", r"\end{table}"]
(TAB / "did_difficulty.tex").write_text("\n".join(lines) + "\n")
pd.DataFrame([{"language": k.split("/")[0], "insertion": k.split("/")[1], "group": k.split("/")[2], "did": v["value"],
               "lo": v["ci"][0], "hi": v["ci"][1], "drop_direct": v["drop_direct"]["value"], "drop_cot": v["drop_cot"]["value"]}
              for k, v in penalty.items()]).to_csv(OUT / "did.csv", index=False)

fig, axes = plt.subplots(1, 2, figsize=(6.3, 2.1), sharey=True)
for ax, (ins, title) in zip(axes, (("similar_insertion", "(a) Time-related distractor"), ("dissimilar_insertion", "(b) Unrelated distractor"))):
    for i, (lang, color, marker) in enumerate((("en_US", "0.0", "o"), ("hi_IN", "0.5", "s"))):
        vals = [penalty[f"{lang}/{ins}/{l}"] for l in DIFFS]
        x = np.arange(len(DIFFS)) + (i - 0.5) * 0.15
        y = [100 * v["value"] for v in vals]
        err = [[100 * (v["value"] - v["ci"][0]) for v in vals], [100 * (v["ci"][1] - v["value"]) for v in vals]]
        ax.errorbar(x, y, yerr=err, marker=marker, linestyle="none", color=color, capsize=2, markersize=4, label=LANG[lang])
    ax.axhline(0, color="black", linewidth=0.6)
    ax.set_xticks(range(len(DIFFS)), [DIFF_LABEL[l] for l in DIFFS], fontsize=7)
    ax.set_title(title)
    ax.grid(axis="y", color="0.85", linewidth=0.5)
axes[0].set_ylabel("CoT drop $-$ direct drop (pts)")
axes[0].legend(frameon=False, loc="lower left", ncol=2)
fig.tight_layout()
fig.savefig(FIG / "did_by_difficulty.pdf")
fig.savefig(FIG / "did_by_difficulty.png", dpi=200)
plt.close(fig)

# 3. Logistic models with question-clustered standard errors
d = df[df["scored"]].copy()
d["cot"] = (d["condition"] == "cot").astype(int)
d["hindi"] = (d["language"] == "hi_IN").astype(int)
d["sim"] = (d["insertion"] == "similar_insertion").astype(int)
d["dis"] = (d["insertion"] == "dissimilar_insertion").astype(int)
d["lvl"] = d["difficulty"].map({l: i for i, l in enumerate(DIFFS)})
d["cell"] = d["task"] + "/" + d["difficulty"] + "/" + d["language"] + "/" + d["condition"]


def fit(formula, data):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return smf.glm(formula, data, family=sm.families.Binomial()).fit(cov_type="cluster", cov_kwds={"groups": data["qi"]})


def odds(model, expr):
    t = model.t_test(expr)
    est, (lo, hi), p = float(t.effect[0]), (float(x) for x in t.conf_int()[0]), float(t.pvalue)
    return {"log_or": est, "or": float(np.exp(est)), "or_ci": [float(np.exp(lo)), float(np.exp(hi))], "p": p}


models = {}
spec = {
    "task_difficulty_fe": "correct ~ cot * sim * hindi + cot * dis * hindi + C(task) + C(difficulty)",
    "cell_fe": "correct ~ C(cell) + cot * sim * hindi + cot * dis * hindi - cot - hindi - cot:hindi",
}
contrasts = {
    "en_cot_x_sim": "cot:sim = 0", "hi_cot_x_sim": "cot:sim + cot:sim:hindi = 0", "hi_minus_en_cot_x_sim": "cot:sim:hindi = 0",
    "en_cot_x_dis": "cot:dis = 0", "hi_cot_x_dis": "cot:dis + cot:dis:hindi = 0", "hi_minus_en_cot_x_dis": "cot:dis:hindi = 0",
    "en_sim_direct": "sim = 0", "hi_sim_direct": "sim + sim:hindi = 0",
}
for name, formula in spec.items():
    for scoring in ("scored", "strict"):
        data = d if scoring == "scored" else df.assign(
            correct=df["strict"], cot=(df["condition"] == "cot").astype(int), hindi=(df["language"] == "hi_IN").astype(int),
            sim=(df["insertion"] == "similar_insertion").astype(int), dis=(df["insertion"] == "dissimilar_insertion").astype(int),
            cell=df["task"] + "/" + df["difficulty"] + "/" + df["language"] + "/" + df["condition"])
        m = fit(formula, data)
        models[f"{name}/{scoring}"] = {"n": int(m.nobs), "converged": bool(m.converged),
                                       **{k: odds(m, v) for k, v in contrasts.items()}}
trend = fit("correct ~ C(task) + lvl * cot * hindi", d)
models["difficulty_trend"] = {
    "n": int(trend.nobs),
    "hindi_gap_per_level_direct": odds(trend, "lvl:hindi = 0"),
    "hindi_gap_per_level_cot": odds(trend, "lvl:hindi + lvl:cot:hindi = 0"),
    "cot_effect_per_level_en": odds(trend, "lvl:cot = 0"),
    "cot_effect_per_level_hi": odds(trend, "lvl:cot + lvl:cot:hindi = 0"),
}
hi = d[d["hindi"] == 1]
did_trend = fit("correct ~ C(task) * cot + C(difficulty) * cot + cot * sim * lvl + cot * dis * lvl - lvl - cot:lvl", hi)
models["hindi_penalty_trend"] = {"n": int(did_trend.nobs), "cot_x_sim_per_level": odds(did_trend, "cot:sim:lvl = 0"),
                                 "cot_x_dis_per_level": odds(did_trend, "cot:dis:lvl = 0")}
numbers["logistic"] = models

rows = [("CoT $\\times$ time-related, English", "en_cot_x_sim"), ("CoT $\\times$ time-related, Hindi", "hi_cot_x_sim"),
        ("\\quad Hindi $/$ English ratio", "hi_minus_en_cot_x_sim"), ("CoT $\\times$ unrelated, English", "en_cot_x_dis"),
        ("CoT $\\times$ unrelated, Hindi", "hi_cot_x_dis"), ("\\quad Hindi $/$ English ratio", "hi_minus_en_cot_x_dis")]


def or_cell(v):
    text = f"{v['or']:.2f} [{v['or_ci'][0]:.2f}, {v['or_ci'][1]:.2f}]"
    return r"\textbf{" + text + "}" if v["p"] < 0.05 else text


lines = [r"\begin{table}[t]", r"\centering", r"\small", r"\setlength{\tabcolsep}{3pt}", r"\begin{tabular}{@{}lll@{}}", r"\toprule",
         r"Interaction & Task + level FE & Cell FE \\", r"\midrule"]
for label, key in rows:
    lines.append(f"{label} & {or_cell(models['task_difficulty_fe/scored'][key])} & {or_cell(models['cell_fe/scored'][key])}" + r" \\")
lines += [r"\bottomrule", r"\end{tabular}",
          r"\caption{Odds ratios for the CoT $\times$ distractor interaction from logistic regressions of correctness, with "
          r"standard errors clustered by question. Below 1 means the distractor costs more odds of a correct answer under CoT "
          r"than under direct answering. Task + level FE adds task and difficulty fixed effects; cell FE adds a fixed effect for "
          r"every task $\times$ level $\times$ language $\times$ condition cell. Bold: $p<0.05$.}",
          r"\label{tab:logit}", r"\end{table}"]
(TAB / "logit.tex").write_text("\n".join(lines) + "\n")

# 4. Strict scoring (cut-off responses counted wrong)
strict = {}
for lang in LANGS:
    strict[f"{lang}/cot_delta"] = cot_delta(sel(language=lang), strict=True)
    for ins in INS[1:]:
        strict[f"{lang}/{ins}/did"] = did(sel(language=lang), ins, strict=True)
numbers["strict"] = strict

# 5. CoT delta by task and level
grid = []
for lang in LANGS:
    for task in TASKS:
        for lvl in DIFFS:
            base = sel(language=lang, task=task, difficulty=lvl)
            r = cot_delta(base)
            grid.append({"language": lang, "task": task, "difficulty": lvl, "direct": r["direct"], "cot": r["cot"],
                         "delta": r["value"], "lo": r["ci"][0], "hi": r["ci"][1], "sig": r["sig"]})
grid = pd.DataFrame(grid)
grid.to_csv(OUT / "cot_delta_task_level.csv", index=False)
numbers["cot_delta_task_level"] = {
    lang: {"sig_negative": [f"{r.task}/{r.difficulty}" for r in g.itertuples() if r.sig and r.delta < 0],
           "sig_positive": int(((g["sig"]) & (g["delta"] > 0)).sum()), "cells": int(len(g))}
    for lang, g in grid.groupby("language")}

fig, axes = plt.subplots(1, 2, figsize=(6.3, 2.9), sharey=True)
for ax, lang in zip(axes, LANGS):
    g = grid[grid["language"] == lang].pivot(index="task", columns="difficulty", values="delta").loc[TASKS, DIFFS] * 100
    s = grid[grid["language"] == lang].pivot(index="task", columns="difficulty", values="sig").loc[TASKS, DIFFS]
    im = ax.imshow(g.to_numpy(), cmap="RdBu", vmin=-80, vmax=80, aspect="auto")
    for i in range(len(TASKS)):
        for j in range(len(DIFFS)):
            v = g.iat[i, j]
            ax.text(j, i, f"{v:+.0f}" + ("*" if s.iat[i, j] else ""), ha="center", va="center", fontsize=6.5,
                    color="white" if abs(v) > 50 else "black")
    ax.set_xticks(range(len(DIFFS)), [DIFF_LABEL[l] for l in DIFFS], rotation=30, ha="right", fontsize=7)
    ax.set_yticks(range(len(TASKS)), [LABEL[t] for t in TASKS], fontsize=7)
    ax.set_title(LANG[lang])
fig.colorbar(im, ax=axes, shrink=0.8, label="CoT $-$ direct (pts)")
fig.savefig(FIG / "cot_delta_task_level.pdf", bbox_inches="tight")
fig.savefig(FIG / "cot_delta_task_level.png", dpi=200, bbox_inches="tight")
plt.close(fig)

# 6. Recurrence answer patterns by level
recur = {}
for lang in LANGS:
    for cond in ("direct", "cot"):
        for lvl in DIFFS:
            s = df[sel(task="date_recurrence", language=lang, condition=cond, difficulty=lvl) & df["recurrence_pattern"].notna().to_numpy()]
            vc = s["recurrence_pattern"].value_counts(normalize=True)
            recur[f"{lang}/{cond}/{lvl}"] = {**{k: float(vc.get(k, 0.0)) for k in ("correct", "first_step", "mirror", "other")}, "n": int(len(s))}
numbers["recurrence_by_level"] = recur
pd.DataFrame([{"key": k, **v} for k, v in recur.items()]).to_csv(OUT / "recurrence_by_level.csv", index=False)

by_k = df[sel(task="date_recurrence") & df["recurrence_pattern"].notna().to_numpy()]
by_k = by_k.groupby(["language", "condition", "recurrence_k"])["recurrence_pattern"].value_counts(normalize=True).unstack(fill_value=0.0)
by_k["n"] = df[sel(task="date_recurrence") & df["recurrence_pattern"].notna().to_numpy()].groupby(["language", "condition", "recurrence_k"]).size()
by_k.reset_index().to_csv(OUT / "recurrence_by_k.csv", index=False)
numbers["recurrence_by_k"] = {f"{l}/{c}/{int(k)}": {**{p: float(r.get(p, 0.0)) for p in ("correct", "first_step", "mirror", "other")}, "n": int(r["n"])}
                              for (l, c, k), r in by_k.iterrows()}

robust = {}
for lang in LANGS:
    for ins in INS[1:]:
        robust[f"{lang}/{ins}/without_recurrence"] = did(sel(language=lang, task=[t for t in TASKS if t != "date_recurrence"]), ins)
        robust[f"{lang}/{ins}/without_recurrence_k1"] = did(sel(language=lang) & ~(sel(task="date_recurrence") & (df["recurrence_k"] == 1).to_numpy()), ins)
numbers["did_robustness"] = robust

replication = {}
mid = df["in_mid"].to_numpy()
vvl = sel(difficulty="very_very_long")
groups = {"mid_report_questions": mid, "new_questions_first_four_levels": ~mid & ~vvl, "new_questions_very_very_long": ~mid & vvl}
for lang in LANGS:
    for ins in INS[1:]:
        for g, m in groups.items():
            replication[f"{lang}/{ins}/{g}"] = {**did(sel(language=lang) & m, ins), "questions": int(df.loc[sel(language=lang) & m, "qid"].nunique())}
        for task in ("date_duration", "time_duration", "date_recurrence", "day_of_week"):
            for g, m in list(groups.items())[:2]:
                if (sel(language=lang, task=task) & m).sum():
                    replication[f"{lang}/{ins}/{task}/{g}"] = {**did(sel(language=lang, task=task) & m, ins),
                                                              "questions": int(df.loc[sel(language=lang, task=task) & m, "qid"].nunique())}
numbers["did_replication"] = replication

# 7. Day of week: Hindi CoT off-by-one by level
dow = {}
for lang in LANGS:
    for lvl in DIFFS:
        s = df[sel(task="day_of_week", language=lang, condition="cot", difficulty=lvl) & df["scored"].to_numpy()]["weekday_offset"].dropna()
        dow[f"{lang}/{lvl}"] = {"correct": float((s == 0).mean()), "plus_one": float((s == 1).mean()),
                                "minus_one": float((s == -1).mean()), "n": int(len(s))}
numbers["day_of_week_cot_by_level"] = dow

with open(OUT / "numbers.json", "w", encoding="utf-8") as f:
    json.dump(numbers, f, ensure_ascii=False, indent=2, default=float)
print("done")
