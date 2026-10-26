import argparse
import json
import random
from collections import Counter, defaultdict
from math import comb
from pathlib import Path

from build_requests import HERE, M, MIN_SHARED, content_words, save

SHARED_TASKS = {"date_recurrence", "interval_date", "day_of_week"}
BOOT = 2000
SEED = 26


def score(rec):
    answer = M.extract_answer(rec["content"])
    answered = answer is not None and rec.get("finish_reason") != "length"
    m = rec["meta"]
    return {
        "answered": answered,
        "correct": answered and M.is_correct(rec),
        "same_as_original": answered and answer == m["original_answer"],
        "remention": len(content_words(rec["content"]) & set(m["distractor_words_strict"])) >= MIN_SHARED
        or bool(content_words(rec["content"]) & set(m["distractor_words_rare"])),
        "cutoff": rec.get("finish_reason") == "length",
    }


def mcnemar(b, c):
    n = b + c
    return 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)


def diff(traces):
    return sum(t["B"]["correct"] - t["C"]["correct"] for t in traces) / len(traces) if traces else None


def ci(traces, stat=diff, groups=None):
    if not traces:
        return None
    rng = random.Random(SEED)
    vals = []
    for _ in range(BOOT):
        sample = [rng.choice(traces) for _ in traces]
        v = stat(sample)
        if v is not None:
            vals.append(v)
    vals.sort()
    return [vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1]]


def summary(traces):
    if not traces:
        return {"n": 0}
    n = len(traces)
    b = sum(t["B"]["correct"] and not t["C"]["correct"] for t in traces)
    c = sum(t["C"]["correct"] and not t["B"]["correct"] for t in traces)
    acc = {v: sum(t[v]["correct"] for t in traces) / n for v in "ABC"}
    return {
        "n": n,
        "acc_A": acc["A"],
        "acc_B": acc["B"],
        "acc_C": acc["C"],
        "B_minus_C": acc["B"] - acc["C"],
        "B_minus_C_ci95": ci(traces),
        "only_B_correct": b,
        "only_C_correct": c,
        "mcnemar_p": mcnemar(b, c),
        "A_same_as_original": sum(t["A"]["same_as_original"] for t in traces) / n,
        "remention": {v: sum(t[v]["remention"] for t in traces) / n for v in "ABC"},
        "unanswered_or_cutoff": {v: sum(not t[v]["answered"] for t in traces) for v in "ABC"},
        "deleted_chars_mean": {"B": sum(t["meta"]["deleted_b_chars"] for t in traces) / n, "C": sum(t["meta"]["deleted_c_chars"] for t in traces) / n},
    }


def by(traces, key):
    groups = defaultdict(list)
    for t in traces:
        groups[key(t)].append(t)
    return {str(k): summary(v) for k, v in sorted(groups.items())}


def pct(x):
    return "-" if x is None else f"{100 * x:.1f}"


def table(title, rows):
    lines = [f"### {title}", "", "| group | n | A | B | C | B-C (95% CI) | only B / only C | McNemar p | A = original |", "|---|---|---|---|---|---|---|---|---|"]
    for name, s in rows.items():
        if not s["n"]:
            continue
        lo, hi = s["B_minus_C_ci95"]
        lines.append(f"| {name} | {s['n']} | {pct(s['acc_A'])} | {pct(s['acc_B'])} | {pct(s['acc_C'])} | {pct(s['B_minus_C'])} [{pct(lo)}, {pct(hi)}] | {s['only_B_correct']} / {s['only_C_correct']} | {s['mcnemar_p']:.3g} | {pct(s['A_same_as_original'])} |")
    return "\n".join(lines) + "\n"


def main(args):
    out = Path(args.output)
    results = json.load(open(out / "results.json", encoding="utf-8"))
    grouped = defaultdict(dict)
    for r in results:
        grouped[r["meta"]["source_id"]][r["meta"]["version"]] = r
    traces = []
    for sid, versions in grouped.items():
        if set(versions) >= set("ABC"):
            traces.append({"id": sid, "meta": versions["A"]["meta"], **{v: score(versions[v]) for v in "ABC"}})
    incomplete = len(grouped) - len(traces)
    lang = lambda t: t["meta"]["language"]
    hi = [t for t in traces if lang(t) == "hi_IN"]
    en = [t for t in traces if lang(t) == "en_US"]
    shared_hi = [t for t in hi if t["meta"]["task"] in SHARED_TASKS]
    shared_en = [t for t in en if t["meta"]["task"] in SHARED_TASKS]

    def gap(_):
        sh = [t for t in _ if lang(t) == "hi_IN"]
        se = [t for t in _ if lang(t) == "en_US"]
        return None if not sh or not se else diff(sh) - diff(se)

    report = {
        "traces": len(traces),
        "incomplete_traces": incomplete,
        "by_language": by(traces, lang),
        "hi_by_task": by(hi, lambda t: t["meta"]["task"]),
        "hi_by_difficulty": by(hi, lambda t: t["meta"]["difficulty"]),
        "hi_by_mention_has_digits": by(hi, lambda t: t["meta"]["mention_has_digits"]),
        "shared_tasks": {"hi_IN": summary(shared_hi), "en_US": summary(shared_en),
                         "gap_hi_minus_en": gap(shared_hi + shared_en), "gap_ci95": ci(shared_hi + shared_en, gap)},
        "keys_used": dict(Counter(r.get("key") for r in results)),
    }
    repeat_path = out / "results_repeat.json"
    if repeat_path.exists():
        main_a = {r["id"]: r for r in results if r["meta"]["version"] == "A"}
        repeats = [r for r in json.load(open(repeat_path, encoding="utf-8")) if r["id"] in main_a]
        report["A_repeat"] = {
            "n": len(repeats),
            "identical_text": sum(r["content"] == main_a[r["id"]]["content"] for r in repeats) / len(repeats),
            "same_answer": sum(M.extract_answer(r["content"]) == M.extract_answer(main_a[r["id"]]["content"]) for r in repeats) / len(repeats),
        }
    save(out / "analysis.json", report)
    md = [f"# Trace deletion results\n\n{len(traces)} complete traces ({incomplete} incomplete). Accuracy in % on originally wrong traces.\n",
          table("By language", report["by_language"]),
          table("Hindi by task", report["hi_by_task"]),
          table("Hindi by difficulty", report["hi_by_difficulty"]),
          table("Hindi by whether the deleted mention has digits", report["hi_by_mention_has_digits"]),
          table("Shared tasks (recurrence, interval, day of week)", {k: report["shared_tasks"][k] for k in ("hi_IN", "en_US")})]
    if "A_repeat" in report:
        rp = report["A_repeat"]
        md.append(f"Repeatability: A run twice on {rp['n']} traces gives identical text in {pct(rp['identical_text'])}% and the same answer in {pct(rp['same_answer'])}%.\n")
    g, gci = report["shared_tasks"]["gap_hi_minus_en"], report["shared_tasks"]["gap_ci95"]
    md.append(f"(B-C) Hindi minus English on shared tasks: {pct(g)} pts" + (f" [{pct(gci[0])}, {pct(gci[1])}]" if gci else "") + "\n")
    md.append("### Re-mention of the distractor in the continuation (%)\n\n| language | A | B | C |\n|---|---|---|---|")
    for k, s in report["by_language"].items():
        md.append(f"| {k} | {pct(s['remention']['A'])} | {pct(s['remention']['B'])} | {pct(s['remention']['C'])} |")
    md.append("\n### Unanswered or cut off, deleted length\n\n| language | unanswered A/B/C | mean deleted chars B / C |\n|---|---|---|")
    for k, s in report["by_language"].items():
        u, d = s["unanswered_or_cutoff"], s["deleted_chars_mean"]
        md.append(f"| {k} | {u['A']}/{u['B']}/{u['C']} | {d['B']:.0f} / {d['C']:.0f} |")
    text = "\n".join(md) + "\n"
    (out / "SUMMARY.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default=str(HERE / "outputs"))
    main(ap.parse_args())
