import io
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats
from scipy.special import expit
from statsmodels.stats.proportion import proportion_confint

from metrics import DIFFICULTY_ORDER

ROOT = Path(__file__).resolve().parent
INPUTS = {"on": ROOT / "edout" / "ron", "off": ROOT / "edout" / "standard"}
OUT = ROOT / "lr_out"
HEADER = "question_id,"
REQUIRED = ["question_id", "difficulty", "task", "insertion", "en_correct", "hi_correct",
            "content_norm_edit_distance", "content_en_len", "content_hi_len"]
KEY = ["reasoning_mode", "difficulty", "task", "insertion", "question_id"]
KEEP = ["uid", "question_id", "difficulty", "task", "insertion", "reasoning_mode", "en_correct", "hi_correct",
        "RDS", "content_en_len", "content_hi_len", "length_gap", "disagree", "source"]
REFERENCE = {"difficulty": "short", "task": "date_addition", "insertion": "no_insertion", "reasoning_mode": "off"}
CONTROLS = "C(difficulty) + C(task) + C(insertion) + C(reasoning_mode)"
MODELS = {
    "primary": f"disagree ~ RDS + {CONTROLS}",
    "length_adjusted": f"disagree ~ RDS + length_gap + {CONTROLS}",
}
PER_MODE_CONTROLS = "C(difficulty) + C(task) + C(insertion)"
ALPHA = 0.05
MAXITER = 200
MIN_LEVEL_EVENTS = 10
MIN_EPV = 10
MAX_ABS_COEF = 10
RDS_BINS = np.round(np.linspace(0, 1, 11), 2)
MIN_BIN_N = 20
GRID_POINTS = 101
GRID_QUANTILES = (0.01, 0.99)
COLORS = {"off": "#2a78d6", "on": "#eb6834", 0: "#2a78d6", 1: "#eb6834"}
SURFACE, INK, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
MODE_LABEL = {"off": "Reasoning OFF", "on": "Reasoning ON"}
DISAGREE_LABEL = {0: "Agree (disagree = 0)", 1: "Disagree (disagree = 1)"}

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
    "text.color": INK, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "axes.grid.axis": "y",
    "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True, "lines.linewidth": 2,
    "font.size": 10, "axes.titlesize": 11, "legend.frameon": False, "figure.dpi": 150,
})


def read_pairs(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    start = next((i for i, line in enumerate(lines) if line.startswith(HEADER)), None)
    if start is None:
        raise ValueError(f"{path}: no pair table header starting with {HEADER!r}")
    return pd.read_csv(io.StringIO("\n".join(lines[start:])))


def load():
    frames = []
    for mode, folder in INPUTS.items():
        paths = sorted(folder.glob("*.csv"))
        if not paths:
            raise FileNotFoundError(f"no CSV files in {folder}")
        for path in paths:
            df = read_pairs(path)
            missing = set(REQUIRED) - set(df.columns)
            if missing:
                raise ValueError(f"{path}: missing columns {sorted(missing)}")
            if set(df["difficulty"].unique()) != {path.stem}:
                raise ValueError(f"{path}: difficulty values {df['difficulty'].unique()} do not match file name")
            frames.append(df[REQUIRED].assign(reasoning_mode=mode, source=str(path.relative_to(ROOT))))
    df = pd.concat(frames, ignore_index=True)
    for column in ["en_correct", "hi_correct"]:
        bad = df[column].notna() & ~df[column].isin([0, 1])
        if bad.any():
            raise ValueError(f"{column} has non-binary values: {sorted(df.loc[bad, column].unique())}")
        df[column] = df[column].astype("Int64")
    duplicates = df[df.duplicated(KEY, keep=False)]
    if not duplicates.empty:
        raise ValueError(f"{len(duplicates)} duplicate rows on {KEY}:\n{duplicates[KEY + ['source']].to_string()}")
    df["uid"] = df["difficulty"] + "|" + df["task"] + "|" + df["question_id"].astype(str)
    df["RDS"] = df["content_norm_edit_distance"]
    both = df["en_correct"].notna() & df["hi_correct"].notna()
    df["disagree"] = (df["en_correct"] != df["hi_correct"]).astype("Int64").where(both)
    longest = df[["content_en_len", "content_hi_len"]].max(axis=1)
    gap = (df["content_en_len"] - df["content_hi_len"]).abs() / longest.where(longest > 0)
    df["length_gap"] = gap.mask(longest == 0, 0.0)
    difficulties = sorted(df["difficulty"].unique(), key=lambda d: DIFFICULTY_ORDER.get(d, len(DIFFICULTY_ORDER)))
    levels = {"difficulty": difficulties, "task": sorted(df["task"].unique()),
              "insertion": sorted(df["insertion"].unique()), "reasoning_mode": ["off", "on"]}
    for column, values in levels.items():
        ordered = [REFERENCE[column]] + [v for v in values if v != REFERENCE[column]] if column != "difficulty" else values
        if ordered[0] != REFERENCE[column]:
            raise ValueError(f"reference level {REFERENCE[column]!r} is not the first {column} level")
        df[column] = pd.Categorical(df[column], categories=ordered)
    return df.sort_values(KEY).reset_index(drop=True)[KEEP]


def exclusions(df):
    reasons = pd.DataFrame({
        "en_correct_missing": df["en_correct"].isna(),
        "hi_correct_missing": df["hi_correct"].isna(),
        "correctness_missing": df["disagree"].isna(),
        "rds_missing": df["RDS"].isna(),
        "length_gap_missing": df["length_gap"].isna(),
    })
    reasons["excluded"] = reasons[["correctness_missing", "rds_missing", "length_gap_missing"]].any(axis=1)
    rows = []
    for mode, group in [("all", df)] + [(m, g) for m, g in df.groupby("reasoning_mode", observed=True)]:
        r = reasons.loc[group.index]
        for reason in reasons.columns:
            mask = r[reason]
            known = group.loc[mask, "disagree"].dropna()
            rows.append({"reasoning_mode": mode, "reason": reason, "pairs": len(group), "excluded": int(mask.sum()),
                         "share": mask.mean(), "with_correctness": len(known),
                         "disagree_rate_when_known": known.mean() if len(known) else np.nan})
    return reasons["excluded"], pd.DataFrame(rows)


def rate_table(df, by):
    groups = df.groupby(by, observed=True)["disagree"] if by else [((), df["disagree"])]
    rows = []
    for key, s in groups:
        key = key if isinstance(key, tuple) else (key,)
        low, high = proportion_confint(s.sum(), len(s), alpha=ALPHA, method="wilson")
        rows.append(dict(zip(by, key)) | {"n": len(s), "disagreements": int(s.sum()), "disagree_rate": s.mean(),
                                          "ci_low": low, "ci_high": high})
    return pd.DataFrame(rows)


def outcome_table(df):
    labels = {(1, 1): "both_correct", (1, 0): "en_correct_hi_wrong", (0, 1): "en_wrong_hi_correct", (0, 0): "both_wrong"}
    rows = []
    for mode, group in [("all", df)] + [(m, g) for m, g in df.groupby("reasoning_mode", observed=True)]:
        counts = group.groupby(["en_correct", "hi_correct"]).size()
        for (en, hi), label in labels.items():
            n = int(counts.get((en, hi), 0))
            rows.append({"reasoning_mode": mode, "outcome": label, "en_correct": en, "hi_correct": hi,
                         "count": n, "share": n / len(group)})
    return pd.DataFrame(rows)


def describe(series):
    return {"n": int(series.count()), "mean": series.mean(), "median": series.median(), "std": series.std(),
            "min": series.min(), "max": series.max()}


def rds_tables(df):
    summary = [{"reasoning_mode": "all"} | describe(df["RDS"])]
    summary += [{"reasoning_mode": m} | describe(g["RDS"]) for m, g in df.groupby("reasoning_mode", observed=True)]
    by_outcome = [{"reasoning_mode": "all", "disagree": d} | describe(g["RDS"]) for d, g in df.groupby("disagree")]
    by_outcome += [{"reasoning_mode": m, "disagree": d} | describe(g["RDS"])
                   for (m, d), g in df.groupby(["reasoning_mode", "disagree"], observed=True)]
    return pd.DataFrame(summary), pd.DataFrame(by_outcome)


def mann_whitney(df):
    rows = []
    for mode, group in [("all", df)] + [(m, g) for m, g in df.groupby("reasoning_mode", observed=True)]:
        a, b = group.loc[group["disagree"] == 1, "RDS"], group.loc[group["disagree"] == 0, "RDS"]
        if len(a) and len(b):
            u, p = stats.mannwhitneyu(a, b, alternative="two-sided")
            rows.append({"reasoning_mode": mode, "n_disagree": len(a), "n_agree": len(b),
                         "median_rds_disagree": a.median(), "median_rds_agree": b.median(), "U": u,
                         "common_language_effect": u / (len(a) * len(b)), "p_value": p})
    return pd.DataFrame(rows)


def separation_checks(df, formula):
    rows = []
    for column in ["difficulty", "task", "insertion", "reasoning_mode"]:
        if f"C({column})" not in formula:
            continue
        table = df.groupby(column, observed=True)["disagree"].agg(["size", "sum"])
        for level, (n, events) in table.iterrows():
            rows.append({"variable": column, "level": level, "n": int(n), "events": int(events),
                         "non_events": int(n - events), "zero_cell": events == 0 or events == n,
                         "sparse": min(events, n - events) < MIN_LEVEL_EVENTS})
    return pd.DataFrame(rows)


def fit(df, formula):
    data = df.assign(disagree=df["disagree"].astype(int))
    groups = pd.factorize(data["uid"])[0]
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = smf.logit(formula, data).fit(disp=0, maxiter=MAXITER, cov_type="cluster",
                                              cov_kwds={"groups": groups})
    messages = sorted({f"{w.category.__name__}: {w.message}" for w in caught})
    events = int(data["disagree"].sum())
    k = len(result.params) - 1
    checks = separation_checks(data, formula)
    issues = []
    if not result.mle_retvals.get("converged", False):
        issues.append("optimizer did not converge")
    issues += [m for m in messages if "Separation" in m or "Convergence" in m or "Hessian" in m]
    if result.bse.isna().any() or not np.isfinite(result.bse).all():
        issues.append("non-finite standard errors")
    exog = pd.DataFrame(result.model.exog, columns=result.model.exog_names).drop(columns="Intercept")
    scale = exog.std().where(exog.nunique() > 2, 1.0)
    big = (result.params.drop("Intercept") * scale)[lambda s: s.abs() > MAX_ABS_COEF]
    issues += [f"very large coefficient {name} = {result.params[name]:.2f} (scaled {value:.2f})" for name, value in big.items()]
    if not checks.empty and checks["zero_cell"].any():
        cells = checks[checks["zero_cell"]]
        issues += [f"zero cell (quasi-separation) for {r.variable} = {r.level}" for r in cells.itertuples()]
    epv = min(events, len(data) - events) / max(k, 1)
    if epv < MIN_EPV:
        issues.append(f"events per parameter {epv:.1f} < {MIN_EPV}")
    return {"result": result, "n": len(data), "events": events, "clusters": int(groups.max() + 1), "k": k,
            "epv": epv, "warnings": messages, "issues": issues, "reliable": not issues, "checks": checks}


def term_table(fitted):
    r = fitted["result"]
    ci = r.conf_int(alpha=ALPHA)
    return pd.DataFrame({"term": r.params.index, "coef": r.params.values, "se": r.bse.values, "z": r.tvalues.values,
                         "p_value": r.pvalues.values, "ci_low": ci[0].values, "ci_high": ci[1].values,
                         "odds_ratio": np.exp(r.params.values), "or_ci_low": np.exp(ci[0].values),
                         "or_ci_high": np.exp(ci[1].values)})


def rds_row(name, fitted, sample):
    r = fitted["result"]
    b, se, p = r.params["RDS"], r.bse["RDS"], r.pvalues["RDS"]
    low, high = r.conf_int(alpha=ALPHA).loc["RDS"]
    margeff = r.get_margeff(at="overall")
    j = list(r.params.index[1:]).index("RDS")
    ame, ame_se = margeff.margeff[j], margeff.margeff_se[j]
    z = stats.norm.ppf(1 - ALPHA / 2)
    return {"model": name, "sample": sample, "n": fitted["n"], "events": fitted["events"],
            "clusters": fitted["clusters"], "parameters": fitted["k"], "events_per_parameter": fitted["epv"],
            "beta_rds": b, "se": se, "z": b / se, "p_value": p, "ci_low": low, "ci_high": high,
            "odds_ratio": np.exp(b), "or_ci_low": np.exp(low), "or_ci_high": np.exp(high),
            "or_per_0_1": np.exp(0.1 * b), "or_per_0_1_ci_low": np.exp(0.1 * low),
            "or_per_0_1_ci_high": np.exp(0.1 * high), "ame_per_0_1_pp": 10 * ame,
            "ame_per_0_1_pp_ci_low": 10 * (ame - z * ame_se), "ame_per_0_1_pp_ci_high": 10 * (ame + z * ame_se),
            "significant": p < ALPHA, "converged": bool(r.mle_retvals.get("converged", False)),
            "reliable": fitted["reliable"], "issues": "; ".join(fitted["issues"])}


def average_predictions(fitted, df):
    r = fitted["result"]
    X, beta, cov = r.model.exog, r.params.values, r.cov_params().values
    j = r.model.exog_names.index("RDS")
    z = stats.norm.ppf(1 - ALPHA / 2)
    rows = []
    for mode in df["reasoning_mode"].cat.categories:
        mask = (df["reasoning_mode"] == mode).to_numpy()
        lo, hi = df.loc[mask, "RDS"].quantile(GRID_QUANTILES)
        for g in np.linspace(lo, hi, GRID_POINTS):
            Xg = X[mask].copy()
            Xg[:, j] = g
            p = expit(Xg @ beta)
            grad = (p * (1 - p)) @ Xg / len(p)
            se = np.sqrt(grad @ cov @ grad)
            rows.append({"reasoning_mode": mode, "RDS": g, "predicted": p.mean(),
                         "ci_low": max(p.mean() - z * se, 0), "ci_high": min(p.mean() + z * se, 1)})
    return pd.DataFrame(rows)


def error_bars(table):
    return np.clip([table["disagree_rate"] - table["ci_low"], table["ci_high"] - table["disagree_rate"]], 0, None)


def save_fig(fig, name):
    fig.tight_layout()
    fig.savefig(OUT / name)
    plt.close(fig)


def plot_rds_distribution(df):
    modes = list(df["reasoning_mode"].cat.categories)
    fig, axes = plt.subplots(1, len(modes), figsize=(5 * len(modes), 3.6), sharex=True)
    bins = np.linspace(0, 1, 26)
    for ax, mode in zip(axes, modes):
        group = df[df["reasoning_mode"] == mode]
        for d in [0, 1]:
            values = group.loc[group["disagree"] == d, "RDS"]
            if values.empty:
                continue
            ax.hist(values, bins=bins, density=True, histtype="step", color=COLORS[d], linewidth=2,
                    label=f"{DISAGREE_LABEL[d]}, n={len(values)}")
            ax.axvline(values.median(), color=COLORS[d], linestyle="--", linewidth=1.2)
        ax.set_title(f"{MODE_LABEL[mode]}")
        ax.set_xlabel("RDS (normalized edit distance)")
        ax.set_ylabel("Density")
        ax.legend(loc="upper left", fontsize=8)
    fig.suptitle("RDS distribution by correctness disagreement (dashed = median)")
    save_fig(fig, "rds_distribution_by_disagreement.png")


def plot_rate_by_bin(df):
    binned = df.assign(rds_bin=pd.cut(df["RDS"], RDS_BINS, include_lowest=True))
    table = rate_table(binned, ["reasoning_mode", "rds_bin"])
    table["mid"] = table["rds_bin"].map(lambda i: i.mid)
    fig, ax = plt.subplots(figsize=(7, 4))
    for mode, group in table[table["n"] >= MIN_BIN_N].groupby("reasoning_mode", observed=True):
        ax.errorbar(group["mid"], group["disagree_rate"],
                    yerr=error_bars(group), color=COLORS[mode], marker="o", markersize=5, capsize=3, label=MODE_LABEL[mode])
    ax.set_xlabel("RDS bin (width 0.1, midpoint shown)")
    ax.set_ylabel("Disagreement rate")
    ax.set_xlim(0, 1)
    ax.set_title(f"Observed disagreement rate by RDS bin, unadjusted\n(Wilson {int(100 * (1 - ALPHA))}% CI; bins with n < {MIN_BIN_N} hidden)")
    ax.legend()
    save_fig(fig, "disagreement_rate_by_rds_bin.png")
    return table.drop(columns="mid").assign(rds_bin=lambda t: t["rds_bin"].astype(str))


def plot_grouped_rates(table, by, name, title):
    levels = list(dict.fromkeys(table[by]))
    modes = list(dict.fromkeys(table["reasoning_mode"]))
    width = 0.8 / len(modes)
    x = np.arange(len(levels))
    fig, ax = plt.subplots(figsize=(max(5, 1.3 * len(levels)), 4))
    for i, mode in enumerate(modes):
        group = table[table["reasoning_mode"] == mode].set_index(by).reindex(levels)
        ax.bar(x + (i - (len(modes) - 1) / 2) * width, group["disagree_rate"], width * 0.92, color=COLORS[mode],
               yerr=error_bars(group), ecolor=INK, capsize=3, error_kw={"linewidth": 1}, label=MODE_LABEL[mode])
    ax.set_xticks(x, [str(level) for level in levels])
    ax.set_ylabel("Disagreement rate")
    ax.set_title(title)
    ax.legend()
    save_fig(fig, name)


def plot_by_mode(table):
    fig, ax = plt.subplots(figsize=(4.5, 4))
    for i, row in enumerate(table.itertuples()):
        ax.bar(i, row.disagree_rate, 0.6, color=COLORS[row.reasoning_mode], ecolor=INK, capsize=4,
               yerr=error_bars(table.iloc[[i]]))
        ax.annotate(f"{row.disagree_rate:.1%}\n({row.disagreements}/{row.n})", (i, row.ci_high),
                    xytext=(0, 4), textcoords="offset points", ha="center", va="bottom", fontsize=8, color=MUTED)
    ax.set_xticks(range(len(table)), [MODE_LABEL[m] for m in table["reasoning_mode"]])
    ax.set_ylabel("Disagreement rate")
    ax.set_ylim(0, table["ci_high"].max() * 1.3)
    ax.set_title(f"Disagreement rate by reasoning mode\n({int(100 * (1 - ALPHA))}% Wilson CI)")
    save_fig(fig, "disagreement_rate_by_mode.png")


def plot_predictions(predictions, df):
    modes = list(dict.fromkeys(predictions["reasoning_mode"]))
    fig, axes = plt.subplots(1, len(modes), figsize=(5 * len(modes), 3.8))
    for ax, mode in zip(axes, modes):
        group = predictions[predictions["reasoning_mode"] == mode]
        ax.fill_between(group["RDS"], group["ci_low"], group["ci_high"], color=COLORS[mode], alpha=0.2, linewidth=0)
        ax.plot(group["RDS"], group["predicted"], color=COLORS[mode])
        observed = df.loc[df["reasoning_mode"] == mode, "RDS"]
        ax.plot(observed, np.zeros_like(observed), "|", color=MUTED, alpha=0.15, markersize=8, transform=ax.get_xaxis_transform())
        ax.set_title(f"{MODE_LABEL[mode]} (n={len(observed)})")
        ax.set_xlabel("RDS")
        ax.set_ylabel("Adjusted P(disagree = 1)")
        ax.set_ylim(bottom=0)
    fig.suptitle("Primary model: average adjusted predictions over observed covariates "
                 f"({int(100 * (1 - ALPHA))}% delta-method CI, clustered SE)", fontsize=10)
    save_fig(fig, "predicted_probability_primary.png")


def pct(x):
    return f"{100 * x:.1f}%"


def fmt_p(p):
    return "< 0.001" if p < 0.001 else f"{p:.3f}"


def rds_sentence(row):
    return (f"β = {row.beta_rds:.3f} (SE {row.se:.3f}, 95% CI {row.ci_low:.3f} to {row.ci_high:.3f}, p {fmt_p(row.p_value)}); "
            f"OR per 0.1 RDS = {row.or_per_0_1:.3f} (95% CI {row.or_per_0_1_ci_low:.3f} to {row.or_per_0_1_ci_high:.3f}); "
            f"average marginal effect per 0.1 RDS = {row.ame_per_0_1_pp:.2f} pp "
            f"(95% CI {row.ame_per_0_1_pp_ci_low:.2f} to {row.ame_per_0_1_pp_ci_high:.2f})")


def findings(df, analysed, excluded_table, outcomes, mode_rates, rds_summary, rds_by_outcome, mw, results, overlap, gap_term):
    o = outcomes[outcomes["reasoning_mode"] == "all"].set_index("outcome")["count"]
    en_only_share = o["en_correct_hi_wrong"] / (o["en_correct_hi_wrong"] + o["en_wrong_hi_correct"])
    prim = results[results["model"] == "primary"].iloc[0]
    rob = results[results["model"] == "length_adjusted"].iloc[0]
    per_mode = results[~results["model"].isin(["primary", "length_adjusted"])]
    excl = excluded_table.set_index(["reasoning_mode", "reason"])
    lines = ["# RDS and English/Hindi correctness disagreement: logistic regression", "",
             "Observational analysis of existing Sarvam-105B outputs; no inference was rerun.", "",
             "## Data", "",
             f"- Inputs: `edout/ron/*.csv` (reasoning ON) and `edout/standard/*.csv` (reasoning OFF); the pair table after the "
             f"`question_id,...` header line is read, the aggregate block above it is ignored.",
             f"- Pairs loaded: {len(df)} ({', '.join(f'{MODE_LABEL[m]}: {n}' for m, n in df['reasoning_mode'].value_counts().sort_index().items())}).",
             f"- Underlying question id `uid = difficulty|task|question_id` (question ids repeat across tasks and difficulties; "
             f"the three insertion variants share a uid). Unique uids: {df['uid'].nunique()}; "
             f"present in both modes: {overlap}.",
             f"- RDS = `content_norm_edit_distance`. disagree = 1 iff `en_correct != hi_correct`.", "",
             "## Exclusions", ""]
    for mode in ["all", "on", "off"]:
        total = excl.loc[(mode, "excluded")]
        known = excl.loc[(mode, "rds_missing")]
        lines.append(f"- {mode}: {int(total.excluded)}/{int(total.pairs)} pairs excluded ({pct(total.share)}): "
                     f"English answer unparseable {int(excl.loc[(mode, 'en_correct_missing')].excluded)}, "
                     f"Hindi unparseable {int(excl.loc[(mode, 'hi_correct_missing')].excluded)}, RDS missing {int(known.excluded)}"
                     + (f" (disagreement rate among RDS-missing pairs with correctness: {pct(known.disagree_rate_when_known)})"
                        if known.with_correctness else "") + ".")
    lines += ["", "Missing correctness was never converted into a disagreement label. Both models use the identical sample.", "",
              "## Descriptives (analysed sample)", "",
              f"- Paired observations: {len(analysed)}; unique questions: {analysed['uid'].nunique()}.",
              "", "| mode | both correct | EN only | HI only | both wrong | disagreement rate |", "|---|---|---|---|---|---|"]
    for mode in ["all", "on", "off"]:
        o = outcomes[outcomes["reasoning_mode"] == mode].set_index("outcome")["count"]
        rate = (o["en_correct_hi_wrong"] + o["en_wrong_hi_correct"]) / o.sum()
        lines.append(f"| {mode} | {o['both_correct']} | {o['en_correct_hi_wrong']} | {o['en_wrong_hi_correct']} | {o['both_wrong']} | {pct(rate)} |")
    lines += ["", "| mode | RDS mean | median | SD | min | max |", "|---|---|---|---|---|---|"]
    for r in rds_summary.itertuples():
        lines.append(f"| {r.reasoning_mode} | {r.mean:.3f} | {r.median:.3f} | {r.std:.3f} | {r.min:.3f} | {r.max:.3f} |")
    lines += ["", "| mode | disagree | n | RDS mean | RDS median |", "|---|---|---|---|---|"]
    for r in rds_by_outcome.itertuples():
        lines.append(f"| {r.reasoning_mode} | {r.disagree} | {r.n} | {r.mean:.3f} | {r.median:.3f} |")
    lines += ["", "Mann-Whitney U (RDS, disagree vs agree; unadjusted):", ""]
    for r in mw.itertuples():
        lines.append(f"- {r.reasoning_mode}: median {r.median_rds_disagree:.3f} vs {r.median_rds_agree:.3f}, "
                     f"P(RDS_disagree > RDS_agree) = {r.common_language_effect:.3f}, p {fmt_p(r.p_value)}.")
    lines += ["", "## Models", "",
              f"Logit with standard errors clustered by uid. Reference levels: "
              + ", ".join(f"{k} = `{v}`" for k, v in REFERENCE.items()) + ".", "",
              "| model | sample | n | events | RDS β | OR per 0.1 (95% CI) | p | AME per 0.1 (pp) | reliable |",
              "|---|---|---|---|---|---|---|---|---|"]
    for r in results.itertuples():
        lines.append(f"| {r.model} | {r.sample} | {r.n} | {r.events} | {r.beta_rds:.3f} | {r.or_per_0_1:.3f} "
                     f"({r.or_per_0_1_ci_low:.3f}–{r.or_per_0_1_ci_high:.3f}) | {fmt_p(r.p_value)} | "
                     f"{r.ame_per_0_1_pp:.2f} | {'yes' if r.reliable else 'no: ' + r.issues} |")
    direction = "higher" if prim.beta_rds > 0 else "lower"
    sig = "statistically significant" if prim.significant else "not statistically significant"
    change = (rob.beta_rds - prim.beta_rds) / abs(prim.beta_rds) if prim.beta_rds else np.nan
    lines += ["", "## Interpretation", ""]
    if not prim.reliable:
        lines.append(f"The primary model could not be estimated reliably ({prim.issues}); its coefficients should not be interpreted. "
                     "See the Mann-Whitney comparison above for a simpler, assumption-light description.")
    else:
        lines += [
            f"**Primary model.** Holding difficulty, task, insertion condition and reasoning mode constant, higher RDS is associated "
            f"with {direction} odds of English/Hindi correctness disagreement: {rds_sentence(prim)}. "
            f"The association is {sig} at α = {ALPHA}. On the odds scale, a 0.1 increase in RDS multiplies the odds of disagreement by "
            f"{prim.or_per_0_1:.3f}. The AME is the average slope dP/dRDS scaled by 0.1, a local probability-scale summary; "
            "the adjusted prediction curves show the non-linear relationship over the observed RDS range.", "",
            f"**Length-adjusted model.** Adding `length_gap` = |len_en − len_hi| / max(len_en, len_hi) (0 when both are empty): "
            f"{rds_sentence(rob)}. The RDS coefficient changes by {pct(change)} relative to the primary model and is "
            f"{'significant' if rob.significant else 'not significant'} at α = {ALPHA}; the association "
            f"{'persists' if rob.significant and np.sign(rob.beta_rds) == np.sign(prim.beta_rds) else 'does not clearly persist'} "
            f"after accounting for relative trace-length differences. The `length_gap` coefficient itself is "
            f"{gap_term.coef:.3f} (OR per 0.1 = {np.exp(0.1 * gap_term.coef):.3f}, p {fmt_p(gap_term.p_value)}).", ""]
    if not per_mode.empty:
        lines.append("**Per-mode models (supplementary).** The pooled sample is dominated by reasoning-OFF pairs, so the RDS slope is "
                     "also estimated within each mode:")
        lines.append("")
        for r in per_mode.itertuples():
            lines.append(f"- {r.model} ({r.sample}): {rds_sentence(r)}"
                         + ("" if r.reliable else f". Not reliable: {r.issues}") + ".")
        lines.append("")
    lines += ["## Limitations", "",
              "- Observational: RDS is measured on the same generations whose answers are scored, so the association cannot be read as "
              "reasoning divergence causing errors; both may reflect question-level difficulty not captured by the controls.",
              f"- Mode imbalance: reasoning ON contributes {len(analysed[analysed['reasoning_mode'] == 'on'])} of {len(analysed)} pairs "
              f"and few disagreements, so the pooled RDS slope mostly reflects reasoning OFF; the model assumes one common slope across modes.",
              "- RDS depends on the step parser and the edit-distance cost scheme (`config/ed.yaml`); parsing errors add measurement "
              "error that would typically attenuate the coefficient.",
              "- Pairs with an unparseable answer in either language are excluded, and exclusion is more common in some conditions, "
              "which can bias the sample toward cleaner generations.",
              "- Clustered SEs account for repeated observations of a question (insertion variants, both modes) but assume independence "
              "across questions; a single generation per prompt means sampling noise in correctness is not separated from systematic effects.",
              f"- {pct(en_only_share)} of disagreements are English correct / Hindi wrong, so the outcome mostly captures Hindi-specific "
              "failures rather than symmetric disagreement.",
              "- RDS is high for most pairs (see the RDS table), so the slope is estimated mainly from the upper part of the RDS range.",
              "- Odds ratios are not percentage-point changes; use the AME column or the prediction curves for the probability scale.", "",
              "## Files", "",
              "- `analysis_dataset.csv`: cleaned combined dataset (all loaded pairs, with `included`).",
              "- `desc_*.csv`: descriptive tables; `exclusions.csv`; `mann_whitney.csv`.",
              "- `rds_results.csv`: RDS coefficient table for all models; `coef_<model>.csv`; `summary_<model>.txt`; "
              "`separation_<model>.csv`; `predicted_probability_primary.csv`.",
              "- `*.png`: plots.", "",
              "Reproduce: `python rds_regression.py` from this folder (requires pandas, numpy, scipy, statsmodels, matplotlib)."]
    (OUT / "findings.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    OUT.mkdir(exist_ok=True)
    df = load()
    excluded, excluded_table = exclusions(df)
    df["included"] = ~excluded
    df.to_csv(OUT / "analysis_dataset.csv", index=False)
    excluded_table.to_csv(OUT / "exclusions.csv", index=False)
    analysed = df[df["included"]].copy()
    analysed["disagree"] = analysed["disagree"].astype(int)
    modes_per_uid = df.groupby("uid")["reasoning_mode"].nunique()
    overlap = int((modes_per_uid == 2).sum())

    outcomes = outcome_table(analysed)
    mode_rates = rate_table(analysed, ["reasoning_mode"])
    rds_summary, rds_by_outcome = rds_tables(analysed)
    mw = mann_whitney(analysed)
    overview = pd.DataFrame([
        {"metric": "pairs_loaded", "value": len(df)},
        {"metric": "pairs_analysed", "value": len(analysed)},
        {"metric": "pairs_excluded", "value": int(excluded.sum())},
        {"metric": "unique_questions_loaded", "value": df["uid"].nunique()},
        {"metric": "unique_questions_analysed", "value": analysed["uid"].nunique()},
        {"metric": "questions_in_both_modes", "value": overlap},
        *[{"metric": f"pairs_analysed_{m}", "value": int(n)} for m, n in analysed["reasoning_mode"].value_counts().sort_index().items()],
        {"metric": "disagreements", "value": int(analysed["disagree"].sum())},
        {"metric": "disagree_rate", "value": analysed["disagree"].mean()},
    ], dtype=object)
    tables = {
        "overview": overview, "outcomes": outcomes, "rate_overall": rate_table(analysed, []),
        "rate_by_mode": mode_rates, "rate_by_difficulty": rate_table(analysed, ["difficulty"]),
        "rate_by_task": rate_table(analysed, ["task"]), "rate_by_insertion": rate_table(analysed, ["insertion"]),
        "rate_by_mode_difficulty": rate_table(analysed, ["reasoning_mode", "difficulty"]),
        "rate_by_mode_task": rate_table(analysed, ["reasoning_mode", "task"]),
        "rate_by_difficulty_task": rate_table(analysed, ["difficulty", "task"]),
        "rds_summary": rds_summary, "rds_by_disagreement": rds_by_outcome,
        "length_gap_summary": pd.DataFrame([{"reasoning_mode": "all"} | describe(analysed["length_gap"])]
                                           + [{"reasoning_mode": m} | describe(g["length_gap"])
                                              for m, g in analysed.groupby("reasoning_mode", observed=True)]),
    }
    for name, table in tables.items():
        table.to_csv(OUT / f"desc_{name}.csv", index=False)
    mw.to_csv(OUT / "mann_whitney.csv", index=False)
    with pd.option_context("display.max_rows", None, "display.width", 200, "display.float_format", "{:.4f}".format):
        for name in ["overview", "outcomes", "rate_by_mode", "rate_by_difficulty", "rate_by_task", "rds_summary", "rds_by_disagreement"]:
            print(f"\n== {name}\n{tables[name].to_string(index=False)}")
        print(f"\n== mann_whitney\n{mw.to_string(index=False)}")

    plot_rds_distribution(analysed)
    plot_rate_by_bin(analysed).to_csv(OUT / "desc_rate_by_mode_rds_bin.csv", index=False)
    plot_grouped_rates(tables["rate_by_mode_difficulty"], "difficulty", "disagreement_rate_by_difficulty.png",
                       f"Disagreement rate by difficulty ({int(100 * (1 - ALPHA))}% Wilson CI)")
    plot_by_mode(mode_rates)

    specs = [(name, formula, analysed, "pooled") for name, formula in MODELS.items()]
    specs += [(f"per_mode_{m}_adjusted", f"disagree ~ RDS + {PER_MODE_CONTROLS}", analysed[analysed["reasoning_mode"] == m], m)
              for m in ["off", "on"]]
    specs += [(f"per_mode_{m}_rds_only", "disagree ~ RDS", analysed[analysed["reasoning_mode"] == m], m) for m in ["off", "on"]]
    results, fits = [], {}
    for name, formula, data, sample in specs:
        fitted = fit(data, formula)
        fits[name] = fitted
        results.append(rds_row(name, fitted, sample))
        term_table(fitted).to_csv(OUT / f"coef_{name}.csv", index=False)
        fitted["checks"].to_csv(OUT / f"separation_{name}.csv", index=False)
        report = [f"model: {name}", f"formula: {formula}", f"sample: {sample}", f"n = {fitted['n']}, events = {fitted['events']}, "
                  f"clusters (uid) = {fitted['clusters']}, parameters (excl. intercept) = {fitted['k']}, "
                  f"events per parameter = {fitted['epv']:.1f}", f"reference levels: {REFERENCE}",
                  f"converged: {fitted['result'].mle_retvals.get('converged')}", f"reliable: {fitted['reliable']}",
                  f"issues: {fitted['issues'] or 'none'}", f"warnings: {fitted['warnings'] or 'none'}", "",
                  str(fitted["result"].summary(alpha=ALPHA)), "", str(fitted["result"].get_margeff(at="overall").summary())]
        (OUT / f"summary_{name}.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    results = pd.DataFrame(results)
    results.to_csv(OUT / "rds_results.csv", index=False)
    with pd.option_context("display.max_columns", None, "display.width", 250, "display.float_format", "{:.4f}".format):
        print("\n== rds_results\n" + results[["model", "n", "events", "beta_rds", "se", "p_value", "ci_low", "ci_high",
                                               "or_per_0_1", "ame_per_0_1_pp", "reliable", "issues"]].to_string(index=False))

    if fits["primary"]["reliable"]:
        predictions = average_predictions(fits["primary"], analysed)
        predictions.to_csv(OUT / "predicted_probability_primary.csv", index=False)
        plot_predictions(predictions, analysed)
    gap_term = term_table(fits["length_adjusted"]).set_index("term").loc["length_gap"]
    findings(df, analysed, excluded_table, outcomes, mode_rates, rds_summary, rds_by_outcome, mw, results, overlap, gap_term)
    print(f"\nOutputs written to {OUT}")


if __name__ == "__main__":
    main()
