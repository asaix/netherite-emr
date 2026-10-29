import argparse
import json
import re
from itertools import combinations
from pathlib import Path

import pandas as pd
import yaml

from metrics import DIFFICULTY_ORDER, extract_answer, is_correct

CONFIG = yaml.safe_load(open(Path(__file__).resolve().parent / "config" / "ed.yaml", encoding="utf-8"))
FIELDS = ["content", "reasoning_content"]
KEYS = ["difficulty", "task", "insertion"]
STATS = ["count", "mean", "median", "std"]
DATED = re.compile(r"\d{4}-\d{2}(?:-\d{2})?")
UNDATED = re.compile(r"\d{1,2}(?:-\d{2})?")


def partial(short, full):
    if not (UNDATED.fullmatch(short) and DATED.fullmatch(full)):
        return False
    parts = [int(p) for p in short.split("-")]
    return [int(p) for p in full.split("-")][-len(parts):] == parts


def same_value(a, b):
    x, y = a.split(".."), b.split("..")
    return len(x) == len(y) and all(p == q or partial(p, q) or partial(q, p) for p, q in zip(x, y))


def substitution(a, b):
    if a == b:
        return 0
    x, y = a.split(" "), b.split(" ")
    if len(x) == len(y) and x[0] == y[0] and all(map(same_value, x[1:], y[1:])):
        return CONFIG["partial_date_cost"]
    return 1


def edit_distance(parsed_list1, parsed_list2):
    previous = list(range(len(parsed_list2) + 1))
    for i, a in enumerate(parsed_list1, 1):
        current = [i]
        for j, b in enumerate(parsed_list2, 1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + substitution(a, b)))
        previous = current
    return previous[-1]


def correct(record):
    text = record["content"]["original"]
    return int(is_correct({**record, "content": text})) if extract_answer(text) is not None else None


def compare(en, hi):
    meta = en["meta"]
    row = {"question_id": meta["question_id"], **{k: meta[k] for k in KEYS}, "en_correct": correct(en), "hi_correct": correct(hi)}
    for field in FIELDS:
        a, b = en[field]["parsed"], hi[field]["parsed"]
        distance = edit_distance(a, b) if a is not None and b is not None else None
        row |= {
            f"{field}_edit_distance": distance,
            f"{field}_norm_edit_distance": None if distance is None else distance / max(len(a), len(b)) if a or b else 0.0,
            f"{field}_en_len": None if a is None else len(a),
            f"{field}_hi_len": None if b is None else len(b),
            f"{field}_en_seq": None if a is None else json.dumps(a, ensure_ascii=False),
            f"{field}_hi_seq": None if b is None else json.dumps(b, ensure_ascii=False),
        }
    return row


def cube(pairs):
    rows = []
    for n in range(len(KEYS) + 1):
        for keys in combinations(KEYS, n):
            groups = pairs.groupby(list(keys), observed=True) if keys else [((), pairs)]
            for values, group in groups:
                row = {k: dict(zip(keys, values)).get(k, "ALL") for k in KEYS} | {"pairs": len(group)}
                for field in FIELDS:
                    column = group[f"{field}_norm_edit_distance"]
                    row |= {f"{field}_norm_edit_distance_{stat}": getattr(column, stat)() for stat in STATS}
                rows.append(row)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output")
    ap.add_argument("--nodrop", action="store_true")
    args = ap.parse_args()

    by_question = {}
    for record in json.load(open(args.input, encoding="utf-8"))["records"]:
        if record["condition"] == "cot":
            meta = record["meta"]
            by_question.setdefault((meta["difficulty"], meta["task"], meta["question_id"], meta["insertion"]), {})[meta["language"]] = record
    pairs = pd.DataFrame([compare(langs["en_US"], langs["hi_IN"]) for langs in by_question.values() if {"en_US", "hi_IN"} <= set(langs)])
    pairs["difficulty"] = pd.Categorical(pairs["difficulty"], categories=sorted(DIFFICULTY_ORDER, key=DIFFICULTY_ORDER.get), ordered=True)
    pairs = pairs.sort_values(KEYS + ["question_id"], key=lambda c: c.astype(int) if c.name == "question_id" else c)
    aggregates = cube(pairs)

    with pd.option_context("display.max_rows", None, "display.max_columns", None, "display.width", None):
        print(aggregates.to_string(index=False, float_format="%.4f"))
    if args.output:
        if not args.nodrop:
            aggregates, pairs = aggregates.dropna(axis=1, how="all"), pairs.dropna(axis=1, how="all")
        with open(args.output, "w", encoding="utf-8", newline="") as f:
            aggregates.to_csv(f, index=False)
            f.write("\n")
            pairs.to_csv(f, index=False)
