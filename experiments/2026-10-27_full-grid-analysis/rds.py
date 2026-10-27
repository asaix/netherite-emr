import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy.stats import mannwhitneyu

import temporal_answers as T

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "rds"))

import parser as P
from ed import edit_distance

M = T.use_parser("current")
OUT = HERE / "outputs" / "rds"
OUT.mkdir(parents=True, exist_ok=True)
DIFFS = ["short", "medium", "long", "very_long", "very_very_long"]


def normalised(a, b):
    return edit_distance(a, b) / max(len(a), len(b)) if a or b else 0.0


records, _ = T.load_records()
traces = {}
for r in records:
    if r["condition"] != "cot":
        continue
    m = r["meta"]
    tokens = P.parse(r["content"], P.find_distractor(r)) or []
    answered = M.extract_answer(r["content"]) is not None
    traces[(m["difficulty"], m["task"], m["question_id"], m["insertion"], m["language"])] = {
        "tokens": tokens, "ops": [t.split()[0] for t in tokens],
        "correct": float(M.is_correct(r)) if answered else np.nan, "words": M.target_words(r)[1],
    }

pairs = []
for (d, t, q, i, lang), en in traces.items():
    if lang != "en_US" or (d, t, q, i, "hi_IN") not in traces:
        continue
    hi = traces[d, t, q, i, "hi_IN"]
    pairs.append({
        "qid": f"{d}/{t}/{q}", "difficulty": d, "task": t, "insertion": i,
        "rds": normalised(en["tokens"], hi["tokens"]), "rds_ops": normalised(en["ops"], hi["ops"]),
        "en_steps": len(en["tokens"]), "hi_steps": len(hi["tokens"]), "en_words": en["words"], "hi_words": hi["words"],
        "en_correct": en["correct"], "hi_correct": hi["correct"],
    })
pairs = pd.DataFrame(pairs)
pairs.to_csv(OUT / "pairs.csv", index=False)

numbers = {"pairs": len(pairs), "parser_commit": "metrics/ed-lr 32ac1bd",
           "empty_parse_share": {"en_US": float((pairs["en_steps"] == 0).mean()), "hi_IN": float((pairs["hi_steps"] == 0).mean())}}
summary = {}
for col in ("rds", "rds_ops"):
    summary[col] = {
        "mean": float(pairs[col].mean()), "median": float(pairs[col].median()),
        "by_difficulty": pairs.groupby("difficulty")[col].mean().reindex(DIFFS).to_dict(),
        "by_task": pairs.groupby("task")[col].mean().to_dict(),
        "by_insertion": pairs.groupby("insertion")[col].mean().to_dict(),
    }
scored = pairs.dropna(subset=["en_correct", "hi_correct"])
outcome = np.select([(scored["en_correct"] == 1) & (scored["hi_correct"] == 1), (scored["en_correct"] == 1) & (scored["hi_correct"] == 0),
                     (scored["en_correct"] == 0) & (scored["hi_correct"] == 1)], ["both_right", "en_only", "hi_only"], "both_wrong")
for col in ("rds", "rds_ops"):
    summary[col]["by_outcome"] = scored.groupby(outcome)[col].agg(["mean", "size"]).to_dict(orient="index")
numbers["summary"] = summary

long = pd.concat([
    scored.assign(language=lang, err=1 - scored[f"{prefix}_correct"], steps=scored[f"{prefix}_steps"], words=scored[f"{prefix}_words"])
    for lang, prefix in (("en_US", "en"), ("hi_IN", "hi"))
], ignore_index=True)
long["log_words"] = np.log1p(long["words"])
long["log_steps"] = np.log1p(long["steps"])
long["qi"] = long["qid"].astype("category").cat.codes


def fit(formula, data):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return smf.glm(formula, data, family=sm.families.Binomial()).fit(cov_type="cluster", cov_kwds={"groups": data["qi"]})


def auroc(y, p):
    pos, neg = p[y == 1], p[y == 0]
    return float(mannwhitneyu(pos, neg).statistic / (len(pos) * len(neg)))


base = "err ~ C(difficulty) + C(task) + C(insertion)"
models = {}
for lang in ("en_US", "hi_IN", "both"):
    data = long if lang == "both" else long[long["language"] == lang]
    extra = " + C(language)" if lang == "both" else ""
    for name, terms in (("controls", ""), ("length", " + log_words"), ("rds", " + rds"), ("rds_ops", " + rds_ops"),
                        ("rds_and_length", " + rds + log_words")):
        m = fit(base + extra + terms, data)
        row = {"auroc": auroc(data["err"].to_numpy(), m.predict(data).to_numpy()), "n": int(m.nobs), "aic": float(m.aic)}
        for term in ("rds", "rds_ops", "log_words"):
            if term in m.params:
                lo, hi = m.conf_int().loc[term]
                row[term] = {"coef": float(m.params[term]), "coef_ci": [float(lo), float(hi)],
                             "or_per_unit": float(np.exp(m.params[term])), "or_per_0.1": float(np.exp(0.1 * m.params[term])),
                             "or_per_0.1_ci": [float(np.exp(0.1 * lo)), float(np.exp(0.1 * hi))], "p": float(m.pvalues[term])}
        models[f"{lang}/{name}"] = row
numbers["logistic"] = models

with open(OUT / "numbers.json", "w", encoding="utf-8") as f:
    json.dump(numbers, f, ensure_ascii=False, indent=2, default=float)
print(len(pairs), "pairs")
