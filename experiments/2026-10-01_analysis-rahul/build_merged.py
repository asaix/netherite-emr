import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent

RUNS = {
    "short": HERE.parent / "2026-09-29_run-short-rahul" / "outputs" / "results.json",
    "medium": HERE.parent / "2026-09-29_run-medium-rahul" / "output" / "results.json",
    "long": HERE.parent / "2026-09-29_run-long-adi" / "outputs" / "long" / "results.json",
    "very_long": HERE.parent / "2026-09-30_run-very-long-aayush" / "output" / "results.json",
}

DATE_TASKS = {"date_addition", "date_subtraction", "date_duration", "date_recurrence", "day_of_week"}
TASKS = {
    "short": DATE_TASKS,
    "medium": DATE_TASKS,
    "long": {"date_addition", "date_duration"},
    "very_long": None,
}

RECORDS_PER_QUESTION = 12


def question(record):
    meta = record["meta"]
    return meta["difficulty"], meta["task"], meta["question_id"]


records = [
    r
    for difficulty, path in RUNS.items()
    for r in json.load(open(path, encoding="utf-8"))
    if TASKS[difficulty] is None or r["meta"]["task"] in TASKS[difficulty]
]
counts = Counter(map(question, records))
merged = [r for r in records if counts[question(r)] == RECORDS_PER_QUESTION]

with open(HERE / "merged_results.json", "w", encoding="utf-8") as f:
    json.dump(merged, f, indent=2, ensure_ascii=False)

dropped = sum(n != RECORDS_PER_QUESTION for n in counts.values())
print(f"{len(merged)} records, {len(merged) // RECORDS_PER_QUESTION} questions, {dropped} incomplete questions dropped")
