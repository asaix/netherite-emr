# Audit brief (shared by all audit agents)

Project: multilingual temporal reasoning in Sarvam-105B through chain-of-thought (CoT), English vs Hindi, on the Temporal Reasoning Dataset (TRD). Read `CLAUDE.md` at the repo root first. Repo root: `/home/adi/proj/netherite-emr`.

The audits feed an ACL-format final paper. The guidelines ask for claims as watertight as possible and every claim backed by prior or empirical results. Your job is to find out what is true, not to defend the existing draft. A corrected or weakened claim is a good outcome.

## What to deliver, in your output folder

1. `verify.py`: recomputes the document's results **independently from the rawest data available** (`responses/`, `dataset/`, experiment `results.json` files). Don't import or copy the original analysis script where you can avoid it. If you must reuse code, say so in `analysis.md`. Run with `.venv/bin/python` (it has numpy, pandas, scipy, statsmodels, matplotlib).
2. `claims.csv`, one row for **every number and every factual claim** in the document, with columns: `claim_id, location, claim_text, reported_value, recomputed_value, source_path, status, note`. `status` is one of: `reproduced` (matches to the printed precision), `differs`, `source_missing` (cited file doesn't exist; say whether you recomputed it another way), `unverifiable`, `overclaimed` (the number holds but the wording goes beyond the evidence).
3. `analysis.md`, a thorough analysis with these headings:
   - **Verdict**: headline claims and whether each holds, in a few lines.
   - **Data existence**: each cited file or folder, whether it exists, record counts, whether counts match the design.
   - **Corrected results**: the results as they should be stated, with tables, CIs and test statistics. Refer to figures by file name.
   - **Limitations**: be blunt. Include threats that the document doesn't mention. Separate what can't be concluded from what was simply not run.
   - **Design rationale from prior work**: why each design choice is defensible (or not), tied to prior work. Say where our design departs from the cited work.
   - **Missing findings**: important findings the document misses. Actually compute them. Label each one `exploratory`, with n, effect size and interval.
   - **Suggested claims for the paper**: 3 to 8 sentences of claim text with the exact numbers, each graded `strong`, `moderate`, `suggestive`.
4. `citations.md`: every prior work you rely on, with full title, authors, year, venue, a URL you actually fetched, and a short **quote or close paraphrase from the source itself** supporting the use. Use WebSearch and WebFetch. Never cite from memory. If you couldn't fetch it, list it as `UNVERIFIED`.
5. `figures.md` plus `fig_data/*.csv`: for every figure in the document and every new figure you recommend, give the figure number, chart type, encoding (what maps to x, y, colour, panel), the exact CSV in `fig_data/` that holds the plotted values, and whether it is core or appendix material. A later step restyles all figures centrally, so keep the same chart type and don't spend time on styling. Draft PNGs are fine for your own checks.

## Rules

- No paid or remote model calls, no Sarvam API, no GPU jobs.
- **Don't modify anything outside your output folder.** Don't edit `docs/`, `responses/`, other experiment folders or root scripts. Don't run `git checkout`, `git switch`, `git stash`, `git commit` or anything else that changes repo state; other agents share this working tree. Read other revisions with `git show` or `git log`.
- Differences get reported. Don't quietly adjust a number to match.
- JSON output is pretty-printed (`indent=2`, `ensure_ascii=False`). Minimal code, no comments.
- The machine has about 3 GB of free RAM and other agents run at the same time. Load one difficulty file at a time where possible, drop raw text you don't need, and don't re-run the parser over the full data. Pre-parsed data exists at `experiments/2026-10-29_ed-analysis/parsed/` and is confirmed current (the `short` split re-parses byte-identically with root `parser.py`, and its `edout/standard/short.csv` is reproduced byte-for-byte by root `ed.py`).

## Shared data facts (verify anything you rely on)

- `responses/INFO.txt` describes each set. `responses/standard/` has 81,000 responses over 6,750 questions (thinking off, temperature 0, 4,096 max tokens). `responses/ron/` is thinking on (`reasoning_effort: low`, 16,000 tokens, questions 0-9). `responses/{clp,en-cot,hinglish}/` cover the first 50 questions per task and difficulty (2,250 questions).
- Conditions: `direct`, `cot`, `en-cot`, CLP's two stages, Hinglish. Insertions: `no_insertion`, `similar_insertion` (time-related distractor), `dissimilar_insertion` (unrelated).
- Team statistics convention: exact McNemar on paired responses, Holm over the nine tasks, cluster bootstrap over questions (B = 2000), Mantel-Haenszel for mention odds ratios.
- Known cross-document inconsistencies to watch: some tables report accuracy over answered responses, others count unanswered as wrong. Part A and Part C print slightly different CIs for the same quantity. State which convention each number uses, and report both answered-only and strict accuracy for headline numbers.
- A mid-eval evaluator criticised results pooled across distractor conditions (none, similar, dissimilar). For every headline number you audit, also give the split by distractor condition and say whether the conclusion holds in each.
- Hyperparameters and prompts: `config/prompt.yaml`, `config/sarvam.yaml`, `config/general.yaml`. Mid report: `docs/ANLP-Netherite-MidReport.pdf` with sources in `experiments/2026-10-02_mid-report-analysis/report/` (its `references.bib` has 39 entries, still to be re-verified by fetching the sources).

## Your final message

Keep it under 250 words: verdict on each headline claim, the claims that changed, anything serious you found, and your output folder path. Everything else belongs in the files.
