import json
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(Path(__file__).parent), str(ROOT / "experiments/2026-10-29_ed-analysis")]
from cube_sweep import OUT, load
from ed import substitution

ANSWERS = {"ANSWER", "SPITANSWER"}
META = ANSWERS | {"GOAL", "PLAN", "RULE", "CHECK", "REVISE", "IGNORE", "FORMAT"}
KEY = ["difficulty", "task", "question_id", "insertion"]
QUESTION = ["difficulty", "task", "question_id"]
VIEWS = {
    "full": lambda s: s,
    "no_answer": lambda s: [t for t in s if t.split(" ")[0] not in ANSWERS],
    "core": lambda s: [t for t in s if t.split(" ")[0] not in META],
    "ops": lambda s: [t.split(" ")[0] for t in s],
    "ops_no_answer": lambda s: [t.split(" ")[0] for t in s if t.split(" ")[0] not in ANSWERS],
    "ops_core": lambda s: [t.split(" ")[0] for t in s if t.split(" ")[0] not in META],
}


def distance(a, b):
    if not a or not b:
        return None
    vocab = sorted(set(a) | set(b))
    index = {t: i for i, t in enumerate(vocab)}
    costs = np.array([[substitution(x, y) for y in vocab] for x in vocab], dtype=float)
    x, y = np.array([index[t] for t in a]), np.array([index[t] for t in b])
    positions = np.arange(len(b) + 1, dtype=float)
    previous = positions.copy()
    for i, token in enumerate(x, 1):
        step = np.empty(len(b) + 1)
        step[0] = i
        step[1:] = np.minimum(previous[1:] + 1, previous[:-1] + costs[token, y])
        previous = np.minimum.accumulate(step - positions) + positions
    return previous[-1] / max(len(a), len(b))


def views(pair):
    a, b = pair
    return {name: distance(view(a), view(b)) for name, view in VIEWS.items()}


def run(pool, pairs):
    return pd.DataFrame(pool.map(views, pairs, chunksize=32))


if __name__ == "__main__":
    frame = load()
    frame["en"] = frame.en_seq.map(json.loads)
    frame["hi"] = frame.hi_seq.map(json.loads)
    rows = []
    with Pool(16) as pool:
        for (s, field), part in frame.groupby(["set", "field"]):
            part = part.reset_index(drop=True)
            meta = {"set": s, "field": field}
            same = run(pool, list(zip(part.en, part.hi)))
            rows.append(pd.concat([part[KEY + ["en_correct", "hi_correct"]], same], axis=1).assign(kind="en_hi_same_q", **meta))
            shifted = part.sort_values(QUESTION[:2] + ["insertion", "question_id"], key=lambda c: c.astype(int) if c.name == "question_id" else c)
            other = shifted.groupby(QUESTION[:2] + ["insertion"]).hi.transform(lambda c: list(np.roll(c.to_numpy(dtype=object), 1)))
            cross = run(pool, list(zip(shifted.en, other)))
            rows.append(pd.concat([shifted[KEY].reset_index(drop=True), cross], axis=1).assign(kind="en_hi_other_q", **meta))
            for lang in ["en", "hi"]:
                wide = part.pivot(index=QUESTION, columns="insertion", values=lang)
                for other_ins in ["similar_insertion", "dissimilar_insertion"]:
                    both = wide[["no_insertion", other_ins]].dropna()
                    self_d = run(pool, list(zip(both["no_insertion"], both[other_ins])))
                    rows.append(pd.concat([both.index.to_frame(index=False), self_d], axis=1).assign(kind=f"{lang}_self", insertion=other_ins, **meta))
    result = pd.concat(rows, ignore_index=True)
    result.to_pickle(OUT / "variants.pkl")
    check = result[result.kind.eq("en_hi_same_q")].merge(frame[["set", "field", *KEY, "norm_ed"]], on=["set", "field", *KEY])
    print("rows", len(check), "max abs diff full vs csv", (check.full - check.norm_ed).abs().max())
    print(result.groupby(["set", "field", "kind"])[list(VIEWS)].mean().round(3).to_string())
    print(result.groupby(["set", "field", "kind"])[list(VIEWS)].median().round(3).to_string())
