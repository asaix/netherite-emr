import csv
import json
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent
TAB = OUT / "tables"
SC = json.load(open(TAB / "scalars.json", encoding="utf-8"))
ED = "experiments/2026-10-29_ed-analysis/parsed/ (rebuilt in pairs.csv.gz); checked against edout/{standard,ron}/*.csv"
LR = "experiments/2026-10-30-LR-aayush/lr_out/; recomputed in verify.py"
rows = []


def add(loc, text, reported, recomputed, source=ED, status="reproduced", note=""):
    rows.append({"claim_id": f"LR{len(rows) + 1:03d}", "location": loc, "claim_text": text, "reported_value": reported, "recomputed_value": recomputed, "source_path": source, "status": status, "note": note})


def num(loc, text, reported, value, source=ED, note="", status=None, tail=""):
    decimals = len(reported.split(".")[1]) if "." in reported else 0
    shown = f"{value:,.{decimals}f}"
    ok = shown == reported or abs(float(shown.replace(",", "")) - float(reported.replace(",", ""))) < 1e-12
    add(loc, text, reported + tail, shown + tail, source, status or ("reproduced" if ok else "differs"), note)


t1 = pd.read_csv(TAB / "t1_outcomes.csv").set_index("mode")
rates = pd.read_csv(TAB / "t1_rates.csv")
mw = pd.read_csv(TAB / "t2_mann_whitney.csv").set_index("sample")
models = pd.read_csv(TAB / "t3_report_models.csv").set_index("model")
counts = pd.read_csv(TAB / "t4_exclusions_counts.csv").set_index("mode")
bins = pd.read_csv(TAB / "t5_bin_rates.csv")
ame = pd.read_csv(TAB / "t6_ame_scaling.csv").set_index("model")
views = pd.read_csv(TAB / "t7_views_models.csv")
within = pd.read_csv(TAB / "t8_views_within_question.csv").set_index("view")
cv = pd.read_csv(TAB / "t10_cv_delta.csv")
modeor = pd.read_csv(TAB / "t11_mode_or.csv").set_index("spec")
match = pd.read_csv(TAB / "t11_matched_450_summary.csv").set_index("mode")
mcn = pd.read_csv(TAB / "t11_matched_mcnemar.csv")
firth = pd.read_csv(TAB / "t12_on_firth.csv").set_index("model")
oncells = pd.read_csv(TAB / "t3_on_task_cells.csv").set_index("task")
excl = pd.read_csv(TAB / "t13_excluded_profile.csv").set_index("mode")
sens = pd.read_csv(TAB / "t14_exclusion_sensitivity.csv").set_index("scenario")
strict = pd.read_csv(TAB / "t14_strict_outcomes.csv").set_index("mode")
lm = pd.read_csv(TAB / "t15_length_models.csv").set_index("spec")
lc = pd.read_csv(TAB / "t15_length_collinearity.csv").set_index("sample")
pw = pd.read_csv(TAB / "t16_linearity.csv")
rt = lambda by, lv: rates[(rates.by == by) & (rates.level == lv) & (rates["mode"] == "all")].iloc[0]
v = lambda view, model: views[(views.view == view) & (views.model == model)].iloc[0]
d = lambda view, sample="all", base="base": cv[(cv.view == view) & (cv["sample"] == sample) & (cv.baseline == base)].iloc[0]

add("Sec 1", "All results come from existing Sarvam-105B outputs; no model retrained or rerun", "no new inference", "every RDS and correctness value rebuilt from stored outputs with no model call", note="Reproducibility shows the numbers come from stored outputs; absence of any rerun outside the repo cannot be proved.")
add("Sec 2", "disagree = 1 when exactly one language is correct", "definition", "matches rds_regression.py and my rebuild", LR)
add("Sec 2", "RDS is the normalized edit distance between English and Hindi reasoning traces", "definition", "content_norm_edit_distance over op tokens that include ANSWER and SPITANSWER and all operands; computed on visible content, not reasoning_content, in both modes", status="overclaimed", note="The report does not say the token sequence contains the final answer, and in the ON mode the 'reasoning trace' is the visible summary. Rebuilt values match the CSVs exactly (max abs diff 0).")
add("Sec 2", "RDS ranges from 0 (identical) to 1 (completely different)", "0 to 1", f"observed answered-sample range 0 to 1; 1 means no token aligned, not unrelated content", note="Unrelated traces from a different question score about 0.96 (tests/ed_audit FINDINGS), so the useful range is compressed.")
add("Sec 2", "Standard errors clustered by question", "clustered", "reproduced; 6,739 clusters pooled, uid = difficulty|task|question_id", LR)
add("Sec 2", "Each question appears in up to three insertion variants and both reasoning modes", "up to 3 x 2", "20,250 OFF pairs over 6,750 questions; 1,350 ON pairs over 450 questions")
add("Sec 2", "Models: primary, length-adjusted, per-mode specifications", "formulas", "match rds_regression.py", LR)
add("Sec 2", "Reference levels short, date_addition, no insertion, reasoning OFF", "reference levels", "match rds_regression.py", LR)
num("Sec 2", "Loaded pairs", "21,600", counts.loc["all", "pairs"])
num("Sec 2", "Pairs dropped", "938", counts.loc["all", "excluded"], note=f"OFF {counts.loc['off', 'excluded']}, ON {counts.loc['on', 'excluded']}.")
num("Sec 2", "Share dropped", "4.3", 100 * counts.loc["all", "excluded"] / counts.loc["all", "pairs"], tail="%", note="OFF 3.8%, ON 11.8%: the pooled figure hides a threefold difference between modes.")
add("Sec 2", "Dropped because the English or Hindi answer could not be parsed", "unparseable", f"{excl.loc['off', 'en_cut_at_limit'] + excl.loc['off', 'hi_cut_at_limit'] + excl.loc['on', 'en_cut_at_limit'] + excl.loc['on', 'hi_cut_at_limit']} of 991 missing answers stopped at the token limit; 4 stopped normally with no answer line", status="overclaimed", note="These are almost all unfinished responses, not parser failures. The wording makes an informative exclusion sound like noise.")
num("Sec 2", "Analysed pairs", "20,662", t1.loc["all", "n"])
num("Sec 2", "Unique questions", "6,739", t1.loc["all", "unique_questions"])
num("Sec 2", "OFF pairs", "19,471", t1.loc["off", "n"])
num("Sec 2", "ON pairs", "1,191", t1.loc["on", "n"])
num("Sec 3.1", "Overall disagreement", "31.4", 100 * t1.loc["all", "disagree_rate"], tail="%", note=f"Answered only. Strict (unanswered = wrong) {100 * strict.loc['all', 'disagree_strict']:.1f}%. By distractor, answered: none {100 * rt('insertion', 'no_insertion').rate:.1f}, similar {100 * rt('insertion', 'similar_insertion').rate:.1f}, dissimilar {100 * rt('insertion', 'dissimilar_insertion').rate:.1f}.")
add("Sec 3.1", "95% CI of overall disagreement", "[30.7, 32.0]", f"Wilson [{100 * t1.loc['all', 'wilson_lo']:.2f}, {100 * t1.loc['all', 'wilson_hi']:.2f}]; cluster bootstrap [{100 * t1.loc['all', 'cluster_lo']:.1f}, {100 * t1.loc['all', 'cluster_hi']:.1f}]", status="overclaimed", note="The printed interval is the Wilson interval, which treats the three variants of a question as independent. The team convention is the cluster bootstrap, which is wider.")
num("Sec 3.1", "Share of disagreements that are English correct, Hindi wrong", "92", 100 * SC["en_share_of_disagree"], tail="%", note=f"Strict: {100 * strict.loc['all', 'en_share_of_disagree']:.1f}%. ON strict: {100 * strict.loc['on', 'en_share_of_disagree']:.1f}%.")
for mode, label in [("all", "All"), ("off", "OFF"), ("on", "ON")]:
    for col, name, rep in [("both_correct", "both correct", {"all": "12,468", "off": "11,309", "on": "1,159"}), ("en_only", "EN only", {"all": "5,967", "off": "5,947", "on": "20"}), ("hi_only", "HI only", {"all": "516", "off": "505", "on": "11"}), ("both_wrong", "both wrong", {"all": "1,711", "off": "1,710", "on": "1"})]:
        num("Table 1", f"{label}: {name}", rep[mode], t1.loc[mode, col])
num("Table 1", "All: disagree rate", "31.4", 100 * t1.loc["all", "disagree_rate"], tail="%")
num("Table 1", "OFF: disagree rate", "33.1", 100 * t1.loc["off", "disagree_rate"], tail="%", note=f"Strict {100 * strict.loc['off', 'disagree_strict']:.1f}%.")
num("Table 1", "ON: disagree rate", "2.6", 100 * t1.loc["on", "disagree_rate"], tail="%", note=f"Answered only. Strict {100 * strict.loc['on', 'disagree_strict']:.1f}%, because 11.8% of ON pairs have no answer in at least one language.")
num("Sec 3.1", "Disagreement, short", "26.7", 100 * rt("difficulty", "short").rate, tail="%")
num("Sec 3.1", "Disagreement, very very long", "38.6", 100 * rt("difficulty", "very_very_long").rate, tail="%")
add("Sec 3.1", "Disagreement rises with difficulty", "rises", "26.7, 26.4, 29.3, 36.2, 38.6", status="overclaimed", note="Medium is below short, so the rise is not monotone. Pooled across modes with ON shares equal by difficulty.")
for task, rep in [("date_recurrence", "65.1"), ("day_of_week", "55.2"), ("date_duration", "12.7"), ("date_addition", "14.9")]:
    r = rt("task", task)
    num("Sec 3.1", f"Disagreement, {task}", rep, 100 * r.rate, tail="%", note=f"Answered only, strict {100 * r.strict_rate:.1f}%.")
add("Sec 3.1", "Disagreement varies most by task", "qualitative", "task range 12.7 to 65.1 vs difficulty 26.4 to 38.6 vs insertion 30.7 to 32.2")
num("Sec 3.1", "Insertion range low", "30.7", 100 * rt("insertion", "no_insertion").rate, tail="%")
num("Sec 3.1", "Insertion range high", "32.2", 100 * rt("insertion", "dissimilar_insertion").rate, tail="%")
ip = pd.read_csv(TAB / "t18_insertion_paired.csv")
x = ip[(ip.contrast == "dissimilar_insertion") & (ip.outcome == "disagree")].iloc[0]
y = ip[(ip.contrast == "similar_insertion") & (ip.outcome == "disagree")].iloc[0]
add("Sec 3.1", "Insertion type has almost no effect on disagreement", "almost no effect", f"paired OFF, vs no insertion: similar {y.diff_pp:+.1f} pp [{y.lo:.1f}, {y.hi:.1f}], dissimilar {x.diff_pp:+.1f} pp [{x.lo:.1f}, {x.hi:.1f}]", note="Holds. The answered-only rates do hide that similar distractors raise the exclusion rate to 5.7% vs 4.0%.")
num("Sec 3.2", "Mean RDS, agree", "0.809", mw.loc["all", "mean_agr"])
num("Sec 3.2", "Mean RDS, disagree", "0.917", mw.loc["all", "mean_dis"], note="OFF 0.918; by distractor in OFF 0.916, 0.918, 0.918.")
num("Sec 3.2", "Median RDS, agree", "0.828", mw.loc["all", "median_agr"])
num("Sec 3.2", "Median RDS, disagree", "0.933", mw.loc["all", "median_dis"])
add("Sec 3.2", "Mann-Whitney p < 0.001", "p < 0.001", f"p iid < 1e-300; cluster bootstrap AUC CI excludes 0.5", status="overclaimed", note="The test assumes independent pairs, and the three variants of a question are not. The conclusion survives clustering, but the gap is largely built in by answer tokens.")
num("Sec 3.2", "A disagreeing pair has higher RDS than an agreeing pair 80% of the time", "80", 100 * mw.loc["all", "u_share"], tail="%", status="overclaimed", note=f"U share {mw.loc['all', 'u_share']:.3f} counts ties as half; strictly greater {mw.loc['all', 'strict_greater']:.3f}; cluster CI [{mw.loc['all', 'cl_lo']:.3f}, {mw.loc['all', 'cl_hi']:.3f}]; OFF {mw.loc['off', 'u_share']:.3f}. Answer tokens removed {v('noans', 'primary').auc_view_alone:.3f}; op types without answers {v('opsnoans', 'primary').auc_view_alone:.3f}. Stable across distractors (0.794, 0.784, 0.788 in OFF).")
add("Fig 1", "RDS distribution by agreement, dashed lines at medians", "plot", "fig_data/fig1_rds_distribution.csv matches: OFF medians 0.833, 0.933, n 13019, 6452; ON medians 0.769, 0.923, n 1160, 31", note="Density axes differ between panels. The ON disagree curve rests on 31 pairs.")
add("Fig 2", "Observed rate by RDS bin, Wilson 95% CI", "plot", "fig_data/fig2_rate_by_rds_bin.csv matches plotted points: OFF 0.000, 0.000, 0.027, 0.026, 0.092, 0.277, 0.572; ON 0.000, 0.000, 0.000, 0.012, 0.029, 0.138", note="Wilson intervals ignore clustering, and cluster bootstrap intervals are in the same CSV. Zero-event bins cannot be bootstrapped.")
TABLE = [("primary", "Primary", "20,662", "15.94", "4.93", "4.58", "5.30", "22.9", "yes"), ("length_adjusted", "Length-adjusted", "20,662", "17.20", "5.58", "5.18", "6.03", "24.5", "yes"), ("off_adjusted", "OFF, adjusted", "19,471", "15.83", "4.87", "4.53", "5.24", "24.0", "yes"), ("off_rds_only", "OFF, RDS only", "19,471", "13.92", "4.02", "3.81", "4.25", "24.0", "yes"), ("on_adjusted", "ON, adjusted", "1,191", "24.67", "11.79", "4.90", "28.37", "4.6", "no"), ("on_rds_only", "ON, RDS only", "1,191", "20.46", "7.74", "3.49", "17.18", "4.6", "yes")]
for key, label, n, b, o, lo, hi, a, rel in TABLE:
    m = models.loc[key]
    num("Table 2", f"{label}: n", n, m.n)
    num("Table 2", f"{label}: beta", b, m.beta)
    num("Table 2", f"{label}: OR per 0.1", o, m["or_per_0.1"], LR, note="Holds arithmetically; includes answer-token leakage.")
    num("Table 2", f"{label}: OR CI low", lo, m.or_lo, LR)
    num("Table 2", f"{label}: OR CI high", hi, m.or_hi, LR)
    note = {"off_adjusted": "Unrounded 23.96; identical to the next row only after rounding (24.02).", "off_rds_only": "Unrounded 24.02.", "on_adjusted": f"Unrounded 4.60, from a non-converged fit. Base rate is 2.6%, so a derivative of 4.6 pp per 0.1 exceeds the base rate; finite +0.1 with RDS capped at 1 gives {ame.loc[key, 'finite_diff_clipped_pp']:.1f} pp.", "on_rds_only": f"Unrounded 4.64; finite +0.1 capped {ame.loc[key, 'finite_diff_clipped_pp']:.1f} pp.", "primary": f"Derivative times 0.1. Finite +0.1 uncapped {ame.loc[key, 'finite_diff_unclipped_pp']:.1f}, capped at RDS 1 {ame.loc[key, 'finite_diff_clipped_pp']:.1f}; {100 * ame.loc[key, 'share_rds_gt_0.9']:.0f}% of pairs lie above 0.9.", "length_adjusted": f"Finite +0.1 capped {ame.loc[key, 'finite_diff_clipped_pp']:.1f}."}[key]
    num("Table 2", f"{label}: AME pp per 0.1", a, m["ame_pp_per_0.1"], LR, note=note)
    if key == "on_adjusted":
        add("Table 2", f"{label}: Reliable", "no", "correct: converged=False, time_duration coefficient -22.6, EPV 2.1", LR)
    elif key == "on_rds_only":
        add("Table 2", f"{label}: Reliable", "yes", f"numerically usable: converged; Firth OR {firth.loc['ON, content, full, x only', 'or_per_0.1']:.2f} [{firth.loc['ON, content, full, x only', 'or_lo_profile']:.2f}, {firth.loc['ON, content, full, x only', 'or_hi_profile']:.2f}]; statsmodels prints a quasi-separation note (11% of observations predicted perfectly)", LR, "overclaimed", "'Reliable' is a check of the optimiser only. This row has no controls, 31 events, and answer-token leakage; AUC falls from 0.86 to 0.60 on op types without answers. The script's check ignores the separation note.")
    else:
        add("Table 2", f"{label}: Reliable", "yes", f"converged, EPV {m.epv:.0f}", LR, "overclaimed", "Numerically sound. 'Reliable' does not cover the validity threats: leakage, exclusions, between-question confounding.")
add("Sec 3.3", "All RDS coefficients positive with p < 0.001", "all p < 0.001", "all six positive with p < 0.001", LR, "overclaimed", "The p-value on the non-converged ON adjusted fit is not valid. Firth p < 0.001 there. With op types and no answers, the primary p is still < 0.001 but OR per SD is only 1.14.")
add("Sec 3.3", "Holding controls fixed, a 0.1 increase multiplies the odds by 4.93", "4.93", f"{models.loc['primary', 'or_per_0.1']:.2f}; answer tokens removed {v('noans', 'primary')['or_per_0.1']:.2f}; answers and answer-valued tokens removed {v('noansval', 'primary')['or_per_0.1']:.2f}; op types {v('ops', 'primary')['or_per_0.1']:.2f}; op types no answers {v('opsnoans', 'primary')['or_per_0.1']:.2f}", LR, "overclaimed", "Number holds. Reading it as evidence about reasoning divergence does not, because most of the slope comes from answer tokens. Within-distractor ORs 5.37, 4.60, 4.95.")
add("Sec 3.3", "About 23 percentage points per 0.1 of RDS", "about 23", f"derivative {models.loc['primary', 'ame_pp_per_0.1']:.1f}; finite capped {ame.loc['primary', 'finite_diff_clipped_pp']:.1f}; observed OFF bin steps +6.6, +18.5, +29.5 pp", LR, "overclaimed", "The AME is an average tangent slope, not a step that holds across the range. Plausible against the 31.4% base rate only as a local average.")
add("Sec 3.3", "Effect is not linear: predicted disagreement stays near zero below 0.7 and climbs steeply above 0.8 (Figure 2)", "qualitative", "adjusted prediction OFF 0.9% at 0.60, 3.9% at 0.70, 14.7% at 0.80, 40.7% at 0.90; observed 2.6% in 0.6 to 0.7, 9.2% in 0.7 to 0.8, 27.7% in 0.8 to 0.9", LR, "differs", "Figure 2 shows observed rates, not predictions, and observed rates are 2.6 to 2.7% below 0.7 in the bins with support, not zero. The climb starts at about 0.75. 'Not linear' refers to the probability scale; the logit scale is also not linear (spline AIC lower by 70).")
num("Sec 3.3", "Length-adjusted OR", "5.58", models.loc["length_adjusted", "or_per_0.1"], LR)
num("Sec 3.3", "Length gap coefficient", "-1.19", SC["gap_beta"][0], LR, note="p < 0.001.")
add("Sec 3.3", "Trace length differences do not explain the association", "negative gap coefficient", f"gap alone beta {lm.loc['gap only', 'gap_beta']:+.2f}; with RDS {lm.loc['rds + gap', 'gap_beta']:+.2f}; floor + excess parameterisation of the same model gives floor {lm.loc['floor + excess', 'gap_beta']:+.2f}, excess {lm.loc['floor + excess', 'excess_beta']:+.2f}", LR, "overclaimed", f"The negative sign comes from RDS being bounded below by the gap, so it says nothing about length explaining the slope. VIF is modest ({lc.loc['all', 'vif_rds']:.2f}, {lc.loc['all', 'vif_gap']:.2f}), r = {lc.loc['all', 'pearson_rds_gap']:.2f}. Floor is 56% of mean RDS. CV AUC with the two lengths 0.769 vs 0.770 with no-answer RDS.")
num("Sec 3.3", "ON disagreement", "2.6", 100 * t1.loc["on", "disagree_rate"], tail="%")
num("Sec 3.3", "OFF disagreement", "33.1", 100 * t1.loc["off", "disagree_rate"], tail="%")
add("Sec 3.3", "Reasoning ON lowers the adjusted odds of disagreement by about 90% (OR 0.10)", "OR 0.10", f"{SC['mode_or_primary'][0]:.3f} [{SC['mode_or_primary'][1]:.3f}, {SC['mode_or_primary'][2]:.3f}]; without RDS {modeor.loc['all_questions, no RDS', 'or_on_vs_off']:.3f}; matched 450 strict {modeor.loc['matched_450, strict outcome, no RDS', 'or_on_vs_off']:.3f} [{modeor.loc['matched_450, strict outcome, no RDS', 'lo']:.3f}, {modeor.loc['matched_450, strict outcome, no RDS', 'hi']:.3f}]", LR, "overclaimed", "OR reproduces but conditions on content RDS, a post-treatment variable on a different kind of text, excludes 11.8% of ON pairs, and 'lowers' implies a causal effect of reasoning alone while budget and question set also change.")
add("Sec 3.3", "RDS slope is positive in both modes", "positive", "positive in content and reasoning channels", LR, note="For content, ON op-type slope Firth OR 1.31 [1.01, 1.74]; 31 events.")
num("Sec 3.3", "ON disagreements", "31", t1.loc["on", "en_only"] + t1.loc["on", "hi_only"])
add("Sec 3.3", "Fully adjusted ON model did not converge because time_duration had zero disagreements", "zero cell", f"time_duration 0 of {oncells.loc['time_duration', 'size']:.0f}; converged=False", LR)
add("Sec 3.3", "Only its RDS-only model should be read", "recommendation", f"Firth with controls is finite: OR {firth.loc['ON, content, full, fully adjusted', 'or_per_0.1']:.2f} profile [{firth.loc['ON, content, full, fully adjusted', 'or_lo_profile']:.2f}, {firth.loc['ON, content, full, fully adjusted', 'or_hi_profile']:.2f}], cluster bootstrap [{firth.loc['ON, content, full, fully adjusted', 'or_lo_clboot']:.2f}, {firth.loc['ON, content, full, fully adjusted', 'or_hi_clboot']:.2f}]", LR, "overclaimed", "A Firth fit was available. Reading the unadjusted model instead removes every control; and EPV 2.1 still limits the adjusted fit.")
add("Sec 4", "Observational; both may reflect question difficulty not captured by controls", "limitation", f"Within-question fixed effects keep a slope for full RDS ({within.loc['full', 'or_per_0.1']:.2f}), and it falls to {within.loc['opsnoans', 'or_per_0.1']:.2f} on op types without answers", note="Correct but misses the larger issue: the outcome is partly built into the predictor.")
num("Sec 4", "OFF share of pooled sample", "94", 100 * SC["share_off"], tail="%")
num("Sec 4", "Hindi failures as share of disagreements", "92", 100 * SC["en_share_of_disagree"], tail="%")
num("Sec 4", "Pairs with RDS above 0.7", "88", 100 * SC["share_rds_gt_0.7"], tail="%", note="Slope below 0.7 is OR 2.36 per 0.1; 0.7 to 0.9 is 4.54; above 0.9 is 6.44.")
add("Sec 4", "RDS depends on the parser and edit-distance costs", "limitation", "true; prior audit 3.7% vs 88% CHECK/REVISE in Hindi and English", "tests/ed_audit/outputs/cube_findings/FINDINGS.md")
add("Sec 4", "Pairs with unparseable answers were dropped", "limitation", "true count; see exclusion row", note="Exclusion is informative: 19.6% of day_of_week pairs and 9.1% of date_recurrence pairs are dropped.")
add("Sec 4", "Models describe associations in this dataset, not predictive accuracy", "limitation", "correct, and then contradicted by 'useful signal' in Sec 5", status="reproduced")
add("Sec 5", "RDS strongly associated with different correctness outcomes", "strong", f"Full RDS OR per SD {v('full', 'primary').or_per_sd:.2f}; no answers {v('noans', 'primary').or_per_sd:.2f}; op types no answers {v('opsnoans', 'primary').or_per_sd:.2f}", status="overclaimed", note="Strong only with answer tokens counted.")
add("Sec 5", "Holds after controlling for difficulty, task, insertion, mode and length", "holds", f"Holds for RDS; for op types no answers length-adjusted OR per SD {v('opsnoans', 'length_adjusted').or_per_sd:.2f} [{v('opsnoans', 'length_adjusted').or_sd_lo:.2f}, {v('opsnoans', 'length_adjusted').or_sd_hi:.2f}]", status="overclaimed", note="Sign holds, size does not. Within nine tasks, only date_recurrence and day_of_week survive Holm within question on op types.")
add("Sec 5", "RDS is a useful signal of cross-lingual reasoning inconsistency", "useful signal", f"CV AUC delta: full {d('full').delta_auc:+.3f}, no answers {d('noans').delta_auc:+.3f} [{d('noans').lo:.3f}, {d('noans').hi:.3f}], op types no answers {d('opsnoans').delta_auc:+.4f} [{d('opsnoans').lo:.4f}, {d('opsnoans').hi:.4f}]; comparing final answers alone AUC {SC['answers_differ_rule']['auc']:.3f}", status="overclaimed", note="Not supported. RDS is also highest on both-wrong pairs (0.925), which count as agreement, so it does not track cross-lingual inconsistency specifically.")
add("Sec 5", "Analysis is correlational and does not show divergence causes the errors", "caveat", "correct and still too weak: the reverse direction is partly arithmetic, since a wrong answer raises RDS by construction")

for r in rows:
    if r["status"] == "differs" and r["reported_value"] in {"4.93", "6.03", "11.79", "28.37"}:
        r["note"] = "Double rounding: the report rounded the 3-decimal value in findings.md. Difference of 0.01. " + r["note"]

with open(OUT / "claims.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
print(pd.DataFrame(rows).status.value_counts().to_string())
print(pd.DataFrame(rows)[lambda t: t.status == "differs"][["claim_id", "claim_text", "reported_value", "recomputed_value"]].to_string())
