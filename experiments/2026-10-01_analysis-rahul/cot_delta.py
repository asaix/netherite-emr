import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools" / "temporal-reasoning-dataset" / "src"))
sys.path.insert(0, str(HERE))

import metrics as M

records = json.load(open(HERE / "merged_results.json", encoding="utf-8"))

by = ("difficulty", "task", "language", "condition")
accuracy = M.average_accuracy(records, by)

rows = [dict(zip(by, k), accuracy=v) for k, v in accuracy.items()]
df = pd.DataFrame(rows)
table = df.pivot(index=["difficulty", "task", "language"], columns="condition", values="accuracy")
table["cot_delta"] = table["cot"] - table["direct"]
table = table.reset_index()
table["difficulty"] = pd.Categorical(table["difficulty"], ["short", "medium", "long", "very_long"], ordered=True)
table = table.sort_values(["difficulty", "task", "language"])

table.round(3).to_csv(HERE / "outputs" / "cot_delta.csv", index=False)
print(table.round(3).to_string(index=False))

