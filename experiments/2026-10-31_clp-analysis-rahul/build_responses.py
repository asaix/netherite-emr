import json
import re

import pandas as pd

import temporal_answers as T
from temporal_answers import (
    HERE,
    KIND,
    TOKEN,
    VERIFICATION,
    candidate_matches,
    distractor_features,
    distractor_texts,
    last_candidate,
    load_responses,
    normalise,
    parse,
    pivot,
    question_key,
    reasoning_candidates,
    reuses_distractor,
    tail,
)

M = T.M

STOP = set(
    """the a an and of to in on at is was for with my i he she it they his her their this that be by as from or are
    have has had will would not but you your we our me always many each every how what which there some very just
    day days month months year years time times date dates week weeks today hour hours minute minutes
    है हैं में की के का को से ने पर और भी यह वह इस उस मैं मुझे मेरा मेरी मेरे हम हमें हमारा था थी थे हूं हूँ हो होता होती
    होते जाता जाती जाते रहता रहती रहते करता करती करते कि कितने कैसे हर नहीं चाहिए गया गई लिए साथ बहुत सबसे वाले वाली
    रही रहा दिन दिनों महीना महीने महीनों साल वर्ष समय तारीख तारीखें तिथि सप्ताह हफ्ते आज घंटे मिनट""".split()
)
CELLS = [("en_US", "direct"), ("en_US", "cot"), ("hi_IN", "direct"), ("hi_IN", "cot"), ("hi_IN", "en-cot"), ("hi_IN", "clp")]
ENGLISH_REASONING = {"en-cot", "clp"}


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


def body_of(content):
    content = content or ""
    matches = list(M.ANSWER.finditer(content))
    return content[: matches[-1].start()] if matches else content


def words(text):
    text = M.ANSWER.sub("", text or "")
    return len(M.HINDI_WORD.findall(text)), len(M.ENGLISH_WORD.findall(text))


def mentions(text, distractor_words):
    return bool(distractor_words & set(TOKEN.findall(normalise(text).casefold()))) if distractor_words else None


def clp_record(r):
    s1, s2 = r["stage1"], r["stage2"]
    return {"id": r["id"], "condition": "clp", "meta": r["meta"], "content": s2["content"], "reasoning_content": None,
            "finish_reason": s2["finish_reason"], "usage": s2["usage"], "stage1": s1}


standard = load_responses("standard")
clp = [clp_record(r) for r in load_responses("clp")]
encot = load_responses("en-cot")
keys = {(r["meta"]["difficulty"], r["meta"]["task"], r["meta"]["question_id"]) for r in clp}
inside = lambda r: (r["meta"]["difficulty"], r["meta"]["task"], r["meta"]["question_id"]) in keys
standard = [r for r in standard if inside(r)]
encot = [r for r in encot if inside(r)]
distractors = distractor_texts(standard)
questions = {question_key(r) + (r["meta"]["insertion"],): tail(r) for r in standard}

checks = {"clp_records": len(clp), "en-cot_records": len(encot), "standard_records": len(standard), "questions": len(keys)}
mismatch = [r["id"] for r in clp if f"Request: {questions[question_key(r) + (r['meta']['insertion'],)].strip()}\n" not in r["stage1"]["message"]]
gold = {question_key(r) + (r["meta"]["insertion"],): r["meta"]["answer"] for r in standard}
checks["clp_question_text_differs_from_standard"] = mismatch
checks["clp_gold_differs_from_standard"] = [r["id"] for r in clp if r["meta"]["answer"] != gold[question_key(r) + (r["meta"]["insertion"],)]]
checks["en-cot_question_text_differs_from_standard"] = [r["id"] for r in encot if tail(r) != questions[question_key(r) + (r["meta"]["insertion"],)]]
checks["en-cot_gold_differs_from_standard"] = [r["id"] for r in encot if r["meta"]["answer"] != gold[question_key(r) + (r["meta"]["insertion"],)]]
checks["en_hi_gold_differs"] = sum(gold[(d, t, "en_US", q, i)] != gold[(d, t, "hi_IN", q, i)] for (d, t, l, q, i) in gold if l == "en_US")

rows = []
for r in standard + encot + clp:
    m = r["meta"]
    key = question_key(r)
    hi_key = (m["difficulty"], m["task"], "hi_IN", m["question_id"])
    en_key = (m["difficulty"], m["task"], "en_US", m["question_id"])
    question = questions[key + (m["insertion"],)]
    kind = KIND[m["task"]]
    extracted = M.extract_answer(r["content"])
    scored = extracted is not None
    correct = scored and M.is_correct(r)
    answer, gold_value = (parse(kind, extracted), parse(kind, m["answer"])) if scored else (None, None)
    body = body_of(r["content"])
    hindi, english = words(r["content"])
    row = {
        "id": r["id"], "qid": f"{m['difficulty']}/{m['task']}/{m['question_id']}", "difficulty": m["difficulty"],
        "task": m["task"], "language": m["language"], "insertion": m["insertion"], "condition": r["condition"],
        "cell": f"{m['language']}/{r['condition']}", "answer_text": extracted, "scored": scored, "correct": bool(correct),
        "cutoff": r["finish_reason"] == "length", "completion_tokens": (r.get("usage") or {}).get("completion_tokens"),
        "hindi_words": hindi, "english_words": english, "verification": bool(VERIFICATION.search(body)),
        "error_type": None, "weekday_offset": None, "predicted_weekday": None, "recurrence_pattern": None,
        "reuse_similar": None, "reuse_dissimilar": None, "mentions_similar": None, "mentions_dissimilar": None,
        "answer_in_reasoning": None, "reasoning_ends_at_gold": None,
    }
    if scored and not correct:
        row["error_type"] = classify(kind, answer, gold_value, pivot(kind, question))
    if m["task"] == "day_of_week" and scored:
        row["weekday_offset"] = None if answer is None else (answer - gold_value + 3) % 7 - 3
        row["predicted_weekday"] = answer
    if m["task"] == "date_recurrence" and scored:
        row["recurrence_pattern"] = recurrence_pattern(question, answer)
    if scored and not correct and answer is not None:
        source = "placebo" if m["insertion"] == "no_insertion" else "inserted"
        for insertion in ("similar_insertion", "dissimilar_insertion"):
            if source == "inserted" and insertion != m["insertion"]:
                continue
            features = distractor_features(distractors[hi_key if m["language"] == "hi_IN" else en_key, insertion])
            if any(features.values()):
                row[f"reuse_{insertion.split('_')[0]}"] = reuses_distractor(kind, answer, gold_value, features)
    dwords = {}
    for insertion in ("similar_insertion", "dissimilar_insertion"):
        if m["insertion"] not in ("no_insertion", insertion):
            continue
        own = content_words(distractors[key, insertion]) - content_words(questions[key + ("no_insertion",)])
        if r["condition"] in ENGLISH_REASONING:
            own |= content_words(distractors[en_key, insertion]) - content_words(questions[en_key + ("no_insertion",)])
        dwords[insertion] = own
    if r["condition"] != "direct" and scored:
        for insertion, w in dwords.items():
            row[f"mentions_{insertion.split('_')[0]}"] = mentions(body, w)
        candidates = reasoning_candidates(kind, body, question)
        last = last_candidate(kind, candidates)
        if answer is not None:
            if kind == "interval":
                row["answer_in_reasoning"] = all(any(candidate_matches("date", c, d) for c in candidates) for d in answer)
            else:
                row["answer_in_reasoning"] = any(candidate_matches(kind, c, answer) for c in candidates)
        row["reasoning_ends_at_gold"] = last is not None and candidate_matches(kind, last, gold_value)
    if r["condition"] == "clp":
        s1 = r["stage1"]
        s1_hindi, s1_english = words(s1["content"])
        row.update({
            "s1_cutoff": s1["finish_reason"] == "length", "s1_tokens": (s1.get("usage") or {}).get("completion_tokens"),
            "s1_hindi_words": s1_hindi, "s1_english_words": s1_english,
            "s1_verification": bool(VERIFICATION.search(s1["content"] or "")),
            "s1_has_value": None, "s1_last_is_gold": None, "s1_last_is_answer": None,
        })
        if kind == "date":
            s1_last = last_candidate(kind, reasoning_candidates(kind, s1["content"] or "", question))
            row.update({
                "s1_has_value": s1_last is not None,
                "s1_last_is_gold": s1_last is not None and candidate_matches(kind, s1_last, parse(kind, m["answer"])),
                "s1_last_is_answer": s1_last is not None and answer is not None and candidate_matches(kind, s1_last, answer),
            })
        for insertion, w in dwords.items():
            row[f"s1_mentions_{insertion.split('_')[0]}"] = mentions(s1["content"], w)
    rows.append(row)

out = HERE / "outputs" / "data"
out.mkdir(parents=True, exist_ok=True)
frame = pd.DataFrame(rows)
frame.to_pickle(out / "responses.pkl")
checks["rows_by_cell"] = frame.groupby("cell").size().to_dict()
checks["questions_by_cell"] = frame.groupby("cell")["qid"].nunique().to_dict()
with open(out / "checks.json", "w", encoding="utf-8") as f:
    json.dump(checks, f, ensure_ascii=False, indent=2, default=str)
print(json.dumps({k: (v if not isinstance(v, list) else len(v)) for k, v in checks.items()}, indent=2, default=str))
