import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
N = json.load(open(HERE / "numbers.json", encoding="utf-8"))
E = N["extras"]
R = []
RESP = "responses/clp; responses/standard; dataset"


def add(loc, text, rep, rec, status, note="", src=RESP):
    R.append([f"A{len(R) + 1:03d}", loc, text, rep, rec, src, status, note])


def num(loc, text, rep, rec, note="", src=RESP, tol=0.051):
    add(loc, text, rep, rec, "reproduced" if abs(float(rep) - float(rec)) <= tol else "differs", note, src)


def cint(loc, text, rep, rec, src=RESP):
    d = max(abs(rep[0] - rec[0]), abs(rep[1] - rec[1]))
    note = "" if d <= 0.051 else f"Largest endpoint gap {d:.2f}, within Monte Carlo error of a 2,000-draw bootstrap with an unknown seed." if d <= 0.4 else f"Largest endpoint gap {d:.2f} exceeds Monte Carlo tolerance."
    add(loc, text, str(rep), str(rec), "reproduced" if d <= 0.4 else "differs", note, src)


T = N["A1"]
A1 = {"date_addition": ("Date addition", 85.6, 98.0, 82.8, 85.1, 92.7, 7.6, 9.9, True, True),
      "date_subtraction": ("Date subtraction", 86.0, 95.2, 84.8, 66.0, 86.9, 20.9, 2.1, True, False),
      "date_duration": ("Date duration", 84.0, 99.3, 78.9, 88.3, 92.7, 4.4, 13.7, True, True),
      "date_recurrence": ("Date recurrence", 22.1, 90.3, 2.8, 20.1, 27.0, 6.8, 24.2, True, True),
      "day_of_week": ("Day of week", 14.9, 69.5, 15.2, 21.0, 31.8, 10.8, 16.6, True, True),
      "interval_date": ("Interval date", 43.2, 50.7, 46.8, 23.9, 35.3, 11.4, -11.5, True, True),
      "time_addition": ("Time addition", 70.5, 95.9, 75.6, 73.5, 88.2, 14.7, 12.6, True, True),
      "time_subtraction": ("Time subtraction", 64.7, 97.7, 64.9, 75.2, 90.1, 14.9, 25.2, True, True),
      "time_duration": ("Time duration", 65.7, 98.9, 44.7, 80.1, 86.7, 6.6, 42.0, True, True),
      "all": ("All tasks", 59.7, 88.9, 55.2, 59.4, 70.3, 10.9, 15.1, True, True)}
for k, v in A1.items():
    for col, cond, val in zip(("English direct", "English CoT", "Hindi direct", "Hindi CoT", "Hindi CLP"), ("en_direct", "en_cot", "hi_direct", "hi_cot", "clp"), v[1:6]):
        num("Table A1", f"{v[0]}: {col} accuracy (answered-only)", val, T[k][cond], f"Strict: {T[k][cond + '_strict']}.")
    for lab, key, val, star in (("CLP - Hindi CoT", "clp-hi_cot", v[6], v[8]), ("CLP - Hindi direct", "clp-hi_direct", v[7], v[9])):
        d = T[k][key]
        num("Table A1", f"{v[0]}: {lab} difference", val, d["diff"], f"95% CI {d['ci']}.")
        if k == "all":
            add("Table A1", f"All tasks: {lab} star (uncorrected exact McNemar p<0.05)", "*", f"p={d['p']:.2e}", "reproduced")
        else:
            add("Table A1", f"{v[0]}: {lab} star (exact McNemar, Holm over nine tasks)", "*" if star else "no star", f"p_holm={d['p_holm']:.2e}", "reproduced" if (d["p_holm"] < 0.05) == star else "differs")
add("Table A1 caption", "2,250 questions x 3 distractor conditions, answered responses", "6,750 per condition", "6,750 records per condition; answered: " + ", ".join(f"{c} {6750 - N['unanswered'][c]['unanswered']}" for c in ("en_direct", "en_cot", "hi_direct", "hi_cot", "clp")), "reproduced")

H = N["headline_by_distractor"]["pooled"]
P = "A.2 prose"
num(P, "CLP accuracy", 70.3, H["acc"]["clp"])
num(P, "Hindi CoT accuracy", 59.4, H["acc"]["hi_cot"])
num(P, "CLP - Hindi CoT", 10.9, H["clp-hi_cot"]["diff"])
cint(P, "CLP - Hindi CoT CI", [9.6, 12.2], H["clp-hi_cot"]["ci"])
num(P, "Pairs where only CLP is right", 1297, H["clp-hi_cot"]["a_only"])
num(P, "Pairs where only Hindi CoT is right", 562, H["clp-hi_cot"]["b_only"])
num(P, "Hindi direct accuracy", 55.2, H["acc"]["hi_direct"])
num(P, "CLP - Hindi direct", 15.1, H["clp-hi_direct"]["diff"])
cint(P, "CLP - Hindi direct CI", [13.6, 16.7], H["clp-hi_direct"]["ci"])
d = N["headline_by_distractor"]
add(P, "CLP beats Hindi CoT on all nine tasks after Holm correction", "9 of 9", f"pooled {H['clp-hi_cot']['tasks_positive_and_holm_sig']}; none {d['none']['clp-hi_cot']['tasks_positive_and_holm_sig']}, time {d['time']['clp-hi_cot']['tasks_positive_and_holm_sig']}, unrelated {d['unrelated']['clp-hi_cot']['tasks_positive_and_holm_sig']}", "reproduced", "Holds only when pooled. Within one distractor condition 5 to 7 tasks survive Holm; the direction is positive throughout, the loss is power.")
add(P, "Mid report found Hindi CoT worse than direct on date subtraction and interval date", "2 tasks", "Stated in experiments/2026-10-02_mid-report-analysis/report/analysis.tex; same ordering on the subset (66.0 vs 84.8; 23.9 vs 46.8)", "reproduced", "", "experiments/2026-10-02_mid-report-analysis/report/analysis.tex")
num(P, "Date subtraction CLP vs Hindi CoT: 86.9", 86.9, T["date_subtraction"]["clp"])
num(P, "Date subtraction Hindi CoT: 66.0", 66.0, T["date_subtraction"]["hi_cot"])
num(P, "Interval date CLP: 35.3", 35.3, T["interval_date"]["clp"])
num(P, "Interval date Hindi CoT: 23.9", 23.9, T["interval_date"]["hi_cot"])
num(P, "Interval date Hindi direct: 46.8", 46.8, T["interval_date"]["hi_direct"])
num(P, "English CoT accuracy", 88.9, H["acc"]["en_cot"])
num(P, "English CoT - CLP", 18.6, H["en_cot-clp"]["diff"])
cint(P, "English CoT - CLP CI", [17.3, 19.9], H["en_cot-clp"]["ci"])
num(P, "CLP strict accuracy", 69.9, H["acc_strict"]["clp"])
num(P, "Hindi CoT strict accuracy", 59.0, H["acc_strict"]["hi_cot"])
num(P, "CLP responses without an Answer line", 39, N["unanswered"]["clp"]["unanswered"])
num(P, "Of those, cut off at token limit", 39, N["unanswered"]["clp"]["unanswered_cutoff"])
add(P, "Counting unanswered responses as wrong changes none of this", "no change", f"CLP-Hindi CoT {H['clp-hi_cot']['strict_diff']} (unchanged); English CoT-CLP {H['en_cot-clp']['diff']} becomes {H['en_cot-clp']['strict_diff']} {H['en_cot-clp']['strict_ci']}; English CoT 88.9 becomes {H['acc_strict']['en_cot']}", "overclaimed", "True of the CLP gain. The gap to English shrinks by 2.5 points because English CoT has 221 cut-offs against CLP's 39.")
add(P, "CLP helps Hindi substantially", "qualitative", f"none {d['none']['clp-hi_cot']['diff']} {d['none']['clp-hi_cot']['ci']}; time {d['time']['clp-hi_cot']['diff']} {d['time']['clp-hi_cot']['ci']}; unrelated {d['unrelated']['clp-hi_cot']['diff']} {d['unrelated']['clp-hi_cot']['ci']}", "reproduced", "Holds in each distractor condition; +9.0 with no distractor is the cleanest statement.")

A2 = {"short": ("Short", 77.8, 93.2, 73.9, 69.5, 77.2, 23.6, [20.7, 27.0], 16.0, [13.0, 19.0]),
      "medium": ("Medium", 69.6, 91.6, 65.3, 65.4, 75.7, 26.2, [23.3, 29.1], 15.9, [13.3, 18.7]),
      "long": ("Long", 61.2, 89.3, 57.9, 60.4, 71.3, 28.9, [25.7, 32.1], 18.0, [15.2, 20.7]),
      "very_long": ("Very long", 54.3, 87.2, 48.4, 53.7, 65.8, 33.5, [30.1, 36.8], 21.4, [18.4, 24.5]),
      "very_very_long": ("Very very long", 35.5, 82.9, 30.3, 47.9, 61.5, 35.0, [31.6, 38.5], 21.4, [18.1, 24.6])}
for k, v in A2.items():
    r = N["A2"][k]
    for col, cond, val in zip(("English direct", "English CoT", "Hindi direct", "Hindi CoT", "Hindi CLP"), ("en_direct", "en_cot", "hi_direct", "hi_cot", "clp"), v[1:6]):
        num("Table A2", f"{v[0]}: {col}", val, r[cond], f"Strict: {r['strict'][cond]}.")
    num("Table A2", f"{v[0]}: En CoT - Hi CoT", v[6], r["en_cot-hi_cot"]["diff"])
    cint("Table A2", f"{v[0]}: En CoT - Hi CoT CI", v[7], r["en_cot-hi_cot"]["ci"])
    num("Table A2", f"{v[0]}: En CoT - Hi CLP", v[8], r["en_cot-clp"]["diff"])
    cint("Table A2", f"{v[0]}: En CoT - Hi CLP CI", v[9], r["en_cot-clp"]["ci"])
add("Figure A1", "Accuracy by level with 95% bootstrap CIs, 450 questions per level", "plotted", "fig_data/figure_a1_accuracy_by_level.csv", "reproduced", "Plotted values match Table A2 by eye; 450 questions per level confirmed.")
W = N["gap_widening"]
P = "A.3 prose"
add(P, "CLP narrows the English-Hindi gap at every level", "every level", ", ".join(f"{k} {N['A2'][k]['clp-hi_cot']['diff']} {N['A2'][k]['clp-hi_cot']['ci']}" for k in A2), "reproduced")
x = W["en_cot-clp_answered"]
y = W["en_cot-clp_strict"]
add(P, "The gap still widens with difficulty (+16.0 to +21.4)", "+5.4 implied", f"answered {x['points_change']} {x['points_ci']}; strict {y['points_change']} {y['points_ci']}; log-odds gap {x['log_odds_gap_short']} to {x['log_odds_gap_vvl']} (change {x['log_odds_change']} {x['log_odds_ci']}); by distractor none {W['en_cot-clp_none']['points_change']} {W['en_cot-clp_none']['points_ci']}, time {W['en_cot-clp_time']['points_change']} {W['en_cot-clp_time']['points_ci']}, unrelated {W['en_cot-clp_unrelated']['points_change']} {W['en_cot-clp_unrelated']['points_ci']}", "overclaimed", "Numbers hold, widening does not hold robustly: not significant under strict scoring or in the no-distractor and time-related conditions, and it reverses on the log-odds scale.")

A = N["A3"]
P = "A.4 prose / Table A3"
num(P, "Stage 1 writes a non-question date", 98.6, A["has_other_date_answered"], "Denominator: stage-2-answered responses (98.5 over all 2,250).")
num(P, "Stage 1 last date is correct", 63.1, A["s1_gold_pct"])
num("Table A3", "Responses, stage 1 ends at gold", 1414, A["s1_gold_n"])
num("Table A3", "Responses, stage 1 ends elsewhere or none", 826, A["s1_other_n"])
num("Table A3", "Responses, all", 2240, A["n"])
num("Table A3", "Stage 2 correct | gold", 97.5, A["s2_correct_given_gold"])
num("Table A3", "Stage 2 correct | other", 20.1, A["s2_correct_given_other"], f"Includes {A['s1_none_n']} responses with no date at all ({A['s2_correct_given_none']}% correct); {A['s2_correct_given_other_date_only']}% when a wrong date is written. Hand check: 18 of 20 sampled recoveries are genuine.")
num("Table A3", "Stage 2 correct | all", 69.0, A["s2_correct_all"])
num("Table A3", "Stage 2 = stage 1 last date | gold", 97.6, A["eq_given_gold"])
num("Table A3", "Stage 2 = stage 1 last date | other", 55.7, A["eq_given_other"])
num("Table A3", "Stage 2 = stage 1 last date | all", 82.1, A["eq_all"])
hc = E["hand_check_40"]
add("Table A3 caption", "The date reading was correct in all 12 responses checked by hand", "12 of 12", f"Our read: {hc['last_date_is_conclusion']} of {hc['n']} ({hc['precision_pct']}%, Wilson {hc['precision_ci']}); bin right in {hc['bin_correct']} of {hc['n']}", "unverifiable", "The 12 responses are not identified, so that check cannot be repeated. Our independent sample finds a low but non-zero error rate caused by trailing notes.", "hand_check_stage1.csv")
add("Table A3 caption", "Stage 1 often prints Answer: as a heading", "often", f"{N['A4']['s1_label_answer_share']}% of stage-1 texts have an Answer label", "reproduced")
add("Table A3 caption", "Times and durations are excluded because the reading is unreliable", "design", "Exclusion is in the document; a gold-string check on all tasks is in fig_data/new_gold_in_stage1_by_task.csv", "reproduced", "The carry-over pattern extends to time and duration tasks (s2 correct 93-95% vs 48-53%).")
num(P, "Wrong stage-2 answers on date tasks", 695, A["wrong_s2"])
num(P, "Of those, repeat stage 1's last date", 461, A["wrong_s2_repeat"])
num(P, "Recurrence: stage 1 reaches correct date", 18.9, A["by_task"]["date_recurrence"]["s1_gold"])
num(P, "Recurrence CLP", 27.0, T["date_recurrence"]["clp"])
num(P, "Recurrence Hindi CoT", 20.1, T["date_recurrence"]["hi_cot"])
num(P, "Recurrence English CoT", 90.3, T["date_recurrence"]["en_cot"])
num(P, "Three date tasks CLP", 69.0, A["tri_task_acc"]["clp"])
num(P, "Three date tasks Hindi CoT", 57.1, A["tri_task_acc"]["hi_cot"])
num(P, "Three date tasks English CoT", 94.6, A["tri_task_acc"]["en_cot"])
F = N["A4"]
num(P, "Stage 1 verification", 5.8, F["ver_s1_scored"], "Answered responses.")
num(P, "Stage 2 verification", 26.9, F["ver_s2_scored"], "Answered responses.")
num(P, "Hindi CoT verification", 1.3, F["ver_hi_cot"])
num(P, "English CoT verification", 86.1, F["ver_en_cot"])
num(P, "Median completion tokens, CLP two stages", 487, F["median_scored_clp_two"], f"Answered responses; {F['median_tokens_clp_two_stages']} over all 6,750.")
num(P, "Median completion tokens, Hindi CoT", 212, F["median_hi_cot_scored"], f"{F['median_hi_cot']} over all.")
num(P, "Median completion tokens, English CoT", 353, F["median_en_cot_scored"], f"{F['median_en_cot']} over all, because 221 cut-offs at 4,096 are excluded from 353.")
num(P, "English word share stage 1", 0.977, E["english_share_answer_line_stripped"]["s1_pooled"], "Pooled over words, answer lines removed. Mean per response is 0.986.", tol=0.0006)
num(P, "English word share stage 2", 0.999, E["english_share_answer_line_stripped"]["s2_pooled"], "", tol=0.0006)
c = N["A3_controlled"]
add(P, "Understanding turn does more than restate the question", "qualitative", f"{hc['states_a_conclusion']} of {hc['n']} sampled stage-1 texts state a conclusion (Wilson {hc['solves_ci']}); no-date group is {A['s1_none_n']} of {A['n']}", "reproduced", "", "hand_check_stage1.csv")
add(P, "Stage 2 mostly writes up stage 1; mistakes rarely corrected (association, not an experiment)", "association", f"Task x level MH risk difference {c['mh_risk_difference_task_level']}; within-question {c['within_question_fe']['beta_points']} {c['within_question_fe']['ci']}; en-CoT negative control {c['encot_benchmark']['mh_rd']}", "reproduced", "Survives control for task, difficulty and question identity. Shared difficulty accounts for about 7 of the 77 raw points. Still observational.")

D = N["A4_table"]
A4 = {"en_direct": ("English direct", 60.6, 59.9, 58.6, 0.7, [-1.0, 2.5], 2.0, [0.4, 3.7]), "en_cot": ("English CoT", 89.3, 88.1, 89.2, 1.2, [-0.5, 2.7], 0.2, [-1.4, 1.6]),
      "hi_direct": ("Hindi direct", 56.0, 54.9, 54.6, 1.2, [-0.5, 2.9], 1.5, [-0.3, 3.2]), "hi_cot": ("Hindi CoT", 60.2, 58.9, 59.1, 1.3, [-0.8, 3.6], 1.2, [-0.9, 3.2]),
      "clp": ("Hindi CLP", 69.3, 69.3, 72.3, -0.1, [-2.1, 2.0], -3.1, [-5.1, -1.1])}
for k, v in A4.items():
    r = D[k]
    num("Table A4", f"{v[0]}: none", v[1], r["none"])
    num("Table A4", f"{v[0]}: time-related", v[2], r["time"])
    num("Table A4", f"{v[0]}: unrelated", v[3], r["unrelated"])
    num("Table A4", f"{v[0]}: drop time-related", v[4], r["drop_time"], f"Strict {r['drop_time_strict']} {r['drop_time_strict_ci']}.")
    cint("Table A4", f"{v[0]}: drop time-related CI", v[5], r["drop_time_ci"])
    num("Table A4", f"{v[0]}: drop unrelated", v[6], r["drop_unrelated"], f"Strict {r['drop_unrelated_strict']} {r['drop_unrelated_strict_ci']}.")
    cint("Table A4", f"{v[0]}: drop unrelated CI", v[7], r["drop_unrelated_ci"])
P = "A.5 prose"
td = E["clp_time_drop_by_task"]
add(P, "Distractors do not hurt CLP", "qualitative", f"Time drop {D['clp']['drop_time']} 95% {D['clp']['drop_time_ci']}, 90% {E['clp_time_drop_90ci']}; recurrence +{td['date_recurrence']['drop']} {td['date_recurrence']['ci']}, day of week +{td['day_of_week']['drop']} {td['day_of_week']['ci']}", "overclaimed", "No pooled drop was detected; a drop up to about 1.9 points is compatible, and the task CIs are too wide to exclude harm on the two hardest tasks.")
num(P, "CLP penalty vs Hindi direct", -1.2, D["clp"]["penalty_time"]["value"])
cint(P, "CLP penalty CI", [-4.1, 1.5], D["clp"]["penalty_time"]["ci"])
num(P, "Hindi CoT penalty", 0.2, D["hi_cot"]["penalty_time"]["value"])
cint(P, "Hindi CoT penalty CI", [-2.6, 2.9], D["hi_cot"]["penalty_time"]["ci"])
g = N["unrelated_gain"]
add(P, "CLP slightly more accurate with unrelated distractor; no tested explanation", "-3.1 [-5.1, -1.1]", f"Holm over Table A4's ten drops p={D['clp']['holm10_unrelated']:.3f}; sentence-cluster CI {g['sentence_cluster_boot']['ci']}; without recurrence {g['leave_one_task_out']['date_recurrence']} {g['leave_one_task_out_ci']['date_recurrence']}", "reproduced", "Not noise by these tests, but post hoc and concentrated in recurrence. See analysis.md for the stage-1 mode explanation.")
add(P, "Neither English CoT nor Hindi CoT shows a significant drop with the time-related distractor on this subset", "not significant", f"English CoT answered {D['en_cot']['drop_time']} {D['en_cot']['drop_time_ci']}, strict {D['en_cot']['drop_time_strict']} {D['en_cot']['drop_time_strict_ci']}; Hindi CoT answered {D['hi_cot']['drop_time']} {D['hi_cot']['drop_time_ci']}, strict {D['hi_cot']['drop_time_strict']} {D['hi_cot']['drop_time_strict_ci']}", "overclaimed", "Answered-only only. English CoT's strict drop is significant because time-related prompts produce more cut-offs (107 vs 68).")
M = N["mention"]
A5 = [("en_cot", "English CoT", 17.3, 8.9, 11.0, 6.3, (0.61, [0.39, 0.93]), (1.63, [0.90, 2.96])), ("hi_cot", "Hindi CoT", 34.0, 10.3, 28.7, 1.9, (0.85, [0.68, 1.07]), (1.30, [1.00, 1.70])),
      ("clp_s2", "CLP stage 2", 17.2, 9.7, 8.7, 2.3, (1.00, [0.72, 1.40]), (1.30, [0.81, 2.07]))]
for k, nm, a, b, c_, d_, o1, o2 in A5:
    num("Table A5", f"{nm}: mentions time-related", a, M[k]["sim_doc"]["rate"])
    num("Table A5", f"{nm}: placebo time-related", b, M[k]["sim_doc"]["placebo"])
    num("Table A5", f"{nm}: mentions unrelated", c_, M[k]["dis_doc"]["rate"])
    num("Table A5", f"{nm}: placebo unrelated", d_, M[k]["dis_doc"]["placebo"])
    num("Table A5", f"{nm}: OR time-related", o1[0], M[k]["sim_doc"]["or"]["or"], tol=0.0051)
    add("Table A5", f"{nm}: OR time-related CI", str(o1[1]), str(M[k]["sim_doc"]["or"]["ci"]), "reproduced" if o1[1] == M[k]["sim_doc"]["or"]["ci"] else "differs")
    num("Table A5", f"{nm}: OR unrelated", o2[0], M[k]["dis_doc"]["or"]["or"], tol=0.0051)
    add("Table A5", f"{nm}: OR unrelated CI", str(o2[1]), str(M[k]["dis_doc"]["or"]["ci"]), "reproduced" if o2[1] == M[k]["dis_doc"]["or"]["ci"] else "differs")
den = E["stage1_mention_denominators"]
num("Table A5", "CLP stage 1: mentions time-related", 62.9, den["sim_s1_all_responses"]["rate"], "Reproduces only over all 2,250 responses, whereas the caption says answered responses (62.8 answered).")
num("Table A5", "CLP stage 1: placebo time-related", 9.4, den["sim_s1_all_responses"]["placebo"], "All responses; 9.3 answered.")
num("Table A5", "CLP stage 1: mentions unrelated", 83.7, den["dis_s1_all_responses"]["rate"], "All responses.")
num("Table A5", "CLP stage 1: placebo unrelated", 2.8, den["dis_s1_all_responses"]["placebo"], "All responses; 2.7 answered.")
add("Table A5", "CLP stage 1: OR time-related", "1.02 [0.79, 1.30]", "1.02 [0.79, 1.31] with unanswered as wrong over all responses; 1.02 [0.80, 1.31] answered-only", "reproduced", "Reproduced only with unanswered counted as wrong, contrary to the caption; upper bound 1.305 rounds either way.")
add("Table A5", "CLP stage 1: OR unrelated", "1.65 [1.19, 2.30]", "1.65 [1.19, 2.30] with unanswered as wrong over all responses (1.655); 1.66 [1.20, 2.31] answered-only", "reproduced", "Same denominator mismatch with the caption.")
add(P, "The understanding turn absorbs the distractor", "qualitative", f"Net mention stage 2 {M['clp_s2']['sim_doc']['net_paired']}/{M['clp_s2']['dis_doc']['net_paired']}, single-turn en-CoT {M['encot']['sim_doc']['net_paired']}/{M['encot']['dis_doc']['net_paired']}, Hindi CoT {M['hi_cot']['sim_doc']['net_paired']}/{M['hi_cot']['dis_doc']['net_paired']}", "overclaimed", "About two thirds of the fall from Hindi CoT to stage 2 is also seen in single-turn en-CoT, which has no understanding turn. Reasoning in English explains most of it; the extra turn adds about 5 to 6 points. Not an experiment on the turn.")
num(P, "Stage 2 net of chance, time-related", 7.5, M["clp_s2"]["sim_doc"]["net"])
num(P, "Stage 2 net of chance, unrelated", 6.5, M["clp_s2"]["dis_doc"]["net"], "Rate 8.7 minus placebo 2.3 prints as 6.4 from rounded figures, 6.5 unrounded.")
num(P, "Hindi CoT net of chance, time-related", 23.8, M["hi_cot"]["sim_doc"]["net"])
num(P, "Hindi CoT net of chance, unrelated", 26.8, M["hi_cot"]["dis_doc"]["net"])
hm = E["hand_check_mentions"]
add(P, "Placebo subtraction gives net-of-chance mention rates", "subtraction", f"Excluding every word seen in any placebo trace: stage 2 {N['mention_specific']['clp_s2']['sim']['rate_excluding_any_word_seen_in_placebo']}/{N['mention_specific']['clp_s2']['dis']['rate_excluding_any_word_seen_in_placebo']}; Hindi words add 0.1 to stage 2; hand precision {hm['time_related']['true_mention']}/15 and {hm['unrelated']['true_mention']}/15", "reproduced", "Subtraction survives the checks. The both-language rule does not inflate CLP because Hindi words have 0.0 placebo and add little.", "fig_data/table_a5_mentions_by_rule.csv; hand_check_mentions.csv")
add(P, "In stage 2, mentioning the time-related distractor is not linked to accuracy", "OR 1.00 [0.72, 1.40]", str(M["clp_s2"]["sim_doc"]["or"]), "reproduced", f"Raw accuracy is {M['clp_s2']['sim_doc']['acc_mention']} vs {M['clp_s2']['sim_doc']['acc_no_mention']}; the link vanishes only after stratifying.")
ru = N["reuse"]
num(P, "Hindi direct reuse", 12.6, ru["hi_direct"]["rate"])
num(P, "Hindi direct placebo", 3.8, ru["hi_direct"]["placebo_rate"])
add(P, "Hindi direct Fisher p<0.001", "<0.001", f"{ru['hi_direct']['fisher_p']:.1e}", "reproduced")
num(P, "CLP reuse", 2.6, ru["clp"]["rate"], f"{ru['clp']['inserted']} of {ru['clp']['inserted_n']}.")
num(P, "CLP placebo", 3.1, ru["clp"]["placebo_rate"], f"{ru['clp']['placebo']} of {ru['clp']['placebo_n']}.")
num(P, "CLP Fisher p", 0.82, ru["clp"]["fisher_p"], tol=0.006)
add(P, "Wrong answers also stop borrowing from the distractor", "qualitative", f"Hindi CoT already {ru['hi_cot']['rate']} vs {ru['hi_cot']['placebo_rate']} (p={ru['hi_cot']['fisher_p']:.2f})", "overclaimed", "Borrowing is a property of direct answers. Hindi CoT shows none on the same questions, so it is not something CLP removes.")

G = N["agreement"]
A6 = [("hi_direct|en_direct", "Hindi direct vs English direct", 6743, 3143, 2138, 881, 581, 0.28, [0.14, 0.42], 43), ("hi_cot|en_cot", "Hindi CoT vs English CoT", 6490, 3778, 557, 2000, 155, 0.07, [-0.01, 0.12], 35), ("clp|en_cot", "CLP vs English CoT", 6497, 4412, 479, 1366, 240, 0.10, [-0.03, 0.14], 35)]
for k, nm, p, br, bw, eo, ho, ph, iq, cells in A6:
    r = G[k]
    for lab, v, rv in (("Pairs", p, r["pairs"]), ("Both right", br, r["both_right"]), ("Both wrong", bw, r["both_wrong"]), ("Only English right", eo, r["only_b_right"]), ("Only Hindi right", ho, r["only_a_right"]), ("Cells with defined phi", cells, r["cells_defined"])):
        num("Table A6", f"{nm}: {lab}", v, rv)
    num("Table A6", f"{nm}: median phi", ph, r["median_phi"], f"All cells: within-cell r {r['within_cell_r']} {r['within_cell_r_ci']}, MH OR {round(r['mh_or'], 2)} {r['mh_or_ci']}.", tol=0.0051)
    add("Table A6", f"{nm}: phi IQR", str(iq), str(r["phi_iqr"]), "reproduced" if iq == r["phi_iqr"] else "differs")
P = "A.6 prose"
self_a = N["self_agreement_across_distractor"]
add(P, "Whether CLP is right is barely related to whether English CoT is right", "median phi 0.10", f"MH OR {round(G['clp|en_cot']['mh_or'], 2)} {G['clp|en_cot']['mh_or_ci']}; r {G['clp|en_cot']['within_cell_r']} {G['clp|en_cot']['within_cell_r_ci']}; each CoT condition's agreement with itself across distractor versions: English r {self_a['en_cot']['within_cell_r']}, CLP r {self_a['clp']['within_cell_r']}", "overclaimed", "The association is small but excludes zero, and it is as large as each condition's agreement with itself. The low phi reflects low question-level reliability, not language-specific failure.")
add(P, "Direct answers in the two languages fail together more often", "0.28", f"r {G['hi_direct|en_direct']['within_cell_r']} {G['hi_direct|en_direct']['within_cell_r_ci']}; self-agreement {self_a['en_direct']['within_cell_r']}/{self_a['hi_direct']['within_cell_r']}", "reproduced", "True, but direct answers are also much more self-consistent, so the contrast is mostly reliability.")
add(P, "Phi undefined where English CoT is right on every question, hence 10 of 45 cells drop for CLP", "10 cells", f"{len(E['phi_missing_cells_clp_en'])} cells, all with English CoT at 100%: " + "; ".join(x["cell"] for x in E["phi_missing_cells_clp_en"]), "reproduced", "Dropping is not at random: the excluded cells are mostly easy date-addition and duration tasks.")
er = N["errors"]
num(P, "Off-by-one share of wrong CLP answers", 26.9, er["clp"]["off_by_one"], f"n={er['clp']['n']}.")
num(P, "Off-by-one, Hindi CoT", 21.2, er["hi_cot"]["off_by_one"], f"n={er['hi_cot']['n']}.")
num(P, "Off-by-one, English CoT", 52.3, er["en_cot"]["off_by_one"], f"n={er['en_cot']['n']}.")
st = N["errors_task_standardised_off_by_one"]
add(P, "CLP's errors keep a Hindi-like profile, close to Hindi CoT and far from English CoT", "26.9 vs 21.2 vs 52.3", f"Equal task weights {st['clp']['uniform']} vs {st['hi_cot']['uniform']} vs {st['en_cot']['uniform']}; date addition {er['clp']['by_task']['date_addition']['off_by_one']} vs {er['hi_cot']['by_task']['date_addition']['off_by_one']} vs {er['en_cot']['by_task']['date_addition']['off_by_one']}; date subtraction {er['clp']['by_task']['date_subtraction']['off_by_one']} vs {er['hi_cot']['by_task']['date_subtraction']['off_by_one']} vs {er['en_cot']['by_task']['date_subtraction']['off_by_one']}", "overclaimed", "Direction holds after standardising, but CLP sits between the two; on date addition and subtraction it is near the midpoint. Same-wrong-answer rates are 23.3% with English CoT and 22.6% with Hindi CoT.")
w = N["day_of_week"]
num(P, "Day of week CLP accuracy", 31.8, T["day_of_week"]["clp"])
num(P, "Day of week Hindi CoT accuracy", 21.0, T["day_of_week"]["hi_cot"])
num(P, "Day after correct, CLP", 22.4, w["clp"]["plus1"], f"n={w['clp']['n']}.")
num(P, "Day after correct, Hindi CoT", 25.3, w["hi_cot"]["plus1"], f"n={w['hi_cot']['n']}.")
rp = N["recurrence_patterns"]
num(P, "Recurrence backwards, CLP", 8.1, rp["clp"]["mirror"], f"n={rp['clp']['n']}.")
num(P, "Recurrence backwards, Hindi CoT", 9.0, rp["hi_cot"]["mirror"], f"n={rp['hi_cot']['n']}.")
num(P, "Recurrence backwards, English CoT", 0.4, rp["en_cot"]["mirror"], f"n={rp['en_cot']['n']}.")
tf = E["task_failures_significance"]
add(P, "Two task-specific failures shrink but remain", "shrink", f"Weekday +1 22.4 vs 25.3 p={tf['dow_plus1_clp_vs_hi_cot_p']:.2f}; mirror 8.1 vs 9.0 p={tf['recurrence_mirror_clp_vs_hi_cot_p']:.2f}; en-CoT mirror {rp['encot']['mirror']}, weekday +1 {w['encot']['plus1']}", "overclaimed", "They remain; shrinkage is not significant. Mirror errors persist at 8.3% under en-CoT, which points to the Hindi question wording and comprehension.")

P = "A.7"
add(P, "CLP improves by +10.9 over Hindi CoT and +15.1 over Hindi direct, on every task", "every task", f"Hindi CoT 9/9 positive; Hindi direct: interval date {T['interval_date']['clp-hi_direct']['diff']} (significantly worse), date subtraction {T['date_subtraction']['clp-hi_direct']['diff']} (p_holm {T['date_subtraction']['clp-hi_direct']['p_holm']:.2f}); 7 of 9 significantly better", "differs", "False for the direct comparison and contradicts Table A1.")
add(P, "It does not close the gap to English; +18.6 ahead and the gap still widens", "+18.6", f"{H['en_cot-clp']['diff']} answered, {H['en_cot-clp']['strict_diff']} strict", "overclaimed", "First half is strong under both conventions; widening is not robust.")
add(P, "Stage 2 mostly writes up stage 1; stage 1 rarely verifies; plausibly limits gain, not tested as a cause", "qualitative", f"On date tasks en-CoT - CLP is {E['date_gap_decomposition']['gap_s1_other']} when stage 1 is wrong and {E['date_gap_decomposition']['gap_s1_gold']} when right", "reproduced", "Appropriately hedged.")
add(P, "CLP is not more vulnerable; understanding turn deals with the distractor and stage 2 seldom uses it", "qualitative", f"Difference in time drop CLP - Hindi CoT {E['difference_in_drops']['clp-hi_cot_time']['diff_in_drop']} {E['difference_in_drops']['clp-hi_cot_time']['ci']}; CLP - en-CoT {E['difference_in_drops']['clp-encot_time']['diff_in_drop']} {E['difference_in_drops']['clp-encot_time']['ci']}", "overclaimed", "'Not more vulnerable' holds. The causal 'deals with' does not follow.")
add(P, "CLP makes accuracy more English-like but not errors; failures remain unrelated to English failures", "qualitative", f"MH OR {round(G['clp|en_cot']['mh_or'], 2)} {G['clp|en_cot']['mh_or_ci']}, same as English CoT's self-agreement OR {round(self_a['en_cot']['mh_or'], 2)}", "overclaimed", "'Unrelated' is false as stated.")

P = "A.8"
s = N["subset"]
add(P, "CLP was run on 2,250 of 6,750 questions (first 50 per task and level)", "2,250", "Confirmed; 1,350 records per level, 6,750 in all, question IDs 0-49", "reproduced")
num(P, "Hindi CoT penalty, subset", 0.2, s["penalty"]["hi_time"]["first50"])
num(P, "Hindi CoT penalty, full grid", 2.2, s["penalty"]["hi_time"]["full"], f"CI {s['penalty']['hi_time']['full_ci']}; printed [+0.6, +3.8] in the editing note.")
add(P, "On the subset the penalty is smaller, so Part A cannot speak to that effect", "smaller", f"Random 50-per-cell draws: mean {s['random_subset_null']['hi_time']['null_mean']}, SD {s['random_subset_null']['hi_time']['null_sd']}, 95% {s['random_subset_null']['hi_time']['null_2.5']} to {s['random_subset_null']['hi_time']['null_97.5']}, p={s['random_subset_null']['hi_time']['two_sided_p']}", "overclaimed", "The conclusion is right but 'smaller' implies a property of the subset. The subset is a nearly i.i.d. draw and +0.2 is a low, unremarkable sample of the same quantity.")
add(P, "CLP follows Qin et al.'s wording with our answer-format instructions added to stage 2", "wording", "Also added: 'Write your entire response in English.' in stage 1, an English-only rule in stage 2; 'Request:' on the same line; temperature 0 in both stages vs 1 and 0.2 in Qin et al.'s code; no CLSP", "overclaimed", "Understates the departures. See analysis.md.", "config/prompt.yaml; clp.py; github.com/LightChen233/cross-lingual-prompting request.py")
add(P, "Stage 1 has no reliable Answer line, read for date tasks only", "qualitative", f"Answer label in {N['A4']['s1_label_answer_share']}% of stage-1 texts", "reproduced")
add(P, "Word matching counts chance matches and misses paraphrases", "qualitative", "Hand precision 53% time-related, 80% unrelated; dismissal-phrase rates in fig_data/new_dismissal_phrase_rates.csv", "reproduced", "", "hand_check_mentions.csv")

P = "A.1"
add(P, "CLP stage prompts as quoted", "quotes", "Match config/prompt.yaml and all records", "reproduced", "", "config/prompt.yaml; responses/clp")
add(P, "Sarvam-105B, thinking off, temperature 0, up to 4,096 tokens per stage", "settings", str(E["clp_request_settings"]), "reproduced")
add(P, "Same conversation for stage 2", "design", "Stage 2's history holds the stage 1 reply verbatim in 6,750 of 6,750 records", "reproduced")
add(P, "Day-of-week answers requested as Hindi weekday names and scored by weekday", "design", "config/prompt.yaml format with language=source in clp.py; scoring by weekday index", "reproduced")
add(P, "Questions 0-49, 2,250 questions, three distractor conditions, 6,750 responses", "6,750", "6,750; errors.json empty in all five levels", "reproduced")
add(P, "Mid-report pipeline: same extraction, scoring, error classes, mention rule, statistics", "same", f"Answer extraction differs from pipeline code in {N['pipeline_extract_differential']['answer_mismatches']} of {N['pipeline_extract_differential']['responses_compared']} responses; every table reproduces under the documented rules", "reproduced", "Checked against experiments/2026-10-27_full-grid-analysis code. The Part A script itself is missing.", "experiments/2026-10-27_full-grid-analysis")
add(P, "On 27,000 standard responses per-response data is identical to the full-grid pipeline's", "identical", "Not directly checkable: the pipeline's outputs/data pickles are not present and the Part A script is missing. Our rows give the same aggregates", "unverifiable", "", "experiments/2026-10-27_full-grid-analysis/outputs/data (absent)")
add(P, "An independent script that shares no code reproduces accuracies and McNemar counts", "exists", "No such script found in the working tree or any ref. Our verify.py is a separate reproduction and agrees", "unverifiable", "Claim cannot be checked directly; say so or cite this audit's script instead.", "experiments/2026-10-31_clp-analysis-rahul (absent)")
add(P, "CLP records have the same question text and gold answer as standard Hindi records", "every case", str(N["data_checks"]), "reproduced", "All 6,750 CLP records match dataset text and gold; standard records match the same dataset.")
add("Notes", "Part A source: experiments/2026-10-31_clp-analysis-rahul (numbers.json, analysis.md)", "exists", "Absent from the working tree and from every local or remote ref (git log --all empty)", "source_missing", "Every Part A number was recomputed from raw responses instead.", "experiments/2026-10-31_clp-analysis-rahul")
add("Notes", "Every table and number was filled from those files by the script that built this document", "scripted", "Script and files are absent", "source_missing", "Numbers themselves reproduce, so the risk is provenance, not value.", "experiments/2026-10-31_clp-analysis-rahul")
add("Notes", "Full-grid Hindi CoT penalty +2.2 [+0.6, +3.8]", "+2.2", f"{s['penalty']['hi_time']['full']} {s['penalty']['hi_time']['full_ci']}", "reproduced", "Pipeline numbers.json has 2.21 [0.58, 3.83]. This is a difference-in-differences: Hindi CoT drop 2.57 minus Hindi direct drop 0.36. Strict 2.24 [0.52, 3.85]; both-answered 2.12 [0.39, 3.72]. The Part B audit values +2.59 (strict) and +2.47 (both-answered) equal the Hindi CoT drop alone, a different quantity; see penalty_check.json. The lower bound moves between 0.48 and 0.60 with the bootstrap seed.", "experiments/2026-10-27_full-grid-analysis/outputs/full/numbers.json; penalty_check.json")

P = "Appendix A"
add(P, "CLP improves Hindi accuracy; better on all 9 tasks (Strong)", "Strong", "Strong vs Hindi CoT; vs Hindi direct 7 better, 1 ns, 1 worse", "overclaimed", "'All 9 tasks' applies only to Hindi CoT.")
add(P, "Gap +16.0 to +21.4, grows with difficulty (Strong)", "Strong", f"Gap exists: strong. Growth: {W['en_cot-clp_answered']['points_change']} {W['en_cot-clp_answered']['points_ci']}, strict {W['en_cot-clp_strict']['points_ci']}", "overclaimed", "Downgrade the growth part to suggestive.")
add(P, "Stage 2 follows stage 1: 97.5 vs 20.1; 461 of 695 (Strong as association)", "Strong", f"Within-question {c['within_question_fe']['beta_points']} {c['within_question_fe']['ci']}", "reproduced", "Could be upgraded: survives question fixed effects.")
add(P, "Distractors do not hurt CLP: -0.1 [-2.1, +2.0]; penalty -1.2 [-4.1, +1.5] (Moderate)", "Moderate", "Values reproduce; moderate is fair if worded as no detected drop", "reproduced")
add(P, "CLP's errors stay Hindi-like: phi 0.10, off-by-one 26.9 vs 52.3 (Moderate)", "Moderate", "See A.6 rows", "overclaimed", "Downgrade: phi cannot carry this claim.")

with open(HERE / "claims.csv", "w", newline="", encoding="utf-8") as f:
    w_ = csv.writer(f)
    w_.writerow(["claim_id", "location", "claim_text", "reported_value", "recomputed_value", "source_path", "status", "note"])
    w_.writerows(R)
from collections import Counter
print(len(R), Counter(r[6] for r in R))
for r in R:
    if r[6] == "differs":
        print(r[:5], r[7][:120])
