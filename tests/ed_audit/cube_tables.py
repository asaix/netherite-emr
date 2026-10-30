import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from cube_sweep import DIMS, OUT, load

ORDER = {"difficulty": ["short", "medium", "long", "very_long", "very_very_long"]}
METRICS = ["norm_ed", "ed_floor", "ed", "en_len", "hi_len", "len_gap", "en_correct", "hi_correct"]

if __name__ == "__main__":
    frame = load()
    pd.set_option("display.width", 220, "display.max_columns", 40, "display.max_rows", 500)
    slices = {"standard/content": frame[frame.set.eq("standard")],
              "ron/content": frame[frame.set.eq("ron") & frame.field.eq("content")],
              "ron/reasoning": frame[frame.set.eq("ron") & frame.field.eq("reasoning_content")]}
    lines = []
    for name, part in slices.items():
        print(f"\n##### {name} n={len(part)} questions={part.groupby(['difficulty','task','question_id']).ngroups}")
        print(part[METRICS].mean().round(3).to_dict())
        for d in ["difficulty", "task", "insertion", "outcome"]:
            table = part.groupby(d, observed=True)[METRICS].mean().join(part.groupby(d, observed=True).size().rename("n"))
            if d in ORDER:
                table = table.reindex(ORDER[d])
            print(f"\n-- by {d}\n{table.round(3).to_string()}")
        for metric in ["norm_ed", "ed_floor", "en_correct", "hi_correct"]:
            piv = part.pivot_table(index="task", columns="difficulty", values=metric, aggfunc="mean").reindex(columns=ORDER["difficulty"])
            print(f"\n-- {metric}: task x difficulty\n{piv.round(3).to_string()}")
        for a, b in [("task", "outcome"), ("difficulty", "outcome"), ("insertion", "outcome"), ("task", "insertion"), ("difficulty", "insertion")]:
            piv = part.pivot_table(index=a, columns=b, values="norm_ed", aggfunc="mean")
            print(f"\n-- norm_ed: {a} x {b}\n{piv.round(3).to_string()}")
        print("\n-- outcome counts by task\n", pd.crosstab(part.task, part.outcome).to_string())
