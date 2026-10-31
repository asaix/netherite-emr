import subprocess
import sys
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
PDF = HERE / "ANLP Final Slides.pdf"
TEAM = "ANLP Final | Team Netherite"

def sv(title, svg, ref, note=None):
    d = dict(title=title, svg=svg, ref=ref if ref.startswith("Error") else f"Report: {ref}")
    if note:
        d["note"] = note
    return d


SECTIONS = {
    "Project": [
        dict(kind="cover", big="Team Netherite", small=["Aayush Batra, Aditya Sai, Rahul Kannan and Shaurya Kochar", "ANLP Final"]),
        dict(kind="cover", big="Evaluating Multilingual Reasoning through a Chain-of-Thought Lens", small=["Final presentation"]),
        sv("English vs Hindi reasoning on date and time questions", "project", "Introduction"),
        sv("We found no study covering all five", "prior_work", "Related Work"),
        dict(title="Research questions", rq=[("RQ1", "Does CoT help, and does that depend on language and difficulty?"), ("RQ2", "Does CoT make distractors more harmful?"), ("RQ3", "How much of the English-Hindi gap follows the language of reasoning?"), ("RQ4", "Does asking for Hinglish reasoning help?"), ("RQ5", "Does divergence between English and Hindi traces track disagreement?"), ("RQ6", "Can we say that distractors in CoT traces cause errors?")], ref="Report: Problem Statement"),
    ],
    "Data": [
        sv("6,750 questions in each language", "dataset", "Experimental Setup"),
        sv("Nine tasks with a fixed answer form", "tasks", "Experimental Setup"),
        sv("Each question also runs with two distractors", "distractors", "Experimental Setup"),
    ],
    "Implementation": [
        sv("Code pipeline", "pipeline", "Figure 1"),
        sv("Prompting conditions", "conditions", "Experimental Setup"),
        sv("Prompts", "prompts", "Experimental Setup"),
        sv("CLP prompts", "clp_prompts", "Experimental Setup"),
        sv("Response sets and settings", "sets", "Experimental Setup"),
        sv("One question, every condition", "one_question", "Figure 1"),
        sv("Parser: trace text to op tokens", "parser_flow", "Experimental Setup"),
        sv("Parser ops", "ops", "Experimental Setup"),
        sv("RQ6 interventions", "rq6_design", "Trace Interventions"),
    ],
    "Metrics": [
        sv("Accuracy: answered and strict", "metric_accuracy", "Experimental Setup"),
        sv("Gain, gap, drop, penalty, share", "metric_diffs", "Problem Statement"),
        sv("Trace measures", "metric_trace", "Experimental Setup"),
        sv("Reasoning divergence score", "metric_rds", "Experimental Setup; Appendix B"),
        sv("RDS on a real pair", "rds_example", "Experimental Setup"),
        sv("RQ5: logistic regression", "lr_setup", "English and Hindi Traces Compared"),
        sv("RQ6: contrasts", "metric_rq6", "Trace Interventions"),
        sv("Statistical tests", "metric_tests", "Experimental Setup"),
    ],
    "Results": [
        dict(title="Answers to the research questions", answers=[("RQ1", "Yes for English, little for Hindi.", "+29.5 vs +4.7 points"), ("RQ2", "Slightly in Hindi, largely through one sentence.", "Penalty 2.2 points"), ("RQ3", "Most of it, descriptively.", "23.5 of 29.5 points"), ("RQ4", "No. Hindi questions don't change, and English questions get worse.", "−0.0 and −18.0 points"), ("RQ5", "Yes as an association, though much of it seems to come from the answers.", "OR 4.92 per 0.1 RDS"), ("RQ6", "No. Removing the distractor helps a little.", "+5.3 points")], ref="Report: Results"),
        sv("Accuracy by set: English CoT is highest in every row", "accuracy", "Results"),
        sv("RQ1: Direct answers score 59.0 in English, 54.7 in Hindi", "direct_results", "Direct Answers"),
        sv("RQ1: CoT helps English far more than Hindi", "cot_gain", "Chain-of-Thought"),
        sv("RQ1: English gains on every task, Hindi falls on two", "gain_tasks", "Chain-of-Thought"),
        sv("RQ1: Hindi falls on subtraction, interval date and short time tasks", "delta_heat", "Chain-of-Thought"),
        sv("RQ1: Two Hindi tasks get worse with CoT", "hindi_tasks", "Chain-of-Thought", "2,250 questions, answered, pooled. All 6,750, no distractor: −19.9 [−23.4, −16.4] and −23.3 [−27.7, −19.0]."),
        sv("RQ1: The gap widens with difficulty, in points only", "by_level", "Chain-of-Thought", "2,250 questions, 95% intervals. All 6,750: gap 24.0 → 34.9 (strict 23.0 → 31.1), trend p = 0.21."),
        sv("RQ2: The CoT penalty in Hindi is 2.2 points", "distractor_penalty", "Chain-of-Thought; Appendix B"),
        sv("RQ2: Penalty by task", "penalties", "Chain-of-Thought"),
        sv("RQ2: Most of the harm comes from one sentence", "january", "Chain-of-Thought; Appendix B"),
        sv("RQ2: The January sentence has the largest penalty in both languages", "sentences", "Chain-of-Thought"),
        sv("RQ2: Hindi traces mention distractors more often", "mentions", "Chain-of-Thought"),
        sv("RQ3: Most of the gap follows the reasoning language", "decomposition", "en-CoT Set; Appendix B"),
        sv("RQ3: The reasoning part is larger on every task and distractor", "breakdown", "en-CoT Set; Figure 2"),
        sv("RQ3: RDS and verification follow the reasoning language", "distance", "en-CoT Set; Appendix C"),
        sv("RQ3: Hindi traces are shorter and rarely check their work", "traces_standard", "Chain-of-Thought"),
        sv("RQ3: CLP scores 70.3%, en-CoT 82.9%", "clp_results", "CLP Set; Appendix B"),
        sv("RQ3: CLP turn 2 mostly follows turn 1", "clp_stages", "CLP Set; Appendix A"),
        sv("RQ3: With thinking on, the gap falls to 1.0 point", "thinking", "Thinking-On Set"),
        sv("RQ3: Thinking on means 79% English reasoning and four times the tokens", "thinking_format", "Thinking-On Set"),
        sv("RQ4: Hinglish changes nothing on Hindi questions, −18.0 on English", "hinglish", "Hinglish Set; Appendix C"),
        sv("RQ4: English loses most when subtraction crosses a month", "hinglish_detail", "Hinglish Set; Appendix B"),
        sv("Errors: Three tasks hold most wrong answers", "error_share", "Chain-of-Thought"),
        sv("Errors: Some patterns come mainly with Hindi reasoning", "error_patterns", "Chain-of-Thought", "Shares of wrong answers of the expected form. Script labels, not hand-checked."),
        sv("Errors: Hindi CoT examples", "examples_hindi", "Chain-of-Thought; Appendix A"),
        sv("Errors: en-CoT keeps the errors from reading Hindi", "recurrence_k", "en-CoT Set; Appendix C"),
        sv("Errors: Other examples", "examples_shared", "Appendix A"),
        sv("Errors: Next-week answers go wrong differently by condition", "week_errors", "Chain-of-Thought; error trends PDF"),
        sv("Errors: Time answers get the minutes right and the hours wrong", "time_errors", "Direct Answers; error trends PDF"),
        sv("Errors: Crossing a boundary raises the error rate", "boundary_errors", "Chain-of-Thought; error trends PDF"),
        sv("Errors: English CoT's cut-offs average 42 re-checking steps", "loop_errors", "Chain-of-Thought; error trends PDF"),
        sv("Errors: Distractors can steer the answer or the reasoning", "steer_errors", "Error trends PDF"),
        sv("RQ5: More divergent traces go with disagreement", "lr_result", "English and Hindi Traces Compared", "Chart is unadjusted; bins under 20 pairs hidden. In-sample association. 88% of pairs above RDS 0.7."),
        sv("RQ5: Removing answer tokens takes the OR from 4.92 to 1.68", "lr_views", "English and Hindi Traces Compared"),
        sv("RQ5: By outcome and task", "lr_outcomes", "English and Hindi Traces Compared"),
        sv("RQ6: Deleting the mention helps no more than a neutral deletion", "deletion", "Trace Interventions"),
        sv("RQ6: Removing the distractor helps a little", "resampling", "Trace Interventions; Appendix C"),
        sv("RQ6: The mention is not distinguishable from an ordinary sentence", "arms", "Trace Interventions; Appendix B"),
        sv("RQ6: One trace, every variant", "one_trace", "Appendix C"),
    ],
    "Wrap-up": [
        sv("Main findings", "findings", "Discussion; Conclusion"),
        dict(title="Limitations", table=[("Scope", "One model, one prompt per condition, one seed, two languages."), ("Causal claims", "Language and prompt wording confounded. No English question with Hindi reasoning."), ("Data", "2,250-question subset for added sets. Hindi distractors not literal."), ("Measurement", "Regex parser and script labels. One LLM annotator, no human validation."), ("Interventions", "Wrong traces only. Quantised self-hosted model."), ("Thinking", "10 questions per cell. Thinking and budget change together.")], ref="Report: Limitations"),
        sv("Future work", "future", "Limitations"),
        dict(kind="cover", big="Thank you", small=["Questions?", "Team Netherite"]),
    ],
}
SLIDES = [dict(s, section=k) for k, v in SECTIONS.items() for s in v]

CSS = """
@page { size: 1280px 720px; margin: 0; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: #fff; color: #222; font-family: 'Liberation Sans', Arial, 'Noto Sans Devanagari', sans-serif; }
.s { width: 1280px; height: 720px; padding: 28px 44px 0; position: relative; page-break-after: always; overflow: hidden; }
h1 { margin: 0; height: 58px; font-size: 32px; letter-spacing: -0.3px; }
.body { width: 1192px; padding-top: 6px; }
.body img { display: block; width: 100%; max-height: 580px; object-fit: contain; object-position: left top; }
.body.noted img { max-height: 515px; }
.note { margin-top: 14px; font-size: 18px; color: #595959; line-height: 1.32; }
.foot { position: absolute; left: 44px; right: 44px; bottom: 18px; display: grid; grid-template-columns: 1fr 1.4fr 1fr; font-size: 13px; color: #595959; border-top: 1px solid #E3E3E3; padding-top: 8px; }
.foot div:nth-child(2) { text-align: center; color: #8C8C8C; }
.foot b { color: #222; }
.foot div:nth-child(3) { text-align: right; }
.cover { display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; height: 660px; }
.cover .big { font-size: 46px; max-width: 980px; line-height: 1.2; }
.cover .small { font-size: 22px; color: #595959; margin-top: 18px; }
.rq { display: grid; grid-template-columns: 100px 1fr; row-gap: 30px; font-size: 27px; line-height: 1.3; }
.rq b { color: #0072B2; }
table { border-collapse: collapse; width: 100%; font-size: 22px; line-height: 1.3; }
td { padding: 15px 14px 15px 0; border-bottom: 1px solid #E3E3E3; vertical-align: top; }
td.k { font-weight: bold; white-space: nowrap; padding-right: 26px; }
td.n { font-weight: bold; white-space: nowrap; text-align: right; padding-left: 26px; padding-right: 0; }
"""


def foot(i, s):
    crumbs = " · ".join(f"<b>{k}</b>" if k == s["section"] else k for k in SECTIONS)
    return f'<div class="foot"><div>{TEAM}</div><div>{crumbs}</div><div>{escape(s.get("ref", ""))} | {i:02d}</div></div>'


def page(i, s):
    if s.get("kind") == "cover":
        small = "".join(f'<div class="small">{escape(x)}</div>' for x in s["small"])
        return f'<section class="s"><div class="cover"><div class="big">{escape(s["big"])}</div>{small}</div></section>'
    body = ""
    if "svg" in s:
        body = f'<img src="svg/{s["svg"]}.svg" alt="{escape(s["title"])}">'
    if "note" in s:
        body += f'<div class="note">{escape(s["note"])}</div>'
    if "rq" in s:
        body = '<div class="rq">' + "".join(f"<b>{a}</b><div>{escape(b)}</div>" for a, b in s["rq"]) + "</div>"
    if "answers" in s:
        body = "<table>" + "".join(f'<tr><td class="k" style="color:#0072B2">{a}</td><td>{escape(b)}</td><td class="n">{escape(c)}</td></tr>' for a, b, c in s["answers"]) + "</table>"
    if "table" in s:
        body = "<table>" + "".join(f'<tr><td class="k">{a}</td><td>{escape(b)}</td></tr>' for a, b in s["table"]) + "</table>"
    cls = "body noted" if "note" in s else "body"
    return f'<section class="s"><h1>{escape(s["title"])}</h1><div class="{cls}">{body}</div>{foot(i, s)}</section>'


html = f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>ANLP Final Slides</title><style>{CSS}</style></head><body>' + "".join(page(i, s) for i, s in enumerate(SLIDES, 1)) + "</body></html>"
(HERE / "slides.html").write_text(html, encoding="utf-8")
subprocess.run([sys.executable, str(HERE / "make_svgs.py")], check=True)
subprocess.run(["google-chrome", "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={PDF}", f"file://{HERE / 'slides.html'}"], check=True, capture_output=True)
print(PDF)
