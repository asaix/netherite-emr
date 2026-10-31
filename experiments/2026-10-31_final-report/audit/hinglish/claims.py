import csv

SRC_H = "responses/hinglish/; responses/standard/"
SRC_E = "responses/en-cot/; responses/hinglish/; responses/standard/"
MISSING = "experiments/2026-10-31_hinglish-analysis-aayush/ (FINDINGS.md); report/make_report.py"
rowsC = []
cid = [0]


def add(loc, text, rep, rec, src, status, note=""):
    cid[0] += 1
    rowsC.append({"claim_id": f"H{cid[0]:03d}", "location": loc, "claim_text": text, "reported_value": rep, "recomputed_value": rec, "source_path": src, "status": status, "note": note})


def num(loc, text, rep, val, src=SRC_H, note="", tol=0.0551):
    add(loc, text, f"{rep:g}", f"{val:.2f}", src, "reproduced" if abs(rep - val) <= tol else "differs", note)


TN = {"date_addition": "Date addition", "date_subtraction": "Date subtraction", "date_duration": "Date duration", "date_recurrence": "Date recurrence", "day_of_week": "Day of week", "interval_date": "Interval date", "time_addition": "Time addition", "time_subtraction": "Time subtraction", "time_duration": "Time duration", "all": "All tasks"}
T1 = {
    "en_US": {"date_addition": (85.6, 98.0, 87.3, 1.7, 0), "date_subtraction": (86.0, 95.2, 70.7, -15.3, 1), "date_duration": (84.0, 99.3, 92.9, 8.9, 1), "date_recurrence": (22.1, 90.3, 53.8, 31.7, 1), "day_of_week": (14.9, 69.5, 34.7, 19.8, 1), "interval_date": (43.2, 50.7, 38.5, -4.7, 0), "time_addition": (70.5, 95.9, 82.9, 12.4, 1), "time_subtraction": (64.7, 97.7, 85.3, 20.6, 1), "time_duration": (65.7, 98.9, 90.0, 24.3, 1), "all": (59.7, 88.9, 70.9, 11.2, 1)},
    "hi_IN": {"date_addition": (82.8, 85.1, 85.9, 3.1, 0), "date_subtraction": (84.8, 66.0, 71.0, -13.8, 1), "date_duration": (78.9, 88.3, 82.8, 3.8, 0), "date_recurrence": (2.8, 20.1, 18.9, 16.1, 1), "day_of_week": (15.2, 21.0, 23.5, 8.3, 1), "interval_date": (46.8, 23.9, 23.6, -23.2, 1), "time_addition": (75.6, 73.5, 72.3, -3.3, 0), "time_subtraction": (64.9, 75.2, 74.2, 9.3, 1), "time_duration": (44.7, 80.1, 80.9, 36.3, 1), "all": (55.2, 59.4, 59.4, 4.2, 1)},
}
for lang, d in T1.items():
    for task, (dr, st_, hi, de, star) in d.items():
        r = N["table1"][f"{lang}/{task}"]
        loc = f"Table 1, {lang}, {TN[task]}"
        num(loc, "Direct accuracy, answered-only", dr, r["direct_answered"], note=f"strict {r['direct_strict']}")
        num(loc, "Standard CoT accuracy, answered-only", st_, r["std_answered"], note=f"strict {r['std_strict']}")
        num(loc, "Hinglish CoT accuracy, answered-only", hi, r["hing_answered"], note=f"strict {r['hing_strict']}")
        num(loc, "Delta Hinglish minus direct, points", de, r["dhing_answered"], note=f"McNemar {r['hd_a_only']} vs {r['hd_b_only']}")
        p = r["hd_p_holm18"] if task != "all" else r["hd_p_mcnemar"]
        ok = (p < 0.05) == bool(star)
        add(loc, "Significance mark on delta (McNemar, Holm over 18; uncorrected for pooled)", "star" if star else "no star", f"p={p:.2g}", SRC_H, "reproduced" if ok else "differs")
for lang in LANGS:
    for ins in INS:
        pass
g = N["gains"]
hf = N["ci_seed_order_check"]["hinglish_first"]


def tri(loc, text, rep, est, lo, hi, note="", src=SRC_H):
    ok = all(abs(a - b) <= 0.0551 for a, b in zip(rep, (est, lo, hi)))
    add(loc, text, f"{rep[0]:+g} [{rep[1]:+g}, {rep[2]:+g}]", f"{est:+.2f} [{lo:+.2f}, {hi:+.2f}]", src, "reproduced" if ok else "differs", note)


h1 = "Standard-column CIs use seed 0 with questions in standard-file order; Hinglish-column CIs reproduce only with questions in Hinglish-file order, a Monte Carlo detail, not a substantive change. "
tri("Table 2", "CoT gain, English, standard", (29.2, 27.5, 30.9), g["en_US/std/answered"]["diff"], g["en_US/std/answered"]["lo"], g["en_US/std/answered"]["hi"], f"Strict {g['en_US/std/strict']['diff']}.")
tri("Table 2", "CoT gain, English, Hinglish", (11.2, 9.6, 12.8), g["en_US/hing/answered"]["diff"], *hf["gain_en"], h1 + f"Strict {g['en_US/hing/strict']['diff']}.")
tri("Table 2", "CoT gain, Hindi, standard", (4.2, 2.6, 5.9), g["hi_IN/std/answered"]["diff"], g["hi_IN/std/answered"]["lo"], g["hi_IN/std/answered"]["hi"], f"Strict {g['hi_IN/std/strict']['diff']}.")
tri("Table 2", "CoT gain, Hindi, Hinglish", (4.2, 2.5, 5.9), g["hi_IN/hing/answered"]["diff"], *hf["gain_hi"], h1 + f"Strict {g['hi_IN/hing/strict']['diff']}.")
G = N["gap"]
for lvl, s1, s2 in (("short", (28.2, 23.9, 32.8), (17.5, 13.1, 21.9)), ("very_long", (40.6, 35.7, 45.3), (8.3, 4.0, 12.3))):
    k = f"std/five/{lvl}/answered"
    tri("Table 2", f"EN-HI gap, five date tasks, {lvl}, standard", s1, G[k]["diff"], G[k]["lo"], G[k]["hi"], f"Strict {G[f'std/five/{lvl}/strict']['diff']}. Five tasks are addition, subtraction, duration, recurrence, day of week; report does not name them.")
    k = f"hing/five/{lvl}/answered"
    tri("Table 2", f"EN-HI gap, five date tasks, {lvl}, Hinglish", s2, G[k]["diff"], *hf[f"gap_{lvl}"], h1 + f"Strict {G[f'hing/five/{lvl}/strict']['diff']}.")
T = N["tokens"]
num("Table 2", "Median completion tokens, English Q, standard", 353, T["cot/en_US"]["median_answered"], note=f"Answered only; all responses {T['cot/en_US']['median_all']}.")
num("Table 2", "Median completion tokens, English Q, Hinglish", 233, T["hinglish/en_US"]["median_answered"])
num("Table 2", "Median completion tokens, Hindi Q, standard", 212, T["cot/hi_IN"]["median_answered"])
num("Table 2", "Median completion tokens, Hindi Q, Hinglish", 223, T["hinglish/hi_IN"]["median_answered"])
U = N["unanswered"]
for k, rep, lab in (("cot/en_US", 3.3, "English standard"), ("hinglish/en_US", 0.8, "English Hinglish"), ("cot/hi_IN", 0.6, "Hindi standard"), ("hinglish/hi_IN", 0.4, "Hindi Hinglish")):
    num("Table 2", f"Cut off before answering, {lab} (%)", rep, U[k]["pct"], note=f"{U[k]['n']} of 6,750; all are finish_reason=length.")
P = N["penalty"]
for lang, ins, s1, s2 in (("en_US", "similar_insertion", (0.4, -1.9, 2.7), (0.1, -2.6, 2.9)), ("hi_IN", "similar_insertion", (0.2, -2.6, 2.9), (0.8, -1.9, 3.6)), ("en_US", "dissimilar_insertion", (-1.9, -4.2, 0.4), (-3.8, -6.5, -1.1)), ("hi_IN", "dissimilar_insertion", (-0.3, -3.0, 2.4), (1.6, -1.1, 4.3))):
    a = P[f"{lang}/std/{ins}/answered"]
    b = P[f"{lang}/hing/{ins}/answered"]
    tri("Table 2", f"CoT distraction penalty, {lang}, {ins}, standard", s1, a["did"], a["lo"], a["hi"], f"Strict {P[f'{lang}/std/{ins}/strict']['did']} [{P[f'{lang}/std/{ins}/strict']['lo']}, {P[f'{lang}/std/{ins}/strict']['hi']}].")
    tri("Table 2", f"CoT distraction penalty, {lang}, {ins}, Hinglish", s2, b["did"], *hf[f"{lang}/{ins}"], h1 + f"Strict {P[f'{lang}/hing/{ins}/strict']['did']}.")
T3 = {("en_US", "roman"): (4109, 68.0, 89.3, 138, 1013), ("en_US", "plain"): (2374, 79.1, 88.5, 103, 327), ("hi_IN", "roman"): (1631, 64.1, 66.9, 187, 233), ("hi_IN", "plain"): (166, 68.7, 60.2, 30, 16), ("hi_IN", "devanagari"): (4882, 57.8, 57.1, 732, 696)}
t3m = {(r["language"], r["style"]): r for r in N["table3"]}
wn = "Function-word list reconstructed: the report prints five words and the script is missing. A 60-word list reproduces every accuracy and discordant count; n differs by 3 of 6,483 on the English rows."
for (l, s), (n_, h_, st_, ho, so) in T3.items():
    r = t3m[(l, s)]
    loc = f"Table 3, {l}, {s}"
    add(loc, "n of paired traces", str(n_), str(r["n"]), SRC_H, "reproduced" if n_ == r["n"] else "differs", wn + " n counts pairs where both responses answered, which the caption does not say.")
    num(loc, "Hinglish accuracy", h_, r["hing"], note=wn)
    num(loc, "Standard accuracy on same items", st_, r["std"], note=wn)
    add(loc, "Pairs where only Hinglish is right", str(ho), str(r["h_only"]), SRC_H, "reproduced" if ho == r["h_only"] else "differs")
    add(loc, "Pairs where only standard is right", str(so), str(r["s_only"]), SRC_H, "reproduced" if so == r["s_only"] else "differs")
F2 = [("en_US", "very_very_long", "Standard CoT", 83), ("en_US", "very_very_long", "Hinglish CoT", 58), ("en_US", "very_very_long", "Direct", 35), ("hi_IN", "very_very_long", "Hinglish CoT", 48), ("hi_IN", "very_very_long", "Direct", 30)]
for l, d, c, v in F2:
    x = [r for r in fig2 if r["language"] == l and r["difficulty"] == d and r["condition"] == c and r["convention"] == "answered"][0]
    num("Figure 2 label", f"{c}, {l}, very very long", v, x["accuracy"], tol=0.51, note="Printed as integer.")
LV = {(r["language"], r["difficulty"]): r for r in N["level_diff"]}
num("Figure 2 caption", "Hinglish loses to English CoT at short", -10, LV[("en_US", "short")]["diff"], tol=0.51, note=f"Strict {LV[('en_US', 'short')]['diff_strict']}.")
num("Figure 2 caption", "Hinglish loses to English CoT at very very long", -25, LV[("en_US", "very_very_long")]["diff"], tol=0.51, note=f"Strict {LV[('en_US', 'very_very_long')]['diff_strict']}, so the rise is smaller under strict scoring.")
add("Figure 2 caption", "For Hindi questions, Hinglish and Hindi CoT coincide at every level", "coincide", "; ".join(f"{d}: {LV[('hi_IN', d)]['diff']:+.2f} [{LV[('hi_IN', d)]['lo']:+.2f}, {LV[('hi_IN', d)]['hi']:+.2f}]" for d in DIFFS), SRC_H, "overclaimed", "Four of five levels are within noise. Short is -3.05 with uncorrected p=0.03; Holm over ten level tests gives p=0.15.")
F3 = N["style"]
num("Figure 3", "English Q, Roman Hinglish share (%)", 63, F3["en_US"]["roman_pct"], tol=0.51)
num("Figure 3", "English Q, plain English share (%)", 37, F3["en_US"]["plain_pct"], tol=0.51)
num("Figure 3", "Hindi Q, Roman Hinglish share (%)", 24, F3["hi_IN"]["roman_pct"], tol=0.51, note=f"Uses Devanagari share under 10%. Under the rule as printed (no Devanagari) it is {F3['hi_IN']['roman_text_pct']}.")
num("Figure 3", "Hindi Q, Devanagari mix share (%)", 73, F3["hi_IN"]["devanagari_pct"], tol=0.51)
F4_ROM = dict(zip(TASKS, (-12.04, -28.47, -13.96, -40.75, -42.95, -16.33, -15.53, -14.98, -12.93)))
F4_PL = dict(zip(TASKS, (-6.21, -12.30, -1.13, -25.19, -25.00, -3.77, -8.24, -3.66, -3.83)))
for r in N["fig4"]:
    t = r["task"]
    num("Figure 4 bar", f"{TN[t]}, Roman Hinglish minus standard (points)", round(F4_ROM[t], 2), r["roman_diff"], tol=0.2, note="Reported value measured from PDF vector coordinates (36.82 units per 10 points); no printed label. Tolerance 0.2 points.")
    num("Figure 4 bar", f"{TN[t]}, plain English minus standard (points)", round(F4_PL[t], 2), r["plain_diff"], tol=0.2, note="Reported value measured from PDF vector coordinates; no printed label. Tolerance 0.2 points.")
add("Figure 1", "Bars per task for direct, standard and Hinglish", "unlabelled bars", "see fig_data/fig1_accuracy_by_task.csv", SRC_H, "reproduced", "Same values as Table 1.")
tb = N["table1"]
add("Figure 1 caption", "For English questions, Hinglish falls well short of standard CoT on every task", "every task", "; ".join(f"{t}: {tb['en_US/' + t]['hs_diff_pairs']:+.1f}" for t in TASKS), SRC_H, "overclaimed", "Direction and significance hold on all nine. 'Well short' is loose for date duration (-6.4) and time duration (-8.8).")
add("Figure 1 caption", "For Hindi questions, the two CoT conditions are close everywhere", "close everywhere", f"date subtraction {tb['hi_IN/date_subtraction']['hs_diff_pairs']:+.2f}; date duration {tb['hi_IN/date_duration']['hs_diff_pairs']:+.2f}", SRC_H, "overclaimed", "Two tasks move about 5 points, in opposite directions.")
add("Figure 4 caption / Section 3.4", "Roman Hinglish traces lose more than plain-English traces on every task; ordering holds in all nine tasks", "9 of 9", f"9 of 9; cell-adjusted difference in every task excludes 0 after Holm; holds in each distractor condition ({N['fig4_by_distractor']}) and all 48 threshold pairs", SRC_H, "reproduced", "Descriptive: the model chooses the style. Smallest task difference is date addition, -5.75 [-11.06, -0.45].")
add("Section 1", "Sarvam-105B gains far more from CoT on English than on Hindi", "true", f"gain {g['en_US/std/answered']['diff']} vs {g['hi_IN/std/answered']['diff']}", SRC_H, "reproduced")
add("Section 1", "Hindi CoT hurts on date subtraction and interval date", "true", f"{tb['hi_IN/date_subtraction']['dstd_answered']}, {tb['hi_IN/interval_date']['dstd_answered']}; Holm p<0.001", SRC_H, "reproduced")
add("Section 1", "Hinglish is how many Indian users actually write", "no number", "not testable from project data", "none", "unverifiable", "No citation given. Winata et al. 2026 (fetched) describe Hindi-English mixing as predominantly Latin script in informal digital text. See citations.md.")
add("Section 2", "Prompt quotation", "ends 'Do not write in Devanagari script.'", "actual prompt continues '(the final \"Answer:\" line is the only exception).'", "experiments/2026-10-30-hinglish-aayush/prompt.yaml", "differs", "Quotation is truncated without an ellipsis.")
add("Section 2", "The answer-line format is the same as in the standard runs", "same", "answer-line sentence identical; 'Write your entire response in {language}.' is absent from the Hinglish template", "experiments/2026-10-30-hinglish-aayush/prompt.yaml; config/prompt.yaml", "overclaimed", "The wider template differs. The standard prompt's language lock ('do not switch to another language') is also absent, so more than the reasoning language changes.")
add("Section 2", "First 50 questions of every task and difficulty: 2,250 questions", "2250", str(N["questions"]), SRC_H, "reproduced", f"IDs match the first 50 dataset keys: {N['unique_questions']['all_ids_match']}; {N['unique_questions']['total_unique']} unique question texts.")
add("Section 2", "13,500 Hinglish responses", "13500", str(N["counts"]["hinglish/en_US"] + N["counts"]["hinglish/hi_IN"]), "responses/hinglish/; experiments/2026-10-30-hinglish-aayush/output/results.json", "reproduced", "errors.json is empty.")
add("Section 2", "Question text and gold answers identical to standard runs", "identical", f"{N['integrity']['prompt_tails_differ']} question-text differences, {N['integrity']['gold_differ']} gold differences", SRC_H, "reproduced")
add("Section 2", "Same settings: Sarvam-105B, thinking off, temperature 0, 4,096 max tokens", "same", json.dumps(N["integrity"]["settings"]["hinglish"]), SRC_H, "reproduced", f"Run dates differ: standard {N['run_times']['cot']}, Hinglish {N['run_times']['hinglish']}. The report does not mention this.")
add("Section 2", "Intervals are 95% cluster bootstraps over questions, B=2000", "method", "reproduced with seed 0", SRC_H, "reproduced")
add("Section 2", "Task-level significance: exact McNemar, Holm over 18 tests", "method", "all 18 stars reproduced", SRC_H, "reproduced", "McNemar treats three distractor variants of a question as independent pairs; a question-level sign-flip test with Holm gives the same 18 decisions.")
sec = "Section 3.1"
num(sec, "English CoT accuracy falls from", 88.9, tb["en_US/all"]["std_answered"], note=f"Strict {tb['en_US/all']['std_strict']}.")
num(sec, "English CoT accuracy falls to", 70.9, tb["en_US/all"]["hing_answered"], note=f"Strict {tb['en_US/all']['hing_strict']}.")
num(sec, "Gain over direct shrinks from", 29.2, g["en_US/std/answered"]["diff"])
num(sec, "Gain over direct shrinks to", 11.2, g["en_US/hing/answered"]["diff"])
add(sec, "Hinglish CoT does worse than English CoT on every task", "every task", "9 of 9; McNemar Holm p<0.001 on all; question-level sign-flip Holm p<=0.001; strict also 9 of 9", SRC_H, "reproduced", "All 27 task-by-distractor cells are negative; 25 of 27 survive Holm within a distractor condition. Interval date is not significant with no distractor (Holm p=0.28) or a similar one (p=1.0).")
for t, a, b in (("day_of_week", 69.5, 34.7), ("date_recurrence", 90.3, 53.8), ("date_subtraction", 95.2, 70.7)):
    num(sec, f"Largest losses: {TN[t]}, standard", a, tb[f"en_US/{t}"]["std_answered"])
    num(sec, f"Largest losses: {TN[t]}, Hinglish", b, tb[f"en_US/{t}"]["hing_answered"], note=f"Strict loss {tb[f'en_US/{t}']['hs_diff_strict']}.")
add(sec, "The largest losses are day of week, date recurrence and date subtraction", "these three", "answered-only top three confirmed; strict order recurrence -32.0, day of week -25.2, subtraction -24.4", SRC_H, "reproduced", "Day of week loss shrinks by over a quarter under strict scoring because 16% of its standard responses are cut off.")
num(sec, "Date subtraction significantly worse than direct", -15.3, tb["en_US/date_subtraction"]["dhing_answered"], note="Holds in all three distractor conditions.")
add(sec, "This is the failure Hindi CoT shows, now appearing in English", "same failure", "month-crossing accuracy: English standard 90.1, Hindi standard 36.2, English Roman Hinglish 35.0, English plain under Hinglish 65.1; same-month accuracy all at least 93.8; failure overlap with Hindi CoT phi 0.40 vs 0.14 for English CoT", "responses/; dataset/", "reproduced", "Supported for date subtraction by a test the report did not run. Same-failure wording should stay limited to this task.")
add(sec, "Hindi accuracy is unchanged (59.4% in both)", "59.4 / 59.4", f"{tb['hi_IN/all']['std_answered']} / {tb['hi_IN/all']['hing_answered']}; paired {tb['hi_IN/all']['hs_diff_pairs']:+.2f} [{tb['hi_IN/all']['hs_lo']}, {tb['hi_IN/all']['hs_hi']}]", SRC_H, "reproduced", f"Aggregate only. {tb['hi_IN/all']['hs_a_only']} and {tb['hi_IN/all']['hs_b_only']} pairs flip in each direction: 28% of pairs disagree.")
add(sec, "Every task-level change is within noise", "all within noise", f"date duration {tb['hi_IN/date_duration']['hs_diff_pairs']:+.2f} [{tb['hi_IN/date_duration']['hs_lo']}, {tb['hi_IN/date_duration']['hs_hi']}], McNemar Holm p={tb['hi_IN/date_duration']['hs_p_holm9']:.3f}; date subtraction {tb['hi_IN/date_subtraction']['hs_diff_pairs']:+.2f} [{tb['hi_IN/date_subtraction']['hs_lo']}, {tb['hi_IN/date_subtraction']['hs_hi']}], Holm p={tb['hi_IN/date_subtraction']['hs_p_holm9']:.3f}", SRC_H, "differs", "False as worded. Date duration falls and date subtraction rises, both Holm-significant by McNemar (over 9 or 18). With question-level sign-flip, duration remains (p=0.015) and subtraction is borderline (p=0.055). Other seven tasks are null.")
num(sec, "Date subtraction, Hindi, Hinglish minus direct", -13.8, tb["hi_IN/date_subtraction"]["dhing_answered"])
num(sec, "Date subtraction, Hindi, standard minus direct", -18.8, tb["hi_IN/date_subtraction"]["dstd_answered"])
num(sec, "Interval date, Hindi, Hinglish minus direct", -23.2, tb["hi_IN/interval_date"]["dhing_answered"])
num(sec, "Interval date, Hindi, standard minus direct", -22.9, tb["hi_IN/interval_date"]["dstd_answered"])
add(sec, "Hinglish does not fix the two Hindi CoT failures; both still significantly worse than direct", "still worse", f"Holm p {tb['hi_IN/date_subtraction']['hd_p_holm18']:.1e}, {tb['hi_IN/interval_date']['hd_p_holm18']:.1e}", SRC_H, "reproduced", "Holds in all three distractor conditions. Date subtraction is partly improved (+5.1).")
sec = "Section 3.2"
num(sec, "EN-HI gap at very long falls from", 40.6, G["std/five/very_long/answered"]["diff"])
num(sec, "EN-HI gap at very long falls to", 8.3, G["hing/five/very_long/answered"]["diff"], note=f"With no distractor: {[r for r in sgap if r['insertion'] == 'no_insertion' and r['condition'] == 'hing' and r['measure'] == 'five_very_long'][0]}")
add(sec, "Figure 2 shows why: Hindi accuracy stays the same while English accuracy drops", "true", f"five date tasks at very long: Hindi {G['std/five/very_long/answered']['b']} to {G['hing/five/very_long/answered']['b']}; English {G['std/five/very_long/answered']['a']} to {G['hing/five/very_long/answered']['a']}", SRC_H, "reproduced")
num(sec, "Hinglish English-question trace median tokens", 233, T["hinglish/en_US"]["median_answered"])
num(sec, "Standard English-question trace median tokens", 353, T["cot/en_US"]["median_answered"])
add(sec, "Distractor penalties stay null in both languages", "null except one", "seven of eight intervals include 0 under answered-only", SRC_H, "reproduced", f"Under strict scoring the English standard unrelated penalty also excludes 0: {P['en_US/std/dissimilar_insertion/strict']}. Both English unrelated penalties share one direct-answer drop of 2.05, so they are not independent.")
add(sec, "English unrelated penalty -3.8 is most likely chance", "chance", f"at the no-distractor style mix it is {N['penalty_style_decomposition']['did_at_no_insertion_style_mix']}; Roman share falls from {N['penalty_style_decomposition']['by_insertion']['no_insertion']['roman_share']} to {N['penalty_style_decomposition']['by_insertion']['dissimilar_insertion']['roman_share']}", SRC_H, "overclaimed", "Untested in the report. About one point comes from unrelated distractors moving traces to plain English, and 2.05 from the direct drop.")
sec = "Section 3.3"
add(sec, "Devanagari mix: at least 10% of words are Devanagari", "definition", "reproduces 4,882 pairs and 73.07%", SRC_H, "reproduced")
add(sec, "Roman Hinglish: no Devanagari, and at least 5% function words", "no Devanagari", f"Table 3's Hindi Roman n=1,631 needs Devanagari share under 10%; {F3['hi_IN']['low_deva_in_roman']} traces in that row contain Devanagari. Literal rule gives {F3['hi_IN']['roman_text_pct']}% and n=1,571", SRC_H, "differs", "The definition as printed does not match the table.")
add(sec, "Function-word list (hai, ko, mein, toh, nahi, ...)", "list not printed in full", "reconstructed", MISSING, "source_missing", "Original list is lost. Recomputed with three lists; see fig_data/wordlist_sensitivity.csv. English Roman n ranges 3,935 to 4,112, accuracy 67.7 to 68.0.")
num(sec, "Hindi Q traces mostly Devanagari Hindi (%)", 73, F3["hi_IN"]["devanagari_pct"], tol=0.51)
add(sec, "73% of Hindi-question traces are 'mostly Devanagari'", "73%", f"{F3['hi_IN']['devanagari_pct']}% reach the 10% threshold; {F3['hi_IN']['deva_ge50_pct']}% have a Devanagari majority", SRC_H, "overclaimed", "A 10% threshold does not mean mostly. Say 68% for a majority, or 73% contain at least 10%.")
num(sec, "Hindi Q traces with no Devanagari (%)", 25.5, F3["hi_IN"]["no_deva_pct"])
num(sec, "Median Devanagari share (%)", 68, F3["hi_IN"]["median_dshare_all"], tol=0.51, note=f"Over all Hindi-question traces. Over Devanagari-mix traces it is {F3['hi_IN']['median_dshare_devmix']}. The report does not say which.")
add(sec, "For English questions the model never uses Devanagari", "never", f"{F3['en_US']['any_deva']} of 6,750 outside the answer line", SRC_H, "reproduced")
num(sec, "37% of English-question traces are essentially plain English", 37, F3["en_US"]["plain_pct"], tol=0.51, note=f"{N['dose']['share_zero']}% of paired traces have zero listed function words.")
ex = N["examples"]
add(sec, "Hindi question example (Devanagari mix, correct)", "19:52 to 20:17, 25 minutes", ex["hindi"][0]["id"] + f" answer {ex['hindi'][0]['answer']} gold {ex['hindi'][0]['gold']}", "responses/hinglish/short.json", "reproduced", "Report does not say it has a similar distractor.")
sec = "Section 3.4"
num(sec, "Roman Hinglish accuracy", 68.0, t3m[("en_US", "roman")]["hing"])
num(sec, "English CoT on same items", 89.3, t3m[("en_US", "roman")]["std"])
add(sec, "1,013 pairs only English CoT right; 138 only Hinglish", "1013 / 138", f"{t3m[('en_US', 'roman')]['s_only']} / {t3m[('en_US', 'roman')]['h_only']}", SRC_H, "reproduced")
num(sec, "Plain-English traces under Hinglish prompt", 79.1, t3m[("en_US", "plain")]["hing"], note="Differs only through the reconstructed word list (3 of 6,483 traces move groups). Loss -9.45 [-11.14, -7.70]: traces without Hindi still lose over 40% of the Roman loss.")
num(sec, "Standard CoT on plain-English group", 88.5, t3m[("en_US", "plain")]["std"])
add(sec, "Standard CoT does about equally well on both groups, so the Roman group is not just the harder questions", "89.3 vs 88.5", f"within task, level and distractor: standard {N['selection']['cell_fe_std']['roman']}, Hinglish {N['selection']['cell_fe_hing']['roman']}, question fixed effects {N['selection']['question_fe_hing']['roman']}", SRC_H, "overclaimed", "The conclusion survives stronger controls, but the printed argument alone is insufficient: it does not address task mix or trace-level selection. Style is measured after treatment and no control removes that.")
num(sec, "Devanagari-mix traces accuracy", 57.8, t3m[("hi_IN", "devanagari")]["hing"])
num(sec, "Standard Hindi CoT on same items", 57.1, t3m[("hi_IN", "devanagari")]["std"])
add(sec, "Devanagari-mix traces match standard Hindi CoT, as expected, since they are close to it", "close", f"accuracy matches; median Devanagari share {N['hindi_std_vs_devmix']['devmix_median_dshare']} vs {N['hindi_std_vs_devmix']['std_median_dshare']}; correctness differs on {N['hindi_std_vs_devmix']['discordant_pct']}% of pairs; identical answers {N['hindi_std_vs_devmix']['answers_identical_pct']}%", SRC_H, "overclaimed", "Same aggregate accuracy, but the traces are not close at the response level.")
add(sec, "Wrong Roman traces show arithmetic slips and shortcuts usually seen in Hindi CoT", "two examples", "subtraction error mix: English Hinglish other 56.4%, off-by-one 26.4%; Hindi CoT other 65.5%, off-by-one 19.6%; English CoT off-by-one 91.7%", "responses/", "overclaimed", "Two examples cannot show 'usually'. A subtraction error-type test supports it for that task only. Not tested for others.")
qq = N["example_questions"]
add(sec, "Example: date subtraction, short", "Today is 2025-05-01...; gold 2025-04-28; answer 2025-04-30; standard correct", f"{ex['subtraction'][0]['id']}; {qq['date_subtraction']}; gold {ex['subtraction'][0]['gold']}; answer {ex['subtraction'][0]['answer']}; standard {ex['subtraction'][0]['std_answer']}", "responses/hinglish/short.json; dataset/short/", "reproduced", "Quoted steps match.")
add(sec, "Example: date recurrence, short", "Today is 2025-06-27...; gold 2025-06-30; answer 2025-06-28; standard correct", f"{ex['recurrence'][0]['id']}; {qq['date_recurrence']}; gold {ex['recurrence'][0]['gold']}; answer {ex['recurrence'][0]['answer']}; standard {ex['recurrence'][0]['std_answer']}", "responses/hinglish/short.json; dataset/short/", "reproduced", "Quoted steps match.")
sec = "Section 4"
add(sec, "Takeaway 1: Hinglish does not close the gap; Hindi unchanged; gap shrinks only because English drops by 18 points", "18 points", f"gap {N['gap_recovered']['std_gap']} to {N['gap_recovered']['hing_gap']}; English {-tb['en_US/all']['hs_diff_strict']:.2f} strict and 17.99 answered; Hindi -0.03", SRC_H, "reproduced", "Report gives only answered-only; strict is 15.7. Holds in each distractor condition.")
add(sec, "Takeaway 2: Reasoning in Hinglish is costly on English questions", "costly", f"{tb['en_US/all']['hs_diff_pairs']} [{tb['en_US/all']['hs_lo']}, {tb['en_US/all']['hs_hi']}]", SRC_H, "reproduced", "What is established is the cost of this prompt. Plain-English traces with no Hindi lose -9.45, against -21.28 for Roman traces.")
add(sec, "Takeaway 2: cost grows with difficulty", "grows", f"slope {N['level_trend']['en_US/answered']}; strict {N['level_trend']['en_US/strict']}", SRC_H, "reproduced", f"Holds in each distractor condition: {N['level_trend_by_insertion']}.")
add(sec, "Takeaway 2: cost grows with how much Hindi the trace contains", "gradient", f"Roman vs plain {N['selection']['cell_fe_did']['roman']}; Roman quartile losses {[q['loss'] for q in N['dose']['quartile_bins_ge15']]}", SRC_H, "overclaimed", f"Function-word share is close to two groups: {N['dose']['share_zero']}% at zero, {N['dose']['share_ge25']}% at 25% or more, {N['dose']['share_between_3_and_15']}% between 3 and 15. Raw loss shrinks across Roman quartiles; the adjusted slope has the opposite sign. A two-group contrast is supported, a gradient is not established.")
add(sec, "Takeaway 2: date subtraction and day of week break down the way they do in Hindi CoT", "both", f"subtraction overlap phi 0.40; day of week phi {[a for a in N['failure_agreement'] if a['task'] == 'day_of_week'][0]['phi_enHing_hiStd']}; correct answers remain modal on English Hinglish day of week ({[d_ for d_ in N['dow_offsets'] if d_['condition'] == 'hinglish' and d_['language'] == 'en_US'][0]})", "responses/", "overclaimed", "Supported for subtraction. Not for day of week: no item overlap with Hindi failures, and Hindi's late-by-one mode does not appear.")
add(sec, "Takeaway 2: en-CoT recovers most of the gap", "most", f"{N['gap_recovered']['std_gap']} to {N['gap_recovered']['encot_gap']} ({N['gap_recovered']['recovered_pct']}% recovered)", SRC_E, "reproduced", "Strict 26.95 to 5.21. Holds in each distractor condition.")
add(sec, "Takeaway 2: reasoning in Hindi, in either script, is what limits CoT, more than reading a Hindi question", "either script", f"en-CoT advantage on Hindi questions: Devanagari mix +22.92, Roman +23.05, plain +14.88 (n=168); reading cost {N['reading_vs_reasoning']['reading_cost_en_reasoning']['answered']['diff']}, reasoning cost {N['reading_vs_reasoning']['reasoning_cost_on_hi_q']['answered']['diff']}", SRC_E, "overclaimed", "Direction supported and 'suggests' is fair, but 'in either script' goes beyond the design. Script is self-selected and cannot be crossed with language (no English question gets Devanagari reasoning); en-CoT differs from the Hinglish prompt in more than language; plain-English traces under the Hinglish prompt also lose 9.45 to 14.88 points.")
add(sec, "Takeaway 3: model does not follow the Roman-script instruction on Hindi questions: 73% mostly Devanagari", "73%", f"{F3['hi_IN']['deva_ge50_pct']}% majority Devanagari; {F3['hi_IN']['devanagari_pct']}% at least 10%; {F3['hi_IN']['no_deva_pct']}% none", SRC_H, "overclaimed", "Non-compliance holds. Replace 'mostly' or use 68%.")
add(sec, "Takeaway 3: the Hindi arm mostly tests code-mixed Devanagari Hindi, not romanised Hinglish", "true", f"{F3['hi_IN']['devanagari_pct']}% Devanagari mix; Roman {F3['hi_IN']['roman_pct']}%", SRC_H, "reproduced", "Holds in each distractor condition (71.4 to 74.4).")
sec = "Section 5"
add(sec, "Thresholds and word list are our own; style comparison is descriptive, not randomised", "caveat", f"threshold sweep: English Roman {N['sensitivity_summary']['en_roman_pct_range']}, adjusted difference {N['sensitivity_summary']['en_did_range']}, Hindi Devanagari {N['sensitivity_summary']['hi_dev_pct_range']}, tasks ordered {N['sensitivity_summary']['tasks_worse_range']}", SRC_H, "reproduced", "Caveat is correct, and the results are not sensitive to thresholds.")
add(sec, "Language drift assumes Hindi traces should be Devanagari", "design note", "consistent with root metrics.target_words", "metrics.py", "reproduced")
vc = N["verification_condition"]
num(sec, "Verification regex rate, English standard (%)", 86, vc["cot/en_US"]["orig"], tol=0.51)
num(sec, "Verification regex rate, English Hinglish (%)", 15, vc["hinglish/en_US"]["orig"], tol=0.51)
pv = N["pure_english_verification"]
add(sec, "The fall from 86% to 15% is mostly because the regex misses Hinglish phrasing", "mostly regex", f"zero-function-word English traces, where the regex applies fully: {pv['orig_hing']}% vs {pv['orig_std']}% on same items (n={pv['n']}); romanised regex lifts Hinglish only to {vc['hinglish/en_US']['ext']}%; text after first answer mention {vc['hinglish/en_US']['afa']} vs {vc['cot/en_US']['afa']}", SRC_H, "differs", "Contradicted. The drop is mainly real. Hand check of 30 Roman traces with no regex match found none with a check step (tail 420 characters only).")
add(sec, "Distractor mention cannot be measured on romanised traces", "design note", "not recomputed", "responses/hinglish/", "unverifiable", "Stated limit is plausible; not tested.")
add(sec, "With 50 questions per task and level, per-task and per-level estimates are noisier", "caveat", f"first-50 vs full grid pooled: English CoT 88.88 vs {[f_ for f_ in frows if f_['task'] == 'all' and f_['language'] == 'en_US' and f_['condition'] == 'cot'][0]['full_grid']}, Hindi CoT 59.40 vs {[f_ for f_ in frows if f_['task'] == 'all' and f_['language'] == 'hi_IN' and f_['condition'] == 'cot'][0]['full_grid']}", "responses/standard/", "reproduced", "Largest task gap: Hindi time duration 80.08 vs 77.70.")
add("Reproduction", "Analysis is in FINDINGS.md of experiments/2026-10-31_hinglish-analysis-aayush/", "exists", "absent from working tree and all refs", MISSING, "source_missing", "All numbers recomputed from raw responses.")
add("Reproduction", "Figures and tables come from report/make_report.py", "exists", "absent from working tree and all refs", MISSING, "source_missing", "All numbers recomputed from raw responses.")
with open(OUT / "claims.csv", "w", newline="", encoding="utf-8") as f:
    w_ = csv.DictWriter(f, fieldnames=list(rowsC[0]))
    w_.writeheader()
    w_.writerows(rowsC)
print(pd.Series([r["status"] for r in rowsC]).value_counts().to_dict(), len(rowsC))
for r in rowsC:
    if r["status"] == "differs":
        print(r["claim_id"], r["location"], r["claim_text"][:70], "|", r["reported_value"][:40], "|", r["recomputed_value"][:80])
