import json
from collections import Counter
from pathlib import Path

import build_requests as br

M = br.M
HERE = Path(__file__).resolve().parent
EMPTY = "<think></think>"
DELETION = HERE.parent / "2026-10-27_trace-deletion-selfhost" / "outputs" / "requests_cap1000.json"


def mentions(sentences, strict, rare):
    return [i for i, s in enumerate(sentences) if len(br.content_words(s) & strict) >= br.MIN_SHARED or br.content_words(s) & rare]


def trace(record, base, rates, deletion_ids):
    content = record["content"] or ""
    answer = M.extract_answer(content)
    if answer is None or record.get("finish_reason") == "length" or M.is_correct(record):
        return None
    lang = record["meta"]["language"]
    q, bq = br.question(record), br.question(base)
    words = br.content_words(q[: len(q) - len(bq)]) - br.content_words(bq)
    strict = words - br.CALENDAR
    rare = {w for w in strict if rates[lang].get(w, 0) < br.RARE}
    text = br.body(content)
    sp = br.spans(text)
    sentences = [text[a:b] for a, b in sp]
    found = mentions(sentences, strict, rare)
    if not found:
        return None
    k = found[0]
    a = br.answer_index(record["meta"]["task"], answer, sentences)
    if k >= a:
        return None
    if base["meta"]["answer"] != record["meta"]["answer"]:
        raise ValueError(f"gold differs between {record['id']} and its no_insertion version")
    prefix = lambda n: br.assemble(text, sp, range(n)) if n > 0 else ""
    arms = {"Q": (base, prefix(k)), "P": (record, prefix(k)), "M": (record, prefix(k + 1))}
    if k >= 1:
        arms["P1"] = (record, prefix(k - 1))
    meta = {
        **record["meta"],
        "source_id": record["id"],
        "original_answer": answer,
        "first_mention": k,
        "opening_mention": k == 0,
        "answer_sentence": a,
        "n_sentences": len(sentences),
        "mention_text": sentences[k].strip(),
        "distractor_words_strict": sorted(strict),
        "distractor_words_rare": sorted(rare),
        "in_trace_deletion": record["id"] in deletion_ids,
    }
    out = []
    for arm, (rec, p) in arms.items():
        out.append({
            "id": f"{record['id']}/{arm}",
            "condition": "cot",
            "messages": [{"role": "user", "content": rec["request"]["messages"][0]["content"]}, {"role": "assistant", "content": p if p.strip() else EMPTY}],
            "meta": {**meta, "arm": arm, "question_has_distractor": arm != "Q", "empty_prefix": not p.strip(), "prefix_chars": len(p)},
        })
    return out


def main():
    records = [r for run in br.RUNS for r in json.load(open(br.ROOT / "experiments" / run / "results.json", encoding="utf-8"))]
    by_id = {r["id"]: r for r in records}
    rates = br.base_rates(records)
    deletion_ids = {r["meta"]["source_id"] for r in json.load(open(DELETION, encoding="utf-8"))}
    requests = []
    for r in sorted(records, key=lambda r: r["id"]):
        if r["condition"] != "cot" or r["meta"]["insertion"] != "similar_insertion":
            continue
        base = by_id.get(r["id"].replace("similar_insertion", "no_insertion"))
        if base is not None:
            requests += trace(r, base, rates, deletion_ids) or []
    traces = {q["meta"]["source_id"]: q["meta"] for q in requests}
    summary = {
        "traces": dict(Counter(m["language"] for m in traces.values())),
        "traces_opening_mention": dict(Counter(f"{m['language']} | opening {m['opening_mention']}" for m in traces.values())),
        "traces_in_trace_deletion": sum(m["in_trace_deletion"] for m in traces.values()),
        "requests_per_round": len(requests),
        "requests_by_arm": dict(Counter(q["meta"]["arm"] for q in requests)),
        "empty_prefix_by_arm": dict(Counter(q["meta"]["arm"] for q in requests if q["meta"]["empty_prefix"])),
    }
    out = HERE / "outputs"
    out.mkdir(exist_ok=True)
    br.save(out / "requests_resample.json", requests)
    br.save(out / "build_summary.json", summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
