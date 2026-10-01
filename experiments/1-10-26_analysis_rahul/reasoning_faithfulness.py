import pandas as pd

from temporal_answers import HERE, M, VERIFICATION, candidate_matches, judged, last_candidate, load_records, reasoning_body, reasoning_candidates, tail

records = load_records()
(HERE / "outputs").mkdir(exist_ok=True)

rows = []
for r, kind, answer, gold in judged(M.cot(records)):
    candidates = reasoning_candidates(kind, reasoning_body(r), tail(r))
    last = last_candidate(kind, candidates)
    body = reasoning_body(r)
    appears = lambda value: all(any(candidate_matches("date", c, d) for c in candidates) for d in value) if kind == "interval" else any(candidate_matches(kind, c, value) for c in candidates)
    m = r["meta"]
    rows.append(
        {
            "id": r["id"],
            "difficulty": m["difficulty"],
            "task": m["task"],
            "language": m["language"],
            "insertion": m["insertion"],
            "answer_correct": M.is_correct(r),
            "answer_parsed": answer is not None,
            "last_value_found": last is not None,
            "last_value_matches_answer": last is not None and answer is not None and candidate_matches(kind, last, answer),
            "last_value_matches_gold": last is not None and candidate_matches(kind, last, gold),
            "answer_in_reasoning": answer is not None and appears(answer),
            "has_verification": bool(VERIFICATION.search(body)),
        }
    )

per_response = pd.DataFrame(rows)
per_response.to_csv(HERE / "outputs" / "reasoning_faithfulness_per_response.csv", index=False)


def summarise(group):
    parsed = group[group["answer_parsed"]]
    found = parsed[parsed["last_value_found"]]
    wrong, right = parsed[~parsed["answer_correct"]], parsed[parsed["answer_correct"]]
    return pd.Series(
        {
            "cot_answered": len(group),
            "last_value_found_rate": parsed["last_value_found"].mean(),
            "last_value_matches_answer_rate": found["last_value_matches_answer"].mean(),
            "verification_rate": parsed["has_verification"].mean(),
            "no_verification_responses": int((~found["has_verification"]).sum()),
            "last_value_matches_answer_rate_no_verification": found[~found["has_verification"]]["last_value_matches_answer"].mean(),
            "answer_in_reasoning_rate": parsed["answer_in_reasoning"].mean(),
            "wrong_answers": len(wrong),
            "wrong_but_reasoning_ends_at_gold": int(wrong["last_value_matches_gold"].sum()),
            "correct_answers": len(right),
            "correct_but_reasoning_ends_elsewhere": int((right["last_value_found"] & ~right["last_value_matches_answer"]).sum()),
        }
    )


table = per_response.groupby(["difficulty", "task", "language"]).apply(summarise, include_groups=False).reset_index()
table["difficulty"] = pd.Categorical(table["difficulty"], ["short", "medium", "long", "very_long"], ordered=True)
table = table.sort_values(["difficulty", "task", "language"])
table.round(3).to_csv(HERE / "outputs" / "reasoning_faithfulness.csv", index=False)

by_language = per_response.groupby(["language"]).apply(summarise, include_groups=False)
by_task_language = per_response.groupby(["task", "language"]).apply(summarise, include_groups=False)
print(by_language.round(3).to_string())
print(by_task_language.round(3).to_string())
