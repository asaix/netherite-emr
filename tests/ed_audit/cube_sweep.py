import json
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
EDOUT = ROOT / "experiments/2026-10-29_ed-analysis/edout"
OUT = Path(__file__).parent / "outputs/cube_findings"
FIELDS = ["content", "reasoning_content"]
DIMS = ["set", "field", "difficulty", "task", "insertion", "outcome"]
METRICS = ["norm_ed", "ed", "len_gap", "ed_floor", "en_len", "hi_len", "en_correct", "hi_correct"]
OUTCOMES = ["both correct", "en only", "hi only", "both wrong", "unanswered"]
TAUTOLOGY = {("en_correct", "outcome"), ("hi_correct", "outcome")}


def outcome(en, hi):
    return "unanswered" if pd.isna(en) or pd.isna(hi) else OUTCOMES[2 * (1 - int(en)) + (1 - int(hi))]


def load():
    frames = []
    for file in sorted(EDOUT.glob("*/*.csv")):
        if file.parent.name == "stats":
            continue
        pairs = pd.read_csv(StringIO(file.read_text(encoding="utf-8").split("\n\n", 1)[1]))
        for field in FIELDS:
            if f"{field}_norm_edit_distance" not in pairs:
                continue
            en, hi = pairs[f"{field}_en_len"], pairs[f"{field}_hi_len"]
            frames.append(pd.DataFrame({
                "set": file.parent.name,
                "field": field,
                **{k: pairs[k] for k in ["question_id", "difficulty", "task", "insertion", "en_correct", "hi_correct"]},
                "outcome": [outcome(e, h) for e, h in zip(pairs["en_correct"], pairs["hi_correct"])],
                "norm_ed": pairs[f"{field}_norm_edit_distance"],
                "ed": pairs[f"{field}_edit_distance"],
                "en_len": en,
                "hi_len": hi,
                "len_gap": hi - en,
                "ed_floor": ((hi - en).abs() / pd.concat([en, hi], axis=1).max(axis=1)).fillna(0),
                "en_seq": pairs[f"{field}_en_seq"],
                "hi_seq": pairs[f"{field}_hi_seq"],
            }).dropna(subset=["norm_ed"]))
    return pd.concat(frames, ignore_index=True)


def r2(y, x_frame):
    y = y - y.mean()
    total = (y ** 2).sum()
    if total == 0 or x_frame.shape[1] == 0:
        return 0.0
    x = np.c_[np.ones(len(y)), x_frame.to_numpy(float)]
    beta = np.linalg.lstsq(x, y, rcond=None)[0]
    return 1 - ((y - x @ beta) ** 2).sum() / total


def view(frame, metric, x, color):
    d = frame[[metric, x] + ([color] if color else [])].dropna()
    y = d[metric].to_numpy(float)
    means = d.groupby(x, observed=True)[metric].mean()
    row = {"n": len(d), "levels": len(means), "min_mean": means.min(), "max_mean": means.max(),
           "range": means.max() - means.min(), "lowest": means.idxmin(), "highest": means.idxmax()}
    row["eta2"] = r2(y, pd.get_dummies(d[x], drop_first=True))
    if color:
        additive = pd.get_dummies(d[[x, color]], drop_first=True)
        cells = pd.get_dummies(d[x].astype(str) + "|" + d[color].astype(str), drop_first=True)
        row["r2_additive"] = r2(y, additive)
        row["r2_cells"] = r2(y, cells)
        row["interaction"] = row["r2_cells"] - row["r2_additive"]
    return row


def sweep(frame):
    slices = {"standard/content": frame[frame.set.eq("standard")],
              "ron/content": frame[frame.set.eq("ron") & frame.field.eq("content")],
              "ron/reasoning": frame[frame.set.eq("ron") & frame.field.eq("reasoning_content")],
              "all": frame}
    bars, scatter = [], []
    for name, part in slices.items():
        live = [d for d in DIMS if part[d].nunique() > 1]
        for metric in METRICS:
            for x in live:
                if (metric, x) in TAUTOLOGY:
                    continue
                for color in [None, *[c for c in live if c != x]]:
                    bars.append({"slice": name, "metric": metric, "x": x, "color": color or "none", **view(part, metric, x, color)})
            for gx in ["ed_floor", "len_gap"]:
                if gx == metric:
                    continue
                for color in ["none", *live]:
                    groups = [("all", part)] if color == "none" else part.groupby(color, observed=True)
                    for level, sub in groups:
                        s = sub[[gx, metric]].dropna()
                        if len(s) > 20 and s[gx].nunique() > 1 and s[metric].nunique() > 1:
                            scatter.append({"slice": name, "metric": metric, "gapx": gx, "color": color, "level": level, "n": len(s),
                                            "spearman": s[gx].rank().corr(s[metric].rank())})
    return pd.DataFrame(bars), pd.DataFrame(scatter)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    frame = load()
    cube_line = (EDOUT / "cube.html").read_text(encoding="utf-8").split("\n")[24]
    cube = json.loads(cube_line[len("const D = "):].rstrip().rstrip(";"))
    print("rows csv", len(frame), "cube", len(cube["question_id"]))
    key = frame.groupby(["set", "field"]).norm_ed.mean().round(4)
    print(key)
    print("cube mean all", round(float(np.mean(cube["num"]["norm_ed"])), 4), "csv", round(frame.norm_ed.mean(), 4))
    unit = frame[frame.set.eq("standard")].groupby(["difficulty", "task", "question_id", "insertion"]).size()
    print("standard unique pair keys", len(unit), "max rows per key", unit.max())
    print("standard questions", frame[frame.set.eq("standard")].groupby(["difficulty", "task", "question_id"]).ngroups)

    bars, scatter = sweep(frame)
    bars.to_csv(OUT / "sweep_views.csv", index=False)
    scatter.to_csv(OUT / "sweep_scatter.csv", index=False)
    print("bar/box/heatmap views", len(bars), "scatter rows", len(scatter))

    pd.set_option("display.width", 200, "display.max_columns", 30, "display.max_rows", 300, "display.max_colwidth", 30)
    for name in ["standard/content", "ron/content", "ron/reasoning"]:
        part = bars[bars.slice.eq(name)]
        print(f"\n=== {name}: main effects, eta2 by metric x group-by")
        print(part[part.color.eq("none")].pivot(index="metric", columns="x", values="eta2").round(3))
        print(f"\n=== {name}: largest interactions")
        cols = ["metric", "x", "color", "n", "eta2", "r2_additive", "r2_cells", "interaction"]
        print(part[part.color.ne("none")].sort_values("interaction", ascending=False).drop_duplicates(["metric", "r2_cells"]).head(12)[cols].round(3).to_string(index=False))
        s = scatter[scatter.slice.eq(name) & scatter.color.eq("none")]
        print(f"\n=== {name}: spearman with scatter x")
        print(s.pivot(index="metric", columns="gapx", values="spearman").round(3))
