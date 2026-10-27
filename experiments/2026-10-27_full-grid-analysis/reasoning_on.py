import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("pdf")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import binomtest

import temporal_answers as T

M = T.use_parser("current")
HERE = Path(__file__).resolve().parent
RUN = HERE.parent / "2026-10-25_test-reasoning-on" / "outputs"
OUT = HERE / "outputs" / "reasoning_on"
(OUT / "plots").mkdir(parents=True, exist_ok=True)

B = 2000
RNG = np.random.default_rng(0)
DIFFS = ["short", "medium", "long", "very_long", "very_very_long"]
DIFF_LABEL = {"short": "Short", "medium": "Medium", "long": "Long", "very_long": "Very long", "very_very_long": "V. v. long"}
LANGS = ["en_US", "hi_IN"]
LANG = {"en_US": "English", "hi_IN": "Hindi"}
INS = ["no_insertion", "similar_insertion", "dissimilar_insertion"]
WAIT = re.compile(r"\bwait\b|\bhmm\b|\bactually\b", re.I)

plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Times New Roman"], "font.size": 9, "axes.titlesize": 9,
    "axes.labelsize": 9, "legend.fontsize": 8, "xtick.labelsize": 8, "ytick.labelsize": 8,
    "pdf.fonttype": 42, "ps.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False,
})


def script_ratio(text, language):
    text = M.ANSWER.sub("", text or "")
    hindi, english = len(M.HINDI_WORD.findall(text)), len(M.ENGLISH_WORD.findall(text))
    target = hindi if language == "hi_IN" else english
    return target / (hindi + english) if hindi + english else None


on_records = [r for d in DIFFS for r in json.load(open(RUN / d / "results.json", encoding="utf-8"))]
rows = []
for r in on_records:
    m = r["meta"]
    answered = M.extract_answer(r["content"]) is not None
    usage = r.get("usage") or {}
    rows.append({
        "id": r["id"], "qid": f"{m['difficulty']}/{m['task']}/{m['question_id']}", "difficulty": m["difficulty"],
        "task": m["task"], "language": m["language"], "insertion": m["insertion"], "condition": r["condition"],
        "scored_on": answered, "correct_on": float(M.is_correct(r)) if answered else np.nan,
        "cutoff_on": r["finish_reason"] == "length",
        "completion_tokens_on": usage.get("completion_tokens"),
        "reasoning_tokens_on": (usage.get("completion_tokens_details") or {}).get("reasoning_tokens"),
        "hidden_target_ratio": script_ratio(r.get("reasoning_content"), m["language"]),
        "visible_target_ratio": script_ratio(r["content"], m["language"]),
        "hidden_mentions_language": len(re.findall(r"\bHindi\b|हिंदी|हिन्दी", r.get("reasoning_content") or "")),
        "hidden_hesitations": len(WAIT.findall(r.get("reasoning_content") or "")),
    })
on = pd.DataFrame(rows)
off = pd.read_pickle(HERE / "outputs" / "data" / "responses_current.pkl")[["id", "scored", "correct", "cutoff", "completion_tokens"]]
off = off.rename(columns={"scored": "scored_off", "correct": "correct_off", "cutoff": "cutoff_off", "completion_tokens": "completion_tokens_off"})
df = on.merge(off, on="id", how="left", validate="one_to_one")
missing_off = int(df["scored_off"].isna().sum())
df = df[df["scored_off"].notna()].reset_index(drop=True)
df["scored_off"] = df["scored_off"].astype(bool)
df["correct_off"] = df["correct_off"].astype(float).where(df["scored_off"], np.nan)
for mode in ("on", "off"):
    df[f"strict_{mode}"] = df[f"correct_{mode}"].fillna(0.0)
qids = df["qid"].unique()
df["qi"] = df["qid"].map({q: i for i, q in enumerate(qids)})
Q = len(qids)
WEIGHTS = np.stack([np.bincount(RNG.integers(0, Q, Q), minlength=Q) for _ in range(B)])


def sel(**kw):
    mask = np.ones(len(df), dtype=bool)
    for k, v in kw.items():
        mask &= df[k].isin(v).to_numpy() if isinstance(v, (list, tuple, set)) else (df[k] == v).to_numpy()
    return mask


def acc(mask, col):
    sub = df[mask & df[col].notna().to_numpy()]
    c = np.bincount(sub["qi"], weights=sub[col], minlength=Q)
    n = np.bincount(sub["qi"], minlength=Q).astype(float)
    return c.sum() / n.sum(), (WEIGHTS @ c) / (WEIGHTS @ n), int(n.sum())


def stat(value, samples):
    lo, hi = np.percentile(samples, [2.5, 97.5])
    return {"value": float(value), "ci": [float(lo), float(hi)], "sig": bool(lo > 0 or hi < 0)}


def on_vs_off(mask, strict=False):
    a, b = ("strict_on", "strict_off") if strict else ("correct_on", "correct_off")
    both = mask & df[a].notna().to_numpy() & df[b].notna().to_numpy()
    v_on, s_on, n = acc(both, a)
    v_off, s_off, _ = acc(both, b)
    sub = df[both]
    up, down = int(((sub[a] == 1) & (sub[b] == 0)).sum()), int(((sub[a] == 0) & (sub[b] == 1)).sum())
    return {"off": float(v_off), "on": float(v_on), "n": n, **stat(v_on - v_off, s_on - s_off), "on_only": up, "off_only": down,
            "p": float(binomtest(up, up + down, 0.5).pvalue) if up + down else 1.0}


def cot_delta(mask, col):
    d, sd, _ = acc(mask & sel(condition="direct"), col)
    c, sc, _ = acc(mask & sel(condition="cot"), col)
    return {"direct": float(d), "cot": float(c), **stat(c - d, sc - sd)}


def did(mask, ins, col):
    drops = {}
    for cond in ("direct", "cot"):
        a0, b0, _ = acc(mask & sel(condition=cond, insertion="no_insertion"), col)
        a1, b1, _ = acc(mask & sel(condition=cond, insertion=ins), col)
        drops[cond] = (a0 - a1, b0 - b1)
    return {"drop_direct": float(drops["direct"][0]), "drop_cot": float(drops["cot"][0]),
            **stat(drops["cot"][0] - drops["direct"][0], drops["cot"][1] - drops["direct"][1])}


numbers = {"records_on": len(df), "questions": Q, "missing_off_pairs": missing_off,
           "settings": {"reasoning_effort": "low", "max_tokens_on": 16000, "max_tokens_off": 4096}}
comparison = {}
for lang in LANGS:
    for cond in ("direct", "cot"):
        comparison[f"{lang}/{cond}"] = on_vs_off(sel(language=lang, condition=cond))
        comparison[f"{lang}/{cond}/strict"] = on_vs_off(sel(language=lang, condition=cond), strict=True)
        for lvl in DIFFS:
            comparison[f"{lang}/{cond}/{lvl}"] = on_vs_off(sel(language=lang, condition=cond, difficulty=lvl))
numbers["on_vs_off"] = comparison

paired = df[df["correct_on"].notna() & df["correct_off"].notna()]
numbers["cot_delta"] = {f"{lang}/{mode}": cot_delta(sel(language=lang) & df["id"].isin(paired["id"]).to_numpy(), f"correct_{mode}")
                        for lang in LANGS for mode in ("off", "on")}
gap = {}
for cond in ("direct", "cot"):
    for mode in ("off", "on"):
        col = f"correct_{mode}"
        m = sel(condition=cond) & df["id"].isin(paired["id"]).to_numpy()
        e, se, _ = acc(m & sel(language="en_US"), col)
        h, sh, _ = acc(m & sel(language="hi_IN"), col)
        gap[f"{cond}/{mode}"] = stat(e - h, se - sh)
numbers["en_hi_gap"] = gap
numbers["did"] = {f"{lang}/{ins}/{mode}": did(sel(language=lang), ins, f"correct_{mode}")
                  for lang in LANGS for ins in INS[1:] for mode in ("off", "on")}

traces = {}
for lang in LANGS:
    for cond in ("direct", "cot"):
        g = df[sel(language=lang, condition=cond)]
        traces[f"{lang}/{cond}"] = {
            "cutoff_on": float(g["cutoff_on"].mean()), "cutoff_off": float(g["cutoff_off"].mean()),
            "unscored_on": float((~g["scored_on"]).mean()),
            "median_completion_tokens_on": float(g["completion_tokens_on"].median()),
            "median_reasoning_tokens_on": float(g["reasoning_tokens_on"].median()),
            "median_completion_tokens_off": float(g["completion_tokens_off"].median()),
            "hidden_target_ratio_median": float(g["hidden_target_ratio"].median()),
            "hidden_target_ratio_mean": float(g["hidden_target_ratio"].mean()),
            "visible_target_ratio_mean": float(g["visible_target_ratio"].mean()),
            "hidden_mentions_language_median": float(g["hidden_mentions_language"].median()),
            "hidden_hesitations_median": float(g["hidden_hesitations"].median()),
        }
numbers["traces"] = traces
by_task = []
for (lang, cond, task), g in df.groupby(["language", "condition", "task"]):
    r = on_vs_off(sel(language=lang, condition=cond, task=task))
    by_task.append({"language": lang, "condition": cond, "task": task, "off": r["off"], "on": r["on"], "delta": r["value"],
                    "lo": r["ci"][0], "hi": r["ci"][1], "n": r["n"], "cutoff_on": float(g["cutoff_on"].mean())})
pd.DataFrame(by_task).to_csv(OUT / "by_task.csv", index=False)

fig, axes = plt.subplots(1, 2, figsize=(6.3, 2.2), sharey=True)
for ax, lang in zip(axes, LANGS):
    for cond, marker in (("direct", "o"), ("cot", "s")):
        for mode, ls, color in (("off", "-", "0.0"), ("on", "--", "0.5")):
            ys = [100 * comparison[f"{lang}/{cond}/{l}"][mode] for l in DIFFS]
            ax.plot(range(len(DIFFS)), ys, marker=marker, linestyle=ls, color=color, markersize=4,
                    markerfacecolor="white" if cond == "direct" else color,
                    label=f"{'CoT' if cond == 'cot' else 'Direct'}, reasoning {mode}")
    ax.set_xticks(range(len(DIFFS)), [DIFF_LABEL[l] for l in DIFFS], fontsize=7)
    ax.set_title(LANG[lang])
    ax.grid(axis="y", color="0.85", linewidth=0.5)
axes[0].set_ylabel("Accuracy (%)")
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.5, -0.04))
fig.tight_layout(rect=(0, 0.1, 1, 1))
fig.savefig(OUT / "plots" / "reasoning_on_off.pdf")
fig.savefig(OUT / "plots" / "reasoning_on_off.png", dpi=200)
plt.close(fig)


def signed(x):
    return f"{100 * x:+.1f}".replace("-", "$-$")


lines = [r"\begin{table}[t]", r"\centering", r"\small", r"\setlength{\tabcolsep}{3.5pt}", r"\begin{tabular}{@{}llrrl@{}}", r"\toprule",
         r"Language & Prompt & Off & On & On $-$ off [95\% CI] \\", r"\midrule"]
for lang in LANGS:
    for cond, name in (("direct", "Direct"), ("cot", "CoT")):
        v = comparison[f"{lang}/{cond}"]
        cell = f"{signed(v['value'])} [{signed(v['ci'][0])}, {signed(v['ci'][1])}]"
        lines.append(f"{LANG[lang] if cond == 'direct' else ''} & {name} & {100 * v['off']:.1f} & {100 * v['on']:.1f} & "
                     + (r"\textbf{" + cell + "}" if v["sig"] else cell) + r" \\")
lines += [r"\bottomrule", r"\end{tabular}",
          r"\caption{Accuracy (\%) with Sarvam's thinking mode off (main runs) and on (\texttt{reasoning\_effort: low}) on the same "
          r"450 questions (10 per task and level), paired by response. Bold: 95\% cluster-bootstrap interval excludes zero. "
          r"Thinking-on runs allowed 16k output tokens, thinking-off runs 4k.}",
          r"\label{tab:reasoning-on}", r"\end{table}"]
(OUT / "reasoning_on.tex").write_text("\n".join(lines) + "\n")

with open(OUT / "numbers.json", "w", encoding="utf-8") as f:
    json.dump(numbers, f, ensure_ascii=False, indent=2, default=float)
print(len(df), "thinking-on responses,", missing_off, "without a thinking-off pair")
