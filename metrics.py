import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "tools" / "temporal-reasoning-dataset" / "src"))

from trd.utils.locale import DAY_NAMES

ANSWER = re.compile(r"(?:Answer|उत्तर)\s*\**\s*[:：]\s*(.*)")
DIGITS = str.maketrans("०१२३४५६७८९٠١٢٣٤٥٦٧٨٩", "0123456789" * 2)
WEEKDAYS = {name.casefold(): day for names in DAY_NAMES.values() for day, name in names.items()}
HINDI_WORD = re.compile(r"[\u0900-\u0963\u0971-\u097F]+")
ENGLISH_WORD = re.compile(r"[A-Za-z]+")


def extract_answer(content):
    matches = ANSWER.findall(content or "")
    return matches[-1].strip().strip("*`.। ").translate(DIGITS) if matches else None


def is_correct(record):
    answer, key = extract_answer(record["content"]), record["meta"]["answer"]
    if record["meta"]["task"] == "day_of_week":
        return WEEKDAYS.get(answer.casefold()) == WEEKDAYS[key.casefold()]
    return answer == key


def answered(records):
    return [r for r in records if extract_answer(r["content"]) is not None]


def cot(records):
    return [r for r in records if r["condition"] == "cot"]


def group(records, by):
    groups = defaultdict(list)
    for r in records:
        fields = {**r["meta"], "condition": r["condition"]}
        groups[tuple(fields[k] for k in by)].append(r)
    return dict(sorted(groups.items()))


def average_accuracy(records, by=()):
    return {k: sum(map(is_correct, rs)) / len(rs) for k, rs in group(answered(records), by).items()}


def target_words(record):
    text = ANSWER.sub("", (record.get("reasoning_content") or "") + record["content"])
    hindi, english = len(HINDI_WORD.findall(text)), len(ENGLISH_WORD.findall(text))
    return {"hi_IN": hindi, "en_US": english}[record["meta"]["language"]], hindi + english


def target_language_cot_ratio(record):
    target, total = target_words(record)
    return target / total if total else None


def average_target_language_cot_ratio(records, by=()):
    averages = {}
    for k, rs in group(cot(records), by).items():
        ratios = [x for x in map(target_language_cot_ratio, rs) if x is not None]
        averages[k] = sum(ratios) / len(ratios) if ratios else None
    return averages


def pooled_target_language_cot_ratio(records, by=()):
    pooled = {}
    for k, rs in group(cot(records), by).items():
        target, total = map(sum, zip(*map(target_words, rs)))
        pooled[k] = target / total if total else None
    return pooled


GROUPINGS = [
    ("language", "condition", "insertion"),
    ("language", "condition", "insertion", "task"),
    ("language", "condition", "difficulty"),
]


def summary(records, by):
    accuracy = average_accuracy(records, by)
    cot_avg = average_target_language_cot_ratio(records, by)
    cot_pooled = pooled_target_language_cot_ratio(records, by)
    return [
        {
            **dict(zip(by, k)),
            "responses": len(rs),
            "scored": len(answered(rs)),
            "accuracy": accuracy.get(k),
            "cot_ratio_avg": cot_avg.get(k),
            "cot_ratio_pooled": cot_pooled.get(k),
        }
        for k, rs in group(records, by).items()
    ]


def per_response(records):
    return [
        {
            "id": r["id"],
            "correct": int(is_correct(r)) if extract_answer(r["content"]) is not None else None,
            "cot_ratio": target_language_cot_ratio(r) if r["condition"] == "cot" else None,
        }
        for r in records
    ]


def write_csv(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def fmt(value):
    if value is None:
        return "-"
    return f"{value:.3f}" if isinstance(value, float) else str(value)


def print_table(title, rows):
    header = list(rows[0])
    cells = [[fmt(v) for v in row.values()] for row in rows]
    widths = [max(len(h), *(len(c[i]) for c in cells)) for i, h in enumerate(header)]
    numeric = [not isinstance(v, str) for v in rows[0].values()]

    def line(values):
        return " | ".join(v.rjust(w) if n else v.ljust(w) for v, w, n in zip(values, widths, numeric))

    print(f"\n{title}")
    print(line(header))
    print("-+-".join("-" * w for w in widths))
    for c in cells:
        print(line(c))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("results", nargs="+")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    records = [r for path in args.results for r in json.load(open(path, encoding="utf-8"))]
    discarded = [r for r in records if extract_answer(r["content"]) is None]
    cut_off = sum(r["finish_reason"] == "length" for r in discarded)
    print(f"{cut_off} discarded because they were cut off at max_tokens")
    if len(discarded) > cut_off:
        print(f"{len(discarded) - cut_off} discarded because they had no answer line")

    for by in GROUPINGS:
        rows = summary(records, by)
        print_table(f"by {', '.join(by)}", rows)
        write_csv(rows, out_dir / f"by_{'_'.join(by)}.csv")

    write_csv(per_response(records), out_dir / "per_response.csv")
    print(f"\ncsvs written to {out_dir}")
