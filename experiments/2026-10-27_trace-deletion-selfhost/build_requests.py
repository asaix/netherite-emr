import argparse
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT))

import metrics as M

RUNS = [
    "2026-10-17_run-short-leftover-rahul/outputs",
    "2026-10-17_run-medium-leftover-rahul/output",
    "2026-10-16_finish-run-long-adi/outputs/long",
    "2026-10-18_run-very-long-leftover-aayush/output",
    "2026-10-18-very_very_long-aayush/output",
]
SEED = 26
PILOT = {"hi_IN": 12, "en_US": 8}
LENGTH_RATIO = 3.0
MIN_SHARED = 2
RARE = 0.02
CALENDAR = {"january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december",
            "जनवरी", "फरवरी", "मार्च", "अप्रैल", "मई", "जून", "जुलाई", "अगस्त", "सितंबर", "सितम्बर", "अक्टूबर", "अक्तूबर", "नवंबर", "नवम्बर", "दिसंबर", "दिसम्बर"} | set(M.WEEKDAYS)

STOP = set(re.search(r'STOP = set\(\s*"""(.*?)"""', (ROOT / "experiments/2026-10-02_mid-report-analysis/build_responses.py").read_text(encoding="utf-8"), re.S).group(1).split())
TOKEN = re.compile(r"[^\s.,!?।'\"():;]+")
SENTENCE = re.compile(r"[^\n]+?(?:[।!?]|\.(?=\s|$)|$)", re.M)
DIGIT = re.compile(r"\d")


def norm(text):
    return (text or "").translate(M.DIGITS)


def content_words(text):
    return {t for t in TOKEN.findall(norm(text).casefold()) if len(t) >= 3 and t not in STOP and not t.isdigit()}


def question(record):
    return record["request"]["messages"][0]["content"].split("\n\n")[-1]


def body(content):
    return content[: list(M.ANSWER.finditer(content))[-1].start()]


def spans(text):
    return [(m.start() + len(m.group()) - len(m.group().lstrip()), m.end()) for m in SENTENCE.finditer(text) if m.group().strip()]


def answer_index(task, answer, sentences):
    values = answer.split(" to ") if task == "interval_date" else [answer]
    patterns = [re.compile(r"(?<![\w:.-])" + re.escape(norm(v).casefold()) + r"(?![\w:-])(?!\.\d)") for v in values]
    for i, s in enumerate(sentences):
        if any(p.search(norm(s).casefold()) for p in patterns):
            return i
    return len(sentences) - 1


def assemble(text, sp, keep):
    pieces = [text[: sp[0][0]]]
    last = max(keep)
    for i in sorted(keep):
        end = sp[i][1] if i == last else sp[i + 1][0]
        pieces.append(text[sp[i][0]:end])
    return "".join(pieces).rstrip()


def base_rates(records):
    docs = defaultdict(Counter)
    totals = Counter()
    for r in records:
        if r["condition"] == "cot" and r["meta"]["insertion"] == "no_insertion" and r["content"]:
            lang = r["meta"]["language"]
            totals[lang] += 1
            docs[lang].update(content_words(r["content"]))
    return {lang: {w: n / totals[lang] for w, n in docs[lang].items()} for lang in docs}


def build(record, base_record, funnel, lang, rates):
    content = record["content"] or ""
    answer = M.extract_answer(content)
    if answer is None or record.get("finish_reason") == "length":
        funnel[lang, "0 unscored or cut off"] += 1
        return None
    correct = M.is_correct(record)
    tag = "right" if correct else "wrong"
    funnel[lang, f"1 {tag}"] += 1
    if correct:
        return None
    q, base = question(record), question(base_record)
    words = content_words(q[: len(q) - len(base)]) - content_words(base)
    strict = words - CALENDAR
    text = body(content)
    sp = spans(text)
    sentences = [text[a:b] for a, b in sp]
    rare = {w for w in strict if rates[lang].get(w, 0) < RARE}
    mentions = [i for i, s in enumerate(sentences) if len(content_words(s) & strict) >= MIN_SHARED or content_words(s) & rare]
    touched = {i for i, s in enumerate(sentences) if content_words(s) & words}
    if not mentions:
        return None
    funnel[lang, "2 mentions distractor"] += 1
    k = mentions[0]
    a = answer_index(record["meta"]["task"], answer, sentences)
    if k >= a:
        funnel[lang, "3x mention at or after answer"] += 1
        return None
    funnel[lang, "3 mention before answer"] += 1
    neutral = [i for i in range(a) if i not in touched and not DIGIT.search(norm(sentences[i]))]
    length = lambda i: len(sentences[i].strip())
    before = [i for i in neutral if i < k]
    after = [i for i in neutral if i > k]
    if before:
        j = min(before, key=lambda i: (abs(length(i) - length(k)), k - i))
    elif after:
        j = after[0]
    else:
        funnel[lang, "4x no neutral sentence"] += 1
        return None
    e = max(k, j)
    window = list(range(e + 1))
    deleted_b = [i for i in mentions if i <= e]
    pool = [i for i in neutral if i <= e]
    if len(pool) < len(deleted_b):
        funnel[lang, "4x too few neutral sentences"] += 1
        return None
    deleted_c = []
    for i in deleted_b:
        pick = min((n for n in pool if n not in deleted_c), key=lambda n: (abs(length(n) - length(i)), abs(n - i)))
        deleted_c.append(pick)
    len_b = sum(length(i) for i in deleted_b)
    len_c = sum(length(i) for i in deleted_c)
    if not 1 / LENGTH_RATIO <= len_c / len_b <= LENGTH_RATIO:
        funnel[lang, "4x length mismatch"] += 1
        return None
    keep_b = [i for i in window if i not in deleted_b]
    keep_c = [i for i in window if i not in deleted_c]
    if not keep_b or not keep_c:
        funnel[lang, "4x empty prefix"] += 1
        return None
    funnel[lang, "4 eligible"] += 1
    return {
        "source_id": record["id"],
        "user_message": record["request"]["messages"][0]["content"],
        "settings": {k_: v for k_, v in record["request"].items() if k_ != "messages"},
        "meta": {
            **record["meta"],
            "original_answer": answer,
            "original_correct": correct,
            "distractor_words": sorted(words),
            "distractor_words_strict": sorted(strict),
            "distractor_words_rare": sorted(rare),
            "n_sentences": len(sentences),
            "first_mention": k,
            "answer_sentence": a,
            "window_end": e,
            "deleted_b": deleted_b,
            "deleted_c": deleted_c,
            "deleted_b_text": [sentences[i].strip() for i in deleted_b],
            "deleted_c_text": [sentences[i].strip() for i in deleted_c],
            "deleted_b_chars": len_b,
            "deleted_c_chars": len_c,
            "mention_has_digits": any(DIGIT.search(norm(sentences[i])) for i in deleted_b),
        },
        "prefixes": {"A": assemble(text, sp, window), "B": assemble(text, sp, keep_b), "C": assemble(text, sp, keep_c)},
    }


def requests(trace):
    out = []
    for version, prefix in trace["prefixes"].items():
        out.append({
            "id": f"{trace['source_id']}/{version}",
            "condition": "cot",
            "settings": trace["settings"],
            "messages": [{"role": "user", "content": trace["user_message"]}, {"role": "assistant", "content": prefix}],
            "meta": {**trace["meta"], "source_id": trace["source_id"], "version": version, "cell_rank": trace["cell_rank"]},
        })
    return out


def save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main(args):
    records = [r for run in RUNS for r in json.load(open(ROOT / "experiments" / run / "results.json", encoding="utf-8"))]
    by_id = {r["id"]: r for r in records}
    rates = base_rates(records)
    funnel = Counter()
    cells = defaultdict(list)
    for r in records:
        m = r["meta"]
        if r["condition"] != "cot" or m["insertion"] != "similar_insertion":
            continue
        base = by_id.get(r["id"].replace("similar_insertion", "no_insertion"))
        if base is None:
            continue
        trace = build(r, base, funnel, m["language"], rates)
        if trace:
            cells[m["language"], m["task"], m["difficulty"]].append(trace)

    selected = []
    for cell in sorted(cells):
        traces = sorted(cells[cell], key=lambda t: t["source_id"])
        random.Random(f"{SEED}/{'/'.join(cell)}").shuffle(traces)
        for rank, t in enumerate(traces):
            t["cell_rank"] = rank
        selected += traces[: args.cap]

    pilot = []
    for lang, n in PILOT.items():
        pool = [t for t in selected if t["meta"]["language"] == lang]
        random.Random(f"{SEED}/pilot/{lang}").shuffle(pool)
        pilot += sorted(pool, key=lambda t: t["cell_rank"])[:n]

    out = HERE / "outputs"
    out.mkdir(exist_ok=True)
    save(out / "funnel.json", {f"{lang} | {stage}": n for (lang, stage), n in sorted(funnel.items())})
    save(out / "eligible_counts.json", {"/".join(c): len(v) for c, v in sorted(cells.items())})
    save(out / f"requests_cap{args.cap}.json", [q for t in selected for q in requests(t)])
    if not args.skip_pilot:
        save(out / "requests_pilot.json", [q for t in pilot for q in requests(t)])

    for (lang, stage), n in sorted(funnel.items()):
        print(f"{lang:6} {stage:32} {n}")
    langs = Counter(t["meta"]["language"] for t in selected)
    print(f"cap {args.cap}: {len(selected)} traces {dict(langs)} -> {3 * len(selected)} requests; pilot {len(pilot)} traces -> {3 * len(pilot)} requests")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cap", type=int, default=10)
    ap.add_argument("--skip-pilot", action="store_true")
    main(ap.parse_args())
