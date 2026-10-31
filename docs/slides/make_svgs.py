import csv
import json
import textwrap
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "svg"
INK, MUTED, GRID, PALE, WHITE = "#222222", "#595959", "#E3E3E3", "#F4F4F2", "#FFFFFF"
EN, HI, ENCOT, CLP, HING, DIRECT = "#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#8C8C8C"
FONT = "'Liberation Sans', Arial, 'Noto Sans Devanagari', sans-serif"


def rows(name):
    with open(HERE / "data" / name, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def t(x, y, s, size=18, weight="normal", anchor="start", fill=INK, style="normal"):
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" fill="{fill}" font-style="{style}">{escape(str(s))}</text>'


def lines(x, y, items, size=18, gap=None, **k):
    gap = gap or size * 1.3
    return "".join(t(x, y + i * gap, s, size, **k) for i, s in enumerate(items))


def r(x, y, w, h, fill=PALE, stroke="none", rx=4, sw=1.5, dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(w, 0):.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>'


def l(x1, y1, x2, y2, stroke=GRID, sw=1.5, dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{sw}"{d}/>'


def c(x, y, rad=6, fill=INK, stroke=WHITE, sw=2):
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rad}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'


def arrow(x1, y1, x2, y2, stroke=MUTED, sw=2):
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{sw}" marker-end="url(#a)"/>'


def save(name, w, h, *body):
    marker = f'<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="{MUTED}"/></marker></defs>'
    (OUT / f"{name}.svg").write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" font-family="{FONT}">{marker}{"".join(body)}</svg>\n', encoding="utf-8")


def sgn(v):
    return "0" if v == 0 else f"{v:+d}".replace("-", "−")


def axis(x0, x1, y, lo, hi, ticks, top=None, fmt="{}", size=15):
    sx = lambda v: x0 + (v - lo) / (hi - lo) * (x1 - x0)
    out = [l(x0, y, x1, y, MUTED)]
    for v in ticks:
        if top is not None:
            out.append(l(sx(v), top, sx(v), y, GRID, 1))
        out.append(t(sx(v), y + size + 5, (fmt(v) if callable(fmt) else fmt.format(v)), size, anchor="middle", fill=MUTED))
    return "".join(out), sx


def spread(cols, to=1110):
    k = to / max(cx for _, cx, _ in cols)
    return [(n, cx * k, a) for n, cx, a in cols]


def tbl(x, y, cols, data, size=17, rowh=30, fill=None, boldrows=()):
    out = []
    rule = any(name for name, _, _ in cols)
    for name, cx, anc in cols:
        out.append(t(x + cx, y + size, name, size, "bold", anc, MUTED))
    width = max(cx for _, cx, _ in cols) + 8
    y += size + 10
    out.append(l(x, y, x + width, y, MUTED) if rule else "")
    for i, row in enumerate(data):
        if row is None:
            y += rowh * 0.3
            out.append(l(x, y, x + width, y, GRID))
            continue
        for j, (cell, (name, cx, anc)) in enumerate(zip(row, cols)):
            if fill and j and fill(i, j, cell):
                w0 = min(cx - cols[j - 1][1] if j > 1 else cols[j + 1][1] - cx, 110)
                out.append(r(x + cx - w0 + 6, y + 2, w0 - 2, rowh - 3, fill(i, j, cell), rx=2))
            for k, part in enumerate(str(cell).split("\n")):
                out.append(t(x + cx, y + rowh * 0.68 + k * size * 1.2, part, size, "bold" if i in boldrows else "normal", anc))
        y += rowh * max(1, max(1 + str(cc).count("\n") * 0.8 for cc in row))
    return "".join(out)


def tbl_height(data, size, rowh):
    return size + 10 + sum(rowh * 0.3 if row is None else rowh * max(1, max(1 + str(cc).count("\n") * 0.8 for cc in row)) for row in data)


def simple(name, cols, data, size=17, rowh=30, fill=None, boldrows=(), width=1120):
    save(name, width, tbl_height(data, size, rowh) + 8, tbl(0, 0, cols, data, size, rowh, fill, boldrows))


def para(x, y, text, size, chars, gap=None, **k):
    return lines(x, y, textwrap.wrap(text, chars), size, gap or size * 1.3, **k)


def num(v, d=1):
    return f"{float(v):.{d}f}".replace("-", "−")


def pm(v, d=1):
    return f"{float(v):+.{d}f}".replace("-", "−")


def span(lo, hi, d=1):
    return f"[{num(lo, d)}, {num(hi, d)}]"


def blend(a, b_, f):
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b_[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * f):02x}" for x, y in zip(ca, cb))


def formula(x, y, w, h, text, size=23):
    return r(x, y, w, h, PALE) + t(x + w / 2, y + h / 2 + size * 0.35, text, size, anchor="middle")


def project():
    b = [t(0, 24, "Questions, Sarvam-105B", 20, "bold")]
    b.append(r(0, 46, 330, 108, PALE) + t(14, 74, "English", 16, "bold") + t(14, 100, "Today is 2025-08-26, what is", 16) + t(14, 124, "the date going to be in 3 days?", 16))
    b.append(r(0, 166, 330, 108, PALE) + t(14, 194, "Hindi", 16, "bold") + t(14, 222, "आज 2025-08-26 है, 3 दिनों में", 17) + t(14, 246, "तिथि क्या होगी?", 17))
    vary = [("Prompt", "direct or chain-of-thought (CoT)"), ("Reasoning language", "English, Hindi or Hinglish"), ("Distractor", "none, time-related or unrelated")]
    b.append(t(410, 24, "Varied", 20, "bold"))
    for i, (a, z) in enumerate(vary):
        y = 46 + i * 78
        b.append(r(410, y, 370, 70, "#E8F1F7") + t(428, y + 29, a, 18, "bold") + t(428, y + 54, z, 16.5))
    b.append(arrow(334, 160, 406, 160))
    b.append(arrow(784, 160, 856, 160))
    b.append(t(860, 24, "Measured", 20, "bold"))
    for i, (a, z) in enumerate([("Accuracy", "vs gold answers"), ("Reasoning traces", "language, steps, checks"), ("Errors", "error types by condition")]):
        y = 46 + i * 78
        b.append(r(860, y, 260, 70, "#E7F4EF") + t(876, y + 29, a, 18, "bold") + t(876, y + 54, z, 16.5))
    b.append(r(0, 306, 1120, 76, "#FBEEE6") + t(560, 353, "Does CoT help temporal reasoning equally in English and Hindi?", 24, "bold", "middle"))
    save("project", 1120, 386, *b)


def metric_accuracy():
    b = [r(0, 92, 150, 70, PALE, "#CFCFCF") + t(75, 133, "Response", 19, "bold", "middle")]
    b.append(arrow(153, 127, 215, 127))
    b.append(f'<path d="M305 62L395 127L305 192L215 127z" fill="{WHITE}" stroke="{MUTED}" stroke-width="1.5"/>' + t(305, 122, "Answer", 17, "bold", "middle") + t(305, 144, "line?", 17, "bold", "middle"))
    b.append(arrow(370, 100, 450, 50) + t(392, 62, "yes", 16, fill=MUTED) + arrow(370, 154, 450, 204) + t(392, 204, "no", 16, fill=MUTED))
    b.append(r(455, 16, 240, 70, "#E7F4EF") + t(575, 58, "Right or wrong", 18, "bold", "middle"))
    b.append(r(455, 168, 240, 70, "#FBEEE6") + t(575, 198, "Answered: left out", 16.5, "bold", "middle") + t(575, 222, "Strict: wrong", 16.5, "bold", "middle"))
    b.append(t(760, 40, "6,750 questions", 17, "bold") + t(960, 40, "Answered", 16, "bold", "middle", MUTED) + t(1060, 40, "Strict", 16, "bold", "middle", MUTED))
    for i, (a, x, y) in enumerate([("English CoT", "88.5", "85.7"), ("Hindi CoT", "59.4", "59.0"), ("English direct", "59.0", "58.9"), ("Hindi direct", "54.7", "54.7")]):
        yy = 76 + i * 38
        b.append(t(760, yy, a, 17) + t(960, yy, x, 17, anchor="middle") + t(1060, yy, y, 17, anchor="middle"))
    b.append(formula(0, 264, 1120, 62, "answered accuracy = correct / responses with an answer line"))
    b.append(formula(0, 338, 1120, 62, "strict accuracy = correct / all responses"))
    save("metric_accuracy", 1120, 404, *b)


def metric_diffs():
    data = [["CoT gain", "acc(CoT) − acc(direct)", "English: 88.5 − 59.0 = +29.5"], ["Gap", "acc(English) − acc(Hindi)", "CoT: 88.5 − 59.4 = 29.1"], ["Drop", "acc(no distractor) − acc(distractor)", "Hindi CoT, time-related: 2.6"], ["CoT penalty", "drop(CoT) − drop(direct)", "Hindi: 2.6 − 0.4 = 2.2"], None, ["Reasoning part", "acc(en-CoT) − acc(Hindi CoT)", "82.9 − 59.4 = 23.5"], ["Question part", "acc(English CoT) − acc(en-CoT)", "88.9 − 82.9 = 6.0"], ["Reasoning share", "reasoning part / gap", "23.5 / 29.5 = 79.7%"]]
    simple("metric_diffs", [("Metric", 0, "start"), ("Formula, percentage points", 230, "start"), ("Example", 730, "start")], data, 20, 46)


def metric_trace():
    b = [formula(0, 0, 1120, 62, "TLR = Devanagari words / (Devanagari words + Latin words)")]
    b.append(t(0, 104, "Verification", 19, "bold") + t(170, 104, "regex match on checking phrases", 19))
    b.append(t(0, 140, "Mention", 19, "bold") + t(170, 140, "regex match on distractor words; placebo is the same question without it", 19))
    b.append(l(0, 164, 1120, 164))
    b.append(t(0, 198, "Mention odds ratio, per task and level stratum", 19, "bold"))
    x0, y0, w, h = 150, 220, 130, 66
    b.append(t(x0 + w / 2, y0 - 4 + 0, "Correct", 16, "bold", "middle", MUTED) + t(x0 + w * 1.5, y0 - 4, "Wrong", 16, "bold", "middle", MUTED))
    for i, (name, a, z) in enumerate([("Mentions", "a", "b"), ("No mention", "c", "d")]):
        y = y0 + 6 + i * (h + 4)
        b.append(t(x0 - 12, y + 40, name, 16, "bold", "end", MUTED) + r(x0, y, w - 4, h, "#E8F1F7") + t(x0 + w / 2 - 2, y + 42, a, 24, "bold", "middle") + r(x0 + w, y, w - 4, h, PALE) + t(x0 + w * 1.5 - 2, y + 42, z, 24, "bold", "middle"))
    b.append(formula(490, 232, 630, 118, "OR = Σ (a · d / n) / Σ (b · c / n)"))
    b.append(t(490, 386, "OR < 1: traces with a mention are correct less often.", 17, fill=MUTED))
    save("metric_trace", 1120, 400, *b)


def metric_rds():
    b = [t(0, 24, "a, b: op-token lists of length n, m", 20, "bold")]
    b.append(formula(0, 44, 1120, 58, "D(i, 0) = i,   D(0, j) = j", 22))
    b.append(formula(0, 110, 1120, 70, "D(i, j) = min { D(i−1, j) + 1,  D(i, j−1) + 1,  D(i−1, j−1) + cost(aᵢ, bⱼ) }", 22))
    b.append(formula(0, 188, 1120, 70, "RDS = D(n, m) / max(n, m)", 26))
    data = [["same token", "0"], ["one token has a partial date, the other the full date", "0.5"], ["otherwise", "1"]]
    b.append(tbl(0, 272, [("cost(aᵢ, bⱼ)", 0, "start"), ("", 620, "end")], data, 18, 30))
    b.append(t(720, 318, "RDS = 0: same steps, same order", 18) + t(720, 352, "RDS = 1: no step in common", 18))
    save("metric_rds", 1120, 400, *b)


def metric_rq6():
    data = [["Q − P", "distractor in the question", "+5.3"], ["M − P", "written mention", "−3.3"], ["P − P1", "ordinary preceding sentence", "−0.7"], ["(M − P) − (P − P1)", "mention beyond an ordinary sentence", "−4.6"], ["B − C", "deleting mention vs neutral sentence", "+0.0"]]
    a = tbl(0, 0, [("Contrast, accuracy in points", 0, "start"), ("Tests", 340, "start"), ("Hindi", 1000, "end")], data, 20, 44)
    b = formula(0, 280, 1120, 66, "excess fraction = (wrong(P) − wrong(Q)) / wrong(P) = (60.05 − 54.78) / 60.05 = 8.8%")
    save("metric_rq6", 1120, 350, a, b)


def metric_tests():
    b = []
    w = 360
    b.append(r(0, 0, w, 380, PALE) + t(16, 34, "Bootstrap intervals", 20, "bold"))
    b.append(lines(16, 70, ["Resample questions; each", "appears in three distractor", "conditions."], 17.5, 25))
    for i in range(3):
        b.append(r(16 + i * 70, 158, 60, 44, "#E8F1F7") + t(46 + i * 70, 186, f"Q{[3, 1, 3][i]}", 16, anchor="middle"))
    b.append(t(16, 240, "B = 2,000", 22, "bold") + t(16, 276, "95% interval = 2.5th and", 17.5) + t(16, 301, "97.5th percentiles", 17.5))
    x = 380
    b.append(r(x, 0, w, 380, PALE) + t(x + 16, 34, "Exact McNemar", 20, "bold"))
    b.append(lines(x + 16, 70, ["Same question under two", "conditions. Only disagreeing", "pairs count."], 17.5, 25))
    b.append(r(x + 16, 158, 150, 44, "#E8F1F7") + t(x + 91, 186, "b: only A right", 15.5, anchor="middle") + r(x + 176, 158, 150, 44, "#E8F1F7") + t(x + 251, 186, "c: only B right", 15.5, anchor="middle"))
    b.append(t(x + 16, 250, "b ~ Binomial(b + c, 0.5)", 21, "bold"))
    x = 760
    b.append(r(x, 0, w, 380, PALE) + t(x + 16, 34, "Holm correction", 20, "bold"))
    b.append(lines(x + 16, 70, ["Nine tasks tested at once.", "Sort p-values, smallest", "first."], 17.5, 25))
    b.append(t(x + 16, 200, "p(i) × (9 − i + 1)", 24, "bold"))
    b.append(t(x + 16, 240, "Stop at the first p(i) above 0.05.", 17.5))
    save("metric_tests", 1120, 384, *b)


def prior_work():
    cols = ["CoT", "Distractors", "Language of reasoning", "Dates and times", "Hindi"]
    cx = [510, 640, 780, 930, 1060]
    data = [("Wei et al.; Sprague et al.", "CoT helps most on math and symbolic tasks", [1, 0, 0, 0, 0]),
            ("Shi et al. (GSM-IC); Mirzadeh et al.", "Irrelevant text hurts English arithmetic", [.5, 1, 0, 0, 0]),
            ("Shi et al. (MGSM)", "Native vs English CoT, ten other languages", [1, 0, 1, 0, 0]),
            ("Mazzia et al. (TRD)", "Dates and times, ten languages, CoT turned off", [0, 1, 0, 1, 1]),
            ("This work", "All five on the same questions", [1, 1, 1, 1, 1])]
    b = []
    for x, s in zip(cx, cols):
        for i, part in enumerate(s.split(" of ") if " of " in s else [s]):
            b.append(t(x, 22 + i * 21 if " of " in s else 32, part + (" of" if " of " in s and i == 0 else ""), 17, "bold", "middle"))
    b.append(l(0, 56, 1120, 56, MUTED))
    for i, (who, what, vals) in enumerate(data):
        y = 62 + i * 76
        last = i == len(data) - 1
        if last:
            b.append(r(0, y, 1120, 72, "#E8F1F7"))
        b.append(t(12, y + 30, who, 19, "bold"))
        b.append(t(12, y + 54, what, 16, fill=MUTED))
        for x, v in zip(cx, vals):
            if v == 1:
                b.append(c(x, y + 36, 11, EN if last else INK))
            elif v == .5:
                b.append(f'<circle cx="{x}" cy="{y+36}" r="10" fill="none" stroke="{INK}" stroke-width="2"/><path d="M{x} {y+26}A10 10 0 0 0 {x} {y+46}z" fill="{INK}"/>')
            else:
                b.append(f'<circle cx="{x}" cy="{y+36}" r="10" fill="none" stroke="#BDBDBD" stroke-width="1.5"/>')
        if not last:
            b.append(l(0, y + 74, 1120, y + 74))
    b.append(c(16, 462, 7, INK) + t(30, 468, "covered", 15, fill=MUTED))
    b.append(f'<circle cx="116" cy="462" r="7" fill="none" stroke="{INK}" stroke-width="2"/><path d="M116 455A7 7 0 0 0 116 469z" fill="{INK}"/>' + t(130, 468, "used, but not compared on and off under the same distractor", 15, fill=MUTED))
    save("prior_work", 1120, 480, *b)


def dataset():
    b = []
    boxes = [(0, 170, "9", "tasks"), (205, 170, "5", "difficulty levels"), (410, 170, "150", "questions per cell"), (620, 210, "6,750", "questions per language")]
    for x, w, big, small in boxes:
        fill = "#E8F1F7" if big == "6,750" else PALE
        b.append(r(x, 0, w, 112, fill) + t(x + w / 2, 62, big, 46, "bold", "middle") + t(x + w / 2, 94, small, 17, anchor="middle", fill=MUTED))
    b += [t(188, 68, "×", 28, anchor="middle", fill=MUTED), t(393, 68, "×", 28, anchor="middle", fill=MUTED), t(600, 68, "=", 28, anchor="middle", fill=MUTED)]
    b.append(r(860, 0, 260, 112, PALE) + t(990, 62, "13,500", 46, "bold", "middle") + t(990, 94, "gold answers rechecked with datetime", 14.5, anchor="middle", fill=MUTED))
    b.append(t(0, 156, "Grid", 19, "bold"))
    for i, (a, z) in enumerate([("Levels", "short, medium, long, very long, very very long"), ("Languages", "en_US, hi_IN, same question IDs"), ("Input variants", "no distractor, time-related, unrelated"), ("Prompts per condition", "6,750 × 3 variants × 2 languages = 40,500"), ("Direct + CoT", "81,000 responses"), ("Generator", "custom-generator.py, seed 9, up to 10 draws per sample, duplicates discarded")]):
        b.append(t(0, 192 + i * 32, a, 18, "bold") + t(230, 192 + i * 32, z, 18))
    save("dataset", 1120, 356, *b)


def conditions():
    x0, y0, cw, ch = 210, 62, 225, 130
    heads = ["No written reasoning", "English", "Hindi", "Hinglish mix"]
    b = [t(x0 + 2 * cw, 18, "Reasoning language", 18, "bold", "middle", MUTED)]
    for i, s in enumerate(heads):
        b.append(t(x0 + i * cw + cw / 2, 50, s, 18, "bold", "middle"))
    grid = {("English", 0): ("Direct", DIRECT, ""), ("English", 1): ("CoT", EN, ""), ("English", 2): None, ("English", 3): ("Hinglish", HING, "2,250 questions"),
            ("Hindi", 0): ("Direct", DIRECT, ""), ("Hindi", 1): ("en-CoT, CLP", ENCOT, "2,250 questions"), ("Hindi", 2): ("CoT", HI, ""), ("Hindi", 3): ("Hinglish", HING, "2,250 questions")}
    for j, q in enumerate(["English", "Hindi"]):
        y = y0 + j * (ch + 10)
        b.append(t(0, y + ch / 2 - 6, q, 19, "bold") + t(0, y + ch / 2 + 18, "question", 17, fill=MUTED))
        for i in range(4):
            x = x0 + i * cw
            g = grid[(q, i)]
            if g is None:
                b.append(r(x + 5, y, cw - 10, ch, WHITE, "#9A9A9A", dash="6 5") + t(x + cw / 2, y + ch / 2 + 6, "Not run", 20, "bold", "middle", MUTED))
            else:
                b.append(r(x + 5, y, cw - 10, ch, PALE) + r(x + 5, y, 8, ch, g[1], rx=2) + t(x + cw / 2 + 4, y + ch / 2 - 2, g[0], 21, "bold", "middle") + t(x + cw / 2 + 4, y + ch / 2 + 24, g[2] or "6,750 questions", 15.5, anchor="middle", fill=MUTED))
    save("conditions", 1120, y0 + 2 * ch + 14, *b)


def pipeline():
    steps = [("custom-generator.py", "TRD classes, seed 9"), ("dataset/", "level/task_lang.json"), ("sarvam.py, clp.py", "Sarvam API"), ("results.json", "text, usage, finish"), ("metrics", "answered, strict"), ("Accuracy tables", "bootstrap, McNemar")]
    w, gap = 164, 27
    b = []
    def row(items, y, fill=PALE):
        for i, (a, s) in enumerate(items):
            x = i * (w + gap)
            b.append(r(x, y, w, 80, fill, "#CFCFCF") + t(x + w / 2, y + 34, a, 15.5, "bold", "middle") + t(x + w / 2, y + 58, s, 14, anchor="middle", fill=MUTED))
            if i < len(items) - 1:
                b.append(arrow(x + w + 3, y + 40, x + w + gap - 3, y + 40))
    row(steps, 0)
    b2 = [("parser.py", "text to op tokens"), ("ed.py", "Levenshtein, RDS"), ("Logistic model", "disagreement")]
    for i, (a, s) in enumerate(b2):
        x = (3 + i) * (w + gap)
        b.append(r(x, 130, w, 80, PALE, "#CFCFCF") + t(x + w / 2, 164, a, 16.5, "bold", "middle") + t(x + w / 2, 188, s, 14, anchor="middle", fill=MUTED))
        if i < 2:
            b.append(arrow(x + w + 3, 170, x + w + gap - 3, 170))
    b.append(arrow(3 * (w + gap) + w / 2, 83, 3 * (w + gap) + w / 2, 127))
    b3 = [("Wrong traces", "526 Hindi, 37 English"), ("Cut at mention", "prefix variants"), ("vLLM, FP8 build", "self-hosted"), ("Continuations", "13,664 resampled")]
    for i, (a, s) in enumerate(b3):
        x = i * (w + gap) + (w + gap) * 2
        b.append(r(x, 260, w, 80, "#E8F1F7", "#CFCFCF") + t(x + w / 2, 294, a, 16.5, "bold", "middle") + t(x + w / 2, 318, s, 14, anchor="middle", fill=MUTED))
        if i < 3:
            b.append(arrow(x + w + 3, 300, x + w + gap - 3, 300))
    b.append(t(0, 174, "Trace analysis", 17, "bold", fill=MUTED) + t(0, 304, "Interventions", 17, "bold", fill=MUTED))
    save("pipeline", 1120, 344, *b)


def cot_gain():
    ax, sx = axis(150, 900, 300, 40, 100, [40, 50, 60, 70, 80, 90, 100], 20, "{}%")
    b = [ax]
    for lang, y, d, v, col, gain, ci in [("English", 90, 59.0, 88.5, EN, "+29.5", "[28.5, 30.6], strict +26.8"), ("Hindi", 210, 54.7, 59.4, HI, "+4.7", "[3.6, 5.7], strict +4.2")]:
        b.append(t(0, y + 6, lang, 22, "bold"))
        b.append(l(sx(d), y, sx(v), y, col, 5))
        b.append(c(sx(d), y, 9, WHITE, col, 3) + c(sx(v), y, 10, col))
        b.append(t(sx(d), y - 18, f"{d}", 17, anchor="middle") + t(sx(v), y - 18, f"{v}", 17, anchor="middle"))
        b.append(t(920, y - 4, gain, 26, "bold") + t(920, y + 22, ci, 15.5, fill=MUTED))
    b.append(c(155, 350, 7, WHITE, MUTED, 2.5) + t(170, 356, "Direct", 16, fill=MUTED) + c(255, 350, 8, MUTED) + t(270, 356, "CoT", 16, fill=MUTED))
    cols = [("", 0, "start"), ("None", 300, "end"), ("Time-related", 460, "end"), ("Unrelated", 610, "end")]
    rowsd = [["English gain", "+28.8", "+29.1", "+30.7"], ["Hindi gain", "+5.6", "+3.4", "+5.0"], ["Gap, CoT", "+28.0", "+29.7", "+29.7"], ["Gap, direct", "+4.8", "+4.0", "+3.9"]]
    b.append(tbl(0, 394, cols, rowsd, 17, 28))
    b.append(t(700, 424, "Gap", 18, "bold") + t(760, 424, "direct 4.3, CoT 29.1 (strict 26.7)", 18))
    b.append(t(700, 458, "Pooled over 3 distractor conditions", 16, fill=MUTED))
    save("cot_gain", 1120, 540, *b)


TASK = {"date_addition": "Date addition", "date_subtraction": "Date subtraction", "date_duration": "Date duration", "date_recurrence": "Date recurrence", "day_of_week": "Day of week", "interval_date": "Interval date", "time_addition": "Time addition", "time_subtraction": "Time subtraction", "time_duration": "Time duration"}
TABLE2 = {"date_addition": (85.6, 98.0, 82.8, 85.1), "date_subtraction": (86.0, 95.2, 84.8, 66.0), "date_duration": (84.0, 99.3, 78.9, 88.2), "date_recurrence": (22.1, 90.3, 2.8, 20.1), "day_of_week": (14.9, 69.5, 15.2, 21.0), "interval_date": (43.2, 50.7, 46.8, 23.9), "time_addition": (70.5, 95.9, 75.6, 73.5), "time_subtraction": (64.7, 97.7, 64.9, 75.2), "time_duration": (65.7, 98.9, 44.7, 80.1)}


def hindi_tasks():
    b = []
    panels = [("English questions", 180, 500, EN, 0), ("Hindi questions", 680, 1000, HI, 2)]
    h = 36
    for title, x0, x1, col, k in panels:
        ax, sx = axis(x0, x1, 40 + 9 * h, 0, 100, [0, 25, 50, 75, 100], 30, "{}")
        b.append(t(x0, 18, title, 19, "bold") + ax)
        for i, (task, v) in enumerate(TABLE2.items()):
            y = 50 + i * h
            d, cc = v[k], v[k + 1]
            worse = cc < d - 15
            if worse:
                b.append(r(x0 - 8, y - 15, x1 - x0 + 16 + 110, 30, "#FBEEE6"))
            b.append(l(sx(d), y, sx(cc), y, col, 3.5))
            b.append(c(sx(d), y, 6.5, WHITE, col, 2.5) + c(sx(cc), y, 7, col))
            b.append(t(x1 + 16, y + 5, f"{d} → {cc}", 15.5, "bold" if worse else "normal"))
    for i, task in enumerate(TABLE2):
        b.append(t(0, 55 + i * 36, TASK[task], 17))
    b.append(c(6, 40 + 9 * h + 30, 6.5, WHITE, MUTED, 2.5) + t(20, 40 + 9 * h + 36, "Direct", 15.5, fill=MUTED) + c(92, 40 + 9 * h + 30, 7, MUTED) + t(106, 40 + 9 * h + 36, "CoT", 15.5, fill=MUTED))
    save("hindi_tasks", 1120, 40 + 9 * h + 46, *b)


def by_level():
    d = rows("figC1_accuracy_by_level.csv")
    lv = ["short", "medium", "long", "very_long", "very_very_long"]
    names = ["Short", "Medium", "Long", "Very long", "Very very long"]
    ax, sx = axis(70, 900, 410, 0, 4, [], None)
    b = [ax]
    sy = lambda v: 410 - (v - 20) / 80 * 372
    for v in range(20, 101, 20):
        b.append(l(70, sy(v), 900, sy(v), GRID, 1) + t(58, sy(v) + 5, v, 15, anchor="end", fill=MUTED))
    b.append(t(0, 16, "Accuracy (%)", 15, fill=MUTED))
    for i, n in enumerate(names):
        b.append(t(sx(i), 436, n, 16, anchor="middle"))
    series = [("English CoT", EN, "", 0), ("Hindi en-CoT", ENCOT, "", 0), ("Hindi CLP", CLP, "7 4", 0), ("Hindi CoT", HI, "", 0), ("Hindi direct", DIRECT, "3 4", 0)]
    label = {"English CoT": "English CoT", "Hindi en-CoT": "en-CoT", "Hindi CLP": "CLP", "Hindi CoT": "Hindi CoT", "Hindi direct": "Hindi direct"}
    for name, col, dash, _ in series:
        pts = [next(x for x in d if x["level"] == k and x["condition"] == name) for k in lv]
        for i, p in enumerate(pts):
            b.append(l(sx(i), sy(float(p["lo"])), sx(i), sy(float(p["hi"])), col, 1.5))
        for i in range(4):
            b.append(l(sx(i), sy(float(pts[i]["accuracy"])), sx(i + 1), sy(float(pts[i + 1]["accuracy"])), col, 2.5, dash))
        for i, p in enumerate(pts):
            b.append(c(sx(i), sy(float(p["accuracy"])), 5.5, col))
        last = float(pts[-1]["accuracy"])
        b.append(t(914, sy(last) + 5, f"{label[name]} {last:.1f}", 16))
    save("by_level", 1100, 446, *b)


def distractor_penalty():
    b = [t(0, 26, "Time-related distractor, drop in Hindi accuracy", 19, "bold")]
    sb = lambda v: v / 3 * 330
    for i, (a, v, col) in enumerate([("Direct", 0.4, DIRECT), ("CoT", 2.6, HI)]):
        y = 58 + i * 64
        b.append(t(0, y + 28, a, 18) + r(100, y, sb(v), 42, col) + t(108 + sb(v), y + 29, f"{v}" + (" [1.3, 3.8]" if v > 1 else ""), 19, "bold"))
    b.append(t(0, 222, "CoT penalty: 2.2", 22, "bold"))
    ax, sx = axis(620, 1100, 200, -1, 5, [-1, 0, 1, 2, 3, 4, 5], 30, sgn)
    b += [t(620, 26, "CoT penalty, 95% interval", 19, "bold"), ax, l(sx(0), 34, sx(0), 200, INK, 1.5, "4 4")]
    for i, (a, m, lo, hi) in enumerate([("Questions as sample", 2.2, "0.6", 3.8), ("45 task-sentence units", 2.3, "−0.1", 4.6)]):
        y = 76 + i * 72
        lv = float(lo.replace("−", "-"))
        b.append(t(sx(0) + 10, y - 14, f"{a}: +{m} [{lo}, {hi}]", 16.5) + l(sx(lv), y + 6, sx(hi), y + 6, HI, 3) + c(sx(m), y + 6, 7, HI))
    b.append(l(0, 256, 1120, 256))
    b.append(t(0, 292, "Leave one sentence out", 18, "bold") + t(290, 292, "penalty 1.8 to 2.6", 18))
    b.append(t(0, 326, "Hindi minus English penalty", 18, "bold") + t(290, 326, "+2.6 [0.4, 4.7] answered, +1.4 [−0.7, 3.5] strict", 18))
    b.append(t(0, 360, "English CoT drop", 18, "bold") + t(290, 360, "0.9 answered, 2.2 [1.3, 3.2] strict", 18))
    b.append(t(0, 394, "Mid-report claim", 18, "bold") + t(290, 394, "withdrawn (fragility only in Hindi)", 18))
    save("distractor_penalty", 1120, 404, *b)


def january():
    b = [r(0, 0, 1120, 58, PALE), t(20, 38, '"The last time I had a weekly commitment was in January."', 24, "bold")]
    x0, x1 = 180, 470
    sy = lambda v: 390 - v / 100 * 280
    b.append(t(0, 92, "Strict accuracy, 134 date recurrence questions", 18, "bold"))
    for v in [0, 25, 50, 75, 100]:
        b.append(l(x0 - 20, sy(v), x1 + 20, sy(v), GRID, 1) + t(x0 - 28, sy(v) + 5, v, 15, anchor="end", fill=MUTED))
    b.append(t(x0, 416, "Without it", 16, anchor="middle") + t(x1, 416, "With it", 16, anchor="middle"))
    for name, a, z, col in [("English CoT", 88.8, 19.4, EN), ("Hindi CoT", 26.9, 2.2, HI)]:
        b.append(l(x0, sy(a), x1, sy(z), col, 3) + c(x0, sy(a), 7, col) + c(x1, sy(z), 7, col))
        b.append(t(x0 + 12, sy(a) - 10, f"{name} {a}", 16.5, "bold"))
        b.append(t(x1 + 28, sy(z) + 5, f"{z}", 17, "bold"))
    b.append(t(590, 92, "English CoT cut-offs", 18, "bold") + t(590, 136, "4 → 92", 36, "bold") + t(730, 136, "of 134", 18))
    b.append(t(590, 184, "Hindi CoT cut-offs", 18, "bold") + t(790, 184, "0", 26, "bold"))
    b.append(l(590, 206, 1120, 206))
    for i, s in enumerate(["Largest of 90 task-sentence units, found post hoc", "None of the 92 cut-offs is a verbatim loop", "Hindi recurrence penalty without it: +4.5 → +0.3 [−4.6, 4.9]", "English recurrence penalty without it: stays +8.5", "January competes with the question's start date"]):
        b.append(t(590, 240 + i * 34, s, 17))
    save("january", 1120, 426, *b)


def decomposition():
    ax, sx = axis(20, 1100, 248, 50, 100, [50, 60, 70, 80, 90, 100], 150, "{}%")
    b = [ax]
    y = 190
    b.append(r(sx(59.4), y, sx(82.9) - sx(59.4) - 2, 44, ENCOT) + r(sx(82.9), y, sx(88.9) - sx(82.9), 44, EN))
    b.append(t((sx(59.4) + sx(82.9)) / 2, y + 30, "+23.5 reasoning language", 20, "bold", "middle", WHITE))
    b.append(t(sx(88.9) + 10, y + 18, "+6.0", 17, "bold") + t(sx(88.9) + 10, y + 40, "question language", 16))
    cards = [(59.4, "Hindi question", "Hindi reasoning", "Hindi CoT", HI), (82.9, "Hindi question", "English reasoning", "en-CoT", ENCOT), (88.9, "English question", "English reasoning", "English CoT", EN)]
    for i, (v, q, rr, n, col) in enumerate(cards):
        x = i * 380
        b.append(r(x, 0, 360, 124, PALE) + r(x, 0, 8, 124, col, rx=2))
        b.append(t(x + 26, 74, f"{v}%", 40, "bold") + t(x + 190, 40, n, 19, "bold") + t(x + 190, 68, q, 16, fill=MUTED) + t(x + 190, 92, rr, 16, fill=MUTED))
    cols = [("", 0, "start"), ("Points", 330, "end"), ("95% interval", 520, "end")]
    b.append(tbl(0, 288, cols, [["Total gap", "29.5", "[28.1, 30.9]"], ["Reasoning part", "23.5", "[22.1, 24.9]"], ["Question part", "6.0", "[5.0, 7.1]"], ["Reasoning share", "79.7%", "[76.4, 82.9]"]], 18, 30))
    b.append(t(620, 318, "Strict reasoning share", 18, "bold") + t(860, 318, "80.7%", 18))
    b.append(t(620, 348, "Direct gap, same questions", 18, "bold") + t(860, 348, "4.5", 18))
    b.append(t(620, 378, "English Q + Hindi reasoning", 18, "bold") + t(880, 378, "not run", 18))
    save("decomposition", 1120, 432, *b)


def breakdown():
    d = {x["cut"]: x for x in rows("new_decomposition.csv") if x["conv"] == "answered"}
    groups = [[("pooled", "All questions")], [("no_insertion", "No distractor"), ("similar_insertion", "Time-related"), ("dissimilar_insertion", "Unrelated")], [("short", "Short"), ("medium", "Medium"), ("long", "Long"), ("very_long", "Very long"), ("very_very_long", "Very very long")], [(k, TASK[k]) for k in TASK]]
    ax, sx = axis(180, 1000, 470, 0, 75, [0, 15, 30, 45, 60, 75], 28)
    b = [ax, t(1000, 508, "English-Hindi CoT gap (points)", 15, anchor="end", fill=MUTED)]
    b.append(r(180, 0, 16, 14, ENCOT, rx=2) + t(202, 13, "Reasoning language (en-CoT minus Hindi CoT)", 15.5) + r(560, 0, 16, 14, EN, rx=2) + t(582, 13, "Question language (English CoT minus en-CoT)", 15.5))
    y = 32
    for g in groups:
        for key, name in g:
            q = float(d[key]["question part (En CoT - en-CoT)"])
            rr = float(d[key]["reasoning part (en-CoT - Hi CoT)"])
            b.append(t(170, y + 13, name, 15.5, anchor="end"))
            b.append(r(sx(0), y, sx(rr) - sx(0) - 1, 17, ENCOT, rx=2) + r(sx(rr) + 1, y, sx(rr + q) - sx(rr) - 1, 17, EN, rx=2))
            b.append(t(sx(rr + q) + 8, y + 13, f"{rr:.1f} + {q:.1f}", 14, fill=MUTED))
            y += 21.5
        y += 11
    save("breakdown", 1120, 512, *b)


def distance():
    d = {x["kind"]: x for x in rows("distance.csv")}
    items = [("E_self", "Distractor added", "English CoT, with vs without", False), ("E_M", "Question language", "English CoT vs en-CoT", True), ("M_H", "Reasoning language", "en-CoT vs Hindi CoT", True), ("E_H", "Question and reasoning language", "English CoT vs Hindi CoT", True), ("E_H_otherq", "Different questions", "English CoT vs Hindi CoT", False)]
    ax, sx = axis(300, 700, 374, 0.7, 1.0, [0.7, 0.8, 0.9, 1.0], 30, "{:.1f}")
    b = [ax, t(0, 18, "Trace pair", 17, "bold"), t(700, 18, "Mean RDS", 16, "bold", "end", MUTED)]
    for i, (k, a, s, solid) in enumerate(items):
        y = 62 + i * 66
        m, lo, hi = float(d[k]["full"]), float(d[k]["full_lo"]), float(d[k]["full_hi"])
        b.append(t(0, y, a, 16.5, "bold") + t(0, y + 22, s, 15, fill=MUTED))
        b.append(l(sx(lo), y + 6, sx(hi), y + 6, EN if solid else MUTED, 2.5))
        b.append(c(sx(m), y + 6, 8, EN) if solid else c(sx(m), y + 6, 7, WHITE, MUTED, 2.5))
        b.append(t(sx(m) + 16 if m < 0.9 else sx(m) - 16, y + 12, f"{m:.3f}", 16.5, anchor="start" if m < 0.9 else "end"))
    b.append(t(300, 412, "0 = same steps, 1 = no steps shared. 2,250 questions.", 15, fill=MUTED))
    b.append(t(770, 18, "Traces with a verification phrase", 17, "bold"))
    for i, (a, v, col) in enumerate([("English CoT", 86.1, EN), ("en-CoT", 74.2, ENCOT), ("Hindi CoT", 1.3, HI)]):
        y = 50 + i * 68
        b.append(t(770, y + 8, a, 16.5) + r(770, y + 18, v / 100 * 260, 24, col) + t(778 + v / 100 * 260, y + 37, f"{v}%", 17, "bold"))
    b.append(l(770, 262, 1120, 262))
    b.append(t(770, 296, "Share of en-CoT gain from verification", 16.5, "bold") + t(770, 322, "1.0% [−6.3, 9.0], observational", 16.5))
    save("distance", 1120, 420, *b)


def hinglish():
    d = rows("fig1_accuracy_by_task.csv")
    b = []
    panels = [("en_US", "English questions: −18.0 [−19.2, −16.8]", 170, 500, EN), ("hi_IN", "Hindi questions: −0.0 [−1.3, 1.2]", 590, 920, HI)]
    h = 36
    for lang, title, x0, x1, col in panels:
        ax, sx = axis(x0, x1, 34 + 10 * h, 0, 100, [0, 25, 50, 75, 100], 24)
        b.append(t(x0, 16, title, 17, "bold") + ax)
        for i, task in enumerate(TASK):
            row = next(x for x in d if x["language"] == lang and x["task"] == task)
            a, z = float(row["std"]), float(row["hing"])
            y = 46 + i * h
            b.append(l(sx(a), y, sx(z), y, col, 3) + c(sx(a), y, 6.5, col) + c(sx(z), y, 6.5, HING))
            b.append(t(x1 + 12, y + 5, f"{a + 1e-9:.1f} → {z + 1e-9:.1f}", 14))
        a, z = (88.9, 70.9) if lang == "en_US" else (59.4, 59.4)
        y = 46 + 9 * h
        b.append(l(x0, y - h / 2, x1, y - h / 2, GRID, 1) + l(sx(a), y, sx(z), y, col, 3) + c(sx(a), y, 7.5, col) + c(sx(z), y, 7.5, HING) + t(x1 + 12, y + 5, f"{a} → {z}", 14, "bold"))
    for i, task in enumerate(list(TASK.values()) + ["All tasks"]):
        b.append(t(0, 51 + i * h, task, 16, "bold" if task == "All tasks" else "normal"))
    b.append(c(176, 34 + 10 * h + 36, 6.5, EN) + c(194, 34 + 10 * h + 36, 6.5, HI) + t(206, 34 + 10 * h + 42, "Standard CoT", 15.5, fill=MUTED) + c(326, 34 + 10 * h + 36, 6.5, HING) + t(340, 34 + 10 * h + 42, "Hinglish prompt. Answered accuracy (%), strict English loss 15.7", 15.5, fill=MUTED))
    save("hinglish", 1120, 34 + 10 * h + 56, *b)


def error_patterns():
    rowsd = [("Date subtraction", "answer on or after today", [("Hindi CoT", 13, 738), ("English CoT", 0, 129), ("en-CoT", 0, 45)], 0),
             ("Interval date", "span not seven days long", [("Hindi CoT", 21, 1720), ("English CoT", 6, 1046), ("en-CoT", 6, 410)], 0),
             ("Date recurrence", "one interval short", [("Hindi CoT", 35, 1758), ("English CoT", 21, 234)], 1),
             ("Day of week", "exactly one day late", [("Hindi CoT", 31, 1696), ("English CoT", 58, 584), ("en-CoT", 50, 313)], 1)]
    col = {"Hindi CoT": HI, "English CoT": EN, "en-CoT": ENCOT}
    sb = lambda v: v * 5.4
    b = [t(0, 16, "Mainly when reasoning in Hindi", 18, "bold")]
    y = 36
    for i, (task, what, vals, grp) in enumerate(rowsd):
        if i == 2:
            y += 14
            b.append(l(0, y, 1120, y) + t(0, y + 28, "In either language", 18, "bold"))
            y += 44
        b.append(t(0, y + 22, task, 18, "bold") + t(0, y + 46, what, 16, fill=MUTED))
        for j, (name, v, n) in enumerate(vals):
            yy = y + j * 26
            b.append(t(390, yy + 18, name, 15.5, anchor="end") + r(400, yy + 2, max(sb(v), 2), 20, col[name], rx=3))
            b.append(t(408 + sb(v), yy + 18, f"{v}% of {n:,}", 15.5, "bold" if name == "Hindi CoT" and not grp else "normal"))
        y += 26 * max(len(vals), 2) + 14
    save("error_patterns", 1120, y + 2, *b)


def recurrence_k():
    d = rows("new_recurrence_error_types_by_k.csv")
    sets = [("En CoT", "English CoT"), ("Hi CoT", "Hindi CoT"), ("CLP", "CLP"), ("en-CoT", "en-CoT")]
    ks = ["1", "2", "3", "4", "5-8", "9-16", "17-32"]
    parts = [("correct%", "#D9D9D9", "Correct"), ("backwards%", HI, "Backwards"), ("k-1 steps%", EN, "One step short"), ("today%", CLP, "Today"), ("other%", "#6F6F6F", "Other")]
    b = []
    x = 0
    for j, (_, name, col) in enumerate([(0, p[2], p[1]) for p in parts]):
        b.append(r(44 + x, 0, 16, 14, col, rx=2) + t(66 + x, 13, name, 15))
        x += 16 + 8 + len(name) * 8.2 + 24
    pw, gap, x0 = 158, 16, 44
    for i, (key, name) in enumerate(sets):
        px = x0 + i * (pw + gap)
        b.append(t(px + pw / 2, 46, name, 16, "bold", "middle"))
        bw = pw / 7
        for n, k in enumerate(ks):
            row = next(x for x in d if x["set"] == key and x["k"] == k)
            y = 56
            for field, col, _ in reversed(parts):
                v = float(row[field]) * 3.1
                if v > 0:
                    b.append(f'<rect x="{px + n * bw + 1:.1f}" y="{y:.1f}" width="{bw - 2:.1f}" height="{v:.1f}" fill="{col}"/>')
                y += v
            tx, ty = px + n * bw + bw / 2 + 4, 56 + 310 + 12
            b.append(f'<text x="{tx:.1f}" y="{ty}" font-size="12.5" text-anchor="end" fill="{MUTED}" transform="rotate(-55 {tx:.1f} {ty})">{k}</text>')
    for v in [0, 50, 100]:
        y = 56 + 310 - v * 3.1
        b.append(t(36, y + 5, v, 14, anchor="end", fill=MUTED))
    b.append(t(x0 + 2 * (pw + gap) - gap / 2, 426, "Occurrence number k. Share of answers (%), 2,250 questions.", 15, anchor="middle", fill=MUTED))
    x = 770
    b.append(t(x, 28, "Backward answers at k = 1", 18, "bold"))
    for i, (a, v, col) in enumerate([("English CoT", 3.5, EN), ("en-CoT", 67.1, ENCOT), ("Hindi CoT", 67.8, HI), ("CLP", 69.0, CLP)]):
        y = 44 + i * 34
        b.append(t(x, y + 19, a, 16) + r(x + 106, y + 2, v * 2.6, 24, col) + t(x + 112 + v * 2.6, y + 20, f"{v}%", 15.5, "bold"))
    b.append(l(x, 190, 1120, 190))
    b.append(lines(x, 220, ["आज को छोड़कर, 1वीं आवृत्ति", "\"excluding today, the 1st occurrence\"", "en-CoT: \"this suggests we need to find", "what comes before\""], 17, 25))
    b.append(l(x, 318, 1120, 318))
    b.append(lines(x, 346, ["1वीं is non-standard. No corrected-template", "rerun. k = 2 to 4: 2 of 229 en-CoT backward.", "\"0 hours\" wrong: en-CoT 19%, others 5%."], 15.5, 23))
    save("recurrence_k", 1120, 434, *b)


def rds_example():
    en = ["GOAL DATE", "GIVEN 2025-09-11", "ADD 2025-09-12 1", "ADD 2025-09-13", "ANSWER 2025-09-13", "SPITANSWER 2025-09-13"]
    hi = ["-", "GIVEN 2025-09-11", "-", "ADD 2025-09-13 2", "ANSWER 2025-09-13", "SPITANSWER 2025-09-13"]
    b = [t(0, 18, "Both correct: \"Today is 2025-09-11, what is the date going to be in 2 days?\"", 18, "bold")]
    w, gap, x0 = 167, 6, 88
    for lab, y in [("English", 42), ("Hindi", 112)]:
        b.append(t(0, y + 28, lab, 18, "bold"))
    for i, (a, z) in enumerate(zip(en, hi)):
        x = x0 + i * (w + gap)
        same = a == z
        fill = "#E7F4EF" if same else "#FBEEE6"
        for s, y in [(a, 42), (z, 112)]:
            b.append(r(x, y, w, 44, fill if s != "-" else WHITE, "#D1D1D1" if s == "-" else "none", dash="4 4" if s == "-" else ""))
            b.append(f'<text x="{x + w / 2:.1f}" y="{y + 28}" font-size="12.5" font-family="\'Liberation Mono\', monospace" text-anchor="middle" fill="{INK}">{escape(s if s != "-" else "gap")}</text>')
        b.append(t(x + w / 2, 180, "match" if same else "edit", 15, anchor="middle", fill=MUTED))
    b.append(t(0, 224, "RDS = edits / longer length = 3 / 6 = 0.50", 22, "bold"))
    b.append(t(620, 214, "0 = same steps in the same order", 17) + t(620, 238, "1 = no steps in common", 17))
    b.append(l(0, 256, 1120, 256))
    for i, (a, z) in enumerate([("Answer tokens count", "same pair, another final answer: 5 / 6 = 0.83"), ("On real pairs", "new Hindi answers on 11,309 both-correct pairs: +0.082, 68% of the 0.120 gap")]):
        b.append(t(0, 292 + i * 34, a, 18, "bold") + t(220, 292 + i * 34, z, 18))
    save("rds_example", 1120, 340, *b)


def lr_setup():
    b = [t(0, 22, "20,662 English-Hindi trace pairs, 19,471 with thinking off", 20, "bold"), t(1120, 22, "Hindi only 516, both wrong 1,711", 16, anchor="end", fill=MUTED)]
    tot = 20662
    x = 0
    for name, n, col in [("Both right", 12468, "#CFCFCF"), ("English only", 5967, EN), ("Hindi only", 516, HI), ("Both wrong", 1711, "#8C8C8C")]:
        w = n / tot * 1120
        b.append(r(x, 40, w - 2, 44, col, rx=3))
        if w > 150:
            b.append(t(x + 12, 68, f"{name} {n:,}", 17, "bold", fill=WHITE if col != "#CFCFCF" else INK))
        x += w
    xh = 12468 / tot * 1120
    xe = (12468 + 5967 + 516) / tot * 1120
    b.append(l(xh, 92, xh, 104, MUTED) + l(xh, 104, xe, 104, MUTED) + l(xe, 92, xe, 104, MUTED))
    b.append(t(xe, 128, "disagree = 1 when exactly one language is right", 17, anchor="end"))
    b.append(formula(0, 150, 1120, 66, "logit P(disagree) = β₀ + β₁ · RDS + task + difficulty + distractor + thinking mode"))
    b.append(formula(0, 228, 1120, 66, "second model adds β₂ · |len en − len hi| / max(len en, len hi)", 21))
    b.append(formula(0, 306, 1120, 66, "OR per 0.1 RDS = exp(0.1 · β₁) = exp(0.1 · 15.94) = 4.92"))
    b.append(t(0, 400, "Standard errors clustered by question. 21,600 pairs loaded, 938 dropped (answer unparsed), 6,739 questions.", 16.5, fill=MUTED))
    save("lr_setup", 1120, 408, *b)


def lr_result():
    d = rows("fig2_rate_by_rds_bin.csv")
    ax, sx = axis(60, 600, 360, 0.3, 1.0, [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0], None, "{:.1f}")
    sy = lambda v: 360 - v / 0.6 * 320
    b = [ax]
    for v in [0, .2, .4, .6]:
        b.append(l(60, sy(v), 600, sy(v), GRID, 1) + t(50, sy(v) + 5, f"{v:.1f}", 15, anchor="end", fill=MUTED))
    b.append(t(0, 16, "Share of pairs that disagree", 15.5, fill=MUTED) + t(330, 402, "RDS (bins of width 0.1, midpoints)", 15, anchor="middle", fill=MUTED))
    for mode, col, name, dash in [("off", EN, "Thinking off", ""), ("on", HI, "Thinking on", "6 4")]:
        pts = [x for x in d if x["mode"] == mode and x["shown_in_report"] == "True"]
        xy = [(float(p["mid"]), float(p["rate"]), float(p["wilson_lo"]), float(p["wilson_hi"])) for p in pts]
        for m, v, lo, hi in xy:
            b.append(l(sx(m), sy(lo), sx(m), sy(hi), col, 1.5))
        for a, z in zip(xy, xy[1:]):
            b.append(l(sx(a[0]), sy(a[1]), sx(z[0]), sy(z[1]), col, 2.5, dash))
        for m, v, lo, hi in xy:
            b.append(c(sx(m), sy(v), 5.5, col))
        m, v = xy[-1][:2]
        b.append(t(sx(m) - 12, sy(v) - 2, name, 16, anchor="end") if mode == "off" else t(sx(m) + 12, sy(v) + 5, name, 16))
    x = 700
    b.append(t(x, 34, "31.4%", 30, "bold") + t(x + 110, 32, "of pairs disagree", 17))
    b.append(t(x, 74, "0.917 vs 0.809", 24, "bold") + t(x + 190, 72, "mean RDS,", 16) + t(x + 190, 92, "disagree vs agree", 16))
    b.append(l(x, 112, 1120, 112))
    b.append(t(x, 140, "Odds ratio per +0.1 RDS, adjusted", 17, "bold"))
    fx = axis(x + 180, 1100, 306, 1, 7, [1, 3, 5, 7], 152)
    b.append(fx[0])
    forest = [("All tokens", 4.92, 4.58, 5.30, EN), ("Plus length gap", 5.58, 5.18, 6.03, EN), ("No answer tokens", 1.68, 1.60, 1.76, MUTED), ("Op types only", 1.10, 1.07, 1.13, MUTED)]
    for i, (a, m, lo, hi, col) in enumerate(forest):
        y = 172 + i * 36
        b.append(t(x, y + 5, a, 16) + l(fx[1](lo), y, fx[1](hi), y, col, 2.5) + c(fx[1](m), y, 6.5, col) + t(min(fx[1](hi) + 8, 1085), y - 7 if m > 5 else y + 5, f"{m:.2f}", 15, "bold"))
    
    save("lr_result", 1120, 408, *b)


def trace_row(b, x, y, keep, w=112, h=34, mark=None):
    for i in range(4):
        s = f"s{i}" if i < 3 else "s3 (k)"
        on = i in keep
        fill = (mark or "#BFD8E8") if on and i == 3 else ("#BFD8E8" if on else WHITE)
        b.append(r(x + i * (w + 6), y, w, h, fill, "none" if on else "#CFCFCF", dash="" if on else "4 4"))
        b.append(t(x + i * (w + 6) + w / 2, y + 23, s, 15.5, anchor="middle", fill=INK if on else "#9A9A9A"))
    return b


def rq6_design():
    b = [r(0, 0, 1120, 118, PALE)]
    b.append(t(16, 28, "Hindi trace, English translation. August is my favourite month. Today is 2026-07-24; what will the date be in 8 days?", 16, "bold"))
    for i, (x, s) in enumerate([(16, "s0  First, we have to understand the given information carefully."), (570, "s1  Today's date is 2026-07-24."), (16, "s2  The question asks what the date will be 8 days from today."), (570, "s3 (k)  The question also says that August is my favourite month.")]):
        b.append(t(x, 62 + (i // 2) * 28, s, 15.5))
    b.append(t(0, 150, "Variant", 16, "bold", fill=MUTED) + t(300, 150, "Prefix kept", 16, "bold", fill=MUTED) + t(830, 150, "Question", 16, "bold", fill=MUTED))
    var = [("P1", "one sentence earlier", [0, 1], "with distractor"), ("P", "just before the mention", [0, 1, 2], "with distractor"), ("M", "including the mention", [0, 1, 2, 3], "with distractor"), ("Q", "same prefix as P", [0, 1, 2], "distractor removed")]
    for i, (n, s, keep, q) in enumerate(var):
        y = 164 + i * 48
        b.append(t(0, y + 24, n, 21, "bold") + t(52, y + 24, s, 16.5))
        trace_row(b, 300, y, keep)
        b.append(t(830, y + 24, q, 16.5, "bold" if n == "Q" else "normal"))
    b.append(l(0, 366, 1120, 366))
    b.append(t(0, 396, "Q − P", 17, "bold") + t(58, 396, "distractor in the question", 17) + t(380, 396, "M − P", 17, "bold") + t(438, 396, "written mention", 17) + t(680, 396, "P − P1", 17, "bold") + t(742, 396, "ordinary sentence", 17))
    b.append(t(0, 428, "Originally wrong traces with a time-related mention: 526 Hindi, 37 English. 7 continuations per start, temperature 0.8.", 15.5, fill=MUTED))
    save("rq6_design", 1120, 438, *b)


def deletion():
    b = [t(0, 24, "Three versions of each trace, one greedy continuation each", 18, "bold")]
    for i, (n, s, keep, fill) in enumerate([("A", "as written", [0, 1, 2, 3], None), ("B", "mention deleted", [0, 1, 2], None), ("C", "neutral sentence deleted", [1, 2, 3], None)]):
        y = 44 + i * 46
        b.append(t(0, y + 24, n, 20, "bold") + t(32, y + 24, s, 16))
        trace_row(b, 245, y, keep, w=62, h=34)
    b.append(lines(0, 208, ["234 traces, 222 Hindi.", "Deletion with sampling: +4.5 [−2.7, 11.7]"], 18, 26))
    ax, sx = axis(640, 1085, 170, -10, 10, [-10, -5, 0, 5, 10], 40, sgn)
    b.append(t(640, 24, "B minus C, points, 95% interval", 18, "bold") + ax)
    b.append(l(sx(0), 96, sx(0), 170, INK, 1.5, "4 4"))
    b.append(l(sx(-6.8), 104, sx(7.2), 104, HI, 3.5) + c(sx(0), 104, 8, HI))
    b.append(t(sx(0), 88, "+0.0 [−6.8, 7.2]", 20, "bold", "middle"))
    b.append(t(640, 228, "Power for a 5-point effect: about 24%", 18))
    save("deletion", 1120, 290, *b)


def resampling():
    d = rows("fig_b1_contrasts.csv")
    panels = [("Q-P", "Q − P: distractor removed", -5, 35, 170, 450, [0, 10, 20, 30]), ("M-P", "M − P: mention kept", -35, 5, 490, 760, [-30, -20, -10, 0]), ("P-P1", "P − P1: sentence before", -20, 10, 800, 1090, [-20, -10, 0, 10])]
    groups = ["Hindi, all", "Hindi, opening", "Hindi, later", "English, all", "English, opening", "English, later"]
    h = 38
    base = 52 + 6 * h + 10
    b = []
    for i, g in enumerate(groups):
        y = 52 + i * h + (12 if i > 2 else 0)
        b.append(t(0, y + 5, g.replace(", ", ": "), 16, "bold" if g == "Hindi, all" else "normal", fill=INK if "Hindi" in g else MUTED))
    for key, title, lo, hi, x0, x1, ticks in panels:
        ax, sx = axis(x0, x1, base, lo, hi, ticks, 30, sgn)
        b.append(ax + t((x0 + x1) / 2, 16, title, 16, "bold", "middle") + l(sx(0), 30, sx(0), base, INK, 1.5, "4 4"))
        for i, g in enumerate(groups):
            y = 52 + i * h + (12 if i > 2 else 0)
            row = [x for x in d if x["contrast"] == key and x["group"] == g]
            if row:
                m, a, z = float(row[0]["mean_pts"]), float(row[0]["ci_low"]), float(row[0]["ci_high"])
                col = HI if "Hindi" in g else "#9A9A9A"
                b.append(l(sx(max(a, lo)), y, sx(min(z, hi)), y, col, 2.5) + c(sx(m), y, 6.5, col))
    y = base + 44
    b.append(t(170, y, "Difference in accuracy (points). English rests on 37 traces and is descriptive.", 15, fill=MUTED))
    y += 14
    cards = [("+5.3 [3.2, 7.4]", "Q − P in Hindi: 45.2% vs 40.0%. With the", "29 sentences as the sample: [−0.3, 9.4]."), ("−3.3 [−5.4, −1.2]", "M − P in Hindi. Not clearly more than an", "ordinary preceding sentence (p = 0.09)."), ("58%", "of the Q − P effect comes from the January", "sentence. Without it: +2.8 [0.4, 5.0].")]
    for i, (big, a, z) in enumerate(cards):
        x = i * 377
        b.append(r(x, y, 366, 96, PALE) + t(x + 14, y + 32, big, 23, "bold") + t(x + 14, y + 60, a, 15) + t(x + 14, y + 82, z, 15))
    save("resampling", 1120, y + 100, *b)


def findings():
    sx = lambda v: 170 + (v - 59.4) / 29.5 * 710
    b = [t(0, 22, "29.5-point gap on Hindi questions: share closed by each prompt", 19, "bold")]
    b.append(t(sx(59.4), 54, "Hindi CoT 59.4%", 15.5, anchor="middle", fill=MUTED) + t(sx(88.9), 54, "English CoT 88.9%", 15.5, anchor="middle", fill=MUTED))
    b.append(r(sx(59.4), 62, sx(88.9) - sx(59.4), 16, "#F0DCCF"))
    for i, (a, v, s, col) in enumerate([("Hinglish", 59.4, "none", HING), ("CLP", 70.3, "about a third", CLP), ("en-CoT", 82.9, "about four-fifths", ENCOT)]):
        y = 106 + i * 40
        b.append(t(0, y + 6, a, 18, "bold") + l(sx(59.4), y, sx(v), y, col, 5) + c(sx(v), y, 8, col) + t(sx(v) + 16, y + 6, f"{v}%: {s}", 17))
    b.append(l(0, 208, 1120, 208))
    items = ["CoT gain: +29.5 English, +4.7 Hindi; gap 4.3 → 29.1",
             "Thinking on, 450 questions: gap 27.3 → 1.0, with four times the tokens",
             "Hindi losses: methods seen mainly in Hindi traces; errors from reading Hindi remain under en-CoT",
             "Distractors: penalty 2.2, largely one sentence",
             "RDS: OR 4.92 per 0.1, association only; 1.10 on step types without answers",
             "Interventions: Q − P +5.3; written mention not isolated"]
    for i, a in enumerate(items):
        b.append(t(0, 244 + i * 38, a, 19))
    save("findings", 1120, 450, *b)


def future():
    pairs = [("Non-standard Hindi carriers", "Rerun recurrence with corrected templates"),
             ("No English questions with Hindi reasoning", "Add that arm"),
             ("One prompt per condition", "Several paraphrases of each prompt"),
             ("CLP's first turn often solves the problem", "CLP with solving forbidden in stage 1"),
             ("Thinking and token budget changed together", "Thinking on and off at equal budgets"),
             ("Interventions cover wrong traces only", "Question-by-mention factorial on correct and wrong traces"),
             ("Labels read by script and one LLM annotator", "Human annotation of samples and error labels")]
    b = [t(0, 20, "Limit", 18, "bold", fill=MUTED), t(560, 20, "Next run", 18, "bold", fill=MUTED)]
    for i, (a, z) in enumerate(pairs):
        y = 36 + i * 54
        b.append(r(0, y, 480, 44, PALE) + t(16, y + 29, a, 17) + arrow(486, y + 22, 552, y + 22) + r(560, y, 560, 44, "#E8F1F7") + t(576, y + 29, z, 17))
    save("future", 1120, 36 + 7 * 54, *b)


def tasks():
    data = [["Date addition", "Today is 2030-03-12, what is the date going to be in 13 days?", "2030-03-25", "YYYY-MM-DD"],
            ["Date subtraction", "Today is 2027-02-02, what was the date 9 days ago?", "2027-01-24", "YYYY-MM-DD"],
            ["Date duration", "How many day(s) (e.g., 5, 9) have passed between 2028-05-28 and 2028-06-12?", "15", "whole days"],
            ["Date recurrence", "Today is 2027-02-19, and I have a recurrence every 11 days.\nWithout counting today, what is the date of the 5 occurrence?", "2027-04-15", "YYYY-MM-DD"],
            ["Interval date", "If today is 2026-12-22, what are the dates for the start and end\nof next week, assuming Monday is the first day of the week?", "2026-12-28 to\n2027-01-03", "A to B"],
            ["Day of week", "What day of the week (e.g., Monday, Tuesday, ...) is 2025-07-31?", "Thursday", "weekday name"],
            ["Time addition", "It is now 07:09, what will the time be in 4 hours and 17 minutes?", "11:26", "HH:MM"],
            ["Time subtraction", "It is now 15:53, what was the time 0 hours and 53 minutes ago?", "15:00", "HH:MM"],
            ["Time duration", "If I looked at the clock at 01:45 and now it is 05:17,\nhow many minutes (e.g., 15, 23) have gone by?", "212", "whole minutes"]]
    simple("tasks", [("Task", 0, "start"), ("Question (level: long)", 165, "start"), ("Gold", 800, "start"), ("Format", 960, "start")], data, 16, 38)


def distractors():
    p = rows("distractor_pool.csv")
    b = []
    for x, kind, name in [(0, "similar", "Time-related: 35 sentence pairs"), (570, "dissimilar", "Unrelated: 43 sentence pairs")]:
        b.append(t(x, 22, name, 19, "bold"))
        seen = []
        for row in p:
            if row["kind"] == kind and row["en"] not in seen:
                seen.append(row["en"])
                if len(seen) <= 6:
                    y = 58 + (len(seen) - 1) * 56
                    b.append(t(x, y, row["en"][:62], 16) + t(x, y + 24, row["hi"][:62], 16, fill=MUTED))
    b.append(l(0, 396, 1120, 396))
    b.append(t(0, 430, "Per task: 5 sentences of each kind, 45 task-sentence units per kind, 90 in all. Prepended to the question.", 17.5))
    save("distractors", 1120, 440, *b)


def prompt_box(x, y, w, h, title, text, chars, size=15.5):
    return r(x, y, w, h, PALE) + t(x + 14, y + 26, title, 17, "bold") + para(x + 14, y + 52, text, size, chars, size * 1.34)


def prompts():
    b = [prompt_box(0, 0, 1120, 112, "Template, all conditions", '{mode} Write your entire response in {language}. End your response with a final line of the form "Answer: <answer>", where <answer> is {format}. Keep the word "Answer:" in English, use Western digits (0-9), and put nothing else on that line.', 138)]
    b.append(prompt_box(0, 124, 550, 112, "Direct", "Answer the following question directly. Do not provide any reasoning or explanation. Give only the final answer.", 66))
    b.append(prompt_box(570, 124, 550, 112, "CoT", "Solve the following question by reasoning through it step by step. Your reasoning must be written entirely in {language}; do not switch to another language at any point.", 66))
    b.append(prompt_box(0, 248, 550, 150, "en-CoT", "The following question is written in {source}. Solve it by reasoning through it step by step in {language}. Your reasoning must be written entirely in {language}; do not switch to another language at any point.", 66))
    b.append(prompt_box(570, 248, 550, 150, "Hinglish", 'Solve the following question by reasoning through it step by step. Your reasoning must be written in Hinglish, naturally mixing Hindi and English using only the Roman (Latin) script. Do not write in Devanagari script (the final "Answer:" line is the only exception).', 66))
    save("prompts", 1120, 402, *b)


def clp_prompts():
    b = [prompt_box(0, 0, 1120, 126, "Turn 1: understand", "Please act as an expert in multi-lingual understanding in {source}. Write your entire response in {target}. Request: {question} Let's understand the task in {target} step-by-step!", 138)]
    b.append(arrow(560, 130, 560, 158))
    b.append(prompt_box(0, 162, 1120, 150, "Turn 2: solve, same conversation", 'After understanding, you should act as an expert in {task} in {target}. Let\'s resolve the task you understand above step-by-step! Your reasoning must be written entirely in {target}; do not switch to another language at any point. End your response with a final line of the form "Answer: <answer>", where <answer> is {format}.', 138))
    data = [["Source, target", "hi_IN, en_US"], ["Task", "temporal reasoning"], ["Changes from Qin et al.", "temperature fixed at 0; added write-in-English rule; no CLSP voting"]]
    b.append(tbl(0, 322, [("", 0, "start"), ("", 240, "start")], data, 17, 30))
    save("clp_prompts", 1120, 450, *b)


def sets():
    data = [["Standard", "Direct, CoT", "both", "6,750", "81,000", "off", "4,096"], ["Thinking-on", "Direct, CoT", "both", "450", "5,400", "low", "16,000"], ["en-CoT", "English CoT", "Hindi", "2,250", "6,750", "off", "4,096"], ["CLP", "two turns", "Hindi", "2,250", "6,750", "off", "4,096 each"], ["Hinglish", "mixed CoT", "both", "2,250", "13,500", "off", "4,096"], ["Interventions", "continuations", "both", "", "13,664", "off", ""]]
    a = tbl(0, 0, spread([("Set", 0, "start"), ("Prompt", 190, "start"), ("Q. language", 370, "start"), ("Questions", 590, "end"), ("Responses", 730, "end"), ("Thinking", 860, "end"), ("Max tokens", 1020, "end")]), data, 18, 36)
    data2 = [["Model", "sarvam-105b"], ["Temperature, top_p", "0.0, 1.0 (resampling 0.8)"], ["Retries", "6, on 429, 500, 502, 503, 504"], ["Concurrency, timeout", "6, 180 s"]]
    save("sets", 1120, 420, a, tbl(0, 268, [("Setting", 0, "start"), ("", 270, "start")], data2, 18, 30))


def one_question():
    data = [["English direct", "", "2027-06-05 ×", "2027-04-19 ×"], ["English CoT", "English", "2027-08-15 ✓", "cut off"], ["Hindi direct", "", "2027-07-27 ×", "2027-03-06 ×"], ["Hindi CoT", "Hindi", "2027-08-02 ×", "2027-04-20 ×"], ["en-CoT (Hindi Q.)", "English", "2027-08-15 ✓", "cut off"], ["CLP (Hindi Q.)", "English", "2027-08-02 ×", "2027-08-02 ×"], ["Hinglish (English Q.)", "Roman mix", "2027-08-02 ×", "2027-08-01 ×"], ["Hinglish (Hindi Q.)", "Devanagari mix", "2027-08-02 ×", "2027-07-06 ×"]]
    b = [t(0, 20, "English", 16.5, "bold") + t(84, 20, "Today is 2027-05-16, and I have a recurrence every 13 days. Without counting today, what is the date of the 7 occurrence?", 15.5)]
    b.append(t(0, 50, "Hindi", 16.5, "bold") + t(84, 50, "आज 2027-05-16 है, और मेरे पास हर 13 दिनों पर एक पुनरावृत्ति है। आज को छोड़कर, 7वीं आवृत्ति की तिथि क्या है?", 16))
    b.append(t(0, 80, "Distractor", 16.5, "bold") + t(84, 80, "The last time I had a weekly commitment was in January. / आखिरी साप्ताहिक प्रतिबद्धता जनवरी में थी।", 15.5))
    b.append(t(0, 110, "Gold", 16.5, "bold") + t(84, 110, "2027-08-15", 16.5) + t(250, 110, "Long, date recurrence, ID 12. 2027-08-02 adds six intervals, not seven.", 15.5, fill=MUTED))
    b.append(tbl(0, 124, spread([("Condition", 0, "start"), ("Reasons in", 280, "start"), ("No distractor", 520, "start"), ("Time-related", 760, "start")], 980), data, 17, 31))
    save("one_question", 1120, 400, *b)


def parser_flow():
    steps = [("Clean", "Hindi digits to 0-9; dash and colon variants unified"), ("Split", "lines, then . ! ? ।; list markers removed"), ("Extract values", "dates, times, weekdays, months, numbers"), ("Written math", "26 + 3 becomes ADD 26 3"), ("Trigger phrases", "per-op cues in config/parser.yaml"), ("Arguments", "fill op args in order")]
    b = []
    w, gap = 168, 20
    for i, (a, s) in enumerate(steps):
        x = i * (w + gap)
        b.append(r(x, 0, w, 124, PALE, "#CFCFCF") + t(x + w / 2, 30, a, 16.5, "bold", "middle") + para(x + 10, 58, s, 14, 20, 19))
        if i < 5:
            b.append(arrow(x + w + 1, 62, x + w + gap - 1, 62))
    data = [["Date", "2025-3-7, Mar 7, 2025, 7 मार्च", "2025-03-07, or 03-07 if partial"], ["Time", "9:05, 1:23 PM", "09:05, 13:23"], ["Weekday", "Thu, गुरुवार, वीरवार", "Thursday"], ["Month", "March 2031, मार्च", "2031-03, 03"], ["Number", "42, twenty-one, दो हज़ार पच्चीस", "42, 21, 2025"]]
    b.append(tbl(0, 140, [("Value", 0, "start"), ("In text", 110, "start"), ("Token", 450, "start")], data, 16.5, 29))
    q = [["Standard CoT", "95-96%"], ["Thinking reasoning", "86-88%"], ["Op right", "85%"], ["Op + arguments", "77%"]]
    b.append(tbl(760, 140, [("Coverage, precision", 0, "start"), ("", 340, "end")], q, 16.5, 29))
    b.append(t(760, 312, "Precision: 240 tokens, one LLM annotator", 14.5, fill=MUTED))
    save("parser_flow", 1120, 328, *b)


def ops():
    data = [("GIVEN", "value", "Read a value from question"), ("GOAL", "target", "Restate what must be found"), ("PLAN", "method", "Choose a solution method"), ("RULE", "rule", "Apply a stated task rule"), ("LEAP", "year", "Decide whether year is leap"), ("MONTHLEN", "month", "Look up days in month"), ("ANCHOR", "date, weekday", "Recall a date's weekday"), ("CONVERT", "value, unit", "Change units or representation"), ("ADD", "x, y", "Add two values"), ("SUB", "x, y", "Subtract one value from another"), ("MUL", "x, y", "Multiply two values"), ("DIV", "x, y", "Divide, remainder or modulo"), ("CMP", "x, y", "Compare two values"), ("ROLL", "unit", "Carry across day, month or year"), ("STEP", "value, delta", "Move one unit at once"), ("CUMADD", "amount", "Add to a running total"), ("CUMSUB", "amount", "Subtract from a running total"), ("CHECK", "", "Verify an earlier result"), ("REVISE", "", "Correct or abandon a step"), ("IGNORE", "", "Mention or dismiss the distractor"), ("FORMAT", "", "Deliberate over format or language"), ("ANSWER", "value", "State the final answer"), ("SPITANSWER", "value", "Write the final answer line")]
    cols = [("Op", 0, "start"), ("Args", 130, "start"), ("Meaning", 250, "start")]
    a = tbl(0, 0, cols, [list(x) for x in data[:12]], 15.5, 31)
    z = tbl(570, 0, cols, [list(x) for x in data[12:]], 15.5, 31)
    save("ops", 1120, 412, a, z)


ACC = {"Date addition": [85.6, 98.0, 82.8, 85.1, 92.7, 95.7, 87.3, 85.9], "Date subtraction": [86.0, 95.2, 84.8, 66.0, 86.9, 94.0, 70.7, 71.0], "Date duration": [84.0, 99.3, 78.9, 88.2, 92.7, 97.7, 92.9, 82.8], "Date recurrence": [22.1, 90.3, 2.8, 20.1, 26.9, 70.3, 53.8, 18.9], "Day of week": [14.9, 69.5, 15.2, 21.0, 31.8, 52.5, 34.7, 23.5], "Interval date": [43.2, 50.7, 46.8, 23.9, 35.3, 44.1, 38.5, 23.6], "Time addition": [70.5, 95.9, 75.6, 73.5, 88.2, 92.6, 82.9, 72.3], "Time subtraction": [64.7, 97.7, 64.9, 75.2, 90.1, 95.7, 85.3, 74.2], "Time duration": [65.7, 98.9, 44.7, 80.1, 86.7, 98.1, 90.0, 80.9], None: None, "Short": [77.8, 93.2, 73.9, 69.5, 77.2, 83.0, 82.9, 66.5], "Medium": [69.6, 91.6, 65.3, 65.4, 75.7, 84.9, 78.8, 67.4], "Long": [61.2, 89.3, 57.9, 60.4, 71.3, 84.4, 70.4, 60.9], "Very long": [54.3, 87.2, 48.4, 53.7, 65.8, 83.5, 64.0, 53.7], "Very very long": [35.5, 82.9, 30.3, 47.9, 61.5, 78.5, 58.2, 48.3], 0: None, "No distractor": [60.6, 89.3, 56.0, 60.2, 69.3, 84.1, 70.6, 61.0], "Time-related": [59.9, 88.2, 54.9, 58.9, 69.3, 81.0, 69.7, 59.1], "Unrelated": [58.6, 89.2, 54.6, 59.1, 72.3, 83.6, 72.3, 58.0], 1: None, "All, answered": [59.7, 88.9, 55.2, 59.4, 70.3, 82.9, 70.9, 59.4], "All, strict": [59.6, 86.0, 55.2, 59.0, 69.9, 80.8, 70.3, 59.1]}


def accuracy():
    data = [None if v is None else [k] + [f"{x:.1f}" for x in v] for k, v in ACC.items()]
    heads = ["En direct", "En CoT", "Hi direct", "Hi CoT", "CLP", "en-CoT", "Hingl. En", "Hingl. Hi"]
    cols = [("2,250 questions, answered", 0, "start")] + [(h, 340 + i * 109, "end") for i, h in enumerate(heads)]
    fill = lambda i, j, cell: blend("#FFFFFF", "#5DA5D1", float(cell) / 100) if j else None
    simple("accuracy", cols, data, 15.5, 22.5, fill)


def gain_tasks():
    d = rows("fig_cot_delta_task_split.csv")
    data = []
    for task, name in TASK.items():
        row = [name]
        for lang in ["en_US", "hi_IN"]:
            for split in ["pooled", "none", "similar", "dissimilar"]:
                x = next(a for a in d if a["scoring"] == "answered" and a["split"] == split and a["lang"] == lang and a["task"] == task)
                row.append(pm(x["delta"]) + ("" if split != "pooled" else ""))
        data.append(row)
    cols = [("CoT gain, 6,750 questions", 0, "start")]
    for i, h in enumerate(["Pooled", "None", "Time", "Unrel."]):
        cols.append((h, 310 + i * 85, "end"))
    for i, h in enumerate(["Pooled", "None", "Time", "Unrel."]):
        cols.append((h, 700 + i * 85, "end"))
    def fill(i, j, cell):
        v = float(cell.replace("−", "-"))
        return blend("#FFFFFF", "#5DA5D1", min(v, 60) / 60) if v >= 0 else blend("#FFFFFF", "#E08A50", min(-v, 30) / 30)
    b = [t(200, 18, "English", 18, "bold"), t(745, 18, "Hindi", 18, "bold"), tbl(0, 28, spread(cols), data, 17, 40, fill)]
    save("gain_tasks", 1120, 440, *b)


def delta_heat():
    d = rows("rq1_cot_delta_task_level.csv")
    levels = ["short", "medium", "long", "very_long", "very_very_long"]
    heads = ["Short", "Med.", "Long", "V. long", "VV. long"]
    b = []
    for lang, x0, title in [("en_US", 170, "English: CoT minus direct"), ("hi_IN", 660, "Hindi: CoT minus direct")]:
        b.append(t(x0, 18, title, 18, "bold"))
        cw = 88
        for i, h in enumerate(heads):
            b.append(t(x0 + i * cw + cw / 2, 44, h, 15, "bold", "middle", MUTED))
        for j, task in enumerate(TASK):
            for i, lev in enumerate(levels):
                row = next(a for a in d if a["scoring"] == "answered" and a["split"] == "pooled" and a["lang"] == lang and a["task"] == task and a["level"] == lev)
                v = float(row["v"])
                col = blend("#FFFFFF", "#5DA5D1", min(v, 80) / 80) if v >= 0 else blend("#FFFFFF", "#E08A50", min(-v, 40) / 40)
                y = 54 + j * 38
                b.append(r(x0 + i * cw + 1, y, cw - 2, 36, col, rx=2) + t(x0 + i * cw + cw / 2, y + 24, pm(v, 0), 15.5, "bold" if row["sig"] == "True" else "normal", "middle"))
    for j, name in enumerate(TASK.values()):
        b.append(t(0, 54 + j * 38 + 24, name, 16))
    b.append(t(0, 54 + 9 * 38 + 24, "Bold: 95% interval excludes zero, uncorrected. 6,750 questions, answered, pooled.", 15, fill=MUTED))
    save("delta_heat", 1120, 54 + 9 * 38 + 32, *b)


def direct_results():
    b = [t(0, 22, "Direct answers", 19, "bold")]
    cols = [("", 0, "start"), ("English", 410, "end"), ("Hindi", 560, "end")]
    data = [["Accuracy", "59.0", "54.7"], ["Date recurrence wrong", "80%", "97%"], ["Day of week: top weekday", "Friday 34.4%", "Sunday 58.7%"], ["Wrong dates off by 10, 20 or 30 days", "35%", "30%"], ["Wrong times off by whole hours", "65%", "57%"], ["Wrong answers reusing distractor values", "6.1%", "11.3%"], ["Placebo", "3.4%", "4.1%"], ["p", "0.004", "<0.001"]]
    b.append(tbl(0, 30, cols, data, 17.5, 34))
    b.append(t(600, 54, "Day of week", 19, "bold"))
    b.append(t(600, 106, "85%", 48, "bold") + t(720, 92, "wrong (3,839 of 4,500)", 18) + t(720, 118, "chance: 85.7%", 18, fill=MUTED))
    b.append(l(600, 140, 1120, 140))
    b.append(t(600, 172, "Off by 10", 19, "bold") + t(600, 204, "36 days after 2029-03-06", 18) + t(600, 232, "Model 2029-04-01, gold 2029-04-11", 18) + t(600, 260, "Rate under English CoT: 3%", 18, fill=MUTED))
    b.append(l(600, 280, 1120, 280))
    b.append(t(600, 312, "Interval date", 19, "bold") + t(600, 342, "22% of wrong English answers give this week", 18))
    save("direct_results", 1120, 370, *b)


def penalties():
    d = rows("rq2_penalty_by_scope.csv")
    def cell(scope, lang, ins="similar_insertion", scoring="answered"):
        x = next(a for a in d if a["scope"] == scope and a["lang"] == lang and a["ins"] == ins and a["scoring"] == scoring)
        return f"{pm(x['v'])} {span(x['lo'], x['hi'])}"
    data = [["All", cell("all", "en_US"), cell("all", "hi_IN"), cell("all", "hi_minus_en")], ["All, strict", cell("all", "en_US", scoring="strict"), cell("all", "hi_IN", scoring="strict"), cell("all", "hi_minus_en", scoring="strict")], ["All, unrelated", cell("all", "en_US", "dissimilar_insertion"), cell("all", "hi_IN", "dissimilar_insertion"), cell("all", "hi_minus_en", "dissimilar_insertion")], None]
    for task, name in TASK.items():
        data.append([name, cell(task, "en_US"), cell(task, "hi_IN"), cell(task, "hi_minus_en")])
    simple("penalties", [("CoT penalty, time-related", 0, "start"), ("English", 300, "start"), ("Hindi", 560, "start"), ("Hindi minus English", 820, "start")], data, 16.5, 30)


def sentences():
    d = [x for x in rows("fig_sentence_penalty.csv") if x["scoring"] == "answered" and x["ins"] == "similar_insertion"]
    d.sort(key=lambda x: -float(x["sent_penalty"]))
    data = [[x["sentence"][:72], TASK[x["task"]], "English" if x["lang"] == "en_US" else "Hindi", x["n_q"], x["cot_cutoffs"], f"{pm(x['sent_penalty'])} {span(x['sent_lo'], x['sent_hi'])}"] for x in d[:9]]
    simple("sentences", [("Time-related sentence", 0, "start"), ("Task", 545, "start"), ("Lang.", 695, "start"), ("n", 790, "end"), ("Cut-offs", 875, "end"), ("Penalty", 895, "start")], data, 15.5, 38)


def mentions():
    d = rows("fig_mention.csv")
    name = {"en_US": "English", "hi_IN": "Hindi"}
    kind = {"similar": "Time-related", "dissimilar": "Unrelated"}
    data = []
    for measure, label in [("low_placebo_words", "Stricter word list"), ("project", "Original word list")]:
        for x in d:
            if x["measure"] == measure:
                data.append([label, name[x["lang"]], kind[x["distractor"]], f"{float(x['rate']):.1f}%", f"{float(x['placebo']):.1f}%", f"{float(x['or']):.2f}", f"[{float(x['or_lo']):.2f}, {float(x['or_hi']):.2f}]"])
        data.append(None)
    b = [tbl(0, 0, [("Word list", 0, "start"), ("Language", 220, "start"), ("Distractor", 360, "start"), ("Mention", 620, "end"), ("Placebo", 760, "end"), ("OR correct", 910, "end"), ("95% interval", 1110, "end")], data[:-1], 17, 32)]
    b.append(t(0, 330, "Literal reading", 18, "bold") + t(170, 330, "After \"My watch runs slow\": \"we cannot get 23:28 because my watch is slow\". Answer 00:00.", 17))
    save("mentions", 1120, 342, *b)


def traces_standard():
    data = [["Median steps", "25", "13"], ["CHECK or REVISE step", "88%", "3.7%"], ["Verification phrase, answered traces", "86.1%", "1.3%"], ["Median tokens, answered", "353", "212"]]
    b = [tbl(0, 0, [("CoT traces", 0, "start"), ("English", 470, "end"), ("Hindi", 590, "end")], data, 18, 36)]
    b.append(t(680, 22, "Hindi CoT language", 19, "bold") + t(680, 76, "0.988", 44, "bold") + t(830, 72, "mean TLR", 18))
    b.append(t(680, 112, "2.14% of traces below 0.9", 18))
    b.append(t(680, 142, "OR correct for those: 2.08 [1.66, 2.60]", 18))
    b.append(l(0, 196, 1120, 196))
    b.append(t(0, 230, "Cut-off English CoT", 19, "bold") + t(0, 278, "42", 44, "bold") + t(60, 278, "check or revise steps on average, 8 on wrong traces that finish", 18))
    b.append(t(0, 326, "29 February in span, longest questions, English CoT", 19, "bold") + t(0, 372, "36%", 44, "bold") + t(95, 372, "wrong, 9% without it. 181 of 186 wrong answers mention the leap year.", 18))
    save("traces_standard", 1120, 384, *b)


def error_share():
    data = [["English CoT", "726", "26.4", "48.9", "86.1", "353"], ["Hindi CoT", "2,723", "21.0", "20.9", "1.3", "212"], ["CLP", "1,993", "24.9", "24.3", "26.9", "487"], ["en-CoT", "1,125", "27.8", "36.4", "74.2", "311"]]
    b = [t(0, 28, "64%", 44, "bold") + t(110, 28, "of wrong answers are day of week, interval date or recurrence (19,583 of 30,421)", 19)]
    b.append(t(0, 62, "78 to 88% when the model reasons in English", 18, fill=MUTED))
    b.append(tbl(0, 84, [("2,250 questions", 0, "start"), ("Wrong", 360, "end"), ("Day of week %", 540, "end"), ("Interval date %", 730, "end"), ("Verify %", 880, "end"), ("Median tokens", 1090, "end")], data, 18, 36))
    d = rows("fig_dow_offsets.csv")
    b.append(t(0, 318, "Day of week: answer minus gold, share of responses (%)", 18, "bold"))
    conds = [("en_US", "cot", "English CoT", EN), ("hi_IN", "cot", "Hindi CoT", HI), ("en_US", "direct", "English direct", "#56B4E9"), ("hi_IN", "direct", "Hindi direct", DIRECT)]
    for i, (lang, cond, name, col) in enumerate(conds):
        x0 = i * 282
        b.append(t(x0, 348, name, 16, "bold"))
        for k in range(-3, 4):
            row = next(a for a in d if a["lang"] == lang and a["cond"] == cond and int(a["offset"]) == k)
            v = float(row["share_pct"])
            h = v * 1.05
            x = x0 + (k + 3) * 37
            b.append(r(x, 438 - h, 33, h, col, rx=2) + t(x + 16, 438 - h - 4, f"{v:.0f}", 13, anchor="middle") + t(x + 16, 456, sgn(k), 13.5, anchor="middle", fill=MUTED))
    save("error_share", 1120, 462, *b)


def card(x, y, w, h, title, items):
    out = r(x, y, w, h, PALE) + t(x + 14, y + 28, title, 17.5, "bold")
    yy = y + 56
    for a, s in items:
        out += t(x + 14, yy, a, 15, "bold", fill=MUTED)
        for part in textwrap.wrap(s, int((w - 110) / 7.6)):
            out += t(x + 96, yy, part, 15.5)
            yy += 22
        yy += 4
    return out


def examples_hindi():
    b = [card(0, 0, 550, 190, "Hindi CoT, date subtraction: counts forward", [("Question", "2027-05-09, 52 days ago"), ("Trace", "From 9 May to 31 May is 22 days. ... April has 30 days, so the date exactly 30 days before 30 April is 1 May."), ("Answer", "2027-05-01, gold 2027-03-18")])]
    b.append(card(570, 0, 550, 190, "Hindi CoT, interval date: two-day week", [("Question", "2030-05-15, next week"), ("Trace", "15 May 2030 is a Saturday. ... The next Monday will be 18 May 2030. ... Sunday will be 19 May 2030."), ("Answer", "2030-05-18 to 05-19, gold 05-20 to 05-26")]))
    b.append(r(0, 204, 1120, 206, PALE) + t(14, 232, "Hindi CoT, time addition: 10:46 plus 19 hours 41 minutes", 17.5, "bold"))
    b.append(t(14, 266, "24 - 19 = 5 घंटे। तो, 19 घंटे और 41 मिनट का मतलब है कि हमें 5 घंटे और 41 मिनट जोड़ने हैं।", 17.5))
    b.append(t(14, 296, "24 - 19 = 5 ghaṇṭe. to, 19 ghaṇṭe aur 41 minaṭ kā matlab hai ki hameṃ 5 ghaṇṭe aur 41 minaṭ joṛne haiṃ.", 15.5, style="italic", fill=MUTED))
    b.append(t(14, 326, "'24 - 19 = 5 hours. So 19 hours and 41 minutes means we have to add 5 hours and 41 minutes.'", 16))
    b.append(t(14, 358, "Answer 16:27, gold 06:27.", 16.5, "bold") + t(14, 388, "Time addition error rate: 24 to 27% at every level.", 16.5))
    save("examples_hindi", 1120, 414, *b)


def examples_shared():
    b = [card(0, 0, 550, 190, "English CoT, day of week: one day late", [("Question", "Day of week of 2029-07-02, gold Monday"), ("Trace", "Total: 31 + 28 + 31 + 30 + 31 + 30 + 2 = 183 days."), ("Answer", "Tuesday. 1 January to 2 July is 182 days.")])]
    b.append(card(570, 0, 550, 190, "English CoT, recurrence: skips 29 February", [("Question", "2028-02-15, every 6 days, 4th occurrence"), ("Trace", "From 2028-02-27 to 2028-03-05: 28 - 27 = 1 day in February, plus 5 days in March = 6 days ✓"), ("Answer", "2028-03-11, gold 2028-03-10")]))
    b.append(card(0, 204, 550, 190, "en-CoT, recurrence at k = 1: goes backwards", [("Question", "आज को छोड़कर, 1वीं आवृत्ति, ID 5"), ("Trace", "Given the phrasing \"excluding today,\" this suggests we need to find what comes before."), ("Answer", "2025-04-06, gold 2025-04-14")]))
    b.append(card(570, 204, 550, 190, "Hinglish, English question: date subtraction", [("Question", "2025-05-01, 3 days ago"), ("Trace", "01 minus 3 karne par hum 31 April par aayenge."), ("Answer", "2025-04-30, gold 2025-04-28")]))
    save("examples_shared", 1120, 398, *b)


def lr_views():
    d = [x for x in rows("t7_views_models.csv") if x["model"] == "primary"]
    names = {"full": "All tokens", "noans": "No answer tokens", "noansval": "No answers, no answer values", "ops": "Op types", "opsnoans": "Op types, no answers", "prefix8": "First 8 tokens", "prefix8ops": "First 8 op types", "precheck": "Before first check", "precheckops": "Op types before first check"}
    data = []
    for k, n in names.items():
        x = next(a for a in d if a["view"] == k)
        data.append([n, f"{float(x['or_per_0.1']):.2f}", f"[{float(x['or_lo']):.2f}, {float(x['or_hi']):.2f}]", f"{float(x['or_per_sd']):.2f}", f"[{float(x['or_sd_lo']):.2f}, {float(x['or_sd_hi']):.2f}]", f"{float(x['ame_pp_per_0.1']):.1f}", f"{float(x['auc_insample']):.3f}"])
    a = tbl(0, 0, [("Token view", 0, "start"), ("OR/0.1", 410, "end"), ("95%", 590, "end"), ("OR/SD", 700, "end"), ("95%", 880, "end"), ("AME", 980, "end"), ("AUC", 1100, "end")], data, 17, 31)
    b = t(0, 356, "Compare final answers alone", 18, "bold") + t(320, 356, "AUC 0.951, recall 1.00, precision 0.82", 18)
    b += t(0, 390, "Step types added out of fold", 18, "bold") + t(320, 390, "AUC +0.0007 [−0.0004, 0.0018]", 18)
    save("lr_views", 1120, 402, a, b)


def lr_outcomes():
    d = rows("t9_rds_by_outcome.csv")
    names = {"both_correct": "Both right", "en_only": "English only", "hi_only": "Hindi only", "both_wrong": "Both wrong"}
    data = []
    for k, n in names.items():
        x = next(a for a in d if a["outcome"] == k)
        data.append([n, f"{int(x['n']):,}", f"{float(x['full']):.3f}", f"{float(x['noans']):.3f}", f"{float(x['opsnoans']):.3f}", x["en_len"], x["hi_len"], f"{float(x['gap']):.3f}"])
    a = tbl(0, 0, [("Thinking off", 0, "start"), ("Pairs", 280, "end"), ("RDS", 420, "end"), ("No answers", 590, "end"), ("Op types", 730, "end"), ("En len", 850, "end"), ("Hi len", 970, "end"), ("Len gap", 1100, "end")], data, 18, 34)
    t17 = rows("t17_splits.csv")
    rowsd = []
    for k, n in TASK.items():
        vals = [n]
        for view in ["full", "noans", "opsnoans"]:
            x = next(q for q in t17 if q["by"] == "task" and q["level"] == k and q["view"] == view)
            vals.append(f"{float(x['or_per_0.1']):.2f}")
        x = next(q for q in t17 if q["by"] == "task" and q["level"] == k and q["view"] == "full")
        vals.insert(1, f"{100 * float(x['rate']):.1f}%")
        rowsd.append(vals)
    z = tbl(0, 176, spread([("By task", 0, "start"), ("Disagree", 340, "end"), ("OR/0.1 all", 520, "end"), ("No answers", 700, "end"), ("Op types", 860, "end")], 1100), rowsd, 15.5, 25)
    save("lr_outcomes", 1120, 440, a, z)


def thinking():
    d = rows("ron_by_task.csv")
    data = []
    for k, n in TASK.items():
        h = next(a for a in d if a["lang"] == "hi_IN" and a["task"] == k and a["cond"] == "cot")
        e = next(a for a in d if a["lang"] == "en_US" and a["task"] == k and a["cond"] == "cot")
        data.append([n, num(e["off"]), num(e["on"]), num(h["off"]), num(h["on"]), num(h["off_strict"]), num(h["on_strict"]), num(h["on_4k_strict"]), num(h["over_4096"])])
    a = tbl(0, 28, [("450 questions", 0, "start"), ("Off", 320, "end"), ("On", 420, "end"), ("Off", 540, "end"), ("On", 640, "end"), ("Off strict", 780, "end"), ("On strict", 910, "end"), ("Cut 4,096", 1020, "end"), ("Over 4,096", 1115, "end")], data, 15.5, 26)
    head = t(250, 18, "English CoT", 16, "bold") + t(470, 18, "Hindi CoT", 16, "bold")
    tot = [["All", "CoT, English", "91.4 → 98.9"], ["All", "CoT, Hindi", "64.1 → 97.9 (strict 59.9 → 89.9)"], ["All", "Direct, English", "64.2 → 97.9"], ["All", "Direct, Hindi", "59.2 → 94.9"], ["Gap", "CoT", "27.3 → 1.0 (strict 27.4 → 2.7)"]]
    z = tbl(0, 300, [("", 0, "start"), ("Thinking off → on", 90, "start"), ("", 320, "start")], tot, 15.5, 26)
    save("thinking", 1120, 480, head, a, z)


def thinking_format():
    b = [t(0, 56, "79%", 44, "bold") + t(110, 44, "English words in hidden Hindi CoT reasoning", 18) + t(110, 68, "Visible answer stays in Hindi", 18, fill=MUTED)]
    b.append(t(600, 56, "43.8%", 44, "bold") + t(750, 44, "strict Hindi CoT cut at 4,096 tokens", 18) + t(750, 68, "59.9% with thinking off", 18, fill=MUTED))
    b.append(l(0, 92, 1120, 92))
    data = [["Hindi direct hidden steps that are FORMAT", "207,097 of 627,487"], ["Visible CoT steps that are FORMAT", "0.2%"], ["FORMAT share, date and time addition", "49.8%"], ["FORMAT share, interval date", "15.3%"], ["Mean FORMAT steps, right vs wrong traces", "157 vs 120"]]
    b.append(tbl(0, 104, [("Format arguments", 0, "start"), ("", 680, "end")], data, 17.5, 32))
    b.append(r(720, 110, 400, 158, PALE) + t(734, 136, "Adding one day: 5,170 words, 361 of 636 FORMAT", 14.5, "bold"))
    b.append(lines(734, 166, ["\"If I write: 2025-04-07. That's not in Hindi. ...", "But if I have no text outside the last line,", "then there's no Hindi text.\""], 16, 25, style="italic"))
    b.append(l(0, 298, 1120, 298))
    b.append(t(0, 332, "Errors", 18, "bold") + t(170, 332, "287 of 422 wrong responses have no answer line, mostly at the 16,000-token limit", 18))
    b.append(t(0, 366, "Disagreement", 18, "bold") + t(170, 366, "31.7% → 10.9% on matched questions, unanswered counted wrong, OR 0.23 [0.18, 0.30]", 18))
    b.append(t(0, 400, "Pairs", 18, "bold") + t(170, 400, "1,159 both right, 20 English only, 11 Hindi only, 1 both wrong", 18))
    save("thinking_format", 1120, 410, *b)


def clp_results():
    diffs = json.loads((HERE / "data" / "clp_diffs.json").read_text())
    keys = ["Date addition", "Date subtraction", "Date duration", "Date recurrence", "Day of week", "Interval date", "Time addition", "Time subtraction", "Time duration", None, "No distractor", "Time-related", "Unrelated", 1, "All, answered", "All, strict"]
    data = []
    for k in keys:
        v = ACC[k]
        if v is None:
            data.append(None)
        else:
            key = {"No distractor": "no_insertion", "Time-related": "similar_insertion", "Unrelated": "dissimilar_insertion", "All, answered": "all", "All, strict": "all strict"}.get(k) or next(a for a, b_ in TASK.items() if b_ == k)
            data.append([k, f"{v[2]:.1f}", f"{v[3]:.1f}", f"{v[4]:.1f}", f"{v[5]:.1f}", pm(diffs[key]["clp-cot"]), pm(diffs[key]["clp-en"])])
    a = tbl(0, 0, spread([("2,250 Hindi questions", 0, "start"), ("Direct", 300, "end"), ("Hindi CoT", 420, "end"), ("CLP", 520, "end"), ("en-CoT", 630, "end"), ("CLP − CoT", 770, "end"), ("CLP − en-CoT", 920, "end")]), data, 15.5, 24.5)
    b = t(0, 456, "CLP − Hindi direct: +15.1 [13.5, 16.7]. en-CoT − CLP: +12.6 [11.4, 13.9]. Qin et al. on MGSM: CLP 70.6, En-CoT 57.8.", 16.5)
    save("clp_results", 1120, 466, a, b)


def clp_stages():
    d = rows("new_gold_in_stage1_by_task.csv")
    sc = lambda v: v * 3.1
    b = [t(0, 18, "% of responses", 18, "bold")]
    b.append(r(330, 6, 16, 14, DIRECT, rx=2) + t(352, 19, "Gold in turn 1", 15) + r(490, 6, 16, 14, ENCOT, rx=2) + t(512, 19, "Turn 2 right if gold", 15) + r(690, 6, 16, 14, HI, rx=2) + t(712, 19, "Turn 2 right if not", 15) + t(900, 19, "n not gold", 15, "bold", fill=MUTED))
    for i, x in enumerate(d):
        y = 36 + i * 42
        b.append(t(0, y + 24, TASK[x["task"]], 16))
        for j, (f, col) in enumerate([("gold_in_s1", DIRECT), ("s2_given_gold_in_s1", ENCOT), ("s2_given_not", HI)]):
            v = float(x[f])
            b.append(r(170, y + j * 12, sc(v), 10, col, rx=2) + t(174 + sc(v), y + j * 12 + 10, f"{v:.1f}", 11.5))
        b.append(t(960, y + 24, x["n_not"], 16, anchor="end"))
    b.append(t(0, 36 + 9 * 42 + 20, "Three date-answer tasks: turn 2 right 97.5% if turn 1 ends at gold, 20.1% if not. Turn 1 not randomised.", 16.5))
    b.append(t(0, 36 + 9 * 42 + 48, "ID 12. Turn 1: \"the date of the 7th occurrence is 2 August 2027.\" Turn 2: \"Adding 78 days to 16 May 2027 also results in 2 August 2027.\" Gold 2027-08-15.", 14.5, fill=MUTED))
    save("clp_stages", 1120, 36 + 9 * 42 + 56, *b)


def hinglish_detail():
    m = rows("new_subtraction_month_cross.csv")
    names = {"cot/en_US": "English CoT", "cot/hi_IN": "Hindi CoT", "en-cot/hi_IN": "en-CoT", "hinglish/en_US": "Hinglish, English Q.", "hinglish/hi_IN": "Hinglish, Hindi Q.", "hinglish/en_US/plain": "English Q., plain", "hinglish/en_US/roman": "English Q., Roman mix"}
    data = [[n, "42.3" if k == "hinglish/en_US" else num(next(a for a in m if a["group"] == k)["acc_cross_month"]), num(next(a for a in m if a["group"] == k)["acc_same_month"])] for k, n in names.items()]
    a = tbl(0, 0, [("Date subtraction", 0, "start"), ("Crosses month", 350, "end"), ("Same month", 490, "end")], data, 16.5, 30)
    st = [["English Q.", "63.1%", "36.9%", "0%"], ["Hindi Q.", "24.4%", "2.6%", "73.1%"]]
    z = tbl(560, 0, [("Script", 0, "start"), ("Roman mix", 230, "end"), ("Plain", 320, "end"), ("Devanagari ≥10%", 500, "end")], st, 16.5, 30)
    v = rows("new_verification_rates.csv")
    vn = {"cot/en_US": "English CoT", "en-cot/hi_IN": "en-CoT", "cot/hi_IN": "Hindi CoT", "hinglish/en_US": "Hinglish, English Q.", "hinglish/hi_IN": "Hinglish, Hindi Q."}
    vd = [[n, num(next(a for a in v if a["condition_language"] == k)["orig"]), num(next(a for a in v if a["condition_language"] == k)["ext"])] for k, n in vn.items()]
    y = tbl(560, 112, [("Verification %", 0, "start"), ("Regex", 380, "end"), ("Extended", 500, "end")], vd, 16.5, 28)
    e = [t(0, 280, "No Hindi function words, English Q.", 17, "bold") + t(330, 280, "n = 1,838", 17, fill=MUTED)]
    e.append(t(0, 312, "−10.3 [−12.3, −8.3] accuracy; verification 86.5% → 18.6%", 17))
    e.append(t(0, 344, "Roman traces, English Q.: −11.3 [−13.6, −9.0] more", 17))
    e.append(t(0, 376, "Roman vs Devanagari, Hindi Q.: −2.8 [−5.2, −0.5]", 17))
    e.append(t(560, 312, "Majority Devanagari, Hindi Q.: 68.5%", 17))
    e.append(t(560, 344, "Hindi Q. task swings: date duration −5.5, date subtraction +5.1", 17))
    save("hinglish_detail", 1120, 390, a, z, y, *e)


def arms():
    d = rows("table_b3_arm_accuracy.csv")
    u = rows("new_unanswered_by_arm.csv")
    gs = ["Hindi, all", "Hindi, opening", "Hindi, later"]
    data = []
    for g in gs:
        row = [g]
        for arm in ["Q", "P", "M", "P1"]:
            x = [a for a in d if a["group"] == g and a["arm"] == arm]
            row.append(num(x[0]["accuracy_pct"]) if x and x[0]["accuracy_pct"] else "")
        for arm in ["Q", "P", "M", "P1"]:
            x = [a for a in u if a["group"] == g and a["arm"] == arm]
            row.append(num(x[0]["unanswered_pct"]) if x and x[0]["unanswered_pct"] else "")
        data.append(row)
    b = [t(250, 18, "Correct (%)", 17, "bold"), t(690, 18, "Unanswered (%)", 17, "bold")]
    cols = [("", 0, "start")] + [(h, 300 + i * 90, "end") for i, h in enumerate(["Q", "P", "M", "P1"])] + [(h, 740 + i * 90, "end") for i, h in enumerate(["Q", "P", "M", "P1"])]
    b.append(tbl(0, 26, cols, data, 17, 32))
    stats = [["Excess fraction, Hindi", "8.8% [5.5, 12.1]"], ["Q − P, sentences as sample", "+5.3 [−0.3, 9.4]"], ["Q − P without January sentence", "+2.8 [0.4, 5.0]"], ["M − P", "−3.3 [−5.4, −1.2]"], ["P − P1", "−0.7 [−3.5, 2.1]"], ["(M − P) − (P − P1), 248 traces", "−4.6 [−9.6, 0.6], p = 0.09"], ["Rollouts mentioning the distractor", "57.8%"]]
    b.append(tbl(0, 170, [("Hindi contrasts", 0, "start"), ("", 590, "end")], stats, 17, 29))
    cal = [["Hindi, 278 questions", "+5.7 [0.5, 10.8]"], ["English, 22 questions", "−24.7"], ["Calibration, 90 questions", "−2.2 [−13.3, 7.8]"]]
    b.append(tbl(660, 170, [("Self-hosted minus API", 0, "start"), ("", 450, "end")], cal, 17, 29))
    save("arms", 1120, 420, *b)


def one_trace():
    b = [r(0, 0, 1120, 148, PALE)]
    b.append(t(14, 26, "Long date addition, ID 11, Hindi, translated", 16, "bold"))
    b.append(t(14, 52, "August is my favourite month. Today is 2026-07-24; what will the date be in 8 days? Gold 2026-08-01.", 16))
    b.append(t(14, 80, "s0 First, we have to understand the given information carefully.   s1 Today's date is 2026-07-24.", 15.5))
    b.append(t(14, 104, "s2 The question asks what the date will be 8 days from today.   s3 (k) The question also says that August is my favourite month.", 15))
    b.append(t(14, 130, "Later: \"One day past 31 July is 1 August, and the remaining 7 days give 8 August.\" Answer 2026-08-08.", 15.5))
    data = [["A as written", "with", "s0 to s3", "1 of 1"], ["B mention deleted", "with", "s0 to s2", "1 of 1"], ["C neutral deleted", "with", "s1 to s3", "1 of 1"], None, ["P before the mention", "with", "s0 to s2", "6 of 7"], ["Q distractor removed", "without", "s0 to s2", "7 of 7"], ["M after the mention", "with", "s0 to s3", "7 of 7"], ["P1 a sentence earlier", "with", "s0 to s1", "6 of 7"]]
    b.append(tbl(0, 158, spread([("Variant", 0, "start"), ("Distractor", 420, "start"), ("Prefix", 620, "start"), ("Correct", 880, "end")]), data, 17, 29))
    save("one_trace", 1120, 420, *b)


def week_errors():
    v = json.loads((HERE / "verify" / "recomputed_errors.json").read_text())
    parts = [("this", "This week", "#56B4E9"), ("one", "One day off", EN), ("satfri", "Saturday to Friday", CLP), ("not7", "Not 7 days", HI), ("other", "Other", "#CFCFCF")]
    b = []
    x = 210
    for _, name, col in parts:
        b.append(r(x, 2, 16, 14, col, rx=2) + t(x + 22, 15, name, 15))
        x += 40 + len(name) * 8.2
    b.append(t(0, 15, "% of two-date answers", 15, "bold", fill=MUTED))
    sc = 9.0
    for i, cond in enumerate(["English direct", "English CoT", "Hindi direct", "Hindi CoT", "en-CoT"]):
        k = v[cond]
        y = 30 + i * 38
        wrong = 100 * k["week|wrong"] / k["week|n"]
        b.append(t(0, y + 21, f"{cond}, {wrong:.0f}% wrong", 15.5))
        x = 210
        rest = 100.0
        for key, _, col in parts:
            share = 100 * k.get(f"week|{key}", 0) / k["week|given"] if key != "other" else rest
            rest -= share if key != "other" else 0
            b.append(r(x, y, share * sc - 2, 30, col, rx=2))
            if share >= 6:
                b.append(t(x + share * sc / 2, y + 21, f"{share:.0f}", 14.5, "bold", "middle", WHITE if col in (EN, HI) else INK))
            x += share * sc
    y = 232
    b.append(card(0, y, 550, 170, "Skips a month end (en-CoT, today 2027-05-27)", [("Trace", "This week ends on Sunday, 2027-05-30. ... Next week starts on Monday, 2027-06-01."), ("Answer", "2027-06-01 to 06-07, gold 05-31 to 06-06")]))
    b.append(card(570, y, 550, 170, "Gives this week (English direct, today 2026-09-13)", [("Why", "13 September 2026 is a Sunday, so the answer is the week ending today."), ("Answer", "2026-09-07 to 09-13, gold 09-14 to 09-20")]))
    save("week_errors", 1120, y + 174, *b)


def time_errors():
    rowsd = [("English direct", 34, 65, 3), ("English CoT", 3, 51, 15), ("Hindi direct", 38, 57, 3), ("Hindi CoT", 24, 41, 4), ("en-CoT", 5, 57, 9)]
    b = [t(0, 16, "Time tasks", 16, "bold", fill=MUTED), t(150, 16, "Wrong", 16, "bold", fill=MUTED), t(440, 16, "Off by whole hours", 16, "bold", fill=MUTED), t(800, 16, "Off by exactly 12 hours", 16, "bold", fill=MUTED)]
    col = {"English direct": "#56B4E9", "English CoT": EN, "Hindi direct": DIRECT, "Hindi CoT": HI, "en-CoT": ENCOT}
    for i, (name, w, h, tw) in enumerate(rowsd):
        y = 30 + i * 38
        b.append(t(0, y + 20, name, 16) + r(150, y, w * 5.4, 28, col[name], rx=3) + t(156 + w * 5.4, y + 20, f"{w}%", 15, "bold"))
        b.append(r(440, y, h * 4.2, 28, col[name], rx=3) + t(446 + h * 4.2, y + 20, f"{h}%", 15, "bold"))
        b.append(r(800, y, tw * 12, 28, col[name], rx=3) + t(806 + tw * 12, y + 20, f"{tw}%", 15, "bold"))
    y = 232
    b.append(card(0, y, 550, 170, "12-hour clock (English CoT): 07:22, 15 h 31 min ago", [("Trace", "6 - 15 = -9 hours. Since I have -9 hours, I need to go back 12 hours to get into the previous day: -9 + 12 = 3 hours."), ("Answer", "03:51, gold 15:51")]))
    b.append(card(570, y, 550, 170, '"0 hours" misread (en-CoT): 12:11, 0 h 4 min ago', [("Trace", "I need to find what time it was 4 hours and 4 minutes before 12:11."), ("Answer", "08:07, gold 12:07")]))
    save("time_errors", 1120, y + 174, *b)


def boundary_errors():
    v = json.loads((HERE / "verify" / "recomputed_errors.json").read_text())
    conds = ["English direct", "English CoT", "Hindi direct", "Hindi CoT", "en-CoT"]
    col = {"English direct": "#56B4E9", "English CoT": EN, "Hindi direct": DIRECT, "Hindi CoT": HI, "en-CoT": ENCOT}
    b = []
    for j, (key, title) in enumerate([("feb29", "29 February in the span"), ("month", "Crosses a month end"), ("mid", "Crosses midnight")]):
        x0 = 150 + j * 325
        ax, sx = axis(x0, x0 + 270, 216, 0, 100, [0, 50, 100], 26, "{}%")
        b.append(t(x0, 16, title, 17, "bold") + ax)
        for i, cond in enumerate(conds):
            k = v[cond]
            a = 100 * k[f"{key}|without|wrong"] / k[f"{key}|without|n"]
            z = 100 * k[f"{key}|with|wrong"] / k[f"{key}|with|n"]
            y = 44 + i * 36
            b.append(l(sx(a), y, sx(z), y, col[cond], 3) + c(sx(a), y, 6.5, WHITE, col[cond], 2.5) + c(sx(z), y, 7, col[cond]) + t(sx(z) + 11, y + 5, f"{z:.0f}", 13.5, "bold"))
    for i, cond in enumerate(conds):
        b.append(t(0, 49 + i * 36, cond, 16))
    b.append(c(156, 258, 6.5, WHITE, MUTED, 2.5) + t(170, 264, "Without", 15, fill=MUTED) + c(250, 258, 7, MUTED) + t(264, 264, "With. % wrong, all levels; date tasks, then time tasks", 15, fill=MUTED))
    y = 282
    b.append(card(0, y, 550, 124, "Knows the leap year, skips the day anyway (Hindi CoT)", [("Trace", "6 दिन बाद: 6 मार्च 2028 ... चूंकि 2028 एक लीप वर्ष है"), ("Answer", "2028-03-06, gold 2028-03-05")]))
    b.append(card(570, y, 550, 124, "Check repeats the mistake (English CoT)", [("Trace", "From 2028-02-27 to 2028-03-05: 28 - 27 = 1 day in February"), ("Answer", "2028-03-11, gold 2028-03-10")]))
    save("boundary_errors", 1120, y + 128, *b)


def loop_errors():
    b = [t(0, 18, "Wrong answers that are cut-offs", 17, "bold")]
    for i, (name, v, col) in enumerate([("Hindi CoT", 2, HI), ("en-CoT", 13, ENCOT), ("English CoT", 22, EN), ("Thinking, Hindi CoT", 81, "#E9A97F"), ("Thinking, English CoT", 85, "#7FB6D6")]):
        y = 32 + i * 34
        b.append(t(0, y + 19, name, 15.5) + r(170, y, v * 2.8, 26, col, rx=3) + t(176 + v * 2.8, y + 19, f"{v}%", 15, "bold"))
    b.append(t(0, 226, "English CoT's 651 cut-offs", 17, "bold"))
    x = 0
    for name, n, col in [("Day of week", 358, EN), ("Recurrence", 156, "#56B4E9"), ("Next week", 89, ENCOT), ("Other", 48, "#CFCFCF")]:
        w = n / 651 * 450
        b.append(r(x, 240, w - 2, 34, col, rx=3) + t(x + 6, 262, str(n), 14.5, "bold", fill=WHITE if col in (EN, ENCOT) else INK))
        x += w
    b.append(t(0, 296, "Day of week, recurrence, next week, other", 14.5, fill=MUTED))
    data = [["Day of week", "23.0", "13.4"], ["Date recurrence", "19.3", "5.0"], ["Time addition", "13.1", "3.5"], ["Date duration", "12.6", "2.8"], ["Time duration", "12.4", "2.0"], ["Time subtraction", "11.7", "3.3"], ["Interval date", "11.2", "7.7"], ["Date subtraction", "6.0", "2.5"], ["Date addition", "2.4", "1.1"]]
    b.append(tbl(540, 0, [("CHECK + REVISE steps, English CoT", 0, "start"), ("Wrong", 450, "end"), ("Right", 570, "end")], data, 16, 28))
    b.append(t(540, 306, "Wrong traces with 20 or more: 869 of 2,903", 15.5, fill=MUTED))
    b.append(r(0, 318, 1120, 96, PALE) + t(14, 344, "English CoT, day of week of 2025-08-21, gold Thursday, no answer", 16.5, "bold"))
    b.append(t(14, 372, "Day 233: (233-1) mod 7 = 1. Wednesday + 1 = Thursday. But month-by-month gave Friday.", 16, style="italic") + t(14, 396, "There's a 1-day discrepancy. Let me recheck July 31 ...", 16, style="italic"))
    save("loop_errors", 1120, 420, *b)


def steer_errors():
    b = [card(0, 0, 550, 194, "Answer lands on the month end (English direct)", [("Question", "I always get confused with months that have 31 days. Today is 2026-12-24, what is the date going to be in 8 days?"), ("Answer", "2026-12-31, gold 2027-01-01")])]
    b.append(card(570, 0, 550, 194, "Pulled into the named month (Hindi direct)", [("Question", "अगस्त मेरा पसंदीदा महीना है। आज 2025-07-29 है, 1 दिनों में तिथि क्या होगी?"), ("English", "August is my favourite month. Today is 2025-07-29. What is the date in 1 day?"), ("Answer", "2025-08-01, gold 2025-07-30")]))
    b.append(card(0, 206, 550, 194, "Changes a fact (Hindi CoT, 2026-09-02, 12 days ago)", [("Trace", "31 दिनों वाले महीने अप्रैल, जून, सितंबर और नवंबर होते हैं।"), ("English", "The months with 31 days are April, June, September and November."), ("Answer", "2026-08-31, gold 2026-08-21")]))
    b.append(card(570, 206, 550, 194, "Argues until the token limit (English CoT)", [("Question", "My watch always runs a bit slow. It is now 13:44, what was the time 59 hours and 37 minutes ago?"), ("Trace", "Could 'it is now 13:44' refer to the watch?"), ("Answer", "none, gold 02:07")]))
    save("steer_errors", 1120, 404, *b)


OUT.mkdir(exist_ok=True)
for old in OUT.glob("*.svg"):
    old.unlink()
for fn in [project, metric_accuracy, metric_diffs, metric_trace, metric_rds, metric_rq6, metric_tests, prior_work, dataset, tasks, distractors, conditions, prompts, clp_prompts, sets, pipeline, one_question, parser_flow, ops, rds_example, lr_setup, rq6_design, accuracy, direct_results, cot_gain, gain_tasks, delta_heat, hindi_tasks, by_level, distractor_penalty, penalties, january, sentences, mentions, traces_standard, error_share, error_patterns, examples_hindi, examples_shared, week_errors, time_errors, boundary_errors, loop_errors, steer_errors, lr_result, lr_views, lr_outcomes, thinking, thinking_format, decomposition, breakdown, distance, recurrence_k, clp_results, clp_stages, hinglish, hinglish_detail, deletion, resampling, arms, one_trace, findings, future]:
    fn()
