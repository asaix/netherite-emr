from collections import defaultdict

import numpy as np
import pandas as pd
from scipy.stats import binomtest

from temporal_answers import HERE, M, load_records

records = load_records()
(HERE / "outputs").mkdir(exist_ok=True)

languages = defaultdict(dict)
for r in records:
    m = r["meta"]
    key = (m["difficulty"], m["task"], r["condition"], m["insertion"], m["question_id"])
    languages[key][m["language"]] = M.is_correct(r) if M.extract_answer(r["content"]) is not None else None

rows = [
    {"difficulty": k[0], "task": k[1], "condition": k[2], "en_correct": v["en_US"], "hi_correct": v["hi_IN"]}
    for k, v in languages.items()
    if len(v) == 2
]
pairs = pd.DataFrame(rows)


def agreement(group):
    scored = group.dropna()
    en, hi = scored["en_correct"].astype(bool), scored["hi_correct"].astype(bool)
    n = len(scored)
    both_right, both_wrong = (en & hi).sum(), (~en & ~hi).sum()
    en_only, hi_only = (en & ~hi).sum(), (~en & hi).sum()
    p_en, p_hi = en.mean(), hi.mean()
    denominator = np.sqrt(p_en * (1 - p_en) * p_hi * (1 - p_hi))
    return pd.Series(
        {
            "pairs": len(group),
            "pairs_scored": n,
            "both_right": both_right,
            "both_wrong": both_wrong,
            "en_only": en_only,
            "hi_only": hi_only,
            "split_rate": (en_only + hi_only) / n,
            "split_rate_if_independent": p_en * (1 - p_hi) + p_hi * (1 - p_en),
            "phi_correlation": (both_right / n - p_en * p_hi) / denominator if denominator else np.nan,
            "en_only_vs_hi_only_p": binomtest(int(en_only), int(en_only + hi_only), 0.5).pvalue if en_only + hi_only else np.nan,
        }
    )


table = pairs.groupby(["difficulty", "task", "condition"]).apply(agreement, include_groups=False).reset_index()
overall = pairs.groupby("condition").apply(agreement, include_groups=False).reset_index()
overall.insert(0, "task", "all")
overall.insert(0, "difficulty", "all")
table = pd.concat([table, overall])
table["difficulty"] = pd.Categorical(table["difficulty"], ["short", "medium", "long", "very_long", "all"], ordered=True)
table = table.sort_values(["difficulty", "task", "condition"])
for column in ("pairs", "pairs_scored", "both_right", "both_wrong", "en_only", "hi_only"):
    table[column] = table[column].astype(int)

table.round(3).to_csv(HERE / "outputs" / "cross_lingual_agreement.csv", index=False)
print(table.round(3).to_string(index=False))
