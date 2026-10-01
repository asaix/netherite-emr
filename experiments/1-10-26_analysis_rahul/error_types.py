import pandas as pd

from temporal_answers import HERE, M, judged, load_records, pivot, tail

records = load_records()
(HERE / "outputs").mkdir(exist_ok=True)


def classify(kind, answer, gold, today):
    if answer is None:
        return "invalid_answer", None
    if answer == gold:
        return "format_only", 0
    if kind == "date":
        error = (answer - gold).days
        if (answer - today).days == -(gold - today).days:
            return "wrong_direction", error
        if abs(error) == 1:
            return "off_by_one", error
        if answer.year == gold.year and answer.day == gold.day:
            return "month_slip", error
        if answer.month == gold.month and answer.day == gold.day:
            return "year_slip", error
        return "other", error
    if kind == "interval":
        shifts = [(a - g).days for a, g in zip(answer, gold)]
        if shifts[0] == shifts[1] and shifts[0] % 7 == 0:
            return "week_shift", shifts[0]
        if all(abs(s) <= 1 for s in shifts):
            return "off_by_one", shifts[0]
        return "other", shifts[0]
    if kind == "weekday":
        error = (answer - gold + 3) % 7 - 3
        return ("off_by_one" if abs(error) == 1 else "other"), error
    if kind == "time":
        error = (answer - gold + 720) % 1440 - 720
        if (answer - today) % 1440 == (today - gold) % 1440:
            return "wrong_direction", error
        if abs(error) == 1:
            return "off_by_one", error
        if abs(error) == 60:
            return "off_by_one_hour", error
        return "other", error
    error = answer - gold
    if kind == "minutes" and answer and (answer * 60 == gold or answer == gold * 60):
        return "unit_confusion", error
    if abs(error) == 1:
        return "off_by_one", error
    if kind == "minutes" and abs(error) == 60:
        return "off_by_one_hour", error
    return "other", error


rows = []
for r, kind, answer, gold in judged(records):
    if M.is_correct(r):
        continue
    error_type, signed_error = classify(kind, answer, gold, pivot(kind, tail(r)))
    m = r["meta"]
    rows.append(
        {
            "id": r["id"],
            "difficulty": m["difficulty"],
            "task": m["task"],
            "language": m["language"],
            "condition": r["condition"],
            "insertion": m["insertion"],
            "error_type": error_type,
            "signed_error": signed_error,
        }
    )

errors = pd.DataFrame(rows)
errors.to_csv(HERE / "outputs" / "error_types_per_response.csv", index=False)

order = ["off_by_one", "off_by_one_hour", "wrong_direction", "month_slip", "year_slip", "week_shift", "unit_confusion", "format_only", "invalid_answer", "other"]
counts = errors.pivot_table(index=["difficulty", "task", "language", "condition"], columns="error_type", values="id", aggfunc="count", fill_value=0)
counts = counts.reindex(columns=[c for c in order if c in counts.columns])
counts.insert(0, "wrong", counts.sum(axis=1))
counts = counts.reset_index()
counts["difficulty"] = pd.Categorical(counts["difficulty"], ["short", "medium", "long", "very_long"], ordered=True)
counts = counts.sort_values(["difficulty", "task", "language", "condition"])
counts.to_csv(HERE / "outputs" / "error_types.csv", index=False)

pooled = errors.pivot_table(index=["task", "language", "condition"], columns="error_type", values="id", aggfunc="count", fill_value=0)
pooled = pooled.reindex(columns=[c for c in order if c in pooled.columns])
print((pooled.div(pooled.sum(axis=1), axis=0)).round(2).assign(wrong=pooled.sum(axis=1)).to_string())
