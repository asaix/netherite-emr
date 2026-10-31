import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
V = json.load(open(HERE / "verify_results.json", encoding="utf-8"))
X = json.load(open(HERE / "verify_extra.json", encoding="utf-8"))
E1 = "experiments/2026-10-27_trace-deletion-selfhost"
E2 = "experiments/2026-10-29_distractor-resampling"
AN = json.load(open(ROOT / E2 / "outputs/resample/analysis.json", encoding="utf-8"))["groups"]
A1 = {r: json.load(open(ROOT / E1 / f"outputs/selfhost_{r}/analysis.json", encoding="utf-8"))["by_language"] for r in "GS"}
SRC2 = f"{E2}/outputs/resample/round_*/results.json"
SRC1 = f"{E1}/outputs/selfhost_{{G,S}}/results.json"
rows = []
n = [0]


def add(loc, text, rep, rec, src, status, note=""):
    n[0] += 1
    rows.append({"claim_id": f"B{n[0]:03d}", "location": loc, "claim_text": text, "reported_value": rep, "recomputed_value": rec, "source_path": src, "status": status, "note": note})


def s1(x):
    return f"{x:+.1f}"


def ci(m, c):
    return f"{m:+.1f} [{c[0]:+.1f}, {c[1]:+.1f}]"


def rd(x):
    return f"{x:.1f}"


FUN = V["funnel"]
HI, EN = FUN["hi_IN|similar_insertion"], FUN["en_US|similar_insertion"]
add("B.1", "English CoT responses with time-related distractor", "6,750", str(EN["responses"]), "responses/standard/*.json", "reproduced")
add("B.1", "Hindi CoT responses with time-related distractor", "6,747", f"{HI['responses']} in responses/standard; 6,747 in {E1}/outputs/funnel.json", f"{E1}/outputs/funnel.json", "differs", "The trace build used the earlier run folders, before the last 3 Hindi very_very_long responses were completed. responses/standard now has 6,750 (right 3,897 vs 3,894; wrong and cut-off counts unchanged). State 6,750 or say the count is from the build date. Eligibility is unaffected.")
add("B.1", "Eligible Hindi traces", "526", str(HI["wrong_pre_answer"]), "responses/standard/*.json (independent rule)", "reproduced", "Independent reimplementation returns the same 563 ids as requests_resample.json (0 differences).")
add("B.1", "Eligible English traces", "37", str(EN["wrong_pre_answer"]), "responses/standard/*.json (independent rule)", "reproduced")
add("B.1", "Hindi eligible share of wrong answers", "18.8%", f"{HI['eligible_share_of_wrong_pct']:.1f}% (526/{HI['wrong']})", "responses/standard/*.json", "reproduced", "Denominator is answered wrong responses; unanswered excluded.")
add("B.1", "English eligible share of wrong answers", "4.7%", f"{EN['eligible_share_of_wrong_pct']:.1f}% (37/{EN['wrong']})", "responses/standard/*.json", "reproduced")
add("B.1", "Mention rule: >=2 strict words or 1 rare word (<2% of no-distractor traces), months and weekdays excluded", "rule", "same rule in build_resample.py and in the reimplementation", f"{E2}/build_resample.py", "reproduced", "Excluding calendar words misses traces that use the distractor's month or weekday only: 191 Hindi and 63 English wrong traces contain such a word but no strict mention.")
add("B.1", "Rule is stricter than the mid-report rule", "stricter", "PLAN.md states it; loose any-word rule flags 1,116 Hindi wrong vs 731 strict", f"{E1}/PLAN.md", "reproduced")
add("B.1", "Sarvam API cannot continue a partial trace", "treated as a finished turn and restarted", "PLAN.md describes it; outputs/diag/continuation_diag.json is not in the repo", f"{E1}/PLAN.md", "source_missing", "Only the text of PLAN.md and pre_final_run_archive/diag.py remain. Not recomputable without API calls.")
add("B.1", "Model and server", "RedHatAI/sarvam-105b-FP8-dynamic, vLLM 0.31.0, two H100", "README and gpu/serve_rh.sh agree", f"{E1}/README.md", "reproduced", "outputs/logs named in README are not in the repo; bring-up logs cannot be checked.")
add("B.1", "Thinking off as in the main study", "thinking off", "API: all 40,500 CoT records have null reasoning_content, one user message, temperature 0. Self-hosted: enable_thinking=false, prefill <think></think>, reasoning_content null in all 13,664 rollouts", "responses/standard; gpu/continue.py; sarvam-105b-fp8 chat_template.jinja", "overclaimed", "Same visible behaviour, different mechanism. The API server prompt is not observable. In fresh sanity requests the self-hosted model opened with <think> reasoning despite enable_thinking=false, so thinking-off holds only because of the prefill. 89 rollouts still contain a think tag.")
cal = V["calibration_90"]
add("B.1", "Calibration size", "90 questions", str(cal["S|all"]["n"]), f"{E1}/outputs/selfhost/calibration_*_S.json", "reproduced", "45 per language, one question per language x task x difficulty, one sample each.")
add("B.1", "Sampling calibration overall self vs API", "71.1 vs 73.3", f"{rd(cal['S|all']['self'])} vs {rd(cal['S|all']['api'])}; diff {ci(cal['S|all']['diff'], cal['S|all']['boot_ci'])}", f"{E1}/outputs/selfhost/calibration_*_S.json", "overclaimed", "Numbers hold. 'Matched' does not: the interval allows about 13 points either way.")
add("B.1", "Sampling calibration English", "82.2 vs 84.4", f"{rd(cal['S|en_US']['self'])} vs {rd(cal['S|en_US']['api'])}; diff {ci(cal['S|en_US']['diff'], cal['S|en_US']['boot_ci'])}", f"{E1}/outputs/selfhost/calibration_*_S.json", "overclaimed", "On the 22 opening-mention English traces FP8 Q is 24.7 points below the API on the same no-distractor questions.")
add("B.1", "Sampling calibration Hindi", "60.0 vs 62.2", f"{rd(cal['S|hi_IN']['self'])} vs {rd(cal['S|hi_IN']['api'])}; diff {ci(cal['S|hi_IN']['diff'], cal['S|hi_IN']['boot_ci'])}; discordant {cal['S|hi_IN']['only_self']}/{cal['S|hi_IN']['only_api']}", f"{E1}/outputs/selfhost/calibration_*_S.json", "overclaimed", "One third of Hindi items flip between the two. Equivalence margin at 90% is about 16.5 points.")
add("B.1", "Sampling finished", "89/90", str(cal["S|all"]["finished"]), f"{E1}/outputs/selfhost/calibration_*_S.json", "reproduced", "Calibrated at 12,288 tokens. Experiment 2 ran at 4,096, which was not calibrated with sampling. 3 English outputs exceeded 4,096 tokens, none correct, so scored accuracy would not change.")
add("B.1", "Greedy English", "73.3%", rd(cal["G|en_US"]["self"]), f"{E1}/outputs/selfhost/calibration_*_G.json", "reproduced", f"Difference {ci(cal['G|en_US']['diff'], cal['G|en_US']['boot_ci'])}, McNemar p {cal['G|en_US']['mcnemar_p']:.2f}: not itself a significant gap. G failed the gate on the finished check only.")
add("B.1", "Greedy finished", "81/90", str(cal["G|all"]["finished"]), f"{E1}/outputs/selfhost/calibration_*_G.json", "reproduced")
add("B.2", "Each trace is cut before its answer sentence", "cut before answer sentence", f"Prefix stops at max(k, j). Median {V['exp1_exp2_prefix_map']['sentences_cut_before_answer_median']:.0f} sentences before the answer; only {V['exp1_exp2_prefix_map']['cut_immediately_before_answer']} of 234 stop right before it", f"{E1}/build_requests.py; requests_cap1000.json", "differs", "Say: cut just after the later of the first mention and the matched neutral sentence.")
add("B.2", "B deletes the sentences that mention the distractor", "sentences", f"Exactly one sentence in all 234 ({V['exp1_exp2_prefix_map']['multi_deleted']} traces delete more)", f"{E1}/outputs/requests_cap1000.json", "differs", "Mentions after the cut are not in the prefix at all, so B removes one sentence.")
add("B.2", "Requiring neutral sentences leaves", "234 (222 Hindi, 12 English)", "234 (222, 12)", f"{E1}/outputs/funnel.json; exp1_prefix_map.csv", "reproduced", "This filter selects: M-P is -1.0 in the 222 and -5.0 in the other 304 Hindi traces, difference +4.0 [+0.1, +8.1].")
add("B.2", "Up to 12,288 tokens, A run twice", "12,288; A repeated", "12,288; 234 repeats per decoding", SRC1, "reproduced", "Repeat used the same seed 0, so flips reflect batching nondeterminism in both decodings.")
for run, lab in [("G", "G"), ("S", "S")]:
    for lang, ln in [("hi_IN", "Hindi"), ("en_US", "English")]:
        t = V["table_b1"][f"{run}|{lang}"]
        a = A1[run][lang]
        rep = {("G", "hi_IN"): ("33.3", "33.8", "33.8", "+0.0 [-6.8, +7.2]", "32 / 32", "1.00"), ("G", "en_US"): ("25.0", "16.7", "25.0", "-8.3 [-25.0, +0.0]", "0 / 1", "1.00"), ("S", "hi_IN"): ("29.3", "32.9", "28.4", "+4.5 [-2.7, +11.7]", "37 / 27", "0.26"), ("S", "en_US"): ("25.0", "33.3", "25.0", "+8.3 [+0.0, +25.0]", "1 / 0", "1.00")}[(run, lang)]
        for key, r0, v0 in [("A", rep[0], rd(t["A"])), ("B", rep[1], rd(t["B"])), ("C", rep[2], rd(t["C"]))]:
            add("Table B1", f"{lab} {ln} accuracy {key}, n={t['n']}", r0, v0, SRC1, "reproduced" if r0 == v0 else "differs")
        printed = ci(100 * a["B_minus_C"], [100 * x for x in a["B_minus_C_ci95"]])
        add("Table B1", f"{lab} {ln} B-C with CI", rep[3], f"analysis.json {printed}; independent {ci(t['B-C'], t['ci'])}", SRC1, "reproduced" if printed.replace("-0.0", "+0.0") == rep[3] else "differs", "Independent interval differs only by Monte Carlo error. These use 2,000 resamples and seed 26, unlike Table B4's 5,000." + (" With n=12 the bootstrap is degenerate; do not print it." if lang == "en_US" else ""))
        add("Table B1", f"{lab} {ln} only B / only C", rep[4], f"{t['only_B']} / {t['only_C']}", SRC1, "reproduced")
        add("Table B1", f"{lab} {ln} McNemar p", rep[5], f"{t['p']:.2f}", SRC1, "reproduced")
add("B.2", "Deleting the distractor did not help", "did not help", "Hindi B-C +0.0 and +4.5, both CIs include 0", SRC1, "overclaimed", "Only 'no detectable benefit' is supported. Power for a true 5-point effect is about 24%.")
add("B.2", "Hindi B re-mention, sampling", "35.1%", rd(V["exp1_remention"]["S|hi_IN|B"]["whole_text_rule_pct"]) + "%", SRC1, "reproduced", "'Wrote it back' needs care: the distractor is still in the question, and C (mention kept) re-mentions at 31.5%. The whole-text and sentence rules give identical rates here.")
add("B.2", "Hindi A re-mention, sampling", "34.7%", rd(V["exp1_remention"]["S|hi_IN|A"]["whole_text_rule_pct"]) + "%", SRC1, "reproduced")
add("B.2", "Rerunning A flips right/wrong, Hindi greedy", "38 of 222", f"{V['exp1_repeat']['G|hi_IN']['flip_right_wrong']} of 222", f"{E1}/outputs/selfhost_G/results_repeat.json", "reproduced")
add("B.2", "Rerunning A flips right/wrong, Hindi sampling", "53 of 222", f"{V['exp1_repeat']['S|hi_IN']['flip_right_wrong']} of 222", f"{E1}/outputs/selfhost_S/results_repeat.json", "reproduced")
ru = V["exp1_runaways"]
add("B.2", "Cut off, greedy", "102 of 702 (14.5%)", f"{ru['G']['cutoff']} ({ru['G']['unanswered_pct']:.1f}%)", SRC1, "reproduced", f"{ru['G']['cut_without_answer']} have no Answer line by metrics.py, 4 have one; README's 99 uses continue.py's regex.")
add("B.2", "Cut off, sampling", "40 (5.7%)", f"{ru['S']['cutoff']} ({ru['S']['unanswered_pct']:.1f}%)", SRC1, "reproduced")
add("B.2", "Repetition loops among cut-offs, greedy", "80 of 102", f"{X['loop_exp1_last60']['G']['last60_seen_3x']} of 102 with last-60-characters-seen-3-times; 70 with adjacent periodic repetition", SRC1, "source_missing", "noise_and_loops.py missing. The rule was reverse engineered: it reproduces all four printed counts exactly. It is not adjacent repetition.")
add("B.2", "Repetition loops among cut-offs, sampling", "34 of 40", f"{X['loop_exp1_last60']['S']['last60_seen_3x']} of 40 same rule; 31 adjacent", SRC1, "source_missing", "As above.")
add("B.2", "Null could reflect method limits; hand edits tend to be repaired (Macar et al.)", "cited", "Macar et al. support regeneration and off-policy weakness in decision tasks; their MATH appendix finds handwritten edits have strong local effects", "citations.md", "overclaimed", "Transfer to arithmetic-like tasks is not established by the source.")
tc = V["trace_counts"]
add("B.3", "All traces used", "563", str(tc["traces"]), SRC2, "reproduced")
add("B.3", "First sentence already mentions", "300 (278 Hindi, 22 English)", f"{tc['opening_hi'] + tc['opening_en']} ({tc['opening_hi']}, {tc['opening_en']})", SRC2, "reproduced")
add("B.3", "Rounds and seeds", "7 rounds, new seed", f"7 rounds of 1,952, seed = round, 13,664 rollouts, {tc['time_min'][:16]} to {tc['time_max'][:16]} UTC", SRC2, "reproduced", "Same seed for all requests in a round. Round count was set by GPU budget, not by results.")
add("B.3", "Sampling and token limit", "T 0.8, top-p 0.95, 4,096", "all 13,664 records", SRC2, "reproduced", "The API traces were written at temperature 0, so continuation policy differs from trace policy.")
add("B.3", "Design and primary contrasts fixed in the README before the run", "fixed before the run", "First git appearance: commit ee32fd1 authored 2026-10-30 17:43 UTC, about 24.5 h after the last round (2026-10-29 17:11 UTC). All files arrive in one commit", f"git log; gh pr view 12; {E2}/README.md", "unverifiable", "Internal evidence supports it (future-tense limitations, NOTES.md records a mock run of analyze_resample.py before boot, requests MD5-matched), but no timestamp predates results. Design was chosen after seeing Experiment 1 on 234 of the same traces.")
add("Appendix A", "Q-P row graded Strong (pre-registered)", "pre-registered", "No registry entry and no commit before the run", "git log", "overclaimed", "Use: specified in advance in an internal design document, per our run notes; not publicly registered and not verifiable from version control.")
add("Table B2", "Example arms for long/date_recurrence_hi_IN/12", "Q 5/7, P 2/7, M 0/7, P1 2/7", f"Q {V['example_b2']['Q']}, P {V['example_b2']['P']}, M {V['example_b2']['M']}, P1 {V['example_b2']['P1']}", SRC2, "reproduced")
add("Table B2", "Example gold and original answer", "gold 2027-08-15, answered 2027-04-20", "2027-08-15, 2027-04-20; mention at sentence 2", f"{E2}/outputs/requests_resample.json", "reproduced")
b3 = {"Hindi, all": ("526", "45.2", "40.0", "36.7", None), "Hindi, opening": ("278", "56.0", "50.7", "49.1", None), "Hindi, later": ("248", "33.1", "27.9", "22.7", "28.6"), "English, all": ("37", "48.3", "31.3", "17.0", None), "English, opening": ("22", "61.7", "37.0", "16.2", None), "English, later": ("15", "28.6", "22.9", "18.1", "27.6")}
for g, (cnt, q, p, m, p1) in b3.items():
    t = V["table_b3_b4"][g]
    add("Table B3", f"{g} traces", cnt, str(t["n"]), SRC2, "reproduced")
    for arm, r0 in [("Q", q), ("P", p), ("M", m), ("P1", p1)]:
        if r0:
            v0 = rd(t["acc"][arm])
            add("Table B3", f"{g} accuracy {arm}", r0, v0, SRC2, "reproduced" if r0 == v0 else "differs", "Strict: unanswered count as wrong. All rows are similar_insertion only.")
MAP = {"Hindi, all": "hi_IN", "Hindi, opening": "hi_IN, mention in opening sentence", "Hindi, later": "hi_IN, mention later", "English, all": "en_US", "English, opening": "en_US, mention in opening sentence", "English, later": "en_US, mention later"}
b4 = {
    ("Hindi, all", "Q-P", "Q - P"): ("+5.3 [+3.2, +7.4]", "<0.001"), ("Hindi, all", "M-P", "M - P"): ("-3.3 [-5.4, -1.2]", "0.002"), ("Hindi, all", "P-P1", "P - P1"): ("-0.7 [-3.5, +2.1]", "0.66"), ("Hindi, all", "DiD", "(M - P) - (P - P1)"): ("-4.6 [-9.6, +0.6]", "0.09"),
    ("Hindi, opening", "Q-P", "Q - P"): ("+5.3 [+2.4, +8.2]", "<0.001"), ("Hindi, opening", "M-P", "M - P"): ("-1.5 [-4.2, +1.2]", "0.29"),
    ("Hindi, later", "Q-P", "Q - P"): ("+5.2 [+2.4, +8.1]", "<0.001"), ("Hindi, later", "M-P", "M - P"): ("-5.2 [-8.3, -2.2]", "0.001"), ("Hindi, later", "P-P1", "P - P1"): ("-0.7 [-3.5, +2.2]", "0.66"), ("Hindi, later", "DiD", "(M - P) - (P - P1)"): ("-4.6 [-9.6, +0.5]", "0.09"),
    ("English, all", "Q-P", "Q - P"): ("+17.0 [+8.9, +25.5]", "<0.001"), ("English, all", "M-P", "M - P"): ("-14.3 [-25.1, -4.2]", "0.02"), ("English, all", "P-P1", "P - P1"): ("-4.8 [-13.3, +3.8]", "0.43"), ("English, all", "DiD", "(M - P) - (P - P1)"): ("+0.0 [-22.9, +23.8]", "1.00"),
    ("English, opening", "Q-P", "Q - P"): ("+24.7 [+14.3, +35.1]", "<0.001"), ("English, opening", "M-P", "M - P"): ("-20.8 [-33.8, -7.8]", "0.006"),
    ("English, later", "Q-P", "Q - P"): ("+5.7 [-2.9, +16.2]", "0.36"), ("English, later", "M-P", "M - P"): ("-4.8 [-22.9, +11.4]", "0.72"), ("English, later", "P-P1", "P - P1"): ("-4.8 [-13.3, +2.9]", "0.43"), ("English, later", "DiD", "(M - P) - (P - P1)"): ("+0.0 [-21.9, +21.9]", "1.00"),
}
for (g, key, anname), (r0, pr) in b4.items():
    c = AN[MAP[g]]["contrasts"][anname]
    mine = V["table_b3_b4"][g][key]
    ptxt = ci(100 * c["mean"], [100 * x for x in c["ci95"]]).replace("-0.0 ", "+0.0 ")
    same = ptxt == r0
    add("Table B4", f"{g} {anname}", r0, f"analysis.json {ptxt}; independent {ci(mine['mean'], mine['ci'])}", SRC2, "reproduced" if same else "differs", "Independent interval differs only by Monte Carlo error.")
    add("Table B4", f"{g} {anname} p", pr, f"analysis.json {c['p']:.4g}; independent {mine['p']:.4g}", SRC2, "reproduced")
add("Table B4", "Resamples and permutations", "5,000 and 20,000", "config/resample.cfg", f"{E2}/config/resample.cfg", "reproduced")
add("Figure B1", "Forest plot of Q-P, M-P, P-P1 by group", "Table B4 values", "fig_data/fig_b1_contrasts.csv", SRC2, "reproduced", "Checked against the rendered page. Panel values match Table B4.")
ef = V["excess_fraction"]
add("B.3", "Distractor causes a minority of these errors", "minority", f"Excess fraction {ci(ef['Hindi, all']['excess_fraction_pct'], ef['Hindi, all']['ci'])}% Hindi, {ci(ef['English, all']['excess_fraction_pct'], ef['English, all']['ci'])}% English", SRC2, "overclaimed", "Excess fraction over new continuations, from the first-mention point onward, on traces selected for being wrong. It is a lower bound on the share in which the distractor was necessary, and excludes any influence on the text before k for later mentions. Cluster bootstrap over distractor sentences includes 0.")
add("B.3", "Hindi wrong with distractor", "60.0%", rd(ef["Hindi, all"]["wrong_P"]) + "%", SRC2, "reproduced")
add("B.3", "Hindi wrong without distractor", "54.8%", rd(ef["Hindi, all"]["wrong_Q"]) + "%", SRC2, "reproduced")
add("B.3", "About one error in eleven", "1 in 11", f"1 in {ef['Hindi, all']['one_in']:.1f} (8.8%, 95% CI 5.5 to 12.1, or 1 in 8 to 1 in 18)", SRC2, "overclaimed", "Arithmetic holds. 'Due to the distractor' and 'fixes' misdescribe it: among the original errors, a fresh continuation is right 45.2% without the distractor and 40.0% with it.")
add("B.3", "One in four in English", "1 in 4; 68.7% vs 51.7%", f"1 in {ef['English, all']['one_in']:.1f}; {rd(ef['English, all']['wrong_P'])} vs {rd(ef['English, all']['wrong_Q'])}; 95% CI 13.6 to 35.9%", SRC2, "overclaimed", "22 opening traces drive it (39% vs 7% later). 17 of 37 use one distractor sentence. FP8 is far below the API on these questions.")
add("B.3", "Reading a wrong trace that engages the distractor mostly misattributes the error", "mostly misattributes", "Supported only as: most errors recur without the distractor", SRC2, "overclaimed", "Only 18.8% of Hindi wrong answers are in scope, and the conclusion is about continuation after k.")
add("B.3", "Written mention matters only in the middle of the reasoning", "only in the middle", f"Later minus opening M-P {ci(V['hi_MP_later_minus_opening']['diff'], V['hi_MP_later_minus_opening']['ci'])}; k=1 {ci(X['P_minus_P1_by_k']['M-P k=1']['mean'], X['P_minus_P1_by_k']['M-P k=1']['ci'])}; k>=2 {ci(X['P_minus_P1_by_k']['M-P k>=2']['mean'], X['P_minus_P1_by_k']['M-P k>=2']['ci'])}", SRC2, "overclaimed", "The split is exploratory, the interaction is not significant, and the effect is largest at the second sentence, not mid-reasoning.")
add("B.3", "Model typically builds the distractor into its computation in later mentions", "typically", "Hand-coded random sample of 30: 12 used in reasoning (40%), 14 restated, 2 dismissed, 1 incidental, 1 detector false positive. 54% contain digits. M-P is -5.3 with digits, -5.1 without", f"{E2}/outputs/requests_resample.json", "overclaimed", "Single coder (this audit), small sample. No analysis in the repo supports 'typically'.")
add("B.3", "Opening mention is usually a remark", "usually", "Hand-coded random sample of 20: 14 restate, acknowledge or dismiss; 5 set out to interpret it; 1 false positive", f"{E2}/outputs/requests_resample.json", "reproduced", "Single coder, small sample. Holds for Hindi. English opening mentions (22/22) are problem framings that embed the distractor, not remarks.")
add("B.3", "Ordinary sentence at the same place has almost none", "-0.7 [-3.5, +2.1]; almost none", "same", SRC2, "overclaimed", "Interval allows -3.5. It is the sentence before the mention, not at the same place. 104 of 248 have P1 as an empty prefix.")
add("B.3", "Six primary tests, Bonferroni 0.0083", "6; 0.0083", "README lists 3 contrasts per language = 6; 0.05/6 = 0.00833", f"{E2}/README.md", "reproduced", "Count matches. The README states no correction; Bonferroni is post hoc. Team convention is Holm.")
add("B.3", "Hindi Q-P, Hindi M-P, English Q-P significant; English M-P (p=0.02) not", "as stated", f"Bonferroni: as stated. Holm: English M-P p={X['english_MP_perm_4M']['p']:.4f} (4M permutations) vs threshold 0.0167, so it passes narrowly", SRC2, "overclaimed", "The verdict on English M-P depends on the correction, and answered-only English Q-P (p=0.017) fails Bonferroni.")
add("B.3", "Experiment 1's null was real", "real", f"Power 24% at 5 points, 50% at 7.5, 78% at 10; SE {V['exp1_power']['S']['se_pts']:.1f} points", SRC1, "overclaimed", "Use: Experiment 1 cannot separate no effect from the 3 to 5 point effects Experiment 2 finds.")
t222 = V["table_b3_b4"]["Hindi, trace-deletion 222"]
add("B.3", "222 Hindi M-P", "-1.0 [-3.9, +1.9]", ci(t222["M-P"]["mean"], t222["M-P"]["ci"]), SRC2, "reproduced", "On 115 traces deletion and forcing are literally the same prefix pair (A=M, B=P), M-P -1.6 [-6.1, +2.7]. On the other 107 they differ, so M-P does not test B there.")
add("B.3", "222 Hindi Q-P", "+7.6 [+4.6, +10.6]", ci(t222["Q-P"]["mean"], t222["Q-P"]["ci"]), SRC2, "reproduced")
add("B.3", "On those traces the distractor acts through the question, not the mention", "through the question", "Q-P includes re-mention in the continuation (P mentions 57.4%), so it is not a mention-free path", SRC2, "overclaimed", "Not identified. See analysis.md.")
cr = V["cutoff"]
add("B.3", "Cut-off rate per round", "9.4% to 11.9%", f"{cr['min']:.1f}% to {cr['max']:.1f}%", SRC2, "source_missing", "noise_and_loops.json missing; recomputed from rounds, matches.")
add("B.3", "Hindi loop cut-offs", "554 of 1,205", f"{X['loop_tail_grid_exp2']['tail60_offset0_count>=3']['hi_IN']} of {cr['hi']} (last 60 characters occur 3+ times); adjacent periodic: 441 to 536", SRC2, "source_missing", "Count reproduced by a reverse-engineered rule.")
add("B.3", "English loop cut-offs", "93 of 232", f"{X['loop_tail_grid_exp2']['tail60_offset0_count>=3']['en_US']} of {cr['en']} by same rule; adjacent periodic: 30 to 45", SRC2, "source_missing", "'Exact repetition loop' overstates it for English: under half are adjacent loops. Sampled flagged tails include re-solving and hedging about the interpretation.")
add("B.3", "Answered 99th percentile tokens", "3,124", f"{V['answered_tokens']['p99']:.0f}", SRC2, "source_missing", "Recomputed from rounds, matches.")
add("B.3", "Answered above 3,500 tokens", "0.7%", f"{V['answered_tokens']['gt3500_pct']:.1f}%", SRC2, "source_missing", "Recomputed from rounds, matches.")
dc = V["decomposition"]["Hindi, all"]
add("B.3", "Hindi unanswered Q", "5.7%", rd(dc["unanswered_Q"]) + "%", SRC2, "reproduced", f"{E2}/outputs/resample/analysis.json also has it.")
add("B.3", "Hindi unanswered P", "10.0%", rd(dc["unanswered_P"]) + "%", SRC2, "reproduced", f"Difference {ci(V['sensitivity']['Hindi, all']['unanswered_P-Q']['mean'], V['sensitivity']['Hindi, all']['unanswered_P-Q']['ci'])}.")
SN = V["sensitivity"]
for g, k, r0 in [("Hindi, all", "answered_only_Q-P", "+3.6 [+1.5, +5.7]"), ("Hindi, all", "answered_only_M-P", "-3.2 [-5.4, -0.9]"), ("Hindi, later", "answered_only_M-P", "-5.7 [-9.3, -2.2]"), ("Hindi, opening", "answered_only_M-P", "-0.9 [-4.0, +1.9]"), ("English, all", "answered_only_Q-P", "+13.4 [+3.4, +24.3]"), ("English, all", "answered_only_M-P", "-16.4 [-31.3, -1.7]")]:
    x = SN[g][k]
    add("B.3", f"{g} {k}, n={x['n']}", r0, ci(x["mean"], x["ci"]), SRC2, "source_missing", "sensitivity.json missing. Point estimate reproduced; interval within Monte Carlo error. Traces with no answered rollout in an arm drop out." + (" 4 of 37 English traces drop." if g == "English, all" and "M-P" in k else ""))
add("B.3", "All conclusions hold on answered-only", "all hold", f"Hindi not-in-deletion Q-P {ci(SN['Hindi, not in deletion 304']['answered_only_Q-P']['mean'], SN['Hindi, not in deletion 304']['answered_only_Q-P']['ci'])}; English Q-P p {SN['English, all']['answered_only_Q-P']['p']:.3f}", SRC2, "overclaimed", "Signs hold on the main rows. English Q-P no longer passes Bonferroni, and in 304 of 526 Hindi traces answered-only Q-P is not distinguishable from 0. Answered-only also conditions on a post-treatment outcome.")
cp = X["comparability"]["Hindi, all"]
add("B.3", "About a third of the Hindi distractor effect is non-termination", "about a third", f"(5.27-3.62)/5.27 = 31%; midpoint decomposition {dc['completion_share_pct']:.0f}%, 95% CI {cp['completion_share_ci_pct'][0]:.0f} to {cp['completion_share_ci_pct'][1]:.0f}%", SRC2, "overclaimed", "Point value is defensible for these rollouts, but the interval is wide and the rate does not transfer to the API: Hindi API unanswered 0.81% to 0.89%, +0.07 [-0.22, +0.39].")
add("B.3", "Hindi P mixed across runs", "372 of 526", str(V["noise_P"]["hi_IN"]["mixed"]), SRC2, "reproduced", "Also in analysis.json.")
add("B.3", "So single continuations mostly measure chance", "mostly chance", "Reasonable: 71% of traces are mixed", SRC2, "overclaimed", "Mixed status is not a variance share. Use the flip counts instead.")
mr = V["mention_rate"]["Hindi, all"]
add("B.3", "Left free the model mentions", "57.8%", rd(mr["P"]) + "%", SRC2, "reproduced", "Opening 62.4%, later 52.6%. This is what dilutes M-P.")
add("B.3", "Detector false positives on Q", "1.2%", rd(mr["Q"]) + "%", SRC2, "reproduced", "English 4.6%. No false-negative estimate exists. 1 of 30 sampled later mentions was a false positive.")
add("B.4 F1", "Removing the distractor fixes about one in eleven such errors, one in four in English", "as stated", "See excess fraction rows", SRC2, "overclaimed", "Not 'fixes'. Hindi 8.8% [5.5, 12.1]; English 24.7% [13.6, 35.9]; net excess, not repair rate.")
add("B.4 F2", "Distractor acts mainly through the question, not the model's mention", "mainly", f"(Q-P)+(M-P): strict {ci(cp['sum_QP_plus_MP_strict']['mean'], cp['sum_QP_plus_MP_strict']['ci'])}; answered {ci(cp['sum_QP_plus_MP_answered']['mean'], cp['sum_QP_plus_MP_answered']['ci'])}. P rollouts without a mention match Q: {ci(V['P_mention_within']['Hindi, all']['Q_minus_P_no_mention_rollouts']['mean'], V['P_mention_within']['Hindi, all']['Q_minus_P_no_mention_rollouts']['ci'])}", SRC2, "overclaimed", "Not identified, and the data lean the other way. Drop this finding.")
add("B.4 F2", "Deleting or forcing the mention usually changes nothing", "usually", "M-P -3.3 is significant, and finding 3 says the opposite for later mentions", SRC2, "overclaimed", "Internally inconsistent.")
add("B.4 F3", "Later mentions about 5 points in Hindi; direct test non-significant", "about 5", ci(V["table_b3_b4"]["Hindi, later"]["M-P"]["mean"], V["table_b3_b4"]["Hindi, later"]["M-P"]["ci"]), SRC2, "overclaimed", "Number holds and is stable across recurrence and other tasks (-4.9, -5.5). 'When the distractor becomes part of the computation' is not established.")
add("B.4 F4", "Distractor nearly doubles Hindi non-termination", "nearly doubles", "5.7 to 10.0 in FP8 rollouts of wrong traces; API population 0.81 to 0.89", f"{SRC2}; responses/standard", "overclaimed", "Holds only for FP8 at T=0.8 on selected traces. In the API data the rise is in English (+1.6 [+1.0, +2.2]), not Hindi.")
add("B.4 F5", "Hindi engages the distractor more often", "more", "Wrong answers with a pre-answer mention 18.8% vs 4.7%; all answered traces 17.9% vs 5.8%", "responses/standard", "reproduced", "Descriptive. Depends on a language-specific lexical detector.")
gp = V["hindi_english_gap"]["Q-P"]
add("B.4 F5", "English is hurt more when it does", "suggestive", f"Hindi minus English Q-P {ci(gp['hi_minus_en'], gp['ci'])}", SRC2, "overclaimed", "Not defensible as a language finding: heavy selection, 17 of 37 from one distractor, FP8 24.7 points below the API on English opening questions, 71% of the English opening effect is non-completion, cluster CI [-2.9, +22.7] includes 0. API population penalties are equal (2.6 vs 2.3).")
add("B.5", "Regression to the mean leaves arm comparisons unaffected", "unaffected", "True as a null test for Q-P with the same prefix. False for M-P and P-P1, where prefix length differs, and for the size of any effect", f"{E2}/README.md", "overclaimed", "See analysis.md.")
add("B.5", "For later mentions Q-P may understate", "may understate", "Lexical leakage before k is low (6.9% any distractor word); later and opening Q-P are equal (5.2, 5.3)", "api_cot.csv.gz", "reproduced", "A valid caveat, untested beyond lexical leakage.")
add("B.5", "Answered-only analysis gives the same conclusions", "same", "Signs yes, see row above", SRC2, "overclaimed")
add("B.5", "Limitations list", "listed", "Omits: wrong-only selection as a generalisation limit, distractor clustering, calibration CI, temperature difference, FP8 non-termination gap, missing scripts", "analysis.md", "overclaimed")
add("Appendix A", "Distractor causes a minority: Strong (pre-registered)", "Strong", "Moderate", SRC2, "overclaimed", "Over distractor sentences the Hindi CI is [-0.3, +9.4]. Effect concentrated in one task.")
add("Appendix A", "Forcing lowers Hindi accuracy, only for later mentions: Strong overall", "Strong", "Moderate for keeping the sentence lowers accuracy; suggestive for the later-only claim", SRC2, "overclaimed", "M-P cannot separate the mention from one more step along a trace that ended wrong.")
add("Appendix A", "Mention matters more than an ordinary sentence: not significant", "-4.6 [-9.6, +0.6], p=0.09", "same", SRC2, "reproduced", "Effect is -9.5 at k=1 and -1.0 at k>=2; exploratory.")
add("Appendix A", "Deleting does not help: Null; confirmed on the same traces by Experiment 2", "confirmed", "Consistent on 115 traces; not tested on 107", f"{SRC1}; {SRC2}", "overclaimed", "'Confirmed' is too strong: M-P -1.6 [-6.1, +2.7] on 115 still allows a 6-point harm.")
add("Notes", "Full-grid Hindi similar penalty (context only)", "+2.2 [+0.6, +3.8]", "Paired over 6,750 questions: strict +2.59 [+1.38, +3.84]; both answered +2.47", "responses/standard", "differs", "Outside Part B. Convention of the printed value is not stated; flag for the Part A auditor.")
add("Notes", "sensitivity.py, noise_and_loops.py exist in the repository", "exist", "Not in any local ref, working tree or dangling commit checked", "git log --all", "source_missing", "All their numbers were recomputed from round outputs.")
add("Notes", "Every number filled from output files by a script", "script-built", "No such builder is in the repo", "git log --all", "unverifiable")
for key, title, rep, rec, status, note in [
    ("Qin", "Qin et al. 2023 EMNLP", "as printed", "Authors and venue verified on arXiv 2310.14799", "reproduced", ""),
    ("Bogdan", "Bogdan, Macar, Nanda, Conmy 2025, arXiv:2506.19143", "as printed", "Verified", "reproduced", ""),
    ("Macar", "Macar, Bogdan et al. 2026, ICLR 2026, arXiv:2510.27484", "as printed", "Verified. ICLR 2026 poster page exists; arXiv page lists no venue; authors Macar, Bogdan, Rajamanoharan, Nanda", "reproduced", "Cite all four authors."),
    ("Lanham", "Lanham et al. 2023, arXiv:2307.13702", "as printed", "Verified", "reproduced", ""),
    ("Yang", "Yang et al. 2025, arXiv:2506.10979", "arXiv only", "Verified; arXiv comment says Findings of EMNLP 2025", "differs", "Add the venue."),
    ("Turpin", "Turpin et al. 2023 (merge note)", "cited", "Verified, NeurIPS 2023, arXiv:2305.04388", "reproduced", "Missing from the reference list."),
    ("Shi", "Shi et al. 2023a GSM-IC (merge note)", "cited", "Verified, ICML 2023, arXiv:2302.00093", "reproduced", "Missing from the reference list."),
]:
    add("References", title, rep, rec, "citations.md", status, note)
with open(HERE / "claims.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
from collections import Counter
print(len(rows), Counter(r["status"] for r in rows))
for r in rows:
    if r["status"] == "differs":
        print(r["claim_id"], r["claim_text"], "|", r["reported_value"], "|", r["recomputed_value"][:90])
