import argparse
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from itertools import takewhile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools" / "temporal-reasoning-dataset" / "src"))

from metrics import extract_answer
from trd.templates.insertions import DISSIMILAR_INSERTIONS, SIMILAR_INSERTIONS

CONFIG = yaml.safe_load(open(ROOT / "config" / "parser.yaml", encoding="utf-8"))
OPS = CONFIG["ops"]
ARITHMETIC = set(CONFIG["notation"])
LETTER = r"\wऀ-ॣ०-ॿ"
NUMERALS = str.maketrans("०१२३४५६७८९٠١٢٣٤٥٦٧٨٩‐‑‒∶", "0123456789" * 2 + "---:")


def fold(text):
    text = unicodedata.normalize("NFD", text.translate(NUMERALS))
    return unicodedata.normalize("NFC", re.sub("[़‌‍]", "", text).replace("ँ", "ं"))


def names(table, lower=False):
    return {fold(form.lower() if lower else form): key for key, forms in table.items() for form in forms}


def word(forms, case=True):
    alternation = "|".join(map(re.escape, sorted(forms, key=len, reverse=True)))
    return rf"(?<![{LETTER}])(?{'-' if case else ''}i:{alternation})(?![{LETTER}])"


WEEKDAYS = names(CONFIG["weekdays"])
MONTHS = names(CONFIG["months"])
NUMBER_WORDS = names(CONFIG["number_words"] | CONFIG["number_scales"], lower=True)
WD, MON = word(WEEKDAYS), word(MONTHS)
NUMWORD = word(NUMBER_WORDS, case=False)
UNIT = re.compile(rf"\s*(?:{'|'.join(map(fold, CONFIG['number_word_units']))})", re.I)

ISO = r"(?<![\d-])\d{4}-\d{1,2}-\d{1,2}(?![\d-])"
DMY = rf"(?<!\d)\d{{1,2}}(?:st|nd|rd|th)?\s+(?:of\s+)?{MON}(?:,?\s+\d{{4}}(?!\d))?"
MDY = rf"{MON}\.?\s+\d{{1,2}}(?:st|nd|rd|th)?(?!\d)(?:,?\s+\d{{4}}(?!\d))?"
DATE = f"(?:{ISO}|{DMY}|{MDY})"
VALUE_PATTERNS = {
    "iso": ISO,
    "time": r"(?<!\d)(?<!\d:)\d{1,2}:\d{2}(?!\d|:\d)(?:\s*[AaPp]\.?[Mm]\.?(?![A-Za-z]))?",
    "dmy": DMY,
    "mdy": MDY,
    "wd": WD,
    "mon": rf"{MON}(?:\s+\d{{4}}(?!\d))?",
    "numw": rf"{NUMWORD}(?:[\s-]+(?:(?:and|और)\s+)?{NUMWORD})*",
    "num": r"(?<![\d.:])(?:-?\d{3,}|(?<!\d{4}-)(?<!\d{4}-\d-)(?<!\d{4}-\d\d-)-?\d{1,2})(?:\.\d+)?(?!\d|st\b|nd\b|rd\b|th\b|वीं|वां|वें|वाँ|वा\b)",
}
KIND = {"iso": "date", "time": "time", "dmy": "date", "mdy": "date", "wd": "weekday", "mon": "month", "numw": "number", "num": "number"}
VALUE = re.compile("|".join(f"(?P<{k}>{p})" for k, p in VALUE_PATTERNS.items()))

OPERATORS = {fold(symbol): op for op, symbols in CONFIG["notation"].items() for symbol in symbols}
OPERATOR = "|".join(rf"(?<![A-Za-z]){s}(?![A-Za-z])" if s.isalpha() else re.escape(s) for s in sorted(OPERATORS, key=len, reverse=True))
OPERAND = "(?>" + "|".join(VALUE_PATTERNS.values()) + ")"
UNIT_WORD = r"(?:\s*(?:days?|hours?|minutes?|mins?|weeks?|दिन|घंटे|घंटा|मिनट|सप्ताह))?"
EXPRESSION = re.compile(rf"(?P<a>{OPERAND}){UNIT_WORD}\s*(?P<op>{OPERATOR})\s*(?=(?P<b>{OPERAND}))")
BRACKET = r"(?:floor\s*)?\((?=(?:[^()]|\([^()]*\))*?[-+−–×*/÷%])(?:[^()]|\([^()]*\))*\)|⌊[^⌊⌋]*⌋|\[[^\[\]]*[-+−–×*/÷%][^\[\]]*\]"
# zero-width, separate passes so nested brackets and the expressions inside them are each still found
BRACKET_EXPRESSIONS = [
    re.compile(rf"(?=(?P<a>{BRACKET}){UNIT_WORD}\s*(?P<op>{OPERATOR})\s*(?P<b>{BRACKET}|{OPERAND}))"),
    re.compile(rf"(?=(?P<a>{OPERAND}){UNIT_WORD}\s*(?P<op>{OPERATOR})\s*(?P<b>{BRACKET}))"),
]


def compile_cues(cues):
    if not cues:
        return None
    patterns = (fold(c).replace("{WD}", WD).replace("{MON}", MON).replace("{DATE}", DATE) for c in cues)
    return re.compile("|".join(f"(?:{p})" for p in patterns), re.I | re.M)


LABELS = {op: {name: compile_cues(label.get("cues")) for name, label in spec.get("labels", {}).items()} for op, spec in OPS.items()}
TRIGGERS = {
    op: compile_cues(spec["cues"] + [c for label in spec.get("labels", {}).values() for c in label.get("cues", [])] if spec.get("labels_trigger") else spec["cues"])
    for op, spec in OPS.items()
}
ANSWER_LINE = re.compile(fold(CONFIG["answer_line"]), re.I | re.M)
SPAN = compile_cues([CONFIG["span"]])
LEAD = re.compile(r"^(?:[\s>#•·]|[*\-+](?=\s))+")
INLINE = re.compile(r"\*\*|__|`|\\[()\[\]]")
NUMBERING = re.compile(r"^(?:(?:step|चरण)\s*\d+\s*[:.)-]|\(?\d{1,2}[.)](?!\d))\s*", re.I)
SENTENCE = re.compile(r"(?<=[^\d\s][.!?])\s+|(?<=।)\s+")
WORD = re.compile(rf"[{LETTER}]{{3,}}")


def words_to_number(run):
    total = current = 0
    for token in re.split(r"[\s-]+", run.lower()):
        value = NUMBER_WORDS.get(token)
        if value is None:
            continue
        if value == 100:
            current = max(current, 1) * 100
        elif value == 1000:
            total, current = total + max(current, 1) * 1000, 0
        else:
            current += value
    return total + current


def normalize(kind, text):
    if kind == "iso":
        year, month, day = map(int, text.split("-"))
        return f"{year:04d}-{month:02d}-{day:02d}"
    if kind in ("dmy", "mdy", "mon"):
        month = MONTHS[re.search(MON, text).group()]
        numbers = re.findall(r"\d+", re.sub(MON, "", text))
        year = next((n for n in numbers if len(n) == 4), None)
        day = next((int(n) for n in numbers if len(n) <= 2), None)
        if kind == "mon":
            return f"{year}-{month:02d}" if year else f"{month:02d}"
        return f"{year}-{month:02d}-{day:02d}" if year else f"{month:02d}-{day:02d}"
    if kind == "time":
        hour, minute = map(int, re.match(r"(\d+):(\d+)", text).groups())
        meridiem = re.search(r"[AaPp](?=\.?[Mm])", text)
        if meridiem and meridiem.group().lower() == "p" and hour < 12:
            hour += 12
        if meridiem and meridiem.group().lower() == "a" and hour == 12:
            hour = 0
        return f"{hour:02d}:{minute:02d}"
    if kind == "wd":
        return WEEKDAYS[text]
    if kind == "numw":
        return str(words_to_number(text))
    return text if "." in text else str(int(text))


def values(segment):
    found = []
    for m in VALUE.finditer(segment):
        if m.lastgroup == "numw" and words_to_number(m.group()) == 1 and not UNIT.match(segment, m.end()):
            continue
        found.append((m.start(), KIND[m.lastgroup], normalize(m.lastgroup, m.group())))
    return found


def first_value(text):
    found = values(text)
    return found[0][2] if found else None


def operand(text):
    return CONFIG["bracket_placeholder"] if text[-1] in ")]⌋" else first_value(text)


def first(vals, *kinds):
    return next((v for _, k, v in vals if k in kinds), None)


def year(vals):
    for _, kind, v in vals:
        if kind == "number" and re.fullmatch(r"\d{4}", v):
            return v
        if kind in ("date", "month") and re.match(r"\d{4}-", v):
            return v[:4]
    return None


def month(vals):
    for _, kind, v in vals:
        if kind == "month":
            return v
        if kind == "date":
            return v[:7] if re.match(r"\d{4}-", v) else v[:2]
    return None


def label(op, segment):
    return next((name for name, rx in LABELS[op].items() if rx and rx.search(segment)), None)


def normalize_answer(raw):
    if not raw:
        return None
    return "..".join(first_value(fold(part)) or part.strip().replace(" ", "_") for part in raw.split(" to "))


def mentions(segment, sentence):
    settings = CONFIG["distractor_overlap"]
    words = set(WORD.findall(fold(sentence).lower()))
    shared = words & set(WORD.findall(segment.lower()))
    return len(words) >= settings["min_words"] and len(shared) >= max(settings["min_words"], settings["min_fraction"] * len(words))


def arguments(op, segment, vals, final):
    if op in ("GOAL", "PLAN", "RULE", "ROLL"):
        raw = [label(op, segment)]
    elif op == "GIVEN":
        raw = [first(vals, "date", "time", "weekday", "number")]
    elif op == "LEAP":
        raw = [year(vals)]
    elif op == "MONTHLEN":
        raw = [month(vals)]
    elif op == "ANCHOR":
        raw = [first(vals, "date"), first(vals, "weekday")]
    elif op == "CONVERT":
        raw = [first(vals, "date", "number", "time"), label(op, segment)]
    elif op in ARITHMETIC:
        # "4 days before X" and "X में से 4" both mean X - 4: a date/time/weekday goes first, then the amount, unless it is an X-to-Y span
        things = [v for _, k, v in vals if k not in ("number", "month")]
        numbers = [v for _, k, v in vals if k == "number"]
        raw = things[:2] if SPAN.search(segment) or not numbers else (things[:1] + numbers)[:2]
    elif op == "STEP":
        raw = [first(vals, "date", "time", "weekday") or first(vals, "number"), label(op, segment)]
    elif op == "ANSWER":
        raw = [final]
    else:
        raw = []
    return list(takewhile(lambda a: a is not None, raw))


def parse_segment(segment, final=None, distractor=None):
    if ANSWER_LINE.search(segment):
        # "उत्तर:" can have its value on the next line, which only the whole-text answer captures
        return [" ".join(["ANSWER", *filter(None, [normalize_answer(extract_answer(segment)) or final])])]
    vals = values(segment)
    found = {op: m.start() for op, rx in TRIGGERS.items() if rx and (m := rx.search(segment))}
    if distractor and mentions(segment, distractor):
        found.setdefault("IGNORE", 0)
    matches = {m.start("op"): m for rx in (*BRACKET_EXPRESSIONS, EXPRESSION) for m in rx.finditer(segment)}
    tokens = [(pos, OPERATORS[m["op"]], list(takewhile(lambda a: a is not None, [operand(m["a"]), operand(m["b"])]))) for pos, m in matches.items()]
    present = {v for _, _, v in vals}
    if "ANSWER" in found and not (final and all(part in present for part in final.split(".."))):
        del found["ANSWER"]
    suppress = bool(tokens) or any(op in found for op in CONFIG["suppress_keyword_arithmetic_with"])
    for op, pos in sorted(found.items(), key=lambda kv: kv[1]):
        if op in ARITHMETIC:
            # prose states one operation per sentence; later arithmetic keywords are usually connectives
            if suppress:
                continue
            suppress = True
        tokens.append((pos, op, arguments(op, segment, vals, final)))
    return [" ".join([op, *args]) for _, op, args in sorted(tokens, key=lambda t: t[0])]


def segments(text):
    for line in fold(text).splitlines():
        line = INLINE.sub("", LEAD.sub("", line)).strip()
        for s in SENTENCE.split(line):
            s = NUMBERING.sub("", s.strip(), count=1)
            if re.search(rf"[{LETTER}]", s):
                yield s


def parse_sentences(text, distractor=None):
    final = normalize_answer(extract_answer(text))
    return [parse_segment(s, final, distractor) for s in segments(text)]


def parse(text, distractor=None):
    if text is None:
        return None
    return [token for sentence in parse_sentences(text, distractor) for token in sentence]


def summarize(counts):
    segments = counts["segments"]
    return {
        "texts": counts["texts"],
        "null": counts["null"],
        "segments": segments,
        "tokens": counts["tokens"],
        "coverage_pct": round(100 * counts["covered"] / segments, 2) if segments else None,
        "unhandled_pct": round(100 * (segments - counts["covered"]) / segments, 2) if segments else None,
    }


def find_distractor(record):
    prompt = record["request"]["messages"][-1]["content"]
    language = record["meta"]["language"]
    sentences = (s for table in (SIMILAR_INSERTIONS, DISSIMILAR_INSERTIONS) for task in table[language].values() for s in task)
    return next((s for s in sentences if s in prompt), None)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    records = json.load(open(args.input, encoding="utf-8"))
    counts = {field: defaultdict(Counter) for field in CONFIG["fields"]}
    for record in records:
        distractor = find_distractor(record)
        for field in CONFIG["fields"]:
            text = record.get(field)
            for c in (counts[field]["all"], counts[field][record["meta"]["language"]]):
                c["null" if text is None else "texts"] += 1
            if text is None:
                record[field] = {"original": None, "parsed": None}
                continue
            sentences = parse_sentences(text, distractor)
            for c in (counts[field]["all"], counts[field][record["meta"]["language"]]):
                c["segments"] += len(sentences)
                c["covered"] += sum(map(bool, sentences))
                c["tokens"] += sum(map(len, sentences))
            record[field] = {"original": text, "parsed": [token for sentence in sentences for token in sentence]}

    stats = {field: {**summarize(c["all"]), "by_language": {lang: summarize(c[lang]) for lang in sorted(c) if lang != "all"}} for field, c in counts.items()}
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    json.dump({"stats": stats, "records": records}, open(args.output, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(json.dumps(stats, indent=2, ensure_ascii=False))
