import json
from pathlib import Path

from analyze import score

HERE = Path(__file__).resolve().parent
LOOP_TAILS = (60, 150, 300)


def loops(text):
    text = text or ""
    return any(text.count(text[-n:]) >= 3 for n in LOOP_TAILS)


report = {}
for run in ("selfhost_G", "selfhost_S"):
    d = HERE / "outputs" / run
    main = json.load(open(d / "results.json", encoding="utf-8"))
    repeat = {r["id"]: r for r in json.load(open(d / "results_repeat.json", encoding="utf-8"))}
    cut = [r for r in main if r.get("finish_reason") == "length"]
    a = {r["id"]: r for r in main if r["id"] in repeat}
    flips = {}
    for lang in ("hi_IN", "en_US"):
        ids = [i for i in a if a[i]["meta"]["language"] == lang]
        first = {i: score(a[i])["correct"] for i in ids}
        second = {i: score(repeat[i])["correct"] for i in ids}
        flips[lang] = {"traces": len(ids), "right_then_wrong": sum(first[i] and not second[i] for i in ids),
                       "wrong_then_right": sum(second[i] and not first[i] for i in ids)}
    report[run] = {"continuations": len(main), "unanswered": sum(not score(r)["answered"] for r in main), "cut_off": len(cut),
                   "cut_off_exact_loop": sum(loops(r["content"]) for r in cut), "A_repeat_flips": flips}
json.dump(report, open(HERE / "outputs" / "noise_and_loops.json", "w", encoding="utf-8"), indent=2)
print(json.dumps(report, indent=2))
