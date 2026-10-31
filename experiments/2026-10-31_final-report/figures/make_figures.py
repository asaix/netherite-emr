from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import style as S

HERE = Path(__file__).parent
ROOT = HERE.parents[2]
A = HERE.parent / "audit"
HI = A / "hinglish" / "fig_data"
LR = A / "lr" / "fig_data"
PB = A / "part_b_interventions" / "fig_data"
PC = A / "part_c_encot" / "fig_data"
ED = ROOT / "tests" / "ed_audit" / "outputs" / "final_report_audit" / "fig_data"
OUT = HERE / "out"

LEVELS = list(S.DIFFICULTY)
TASKS = list(S.TASK_LABEL)
INS = {"no_insertion": "none", "similar_insertion": "similar", "dissimilar_insertion": "dissimilar"}
S.apply()


def by_level():
    d = pd.read_csv(PC / "figC1_accuracy_by_level.csv")
    fig, ax = plt.subplots(figsize=(S.COLUMN_IN, 2.15))
    x = np.arange(5)
    for c in ["English CoT", "Hindi en-CoT", "Hindi CLP", "Hindi CoT", "Hindi direct"]:
        r = d[d.condition == c].set_index("level").loc[LEVELS]
        st = S.condition(c)
        ax.errorbar(x, r.accuracy, yerr=[r.accuracy - r.lo, r.hi - r.accuracy], color=st["color"], marker=st["marker"],
                    ls=st["ls"], label=S.ALIASES.get(c, c), mec="white", mew=0.3)
    ax.set_xticks(x, [S.DIFFICULTY_LABEL[l] for l in LEVELS])
    ax.set_ylabel("Accuracy (%)")
    ax.set_ylim(20, 100)
    ax.legend(ncol=3, loc="lower center", bbox_to_anchor=(0.5, 1.0), columnspacing=1.0)
    S.save(fig, OUT / "by_level")


def task_bars():
    d = pd.read_csv(PC / "figC2_accuracy_by_task.csv").set_index("task").loc[TASKS]
    fig, ax = plt.subplots(figsize=(S.FULL_IN, 1.75))
    w = 0.2
    for i, c in enumerate(["Hindi CoT", "Hindi CLP", "Hindi en-CoT", "English CoT"]):
        st = S.condition(c)
        ax.bar(np.arange(9) + (i - 1.5) * w, d[c], w * 0.92, color=st["color"], hatch=st["hatch"], edgecolor="white",
               label=S.ALIASES.get(c, c))
    ax.set_xticks(np.arange(9), [S.TASK_LABEL[t].replace(" ", "\n", 1) for t in TASKS], fontsize=7)
    ax.set_ylabel("Accuracy (%)")
    ax.set_ylim(0, 100)
    ax.legend(ncol=4, loc="lower center", bbox_to_anchor=(0.5, 1.0))
    S.save(fig, OUT / "task_bars")


def decomposition():
    d = pd.read_csv(PC / "new_decomposition.csv")
    d = d[d["conv"] == "answered"].set_index("cut")
    cuts = ["pooled", "no_insertion", "similar_insertion", "dissimilar_insertion"] + LEVELS + TASKS
    labels = {"pooled": "All questions", "no_insertion": "No distractor", "similar_insertion": "Time-related",
              "dissimilar_insertion": "Unrelated", **S.DIFFICULTY_LABEL, **S.TASK_LABEL}
    y = []
    pos = 0
    for c in cuts:
        y.append(pos)
        pos += 1
        if c in ("pooled", "dissimilar_insertion", "very_very_long"):
            pos += 0.6
    r = d.loc[cuts]
    a = r["reasoning part (en-CoT - Hi CoT)"].astype(float)
    b = r["question part (En CoT - en-CoT)"].astype(float)
    fig, ax = plt.subplots(figsize=(S.COLUMN_IN, 3.0))
    ax.barh(y, a, 0.78, color=S.CONDITIONS["en-CoT"]["color"], edgecolor="white", label="Reasoning language (en-CoT − Hindi CoT)")
    ax.barh(y, b, 0.78, left=a, color=S.CONDITIONS["English CoT"]["color"], hatch="///", edgecolor="white", label="Question language (English CoT − en-CoT)")
    ax.set_yticks(y, [labels[c] for c in cuts], fontsize=7)
    ax.invert_yaxis()
    ax.set_xlabel("English−Hindi CoT gap (points)")
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True)
    ax.legend(loc="lower center", bbox_to_anchor=(0.32, 1.0), fontsize=7, ncol=1)
    S.save(fig, OUT / "decomposition")


def lr_forest():
    d = pd.read_csv(LR / "fig3_or_by_token_view.csv")
    d = d[d.model == "primary"].set_index("view")
    views = [("full", "All tokens (as reported)"), ("noans", "No answer tokens"), ("noansval", "No answer-valued tokens"),
             ("ops", "Op types"), ("opsnoans", "Op types, no answer ops")]
    fig, ax = plt.subplots(figsize=(S.COLUMN_IN, 1.25))
    for i, (v, l) in enumerate(views):
        r = d.loc[v]
        ax.errorbar(r.or_per_sd, i, xerr=[[r.or_per_sd - r.or_sd_lo], [r.or_sd_hi - r.or_per_sd]], color=S.INK, marker="o", capsize=1.5)
        ax.annotate(f"{r.or_per_sd:.2f}", (r.or_sd_hi, i), xytext=(3, 0), textcoords="offset points", va="center", fontsize=7, color=S.MUTED)
    ax.axvline(1, color=S.MUTED, lw=0.6, ls="--")
    ax.set_xscale("log")
    ax.set_xticks([1, 2, 4, 8], ["1", "2", "4", "8"])
    ax.minorticks_off()
    ax.set_xlim(0.9, 12)
    ax.set_yticks(range(len(views)), [l for _, l in views], fontsize=7)
    ax.invert_yaxis()
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True)
    ax.set_xlabel("Odds ratio of disagreement per SD of divergence")
    S.save(fig, OUT / "lr_forest")


def distance():
    d = pd.read_csv(HERE / "data" / "distance.csv").set_index("kind")
    names = [("E_self", "Only a distractor added", "English CoT, with vs without", True),
             ("E_M", "Only the question language", "English CoT vs en-CoT", False),
             ("M_H", "Only the reasoning language", "en-CoT vs Hindi CoT", False),
             ("E_H", "Question + reasoning language", "English CoT vs Hindi CoT", False),
             ("E_H_otherq", "Different questions", "English CoT vs Hindi CoT", True)]
    fig, ax = plt.subplots(figsize=(S.COLUMN_IN, 2.0))
    fig.subplots_adjust(left=0.47, right=0.9, top=0.9, bottom=0.2)
    tr = ax.get_yaxis_transform()
    for i, (k, what, pair, ref) in enumerate(names):
        r = d.loc[k]
        c = S.MUTED if ref else S.CONDITIONS["English CoT"]["color"]
        ax.errorbar(r.full, i, xerr=[[r.full - r.full_lo], [r.full_hi - r.full]], color=c, marker="o" if ref else "s",
                    mfc="white" if ref else c, ms=4, lw=0.9, capsize=1.5)
        ax.annotate(f"{r.full:.3f}", (r.full_hi, i), xytext=(3, 0), textcoords="offset points", va="center", fontsize=7, color=S.INK)
        ax.text(-0.03, i - 0.04, what, transform=tr, ha="right", va="bottom", fontsize=6.5, fontweight="bold", color=S.INK)
        ax.text(-0.03, i + 0.04, pair, transform=tr, ha="right", va="top", fontsize=6, color=S.MUTED)
    ax.text(-0.03, 1.01, "What differs between the two traces", transform=ax.transAxes, ha="right", va="bottom", fontsize=6,
            fontstyle="italic", color=S.MUTED)
    ax.set_yticks([])
    ax.set_ylim(len(names) - 0.4, -0.6)
    ax.set_xlim(0.68, 1.0)
    ax.set_xticks([0.7, 0.8, 0.9, 1.0])
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True)
    ax.set_xlabel("Mean RDS\n(0 = same steps, 1 = no steps shared)", fontsize=7)
    S.save(fig, OUT / "distance")


def interventions():
    d = pd.read_csv(PB / "fig_b1_contrasts.csv")
    groups = ["Hindi, all", "Hindi, opening", "Hindi, later", "English, all", "English, opening", "English, later"]
    labels = {"a": "Q − P\ndistractor removed", "b": "M − P\nmention kept", "c": "P − P1\nsentence before"}
    fig, axes = plt.subplots(1, 3, figsize=(S.COLUMN_IN, 1.55), sharey=True)
    for ax, p in zip(axes, "abc"):
        for i, g in enumerate(groups):
            r = d[(d.panel == p) & (d.group == g)]
            if r.empty:
                continue
            r = r.iloc[0]
            st = S.LANGUAGE["Hindi" if g.startswith("Hindi") else "English"]
            ax.errorbar(r.mean_pts, i, xerr=[[r.mean_pts - r.ci_low], [r.ci_high - r.mean_pts]], color=st["color"], marker=st["marker"], capsize=1.2, ms=3.2, lw=0.9)
        ax.axvline(0, color=S.MUTED, lw=0.6, ls="--")
        ax.set_title(labels[p], fontsize=7)
        ax.grid(axis="y", visible=False)
        ax.grid(axis="x", visible=True)
        ax.tick_params(axis="x", labelsize=6.5)
        ax.locator_params(axis="x", nbins=3)
    axes[0].set_yticks(range(6), [g.replace(", ", ": ") for g in groups], fontsize=7)
    axes[0].invert_yaxis()
    fig.supxlabel("Difference in accuracy (points)", fontsize=7.5, y=-0.1)
    fig.subplots_adjust(wspace=0.12)
    S.save(fig, OUT / "interventions")


def recurrence():
    d = pd.read_csv(PC / "new_recurrence_error_types_by_k.csv")
    sets = [s for s in ["En CoT", "Hi CoT", "CLP", "en-CoT"] if s in set(d["set"])]
    parts = [("correct%", "Correct", "#D9D9D9", ""), ("backwards%", "Backwards", S.CONDITIONS["Hindi CoT"]["color"], "///"),
             ("k-1 steps%", "One step short", S.CONDITIONS["English CoT"]["color"], "..."), ("today%", "Today", S.CONDITIONS["CLP"]["color"], "xxx"),
             ("other%", "Other", "#6F6F6F", "")]
    fig, axes = plt.subplots(1, len(sets), figsize=(S.COLUMN_IN, 1.45), sharey=True)
    for ax, s in zip(np.atleast_1d(axes), sets):
        r = d[d["set"] == s]
        x = np.arange(len(r))
        bottom = np.zeros(len(r))
        for col, lab, c, h in parts:
            ax.bar(x, r[col], 0.85, bottom=bottom, color=c, hatch=h, edgecolor="white", label=lab, lw=0.2)
            bottom += r[col].to_numpy()
        ax.set_title({"En CoT": "English CoT", "Hi CoT": "Hindi CoT"}.get(s, s), fontsize=7)
        ax.set_xticks(x, r["k"].astype(str), fontsize=5, rotation=90)
        ax.grid(False)
    np.atleast_1d(axes)[0].set_ylabel("Share of answers (%)", fontsize=7)
    h, l = np.atleast_1d(axes)[0].get_legend_handles_labels()
    fig.legend(h, l, ncol=5, loc="lower center", bbox_to_anchor=(0.5, 0.98), fontsize=6.2, columnspacing=0.7, handlelength=1.1)
    fig.supxlabel("Occurrence number k", fontsize=7, y=-0.2)
    S.save(fig, OUT / "recurrence_k")


def hinglish_dumbbell():
    d = pd.read_csv(HI / "fig1_accuracy_by_task.csv")
    order = TASKS + ["all"]
    labs = {**S.TASK_LABEL, "all": "All tasks"}
    fig, axes = plt.subplots(1, 2, figsize=(S.COLUMN_IN, 2.0), sharey=True, sharex=True)
    for ax, lang, title in zip(axes, ["en_US", "hi_IN"], ["English questions", "Hindi questions"]):
        r = d[d.language == lang].set_index("task").reindex(order)
        y = np.arange(len(order))
        ax.hlines(y, r[["direct", "std", "hing"]].min(axis=1), r[["direct", "std", "hing"]].max(axis=1), color="#D0D0D0", lw=1.6, zorder=1)
        ax.scatter(r.direct, y, color=S.MUTED, marker="X", s=11, label="Direct", zorder=2, lw=0)
        ax.scatter(r["std"], y, color=S.CONDITIONS["English CoT"]["color"], marker="s", s=10, label="Standard CoT", zorder=2, lw=0)
        ax.scatter(r.hing, y, color=S.CONDITIONS["Hinglish CoT"]["color"], marker="v", s=13, label="Hinglish CoT", zorder=3, lw=0)
        ax.set_title(title, fontsize=7.5)
        ax.grid(axis="y", visible=False)
        ax.grid(axis="x", visible=True)
    axes[0].set_yticks(np.arange(len(order)), [labs[o] for o in order], fontsize=6.8)
    axes[0].invert_yaxis()
    axes[0].set_xlim(0, 102)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, ncol=3, loc="lower center", bbox_to_anchor=(0.55, -0.16), fontsize=7)
    fig.supxlabel("Accuracy (%)", fontsize=7.5, y=-0.04, x=0.6)
    S.save(fig, OUT / "hinglish_tasks")


def hinglish_level():
    d = pd.read_csv(HI / "fig2_accuracy_by_level.csv")
    d = d[d.convention == "answered"]
    fig, axes = plt.subplots(1, 2, figsize=(S.COLUMN_IN, 1.5), sharey=True)
    x = np.arange(5)
    conds = sorted(d.condition.unique())
    name = {"Direct": ("Direct", S.MUTED, "X", ":"), "Standard CoT": ("Standard CoT", S.CONDITIONS["English CoT"]["color"], "s", "-"),
            "Hinglish CoT": ("Hinglish CoT", S.CONDITIONS["Hinglish CoT"]["color"], "v", "-.")}
    for ax, lang, title in zip(axes, ["en_US", "hi_IN"], ["English questions", "Hindi questions"]):
        for c in ["Direct", "Standard CoT", "Hinglish CoT"]:
            match = [k for k in conds if k.lower().startswith(c.split()[0].lower())]
            r = d[(d.language == lang) & (d.condition == match[0])].set_index("difficulty").loc[LEVELS]
            n, col, m, ls = name[c]
            ax.plot(x, r.accuracy, color=col, marker=m, ls=ls, ms=3, label=n)
            ax.fill_between(x, r.lo, r.hi, color=col, alpha=0.15, lw=0)
        ax.set_title(title, fontsize=7.5)
        ax.set_xticks(x, ["S", "M", "L", "VL", "VVL"], fontsize=6.5)
    axes[0].set_ylabel("Accuracy (%)", fontsize=7.5)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, ncol=3, loc="lower center", bbox_to_anchor=(0.55, 0.96), fontsize=7)
    S.save(fig, OUT / "hinglish_level")


def hinglish_style():
    d = pd.read_csv(HI / "fig3_style_shares.csv")
    fig, ax = plt.subplots(figsize=(S.COLUMN_IN, 0.85))
    parts = [("roman", "Roman Hinglish", S.CONDITIONS["Hinglish CoT"]["color"], ""), ("plain", "Plain English", S.CONDITIONS["English CoT"]["color"], "///"),
             ("devanagari", "Devanagari mix", S.CONDITIONS["Hindi CoT"]["color"], "...")]
    styles = set(d["style"])
    for i, lang in enumerate(["en_US", "hi_IN"]):
        left = 0
        for key, lab, c, h in parts:
            k = [s for s in styles if s.lower().startswith(key[:4])]
            v = d[(d.language == lang) & (d["style"] == k[0])].pct_of_traces.sum() if k else 0
            ax.barh(i, v, 0.7, left=left, color=c, hatch=h, edgecolor="white", label=lab if i == 0 else None)
            if v > 8:
                ax.text(left + v / 2, i, f"{v:.0f}%", ha="center", va="center", fontsize=7, color="white", bbox={"fc": c, "ec": "none", "pad": 0.6})
            left += v
    ax.barh(0, 0, color=parts[2][2], hatch=parts[2][3], label=None)
    ax.set_yticks([0, 1], ["English Q.", "Hindi Q."], fontsize=7)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.grid(False)
    ax.set_xlabel("Share of Hinglish-prompted traces (%)", fontsize=7.5)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(fc=c, hatch=h, ec="white", label=l) for _, l, c, h in parts], ncol=3, loc="lower center", bbox_to_anchor=(0.45, 0.98), fontsize=6.8)
    S.save(fig, OUT / "hinglish_style")


def hinglish_bytask():
    d = pd.read_csv(HI / "fig4_style_by_task.csv").set_index("task").loc[TASKS]
    fig, ax = plt.subplots(figsize=(S.COLUMN_IN, 1.6))
    y = np.arange(9)
    ax.barh(y - 0.2, d.roman_diff, 0.38, color=S.CONDITIONS["Hinglish CoT"]["color"], edgecolor="white", label="Roman Hinglish")
    ax.barh(y + 0.2, d.plain_diff, 0.38, color=S.CONDITIONS["English CoT"]["color"], hatch="///", edgecolor="white", label="Plain English")
    ax.set_yticks(y, [S.TASK_LABEL[t] for t in TASKS], fontsize=6.8)
    ax.invert_yaxis()
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True)
    ax.set_xlabel("Hinglish CoT minus standard CoT (points)", fontsize=7.5)
    ax.legend(loc="lower left", fontsize=6.8)
    S.save(fig, OUT / "hinglish_bytask")


def lr_hist():
    d = pd.read_csv(LR / "fig1_rds_distribution.csv")
    fig, axes = plt.subplots(1, 2, figsize=(S.COLUMN_IN, 1.35), sharex=True)
    for ax, mode, title in zip(axes, ["off", "on"], ["Thinking off", "Thinking on"]):
        for k, lab, c, ls in [(0, "Agree", S.BINARY[0], "-"), (1, "Disagree", S.BINARY[1], "--")]:
            r = d[(d["mode"] == mode) & (d.disagree == k)]
            ax.step(r.bin_lo, r.density, where="post", color=c, ls=ls, label=lab)
            ax.axvline(r["median"].iloc[0], color=c, lw=0.6, ls=":")
        ax.set_title(title, fontsize=7.5)
        ax.set_xlabel("RDS", fontsize=7.5)
    axes[0].set_ylabel("Density", fontsize=7.5)
    axes[0].legend(fontsize=6.8, loc="upper left")
    S.save(fig, OUT / "lr_hist")


def lr_bins():
    d = pd.read_csv(LR / "fig2_rate_by_rds_bin.csv")
    d = d[d.shown_in_report == True]
    fig, ax = plt.subplots(figsize=(S.COLUMN_IN, 1.45))
    for mode, lab, m, ls in [("off", "Thinking off", "s", "-"), ("on", "Thinking on", "o", "--")]:
        r = d[d["mode"] == mode].sort_values("mid")
        lo = r.cluster_lo.fillna(r.wilson_lo)
        hi = r.cluster_hi.fillna(r.wilson_hi)
        ax.errorbar(r.mid, r.rate, yerr=[(r.rate - lo).clip(lower=0), (hi - r.rate).clip(lower=0)], color=S.BINARY[mode], marker=m, ls=ls, label=lab, capsize=1.5, ms=3.5)
    ax.set_xlabel("RDS bin (width 0.1, midpoint)", fontsize=7.5)
    ax.set_ylabel("Disagreement rate", fontsize=7.5)
    ax.legend(fontsize=6.8, loc="upper left")
    S.save(fig, OUT / "lr_bins")


def ed_task_difficulty():
    d = pd.read_csv(ED / "doc_content_task_by_difficulty.csv")
    fig, ax = plt.subplots(figsize=(S.FULL_IN, 1.5))
    w = 0.16
    for i, l in enumerate(LEVELS):
        r = d[d.difficulty == l].set_index("task").loc[TASKS]
        ax.bar(np.arange(9) + (i - 2) * w, r["mean"], w * 0.92, color=S.DIFFICULTY[l], edgecolor="white", yerr=r.ci_cube,
               error_kw={"lw": 0.5, "ecolor": S.INK}, label=S.DIFFICULTY_LABEL[l])
    ax.set_xticks(np.arange(9), [S.TASK_LABEL[t].replace(" ", "\n", 1) for t in TASKS], fontsize=7)
    ax.set_ylabel("Normalised edit distance", fontsize=7.5)
    ax.set_ylim(0, 1)
    ax.legend(ncol=5, loc="lower center", bbox_to_anchor=(0.5, 1.0), fontsize=7)
    S.save(fig, OUT / "ed_task_difficulty")


def ed_outcome():
    d = pd.read_csv(ED / "doc_content_outcome_by_insertion.csv")
    outs = ["both correct", "en only", "hi only", "both wrong", "unanswered"]
    fig, ax = plt.subplots(figsize=(S.COLUMN_IN, 1.45))
    w = 0.26
    for i, (k, v) in enumerate(INS.items()):
        st = S.INSERTION[v]
        r = d[d.insertion == k].set_index("outcome").loc[outs]
        ax.bar(np.arange(5) + (i - 1) * w, r["mean"], w * 0.92, color=st["color"], hatch=st["hatch"], edgecolor="white", yerr=r.ci_cube,
               error_kw={"lw": 0.5, "ecolor": S.INK}, label=st["label"])
    ax.set_xticks(np.arange(5), ["Both\ncorrect", "English\nonly", "Hindi\nonly", "Both\nwrong", "Unanswered"], fontsize=6.8)
    ax.set_ylabel("Normalised edit distance", fontsize=7.5)
    ax.set_ylim(0, 1.05)
    ax.legend(ncol=3, loc="lower center", bbox_to_anchor=(0.5, 1.0), fontsize=6.8)
    S.save(fig, OUT / "ed_outcome")


def ed_task_set():
    d = pd.read_csv(ED / "doc_content_task_by_set.csv")
    fig, ax = plt.subplots(figsize=(S.COLUMN_IN, 1.45))
    w = 0.4
    col = "set" if "set" in d else d.columns[1]
    for i, (k, lab, c, h) in enumerate([("standard", "Thinking off", S.BINARY["off"], ""), ("ron", "Thinking on, visible reply", S.BINARY["on"], "///")]):
        r = d[d[col] == k].set_index("task").loc[TASKS]
        ax.bar(np.arange(9) + (i - 0.5) * w, r["mean"], w * 0.92, color=c, hatch=h, edgecolor="white", yerr=r.ci_cube, error_kw={"lw": 0.5, "ecolor": S.INK}, label=lab)
    ax.set_xticks(np.arange(9), [S.TASK_LABEL[t] for t in TASKS], fontsize=6, rotation=35, ha="right", rotation_mode="anchor")
    ax.set_ylabel("Normalised edit distance", fontsize=7.5)
    ax.set_ylim(0, 1.05)
    ax.legend(ncol=2, loc="lower center", bbox_to_anchor=(0.5, 1.0), fontsize=6.8)
    S.save(fig, OUT / "ed_task_set")


def ed_insertion_difficulty():
    d = pd.read_csv(ED / "doc_content_insertion_by_difficulty.csv")
    fig, ax = plt.subplots(figsize=(S.COLUMN_IN, 1.45))
    w = 0.16
    keys = list(INS)
    for i, l in enumerate(LEVELS):
        r = d[d.difficulty == l].set_index("insertion").loc[keys]
        ax.bar(np.arange(3) + (i - 2) * w, r["mean"], w * 0.92, color=S.DIFFICULTY[l], edgecolor="white", yerr=r.ci_cube, error_kw={"lw": 0.5, "ecolor": S.INK}, label=S.DIFFICULTY_LABEL[l])
    ax.set_xticks(np.arange(3), [S.INSERTION[INS[k]]["label"] for k in keys], fontsize=7)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Normalised edit distance", fontsize=7.5)
    ax.legend(ncol=5, loc="lower center", bbox_to_anchor=(0.5, 1.0), fontsize=6.2, columnspacing=0.6, handlelength=1.0)
    S.save(fig, OUT / "ed_insertion_difficulty")


def ed_set_box():
    d = pd.read_csv(ED / "doc_content_set_by_insertion.csv")
    col = "set" if "set" in d else d.columns[0]
    fig, ax = plt.subplots(figsize=(S.COLUMN_IN, 1.45))
    stats, pos, cols = [], [], []
    for i, s in enumerate(["standard", "ron"]):
        for j, k in enumerate(INS):
            r = d[(d[col] == s) & (d.insertion == k)].iloc[0]
            stats.append({"med": r["median"], "q1": r.q1, "q3": r.q3, "whislo": r.minimum, "whishi": r.maximum, "fliers": []})
            pos.append(i * 1.1 + (j - 1) * 0.3)
            cols.append(S.INSERTION[INS[k]])
    b = ax.bxp(stats, positions=pos, widths=0.25, patch_artist=True, showfliers=False)
    for p, c in zip(b["boxes"], cols):
        p.set(facecolor=c["color"], hatch=c["hatch"], edgecolor=S.INK, linewidth=0.4)
    for m in b["medians"]:
        m.set(color="white", linewidth=0.9)
    ax.set_xticks([0, 1.1], ["Thinking off", "Thinking on, visible reply"], fontsize=7)
    ax.set_ylabel("Normalised edit distance", fontsize=7.5)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(fc=S.INSERTION[v]["color"], hatch=S.INSERTION[v]["hatch"], ec="white", label=S.INSERTION[v]["label"]) for v in INS.values()], ncol=3,
              loc="lower center", bbox_to_anchor=(0.5, 1.0), fontsize=6.8)
    S.save(fig, OUT / "ed_set_box")


for f in [by_level, task_bars, decomposition, lr_forest, distance, interventions, recurrence, hinglish_dumbbell, hinglish_level, hinglish_style,
          hinglish_bytask, lr_hist, lr_bins, ed_task_difficulty, ed_outcome, ed_task_set, ed_insertion_difficulty, ed_set_box]:
    try:
        f()
        print("ok", f.__name__)
    except Exception as e:
        print("FAIL", f.__name__, repr(e))
