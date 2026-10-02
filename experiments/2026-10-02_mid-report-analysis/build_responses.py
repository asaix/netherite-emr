import re

import pandas as pd

from temporal_answers import (
    HERE,
    M,
    TOKEN,
    VERIFICATION,
    candidate_matches,
    distractor_texts,
    judged,
    last_candidate,
    load_records,
    normalise,
    pivot,
    question_key,
    reasoning_body,
    reasoning_candidates,
    reuses_distractor,
    distractor_features,
    tail,
)

STOP = set(
    """the a an and of to in on at is was for with my i he she it they his her their this that be by as from or are
    have has had will would not but you your we our me always many each every how what which there some very just
    day days month months year years time times date dates week weeks today hour hours minute minutes
    है हैं में की के का को से ने पर और भी यह वह इस उस मैं मुझे मेरा मेरी मेरे हम हमें हमारा था थी थे हूं हूँ हो होता होती
    होते जाता जाती जाते रहता रहती रहते करता करती करते कि कितने कैसे हर नहीं चाहिए गया गई लिए साथ बहुत सबसे वाले वाली
    रही रहा दिन दिनों महीना महीने महीनों साल वर्ष समय तारीख तारीखें तिथि सप्ताह हफ्ते आज घंटे मिनट""".split()
)


def classify(kind, answer, gold, today):
    if answer is None:
        return "invalid_answer"
    if answer == gold:
        return "format_only"
    if kind == "date":
        if (answer - today).days == -(gold - today).days:
            return "wrong_direction"
        if abs((answer - gold).days) == 1:
            return "off_by_one"
        if answer.year == gold.year and answer.day == gold.day:
            return "month_slip"
        if answer.month == gold.month and answer.day == gold.day:
            return "year_slip"
        return "other"
    if kind == "interval":
        shifts = [(a - g).days for a, g in zip(answer, gold)]
        if shifts[0] == shifts[1] and shifts[0] % 7 == 0:
            return "week_shift"
        return "off_by_one" if all(abs(s) <= 1 for s in shifts) else "other"
    if kind == "weekday":
        return "off_by_one" if abs((answer - gold + 3) % 7 - 3) == 1 else "other"
    if kind == "time":
        if (answer - today) % 1440 == (today - gold) % 1440:
            return "wrong_direction"
        error = (answer - gold + 720) % 1440 - 720
        if abs(error) == 1:
            return "off_by_one"
        return "off_by_one_hour" if abs(error) == 60 else "other"
    if kind == "minutes" and answer and (answer * 60 == gold or answer == gold * 60):
        return "unit_confusion"
    if abs(answer - gold) == 1:
        return "off_by_one"
    if kind == "minutes" and abs(answer - gold) == 60:
        return "off_by_one_hour"
    return "other"


def content_words(text):
    return {t for t in TOKEN.findall(normalise(text).casefold()) if len(t) >= 3 and t not in STOP and not t.isdigit()}


def weekday_offset(answer, gold):
    return None if answer is None else (answer - gold + 3) % 7 - 3


def recurrence_pattern(question, answer):
    q = normalise(question)
    interval = re.search(r"every (\d+) day|हर (\d+) दिन", q)
    k = re.search(r"the (\d+) occurrence|(\d+)वीं", q)
    if answer is None or not interval or not k:
        return None
    interval = int(next(g for g in interval.groups() if g))
    k = int(next(g for g in k.groups() if g))
    offset = (answer - pivot("date", question)).days
    if offset == interval * k:
        return "correct"
    if offset == -interval * k:
        return "mirror"
    if offset == interval:
        return "first_step"
    return "other"


records = load_records()
distractors = distractor_texts(records)
judgement = {r["id"]: (kind, answer, gold) for r, kind, answer, gold in judged(records)}

rows = []
for r in records:
    m = r["meta"]
    kind, answer, gold = judgement.get(r["id"], (None, None, None))
    scored = r["id"] in judgement
    correct = scored and M.is_correct(r)
    question = tail(r)
    body = reasoning_body(r)
    target, total = M.target_words(r)
    key = question_key(r)
    base = question if m["insertion"] == "no_insertion" else question[len(distractors[key, m["insertion"]]):].strip()
    row = {
        "id": r["id"],
        "qid": f"{m['difficulty']}/{m['task']}/{m['question_id']}",
        "difficulty": m["difficulty"],
        "task": m["task"],
        "language": m["language"],
        "insertion": m["insertion"],
        "condition": r["condition"],
        "scored": scored,
        "correct": correct,
        "cutoff": r["finish_reason"] == "length",
        "completion_tokens": (r.get("usage") or {}).get("completion_tokens"),
        "words": total,
        "target_words": target,
        "verification": bool(VERIFICATION.search(body)),
        "error_type": None,
        "weekday_offset": None,
        "predicted_weekday": None,
        "recurrence_pattern": None,
        "reuses_distractor": None,
        "reuse_source": None,
        "mentions_similar": None,
        "mentions_dissimilar": None,
        "answer_in_reasoning": None,
        "reasoning_ends_at_gold": None,
    }
    if scored and not correct:
        row["error_type"] = classify(kind, answer, gold, pivot(kind, question))
    if m["task"] == "day_of_week" and scored:
        row["weekday_offset"] = weekday_offset(answer, gold)
        row["predicted_weekday"] = answer
    if m["task"] == "date_recurrence" and scored:
        row["recurrence_pattern"] = recurrence_pattern(question, answer)
    if scored and not correct and answer is not None:
        source = "placebo" if m["insertion"] == "no_insertion" else "inserted"
        for insertion in ("similar_insertion", "dissimilar_insertion"):
            if source == "inserted" and insertion != m["insertion"]:
                continue
            features = distractor_features(distractors[key, insertion])
            if any(features.values()):
                row[f"reuse_{insertion.split('_')[0]}"] = reuses_distractor(kind, answer, gold, features)
    if r["condition"] == "cot" and scored:
        tokens = set(TOKEN.findall(normalise(body).casefold()))
        for insertion in ("similar_insertion", "dissimilar_insertion"):
            if m["insertion"] not in ("no_insertion", insertion):
                continue
            words = content_words(distractors[key, insertion]) - content_words(base)
            if words:
                row[f"mentions_{insertion.split('_')[0]}"] = bool(words & tokens)
        candidates = reasoning_candidates(kind, body, question)
        last = last_candidate(kind, candidates)
        if answer is not None:
            if kind == "interval":
                row["answer_in_reasoning"] = all(any(candidate_matches("date", c, d) for c in candidates) for d in answer)
            else:
                row["answer_in_reasoning"] = any(candidate_matches(kind, c, answer) for c in candidates)
        row["reasoning_ends_at_gold"] = last is not None and candidate_matches(kind, last, gold)
    rows.append(row)

out = HERE / "outputs" / "data"
out.mkdir(parents=True, exist_ok=True)
frame = pd.DataFrame(rows).drop(columns=["reuses_distractor", "reuse_source"])
frame.to_pickle(out / "responses.pkl")
frame.drop(columns=["predicted_weekday"]).to_csv(out / "responses.csv", index=False)
print(len(frame), "responses", frame["scored"].sum(), "scored")
