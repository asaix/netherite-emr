import json
from pathlib import Path

HERE = Path(__file__).parent
h = json.loads((HERE.parent / "headline.json").read_text())
s, f = h["subset"], h["full"]
(HERE / "tables").mkdir(exist_ok=True)
TASKS = {"date_addition": "Date addition", "date_subtraction": "Date subtraction", "date_duration": "Date duration",
         "date_recurrence": "Date recurrence", "day_of_week": "Day of week", "interval_date": "Interval date",
         "time_addition": "Time addition", "time_subtraction": "Time subtraction", "time_duration": "Time duration"}
COLS = ["en_direct", "en_cot", "hi_direct", "hi_cot", "clp", "encot", "en_hing", "hi_hing"]
INS = {"no_insertion": "No distractor", "similar_insertion": "Time-related", "dissimilar_insertion": "Unrelated"}
LEVELS = {"short": "Short", "medium": "Medium", "long": "Long", "very_long": "Very long", "very_very_long": "Very very long"}


def row(label, vals):
    return label + " & " + " & ".join(f"{v:.1f}" for v in vals) + r" \\"


lines = [r"\begin{tabular}{@{}lrrrrrrrr@{}}", r"\toprule",
         r"& \multicolumn{2}{c}{English Q.} & \multicolumn{4}{c}{Hindi Q.} & \multicolumn{2}{c}{Hinglish prompt} \\",
         r"\cmidrule(lr){2-3}\cmidrule(lr){4-7}\cmidrule(l){8-9}",
         r"& Direct & CoT & Direct & CoT & CLP & en-CoT & English Q. & Hindi Q. \\", r"\midrule"]
for t, name in TASKS.items():
    lines.append(row(name, [s["by_task"][t][c]["answered"] for c in COLS]))
lines.append(r"\midrule")
for l, name in LEVELS.items():
    lines.append(row(name, [s["by_level"][l][c]["answered"] for c in COLS]))
lines.append(r"\midrule")
for i, name in INS.items():
    lines.append(row(name, [s["acc"][c]["by_ins"][i]["answered"] for c in COLS]))
lines.append(r"\midrule")
lines.append(row(r"\textbf{All, answered}", [s["acc"][c]["answered"] for c in COLS]))
lines.append(row(r"\textbf{All, strict}", [s["acc"][c]["strict"] for c in COLS]))
lines += [r"\bottomrule", r"\end{tabular}"]
(HERE / "tables" / "accuracy.tex").write_text("\n".join(lines) + "\n")


def p(v):
    return f"{v[0]:+.1f}".replace("-", "$-$")


def ci(v):
    return f"{v[0]:+.1f} [{v[1]:.1f}, {v[2]:.1f}]".replace("-", "$-$")


lines = [r"\begin{tabular}{@{}lrrrr@{}}", r"\toprule", r"& Direct & CoT & Gain [95\% CI] & Strict \\", r"\midrule"]
for lang, name, cot, dire in [("en", "English", "en_cot", "en_direct"), ("hi", "Hindi", "hi_cot", "hi_direct")]:
    d = f["cot_delta"][lang]
    lines.append(f"{name} & {f['acc'][dire]['answered']:.1f} & {f['acc'][cot]['answered']:.1f} & {ci(d['pooled']['answered'])} & {p(d['pooled']['strict'])} \\\\")
lines += [r"\midrule", r"By distractor & \multicolumn{2}{c}{None} & Time-related & Unrelated \\"]
for lang, name in [("en", "English"), ("hi", "Hindi")]:
    d = f["cot_delta"][lang]
    lines.append(f"{name} & \\multicolumn{{2}}{{c}}{{{p(d['no_insertion']['answered'])}}} & {p(d['similar_insertion']['answered'])} & {p(d['dissimilar_insertion']['answered'])} \\\\")
g = f["gap_cot"]
lines.append(f"Gap under CoT & \\multicolumn{{2}}{{c}}{{{p(g['no_insertion']['answered'])}}} & {p(g['similar_insertion']['answered'])} & {p(g['dissimilar_insertion']['answered'])} \\\\")
g = f["gap_direct"]
lines.append(f"Gap, direct & \\multicolumn{{2}}{{c}}{{{p(g['no_insertion']['answered'])}}} & {p(g['similar_insertion']['answered'])} & {p(g['dissimilar_insertion']['answered'])} \\\\")
lines += [r"\bottomrule", r"\end{tabular}"]
(HERE / "tables" / "baseline.tex").write_text("\n".join(lines) + "\n")
print("ok")
