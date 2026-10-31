import json
import re
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
CACHE = OUT / "_cache"
DIFFS = ["short", "medium", "long", "very_long", "very_very_long"]
TASKS = ["date_addition", "date_subtraction", "date_duration", "date_recurrence", "day_of_week", "interval_date", "time_addition", "time_subtraction", "time_duration"]

ANS = re.compile(r"(?:Answer|उत्तर(?:\s*है)?|जवाब)\s*\**\s*[:：]\s*(?!Answer|उत्तर|जवाब)(.*)")
LOOSE_ANS = re.compile(r"(?:answer|uttar|jawab|javab|उत्तर|जवाब)\s*(?:hai|है)?\s*\**\s*[:：]\s*(.*)", re.I)
DEVA = re.compile(r"[ऀ-ॣॱ-ॿ]+")
LATIN = re.compile(r"[A-Za-z]+")
DIG = str.maketrans("०१२३४५६७८९", "0123456789")
ISO = re.compile(r"\d{4}-\d{2}-\d{2}")
CLOCK = re.compile(r"\d{1,2}:\d{2}")
NUM = re.compile(r"\d+")
DAYS = {
    0: ["monday", "सोमवार", "somvar", "somwar", "somvaar", "somwaar"],
    1: ["tuesday", "मंगलवार", "mangalvar", "mangalwar", "mangalvaar", "mangalwaar"],
    2: ["wednesday", "बुधवार", "budhvar", "budhwar", "budhvaar", "budhwaar"],
    3: ["thursday", "गुरुवार", "गुरूवार", "guruvar", "guruwar", "guruvaar", "guruwaar", "brihaspativar", "veervar", "virvar"],
    4: ["friday", "शुक्रवार", "shukravar", "shukrawar", "shukravaar", "shukrawaar", "sukravar"],
    5: ["saturday", "शनिवार", "shanivar", "shaniwar", "shanivaar", "shaniwaar"],
    6: ["sunday", "रविवार", "ravivar", "raviwar", "ravivaar", "raviwaar", "itvaar", "itwar"],
}
SCRIPT_DAY = {n: d for d, ns in DAYS.items() for n in ns[:2]} | {"गुरूवार": 3}
ANY_DAY = {n: d for d, ns in DAYS.items() for n in ns}
FN = {
    "listed5": "hai ko mein toh nahi",
    "core": "hai hain ko mein toh nahi nahin ka ki ke se aur bhi",
    "wide": "hai hain ho hoga hogi honge hua hui hue tha thi ko mein me toh nahi nahin ka ki ke se aur bhi ya par pe ab phir agar lekin isliye kyunki yeh ye woh wo kya kitne kitna kaise jo hum humein hame hamein mujhe karna karne karke karenge karte kar raha rahe rahi wala wale wali liye",
}
FN = {k: set(v.split()) for k, v in FN.items()}
VERIF_ORIG = re.compile(r"verif|double.?check|let me check|check (?:this|by|again)|sanity|alternatively|another way|cross.?check|सत्यापित|जांच|जाँच|पुष्टि|दोबारा|वैकल्पिक|दूसरे तरीके", re.I)
VERIF_EXT = re.compile(r"verif|double.?check|cross.?check|re-?check|\bcheck\b|\bconfirm|sanity|alternatively|another way|dobara|doosre tarike|dusre tarike|jaanch|janch|pushti|सत्यापित|जांच|जाँच|पुष्टि|दोबारा|वैकल्पिक|दूसरे तरीके", re.I)
STEP = re.compile(r"(?:^|\n)\s*(?:\*\*)?(?:step|चरण|स्टेप|\d+[.)])", re.I)


def question_key(r):
    m = r["meta"]
    return m["difficulty"], m["task"], m["language"], m["question_id"], m["insertion"]


def answer_of(content):
    found = ANS.findall(content or "")
    if not found:
        return None
    return re.sub(r"\s+से\s+", " to ", found[-1].strip().strip("*`.। ").translate(DIG))


def score(task, ans, gold, table):
    if ans is None:
        return False
    if task == "day_of_week":
        return table.get(ans.casefold()) == SCRIPT_DAY[gold.casefold()]
    return ans == gold


def row(r):
    m = r["meta"]
    content = r["content"] or ""
    hits = list(ANS.finditer(content))
    body = content[: hits[-1].start()] if hits else content
    body_all = ANS.sub("", content)
    ans = answer_of(content)
    deva = len(DEVA.findall(body_all))
    words = [w.lower() for w in LATIN.findall(body_all)]
    c = Counter(words)
    tail = body.rfind(ans) if ans else -1
    first = body.find(ans) if ans else -1
    usage = r.get("usage") or {}
    out = {
        "difficulty": m["difficulty"], "task": m["task"], "language": m["language"], "qnum": int(m["question_id"]), "insertion": m["insertion"],
        "condition": r["condition"], "gold": m["answer"], "answer": ans, "answered": ans is not None,
        "correct": score(m["task"], ans, m["answer"], SCRIPT_DAY),
        "correct_lenient": score(m["task"], ans, m["answer"], ANY_DAY),
        "loose_answer": bool(LOOSE_ANS.search(content)),
        "finish": r["finish_reason"], "tokens": usage.get("completion_tokens"), "time": r.get("time"),
        "n_deva": deva, "n_latin": len(words), "chars": len(body),
        "verif_orig": bool(VERIF_ORIG.search(body)), "verif_ext": bool(VERIF_EXT.search(body)),
        "n_steps": len(STEP.findall(body)),
        "n_dates": len(ISO.findall(body.translate(DIG))), "n_clock": len(CLOCK.findall(body.translate(DIG))), "n_nums": len(NUM.findall(body.translate(DIG))),
        "ans_mentions": body.count(ans) if ans else 0,
        "after_first_ans": (len(body) - first - len(ans)) / len(body) if ans and first >= 0 and body else None,
        "last_ans_pos": tail / len(body) if ans and tail >= 0 and body else None,
    }
    for k, v in FN.items():
        out[f"fn_{k}"] = sum(c[w] for w in v)
    return out


def build():
    CACHE.mkdir(exist_ok=True)
    path = CACHE / "features.pkl"
    if path.exists():
        return pd.read_pickle(path)
    rows, audit = [], {"prompt_tails_differ": 0, "gold_differ": 0, "settings": {}, "missing_in_standard": 0, "per_level": {}}
    for d in DIFFS:
        hing = json.load(open(ROOT / "responses/hinglish" / f"{d}.json", encoding="utf-8"))
        qs = {question_key(r): r["request"]["messages"][0]["content"].split("\n\n", 1)[1] for r in hing}
        golds = {question_key(r): r["meta"]["answer"] for r in hing}
        qnums = {(r["meta"]["task"], r["meta"]["language"], r["meta"]["question_id"]) for r in hing}
        audit["settings"]["hinglish"] = {k: hing[0]["request"][k] for k in ("model", "reasoning_effort", "max_tokens", "temperature", "top_p")}
        rows += [row(r) for r in hing]
        audit["per_level"][d] = {"hinglish": len(hing)}
        del hing
        std = json.load(open(ROOT / "responses/standard" / f"{d}.json", encoding="utf-8"))
        audit["per_level"][d]["standard_all"] = len(std)
        audit["settings"]["standard"] = {k: std[0]["request"][k] for k in ("model", "reasoning_effort", "max_tokens", "temperature", "top_p")}
        kept = 0
        seen = set()
        for r in std:
            m = r["meta"]
            if (m["task"], m["language"], m["question_id"]) not in qnums:
                continue
            kept += 1
            k = question_key(r)
            seen.add(k)
            if r["request"]["messages"][0]["content"].split("\n\n", 1)[1] != qs[k]:
                audit["prompt_tails_differ"] += 1
            if m["answer"] != golds[k]:
                audit["gold_differ"] += 1
            rows.append(row(r))
        audit["per_level"][d]["standard_kept"] = kept
        audit["missing_in_standard"] += len(set(qs) - seen)
        del std
        en = json.load(open(ROOT / "responses/en-cot" / f"{d}.json", encoding="utf-8"))
        audit["per_level"][d]["encot"] = len(en)
        for r in en:
            k = question_key(r)
            if k not in qs or r["request"]["messages"][0]["content"].split("\n\n", 1)[1] != qs[k]:
                audit["prompt_tails_differ"] += 1
            rows.append(row(r))
        audit["settings"]["encot"] = {k: en[0]["request"][k] for k in ("model", "reasoning_effort", "max_tokens", "temperature", "top_p")}
        del en
    df = pd.DataFrame(rows)
    df["qid"] = df.difficulty + "/" + df.task + "/" + df.qnum.astype(str)
    df.to_pickle(path)
    (CACHE / "integrity.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    return df


if __name__ == "__main__":
    print(build().groupby(["condition", "language"]).size())
