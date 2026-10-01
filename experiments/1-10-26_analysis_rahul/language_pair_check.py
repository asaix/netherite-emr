import json
import re
from collections import defaultdict

from temporal_answers import HERE, KIND, distractor_features, distractor_texts, load_records, normalise, parse, question_key, question_texts, tail

records = load_records()
questions = question_texts(records)
distractors = distractor_texts(records)
(HERE / "outputs").mkdir(exist_ok=True)

by_question = defaultdict(list)
for r in records:
    m = r["meta"]
    by_question[(m["difficulty"], m["task"], m["question_id"])].append(r)

report = {"questions": len(by_question)}
checks = {}


def record_check(name, failures, total):
    checks[name] = {"checked": total, "failed": len(failures), "examples": failures[:10]}


wrong_count = [list(k) for k, rs in by_question.items() if len(rs) != 12 or {r["meta"]["language"] for r in rs} != {"en_US", "hi_IN"}]
record_check("question_has_12_records_in_both_languages", wrong_count, len(by_question))

answer_mismatch, number_mismatch, per_answer = [], [], {}
for (difficulty, task, qid), rs in by_question.items():
    kind = KIND[task]
    answers = {lang: {parse(kind, r["meta"]["answer"]) if kind == "weekday" else r["meta"]["answer"] for r in rs if r["meta"]["language"] == lang} for lang in ("en_US", "hi_IN")}
    per_answer[(difficulty, task, qid)] = answers
    if any(len(a) != 1 for a in answers.values()) or answers["en_US"] != answers["hi_IN"]:
        answer_mismatch.append([difficulty, task, qid, str(answers)])
    en, hi = (sorted(re.findall(r"\d+", normalise(questions.get((difficulty, task, lang, qid), "")))) for lang in ("en_US", "hi_IN"))
    if en != hi:
        number_mismatch.append([difficulty, task, qid, en, hi])
record_check("gold_answer_same_in_en_and_hi_and_across_all_12_records", answer_mismatch, len(by_question))
record_check("numbers_in_no_insertion_question_same_in_en_and_hi_ignoring_order", number_mismatch, len(by_question))

prompt_mismatch = []
for r in records:
    key = question_key(r)
    if not tail(r).endswith(questions[key]):
        prompt_mismatch.append(r["id"])
record_check("prompt_ends_with_no_insertion_question", prompt_mismatch, len(records))

tail_by_condition = defaultdict(set)
for r in records:
    tail_by_condition[(question_key(r), r["meta"]["insertion"])].add(tail(r))
record_check("prompt_tail_same_for_direct_and_cot", [list(map(str, k)) for k, v in tail_by_condition.items() if len(v) != 1], len(tail_by_condition))

en_to_hi = defaultdict(lambda: defaultdict(set))
hi_to_en = defaultdict(lambda: defaultdict(set))
feature_mismatch = []
for (key, insertion), text in distractors.items():
    difficulty, task, language, qid = key
    if language != "en_US":
        continue
    hindi = distractors.get(((difficulty, task, "hi_IN", qid), insertion))
    en_to_hi[insertion][text].add(hindi)
    hi_to_en[insertion][hindi].add(text)
    if hindi is None or distractor_features(text) != distractor_features(hindi):
        feature_mismatch.append([difficulty, task, qid, insertion, text, hindi])
record_check("distractor_numbers_months_weekdays_same_in_en_and_hi", feature_mismatch, len(distractors) // 2)

for insertion in en_to_hi:
    ambiguous_en = {en: sorted(map(str, his)) for en, his in en_to_hi[insertion].items() if len(his) > 1}
    ambiguous_hi = {hi: sorted(ens) for hi, ens in hi_to_en[insertion].items() if len(ens) > 1}
    checks[f"{insertion}_distractor_pairing_is_one_to_one"] = {
        "distinct_en_distractors": len(en_to_hi[insertion]),
        "distinct_hi_distractors": len(hi_to_en[insertion]),
        "en_with_several_hi": len(ambiguous_en),
        "hi_with_several_en": len(ambiguous_hi),
        "examples": {**dict(list(ambiguous_en.items())[:5]), **dict(list(ambiguous_hi.items())[:5])},
    }

report["checks"] = checks
report["all_passed"] = all(c.get("failed", 0) == 0 and not c.get("en_with_several_hi") and not c.get("hi_with_several_en") for c in checks.values())
json.dump(report, open(HERE / "outputs" / "language_pair_check.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print(json.dumps({"all_passed": report["all_passed"], **{k: {kk: vv for kk, vv in v.items() if kk != "examples"} for k, v in checks.items()}}, indent=2, ensure_ascii=False))
