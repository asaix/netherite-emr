import ast
import csv
import json
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent
T = OUT / "tables"
rows = []


def add(loc, text, rep, rec, src, status=None, note=""):
    if status is None:
        status = "reproduced" if str(rep) == str(rec) else "differs"
    rows.append({"claim_id": f"C{len(rows) + 1:03d}", "location": loc, "claim_text": text, "reported_value": rep, "recomputed_value": rec, "source_path": src, "status": status, "note": note})


NM = {"English direct": "English direct", "English CoT": "English CoT", "Hindi direct": "Hindi direct", "Hindi CoT": "Hindi CoT", "Hindi CLP": "Hindi CLP", "Hindi en-CoT": "Hindi en-CoT"}
C1 = {
    "date_addition": [85.6, 98.0, 82.8, 85.1, 92.7, 95.7, 10.7, 12.9, 3.1], "date_subtraction": [86.0, 95.2, 84.8, 66.0, 86.9, 94.0, 28.0, 9.2, 7.1],
    "date_duration": [84.0, 99.3, 78.9, 88.3, 92.7, 97.7, 9.5, 18.8, 5.1], "date_recurrence": [22.1, 90.3, 2.8, 20.1, 27.0, 70.3, 50.2, 67.5, 43.4],
    "day_of_week": [14.9, 69.5, 15.2, 21.0, 31.8, 52.5, 31.5, 37.3, 20.7], "interval_date": [43.2, 50.7, 46.8, 23.9, 35.3, 44.1, 20.3, -2.7, 8.8],
    "time_addition": [70.5, 95.9, 75.6, 73.5, 88.2, 92.6, 19.2, 17.0, 4.4], "time_subtraction": [64.7, 97.7, 64.9, 75.2, 90.1, 95.7, 20.5, 30.8, 5.6],
    "time_duration": [65.7, 98.9, 44.7, 80.1, 86.7, 98.1, 18.1, 53.5, 11.5], "all": [59.7, 88.9, 55.2, 59.4, 70.3, 82.9, 23.5, 27.7, 12.6]}
d = pd.read_csv(T / "c1_by_task.csv").set_index("task")
cols = list(NM) + ["d Hindi CoT", "d Hindi direct", "d Hindi CLP"]
for t, vals in C1.items():
    for c, v in zip(cols, vals):
        add("Table C1", f"{t}: {c}", v, float(d.loc[t, c]), "responses/{standard,clp,en-cot}; tables/c1_by_task.csv")
    if t != "all":
        for ref in ("Hindi CoT", "Hindi direct", "Hindi CLP"):
            sig = float(d.loc[t, f"holm {ref}"]) < .05
            exp = not (t == "interval_date" and ref == "Hindi direct")
            add("Table C1", f"{t}: en-CoT vs {ref} Holm significance mark", exp, sig, "tables/c1_by_task.csv", note=f"Holm p={float(d.loc[t, f'holm {ref}']):.3g}")
C2 = {"short": [93.2, 69.5, 77.2, 83.0, 23.6, (20.6, 26.7), 10.2, (7.8, 12.7)], "medium": [91.6, 65.4, 75.7, 84.9, 26.2, (23.3, 29.0), 6.7, (4.6, 8.7)], "long": [89.3, 60.4, 71.3, 84.4, 28.9, (25.7, 32.2), 4.9, (3.1, 6.8)],
      "very_long": [87.2, 53.7, 65.8, 83.5, 33.5, (30.1, 37.0), 3.6, (1.5, 6.1)], "very_very_long": [82.9, 47.9, 61.5, 78.5, 35.0, (31.5, 38.4), 4.3, (1.9, 6.6)]}
d = pd.read_csv(T / "c2_by_level.csv").set_index("level")
for lv, v in C2.items():
    for c, x in zip(("English CoT", "Hindi CoT", "Hindi CLP", "Hindi en-CoT"), v[:4]):
        add("Table C2", f"{lv}: {c}", x, float(d.loc[lv, c]), "tables/c2_by_level.csv")
    add("Table C2", f"{lv}: En CoT - Hi CoT", v[4], float(d.loc[lv, "gap Hindi CoT"]), "tables/c2_by_level.csv")
    add("Table C2", f"{lv}: En CoT - Hi CoT CI", v[5], ast.literal_eval(d.loc[lv, "ci2000seed0 Hindi CoT"]), "tables/c2_by_level.csv", note=f"seed 0, B=2000. Use B=10000: {d.loc[lv, 'ci10000 Hindi CoT']}. Part A prints a different draw.")
    add("Table C2", f"{lv}: En CoT - en-CoT", v[6], float(d.loc[lv, "gap Hindi en-CoT"]), "tables/c2_by_level.csv")
    add("Table C2", f"{lv}: En CoT - en-CoT CI", v[7], ast.literal_eval(d.loc[lv, "ci2000seed0 Hindi en-CoT"]), "tables/c2_by_level.csv", note=f"seed 0, B=2000. Use B=10000: {d.loc[lv, 'ci10000 Hindi en-CoT']}")
C3 = {"English direct": [60.6, 59.9, 58.6, .7, (-1.0, 2.6), 2.0, (.3, 3.8)], "English CoT": [89.3, 88.1, 89.2, 1.2, (-.4, 2.7), .2, (-1.4, 1.7)], "Hindi direct": [56.0, 54.9, 54.6, 1.2, (-.5, 2.9), 1.5, (-.3, 3.2)],
      "Hindi CoT": [60.2, 58.9, 59.1, 1.3, (-.9, 3.5), 1.2, (-.9, 3.3)], "Hindi CLP": [69.3, 69.3, 72.3, -.1, (-2.2, 2.0), -3.1, (-5.1, -1.2)], "Hindi en-CoT": [84.1, 81.0, 83.6, 3.2, (1.3, 4.9), .6, (-1.2, 2.3)]}
d = pd.read_csv(T / "c4_drops.csv")
d = d[d.conv == "answered"].set_index(["cond", "ins"])
for c, v in C3.items():
    s_, u = d.loc[(c, "similar_insertion")], d.loc[(c, "dissimilar_insertion")]
    add("Table C3", f"{c}: none", v[0], float(s_["none"]), "tables/c4_drops.csv")
    add("Table C3", f"{c}: time-related", v[1], float(s_["with"]), "tables/c4_drops.csv")
    add("Table C3", f"{c}: unrelated", v[2], float(u["with"]), "tables/c4_drops.csv")
    add("Table C3", f"{c}: drop time-related", v[3], float(s_["drop"]), "tables/c4_drops.csv")
    add("Table C3", f"{c}: drop time-related CI", v[4], ast.literal_eval(s_["ci_seed0_2000"]), "tables/c4_drops.csv", note=f"B=10000: {s_['ci']}")
    add("Table C3", f"{c}: drop unrelated", v[5], float(u["drop"]), "tables/c4_drops.csv")
    add("Table C3", f"{c}: drop unrelated CI", v[6], ast.literal_eval(u["ci_seed0_2000"]), "tables/c4_drops.csv", note=f"B=10000: {u['ci']}")
C4 = {"English CoT": ("own", 17.3, 8.9, 11.0, 6.3, (.61, .39, .93), (1.63, .9, 2.96)), "Hindi CoT": ("own", 34.0, 10.3, 28.7, 1.9, (.85, .68, 1.07), (1.3, 1.0, 1.7)), "Hindi en-CoT": ("both", 22.0, 9.3, 17.0, 5.5, (.82, .59, 1.13), (.91, .58, 1.43))}
d = pd.read_csv(T / "c4_mentions.csv")
for c, v in C4.items():
    w = d[(d.cond == c) & (d.words == v[0])].set_index("ins")
    add("Table C4", f"{c}: mention time-related", v[1], float(w.loc["similar", "mention"]), "tables/c4_mentions.csv")
    add("Table C4", f"{c}: placebo time-related", v[2], float(w.loc["similar", "placebo"]), "tables/c4_mentions.csv")
    add("Table C4", f"{c}: mention unrelated", v[3], float(w.loc["dissimilar", "mention"]), "tables/c4_mentions.csv")
    add("Table C4", f"{c}: placebo unrelated", v[4], float(w.loc["dissimilar", "placebo"]), "tables/c4_mentions.csv")
    add("Table C4", f"{c}: OR time-related", v[5], ast.literal_eval(w.loc["similar", "OR"]), "tables/c4_mentions.csv")
    add("Table C4", f"{c}: OR unrelated", v[6], ast.literal_eval(w.loc["dissimilar", "OR"]), "tables/c4_mentions.csv")
C5 = {"Hindi direct": (6743, 3143, 2138, 881, 581, .28, [.14, .42], 43), "Hindi CoT": (6490, 3778, 557, 2000, 155, .07, [-.01, .12], 35), "Hindi en-CoT": (6395, 5033, 370, 672, 320, .02, [-.03, .19], 34)}
d = pd.read_csv(T / "c5_agreement.csv")
for c, v in C5.items():
    ref = "English direct" if c == "Hindi direct" else "English CoT"
    w = d[(d.cond == c) & (d.ref == ref)].iloc[0]
    for k, x in zip(("pairs", "both right", "both wrong", "only ref", "only cond", "median phi"), v[:6]):
        add("Table C5", f"{c}: {k}", x, float(w[k]) if k == "median phi" else int(w[k]), "tables/c5_agreement.csv")
    add("Table C5", f"{c}: phi IQR", v[6], ast.literal_eval(w["iqr"]), "tables/c5_agreement.csv", note="Interpretation fails; see analysis.md")
    add("Table C5", f"{c}: defined phi cells of 45", v[7], int(w["phi cells"]), "tables/c5_agreement.csv")
P = [
    ("C.1", "en-CoT cites Shi et al., 2023", "Shi et al. 2023", "EN-COT there is few-shot on MGSM, no Hindi", "citations.md", "overclaimed", "Say adapted from; ours is zero-shot instruction, different task and model."),
    ("C.1", "Single turn, thinking off, temperature 0, up to 4,096 tokens", "as stated", "all 6750 requests match", "responses/en-cot", "reproduced", ""),
    ("C.1", "Day-of-week requested as Hindi names, scored by weekday", "as stated", "prompt asks Hindi name; scorer maps weekday names", "responses/en-cot; build.py", "reproduced", "The same prompt also says write the entire response in English."),
    ("C.1", "Questions 0 to 49, 2,250 questions, 6,750 responses", "2250/6750", "2250/6750", "responses/en-cot", "reproduced", ""),
    ("C.1", "Same 2,250 questions as CLP", "same", "same qids", "responses/clp", "reproduced", ""),
    ("C.1", "Pipeline and statistics same as Part A", "same", "Part A script missing", "experiments/2026-10-31_clp-analysis-rahul", "source_missing", "Numbers recomputed; CIs consistent with a different draw."),
    ("C.1", "99.9% of words in en-CoT reasoning are English", 99.9, "99.9 mean of ratios; 99.8 pooled", "numbers.json", "reproduced", "12.8% of traces contain some Devanagari."),
    ("C.2", "en-CoT vs Hindi CoT CI and pairs", "+23.5 [22.1, 24.9]; 1742/272", "+23.5 [22.1, 24.9]; 1742/272", "tables/c1_by_task.csv", "reproduced", "Each distractor: +23.9, +22.0, +24.5."),
    ("C.2", "en-CoT vs Hindi direct CI", "+27.7 [25.8, 29.5]", "+27.7 [25.8, 29.5] seed 0; [26.0, 29.5] B=10000", "tables/c1_by_task.csv", "reproduced", ""),
    ("C.2", "en-CoT vs CLP CI and pairs", "+12.6 [11.2, 13.8]; 1158/400", "+12.6 [11.2, 13.8] seed 0; [11.3, 13.9] B=10000; 1158/400", "tables/c1_by_task.csv", "reproduced", ""),
    ("C.2", "Beats Hindi CoT and CLP on all nine tasks after Holm", "9/9 and 9/9", "pooled 9/9 and 9/9; CLP by distractor 8, 6, 3 of 9", "tables/c1_task_by_distractor.csv", "overclaimed", "True only pooled over distractors and levels for CLP."),
    ("C.2", "Date subtraction 94.0 vs Hindi CoT 66.0", "94.0/66.0", "94.0/66.0", "tables/c1_by_task.csv", "reproduced", ""),
    ("C.2", "Interval date reaches 44.1, Hindi CoT 23.9, level with Hindi direct 46.8; not significant", "44.1/23.9/46.8; n.s.", "-2.7 [-7.6, +2.2], p=0.163; time-related -12.7 [-20.0, -5.6]", "tables/c1_interval_vs_direct.csv", "overclaimed", "Not equivalence; reverses at time-related and short."),
    ("C.2", "Biggest jumps recurrence 20.1 to 70.3, day of week 21.0 to 52.5", "as stated", "as stated", "tables/c1_by_task.csv", "reproduced", "By points, date subtraction +28.0 and others are smaller than these two."),
    ("C.2", "English CoT ahead by +6.0 [5.0, 7.0]", "+6.0 [5.0, 7.0]", "+6.0 [5.0, 7.0]", "tables/c1_headline_by_distractor.csv", "reproduced", "Strict +5.2 [4.2, 6.3]."),
    ("C.2", "Strict accuracy en-CoT, CLP, Hindi CoT", "80.8/69.9/59.0", "80.8/69.9/59.0", "tables/c1_cutoffs.csv", "reproduced", "English CoT strict 86.0."),
    ("C.2", "Counting unanswered as wrong does not change the picture", "no change", "direction holds; English gap 5.2; day of week gap 12.3", "tables/c1_by_task.csv", "reproduced", ""),
    ("C.2", "No Answer line 174, 43, 221; all cut off", "174/43/221", "174/43/221; all finish_reason=length", "tables/c1_cutoffs.csv", "reproduced", "Reads as a task-mix and trace-length effect, not robustness."),
    ("C.3", "Gap shrinks as questions get harder", "+10.2 to +4.3", "+5.9 [2.3, 9.5]; no k<=2 +0.8 [-2.5, 4.1]", "tables/c3_trend.csv; tables/c3_trend_k_removed.csv", "overclaimed", "Recurrence-driven; significant only pooled."),
    ("C.3", "Hindi CoT gap grows +23.6 to +35.0", "+23.6/+35.0", "+23.6/+35.0; difference -11.4 [-16.0, -6.7]", "tables/c3_trend.csv", "reproduced", ""),
    ("C.3", "CLP gap grows +16.0 to +21.4 (Part A)", "+16.0/+21.4", "+16.0/+21.4; -5.4 [-9.7, -1.0]; strict -2.1 [-6.4, 2.1]", "tables/c3_trend.csv", "reproduced", "Not significant under strict scoring."),
    ("C.3", "en-CoT stays between 78.5 and 84.9", "78.5-84.9", "78.5-84.9", "tables/c2_by_level.csv", "reproduced", ""),
    ("C.3", "Weakest against English at short, mostly recurrence k = 1, 2", "as stated", "short gap 10.2; contribution 5.8 of 10.2 from recurrence; no k<=2 gap 5.1", "tables/c3_gap_contribution_points.csv", "reproduced", ""),
    ("C.4", "Only condition that loses accuracy with time-related distractor", "only", "five of six point estimates positive; strict English CoT +2.7, Holm 0.016", "tables/c4_drops.csv", "overclaimed", "Only significant on answered-only."),
    ("C.4", "Drop +3.2 [1.3, 4.9]", "+3.2 [1.3, 4.9]", "+3.2 [1.3, 4.9] seed 0; [1.3, 5.0] B=10000; McNemar 223/163, Holm12 0.029", "tables/c4_drops.csv", "reproduced", "Against direct +2.0 [-0.5, +4.5]."),
    ("C.4", "Unrelated distractor makes no difference", "no difference", "+0.6 [-1.2, 2.3]", "tables/c4_drops.csv", "reproduced", ""),
    ("C.4", "One possibility: Hindi distractor carried into the English reasoning", "hypothesis", "one recurrence sentence: en-CoT 24/44 cut-offs vs 1/44, but English CoT 29/44 vs 2/44 on its English version", "tables/c4_similar_by_sentence.csv", "unverifiable", "Stated as untested; the sentence effect is not specific to Hindi."),
    ("C.4", "Table C4 uses the mid-report rule; en-CoT adds English words", "stated with extension", "Hindi-only rule gives 3.6 and 0.4", "tables/c4_mentions.csv", "overclaimed", "All en-CoT signal comes from the English list."),
    ("C.4", "en-CoT talks about the distractor about half as often as Hindi CoT", "half", "net 12.7/23.8=0.53; 11.5/26.8=0.43", "tables/c4_mentions.csv", "overclaimed", "Different word lists; English CoT like-for-like net is 8.4 and 4.7."),
    ("C.4", "Net mentions 12.7, 11.5, 23.7, 26.8", "12.7/11.5/23.7/26.8", "12.7/11.5/23.8/26.8", "tables/c4_mentions.csv", "differs", "23.7 is from rounded values or the union list."),
    ("C.4", "Mentioning is not linked to wrong answers", "OR 0.82, 0.91", "intervals reach 0.59 and 0.58", "tables/c4_mentions.csv", "overclaimed", "A moderate harm isn't excluded."),
    ("C.5", "Still fails on different questions; barely related", "phi 0.02", "MH OR 1.99 [1.62, 2.46]; within-cell phi 0.116 [0.079, 0.153]; self-agreement 0.06-0.10", "tables/c5_agreement.csv; tables/c5_self_ceiling.csv", "overclaimed", "phi undefined in 11 cells."),
    ("C.5", "Off by one 42.3, 21.2, 52.3, CLP 26.9", "42.3/21.2/52.3/26.9", "42.3/21.2/52.3/26.9", "tables/c5_error_profile.csv", "reproduced", "Task-standardised 44.7/23.5/49.1/31.4."),
    ("C.5", "Verification 74.2, 1.3, 86.1", "74.2/1.3/86.1", "74.2/1.3/86.1", "tables/c5_error_profile.csv", "reproduced", "Wider Hindi regex 3.5."),
    ("C.5", "Median completion tokens 311, 212, 353, 487", "311/212/353/487", "311/212/353/487", "tables/c5_error_profile.csv", "reproduced", "Answered only."),
    ("C.6", "Day of week 52.5, 21.0, 69.5", "52.5/21.0/69.5", "52.5/21.0/69.5", "tables/c1_by_task.csv", "reproduced", ""),
    ("C.6", "One day late 24.0, 25.3, 16.2", "24.0/25.3/16.2", "24.0/25.3/16.2", "tables/c6_dow_mechanism.csv", "reproduced", ""),
    ("C.6", "Same slip English CoT makes, counting 1 January", "asserted", "late traces: doy without doy-1 77.8 and 83.3; correct 13.0 and 3.2; hand read 11/12 and 10/12", "tables/c6_dow_mechanism.csv; tables/c6_dow_sample_traces.json", "reproduced", "Counts the anchor day; anchor is not always 1 January."),
    ("C.6", "Backwards 8.3, 9.0, 0.4", "8.3/9.0/0.4", "8.3/9.0/0.4", "tables/c6_recurrence_by_k.csv", "reproduced", ""),
    ("C.6", "Comes from reading the Hindi question, not reasoning in Hindi", "causal", "same k=1 rate across reasoning languages; template not separated", "tables/c6_recurrence_by_k.csv", "overclaimed", "No corrected-template run."),
    ("C.6", "Model reads excluding today, 1st occurrence as before today; quoted trace", "quote", "verbatim in 1 record; 87% of k=1 mirror traces say before", "tables/c6_trace_glosses.csv", "reproduced", "short/date_recurrence_hi_IN/43/no_insertion/en-cot"),
    ("C.6", "Errors sit in k = 1 and k = 2 cells", "k=1,2", "backwards: k=1 only (55/58); k=2 is 0.8%", "tables/c6_recurrence_by_k.csv", "differs", "k=2 is a separate one-step-short error."),
    ("C.7", "+23.5, +27.7, +12.6 on every task", "every task", "direct is not on every task: interval -2.7", "tables/c1_by_task.csv", "differs", "Bullet groups three comparisons; interval vs direct fails."),
    ("C.7", "Within 6.0 and unlike CLP the gap shrinks", "as stated", "see C.3", "tables/c3_trend.csv", "overclaimed", ""),
    ("C.7", "What is left comes mostly from backwards recurrence and one-day-late", "mostly", "about 0.9 + 0.9 of 6.0 points, about 30%", "tables/c5_error_profile.csv; numbers.json", "overclaimed", "55 and 84 of 672 only-English-right pairs."),
    ("C.7", "Errors and habits look more like English CoT's", "asserted", "off-by-one and verification hold; length holds", "tables/c5_error_profile.csv", "reproduced", ""),
    ("C.7", "Small but significant 3.2 points", "3.2", "3.2, Holm 0.029; not against direct", "tables/c4_drops.csv", "overclaimed", "Attribution to the distractor beyond baseline noise is not shown."),
    ("C.7", "One English turn beats CLP's two turns", "as stated", "+12.6 [11.3, 13.9]", "tables/c1_by_task.csv", "reproduced", "Reason offered is flagged untested; verification mediation holds only for day of week."),
    ("C.8", "2,250 of 6,750 questions", "2250/6750", "2250/6750", "dataset; responses", "reproduced", "No representativeness problem found at table resolution."),
    ("C.8", "174 unanswered; strict 80.8", "174/80.8", "174/80.8", "tables/c1_cutoffs.csv", "reproduced", ""),
    ("App C", "Gap shrinks with difficulty rated Strong", "Strong", "Moderate at best", "tables/c3_trend_k_removed.csv", "overclaimed", ""),
    ("App C", "What's left comes from reading Hindi plus a shared slip rated Moderate", "Moderate", "about 30% of the gap", "numbers.json", "overclaimed", ""),
    ("App C", "Fails on different questions rated Moderate", "Moderate", "Should be withdrawn", "tables/c5_agreement.csv", "overclaimed", ""),
    ("App C", "Time-related distractor slightly hurts, Moderate", "Moderate", "Holds with caveats", "tables/c4_drops.csv", "reproduced", ""),
]
for loc, text, rep, rec, src, status, note in P:
    add(loc, text, rep, rec, src, status, note)
with open(OUT / "claims.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
x = pd.DataFrame(rows)
print(x.status.value_counts())
print(x[x.status == "differs"][["location", "claim_text", "reported_value", "recomputed_value"]].to_string())
