import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools" / "temporal-reasoning-dataset" / "src"))
sys.path.insert(0, str(HERE))

import metrics as M

INSERTIONS = {"none": "no_insertion", "similar": "similar_insertion", "dissimilar": "dissimilar_insertion"}
DELTAS = [
    "cot_delta_none",
    "cot_delta_similar",
    "cot_delta_dissimilar",
    "cot_none_minus_similar",
    "cot_none_minus_dissimilar",
    "cot_similar_minus_dissimilar",
    "direct_none_minus_similar",
    "direct_none_minus_dissimilar",
    "direct_similar_minus_dissimilar",
    "cot_drop_minus_direct_drop_none_similar",
    "cot_drop_minus_direct_drop_none_dissimilar",
    "cot_drop_minus_direct_drop_similar_dissimilar",
]

records = json.load(open(HERE / "merged_results.json", encoding="utf-8"))
(HERE / "outputs").mkdir(exist_ok=True)


def diff(x, y):
    return None if x is None or y is None else round(x - y, 3)


by = ("difficulty", "task", "language", "insertion", "condition")
accuracy = M.average_accuracy(records, by)
scored = {k: len(M.answered(rs)) for k, rs in M.group(records, by).items()}

rows = []
for difficulty, task, language in dict.fromkeys(k[:3] for k in accuracy):
    cell = lambda condition, ins: (difficulty, task, language, INSERTIONS[ins], condition)
    acc = {(c, i): accuracy.get(cell(c, i)) for c in ("direct", "cot") for i in INSERTIONS}
    row = {"difficulty": difficulty, "task": task, "language": language}
    row.update({f"{c}_{i}": None if v is None else round(v, 3) for (c, i), v in acc.items()})
    for i in INSERTIONS:
        row[f"cot_delta_{i}"] = diff(acc["cot", i], acc["direct", i])
    row["cot_none_minus_similar"] = diff(acc["cot", "none"], acc["cot", "similar"])
    row["cot_none_minus_dissimilar"] = diff(acc["cot", "none"], acc["cot", "dissimilar"])
    row["cot_similar_minus_dissimilar"] = diff(acc["cot", "similar"], acc["cot", "dissimilar"])
    row["direct_none_minus_similar"] = diff(acc["direct", "none"], acc["direct", "similar"])
    row["direct_none_minus_dissimilar"] = diff(acc["direct", "none"], acc["direct", "dissimilar"])
    row["direct_similar_minus_dissimilar"] = diff(acc["direct", "similar"], acc["direct", "dissimilar"])
    row["cot_drop_minus_direct_drop_none_similar"] = diff(row["cot_none_minus_similar"], row["direct_none_minus_similar"])
    row["cot_drop_minus_direct_drop_none_dissimilar"] = diff(row["cot_none_minus_dissimilar"], row["direct_none_minus_dissimilar"])
    row["cot_drop_minus_direct_drop_similar_dissimilar"] = diff(row["cot_similar_minus_dissimilar"], row["direct_similar_minus_dissimilar"])
    row["min_scored"] = min(scored.get(cell(c, i), 0) for c in ("direct", "cot") for i in INSERTIONS)
    rows.append(row)

M.write_csv(rows, HERE / "outputs" / "deltas_by_language.csv")

by_pair = {(r["difficulty"], r["task"], r["language"]): r for r in rows}
paired = []
for difficulty, task in dict.fromkeys(k[:2] for k in by_pair):
    en, hi = by_pair.get((difficulty, task, "en_US")), by_pair.get((difficulty, task, "hi_IN"))
    if en is None or hi is None:
        continue
    row = {"difficulty": difficulty, "task": task}
    for name in DELTAS:
        row[f"{name}_en"] = en[name]
        row[f"{name}_hi"] = hi[name]
        row[f"{name}_en_minus_hi"] = diff(en[name], hi[name])
    paired.append(row)

M.write_csv(paired, HERE / "outputs" / "deltas_en_vs_hi.csv")

ratio_by = ("difficulty", "task", "language", "insertion")
average = M.average_target_language_cot_ratio(records, ratio_by)
pooled = M.pooled_target_language_cot_ratio(records, ratio_by)
ratios = [
    {
        **dict(zip(ratio_by, k)),
        "cot_responses": len(rs),
        "cot_ratio_avg": None if average[k] is None else round(average[k], 3),
        "cot_ratio_pooled": None if pooled[k] is None else round(pooled[k], 3),
    }
    for k, rs in M.group(M.cot(records), ratio_by).items()
]
M.write_csv(ratios, HERE / "outputs" / "cot_ratio.csv")

print(f"{len(rows)} rows -> outputs/deltas_by_language.csv")
print(f"{len(paired)} rows -> outputs/deltas_en_vs_hi.csv")
print(f"{len(ratios)} rows -> outputs/cot_ratio.csv")
