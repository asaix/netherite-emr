from common import *

D = pd.read_csv(FIG / "rq1_cot_delta_by_scope_split.csv")
P = pd.read_csv(FIG / "fig_penalty_forest.csv")
Gp = pd.read_csv(FIG / "rq1_gap_by_scope_split.csv")
GG = pd.read_csv(FIG / "rq1_gain_gap_by_scope_split.csv")


def c(r, k="v"):
    return f"{r[k]:+.1f} [{r['lo']:+.1f}, {r['hi']:+.1f}]"


def tab_overall():
    out = ["| Language, scoring | Direct | CoT | Pooled delta | None | Time-related | Unrelated | McNemar CoT vs direct wins, pooled |", "|---|---|---|---|---|---|---|---|"]
    for l, n in (("en_US", "English"), ("hi_IN", "Hindi")):
        for s in ("answered", "strict"):
            x = D[(D.lang == l) & (D.scoring == s) & (D.scope == "all")].set_index("split")
            out.append(f"| {n}, {s} | {x.loc['pooled', 'direct']:.1f} | {x.loc['pooled', 'cot']:.1f} | {c(x.loc['pooled'])} | {c(x.loc['none'])} | {c(x.loc['similar'])} | {c(x.loc['dissimilar'])} | {x.loc['pooled', 'cot_wins']:,} vs {x.loc['pooled', 'direct_wins']:,} |")
    return "\n".join(out)


def tab_task():
    out = ["| Language | Task | Pooled | None | Time-related | Unrelated |", "|---|---|---|---|---|---|"]
    for l, n in (("en_US", "English"), ("hi_IN", "Hindi")):
        for t in TASKS:
            x = D[(D.lang == l) & (D.scoring == "answered") & (D.scope == t)].set_index("split")
            cells = []
            for s in ("pooled", "none", "similar", "dissimilar"):
                star = "*" if x.loc[s, "q_t_holm"] < 0.05 else ""
                cells.append(f"{x.loc[s, 'v']:+.1f}{star} [{x.loc[s, 'lo']:+.1f}, {x.loc[s, 'hi']:+.1f}]")
            out.append(f"| {n} | {t} | " + " | ".join(cells) + " |")
    return "\n".join(out)


def tab_level():
    out = ["| Language | Level | Pooled | None | Time-related | Unrelated |", "|---|---|---|---|---|---|"]
    for l, n in (("en_US", "English"), ("hi_IN", "Hindi")):
        for t in LEVELS:
            x = D[(D.lang == l) & (D.scoring == "answered") & (D.scope == t)].set_index("split")
            out.append(f"| {n} | {t} | " + " | ".join(c(x.loc[s]) for s in ("pooled", "none", "similar", "dissimilar")) + " |")
    return "\n".join(out)


def tab_gap():
    out = ["| Scoring | Condition | Pooled | None | Time-related | Unrelated |", "|---|---|---|---|---|---|"]
    for s in ("answered", "strict"):
        for k in ("direct", "cot"):
            x = Gp[(Gp.scoring == s) & (Gp.cond == k) & (Gp.scope == "all")].set_index("split")
            out.append(f"| {s} | {k} | " + " | ".join(c(x.loc[p]) for p in ("pooled", "none", "similar", "dissimilar")) + " |")
    return "\n".join(out)


def tab_gain():
    out = ["| Scope | Pooled | None | Time-related | Unrelated |", "|---|---|---|---|---|"]
    for t in ["all"] + TASKS:
        x = GG[(GG.scoring == "answered") & (GG.scope == t)].set_index("split")
        out.append(f"| {t} | " + " | ".join(c(x.loc[p]) for p in ("pooled", "none", "similar", "dissimilar")) + " |")
    return "\n".join(out)


def tab_pen(scope_list):
    out = ["| Scope | Distractor | English | Hindi | Hindi minus English | p (paired by question) |", "|---|---|---|---|---|---|"]
    for sc in ("answered", "strict"):
        for i, nm in (("similar_insertion", "time-related"), ("dissimilar_insertion", "unrelated")):
            for t in scope_list:
                x = P[(P.scoring == sc) & (P.ins == i) & (P.scope == t)].set_index("lang")
                f = lambda l: f"{x.loc[l, 'penalty']:+.1f} [{x.loc[l, 'lo']:+.1f}, {x.loc[l, 'hi']:+.1f}]"
                out.append(f"| {t}, {sc} | {nm} | {f('en_US')} | {f('hi_IN')} | {f('hi_minus_en')} | {x.loc['hi_minus_en', 'q_t_p']:.3f} |")
    return "\n".join(out)


def tab_task_pen():
    out = ["| Task | English: direct drop, CoT drop, penalty | Hindi: direct drop, CoT drop, penalty | Hindi minus English |", "|---|---|---|---|"]
    x = P[(P.scoring == "answered") & (P.ins == "similar_insertion")]
    for t in TASKS:
        y = x[x.scope == t].set_index("lang")
        f = lambda l: f"{y.loc[l, 'drop_direct']:+.1f}, {y.loc[l, 'drop_cot']:+.1f}, **{y.loc[l, 'penalty']:+.1f}** [{y.loc[l, 'lo']:+.1f}, {y.loc[l, 'hi']:+.1f}]" + ("*" if y.loc[l, "q_t_holm"] < 0.05 else "")
        z = y.loc["hi_minus_en"]
        out.append(f"| {t} | {f('en_US')} | {f('hi_IN')} | {z.penalty:+.1f} [{z.lo:+.1f}, {z.hi:+.1f}]" + ("*" if z.q_t_holm < 0.05 else "") + " |")
    return "\n".join(out)


body = (HERE / "analysis_template.md").read_text(encoding="utf-8")
for k, v in {"T_OVERALL": tab_overall(), "T_TASK": tab_task(), "T_LEVEL": tab_level(), "T_GAP": tab_gap(), "T_GAIN": tab_gain(), "T_PEN_ALL": tab_pen(["all"]), "T_PEN_LEVEL": tab_pen(LEVELS), "T_TASK_PEN": tab_task_pen()}.items():
    body = body.replace("{{" + k + "}}", v)
(HERE / "analysis.md").write_text(body, encoding="utf-8")
