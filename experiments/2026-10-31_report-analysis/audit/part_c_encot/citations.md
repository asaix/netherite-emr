# Citations

Fetched during this audit unless marked `UNVERIFIED`. Quotes come from the fetched text or fetch summaries.

## Language Models are Multilingual Chain-of-Thought Reasoners

- Authors: Freda Shi, Mirac Suzgun, Markus Freitag, Xuezhi Wang, Suraj Srivats, Soroush Vosoughi, Hyung Won Chung, Yi Tay, Sebastian Ruder, Denny Zhou, Dipanjan Das, Jason Wei. 2022 preprint.
- Venue: ICLR 2023 per the team's `references.bib`. **The venue is UNVERIFIED by fetch**; the OpenReview fetch failed, and the arXiv page lists no venue.
- URLs fetched: https://arxiv.org/abs/2210.03057, https://arxiv.org/pdf/2210.03057
- Used for: the origin of the EN-CoT condition, and how ours departs from it.
- Quotes from the PDF text:
  - "we can ask the model to predict the chain of thought in English (EN-COT), regardless of the problem language."
  - "We use 6 questions and solutions as the few-shot exemplar whenever possible"
  - Languages: "Bengali (BN), Chinese (ZH), French (FR), German (DE), Japanese (JA), Russian (RU), Spanish (ES), Swahili (SW), Telugu (TE), and Thai (TH)." Hindi isn't included.
  - "reasoning in English (EN-COT) consistently achieves competitive or better performance than reasoning in the native language of the question (NATIVE-COT)"
- Table 3 (last model block, extracted text): NATIVE-COT 48.1, EN-COT 51.3, TRANSLATE-EN 55.0 average. The row label was cut off in my extraction; the surrounding text discusses PaLM-540B. Check before quoting.

## Benchmarking Multilingual Temporal Reasoning in LLMs: The Temporal Reasoning Dataset

- Authors: Vittorio Mazzia, Sandro Pollastrini, Davide Bernardi, Chiara Rubagotti, Daniele Amberti. 2026.
- Venue: IWSDS 2026 (the paper's footer gives February 26 to March 1, 2026, Association for Computational Linguistics).
- URL fetched: https://aclanthology.org/2026.iwsds-1.19.pdf
- Used for: how templates were written, the English carrier form, the no-CoT baseline, insertion effects.
- Quotes:
  - "These phrases were written and reviewed in collaboration with native speakers and language experts to ensure natural phrasing, grammatical correctness, and logical clarity."
  - "Each language has its own dedicated set of carrier phrases adapted to its syntax and lexical conventions."
  - Table 2 example: "Without counting today, what is the date of the 2 occurrence?"
  - "Chain-of-thought (CoT) ... prompting was disabled"
  - "the average performance impact of insertions is small but consistently with a negative average."

## Crosslingual Reasoning through Test-Time Scaling

- Authors: Zheng-Xin Yong, M. Farid Adilazuarda, Jonibek Mansurov, Ruochen Zhang, Niklas Muennighoff, Carsten Eickhoff, Genta Indra Winata, Julia Kreutzer, Stephen H. Bach, Alham Fikri Aji. 2025. arXiv preprint.
- URL fetched: https://arxiv.org/abs/2505.05408
- Used for: English-dominant reasoning traces on non-English input.
- Quotes from the abstract: "consistently follow a quote-and-think pattern"; "reason better and more efficiently in high-resource languages"; "let English-centric RLMs reason in high-resource languages".

## When Models Reason in Your Language: Controlling Thinking Language Comes at the Cost of Accuracy

- Authors: Jirui Qi, Shan Chen, Zidi Xiong, Raquel Fernández, Danielle S. Bitterman, Arianna Bisazza. 2025. Findings of EMNLP 2025.
- URL fetched: https://arxiv.org/abs/2505.22888
- Used for: reasoning-language accuracy trade-off.
- Quotes: "Prompt based interventions that force models to reason in the users language improve readability and oversight"; these "reduce answer accuracy, exposing an important trade off."

## Do Llamas Work in English? On the Latent Language of Multilingual Transformers

- Authors: Chris Wendler, Veniamin Veselovsky, Giovanni Monea, Robert West. 2024. arXiv preprint; the page names no peer-reviewed venue.
- URL fetched: https://arxiv.org/abs/2402.10588
- Used for: hypothesis about English-leaning intermediate representation only. Studied Llama-2, not Sarvam.
- Quote: "our evidence suggests that the abstract \"concept space\" lies closer to English than to other languages".

## How do Large Language Models Handle Multilingualism?

- Authors: Yiran Zhao, Wenxuan Zhang, Guizhen Chen, Kenji Kawaguchi, Lidong Bing. 2024. arXiv preprint page lists no venue; NeurIPS 2024 appears in search results (https://neurips.cc/virtual/2024/poster/94375, not opened).
- URL fetched: https://arxiv.org/abs/2402.18815
- Used for: hypothesis of an English-centred workflow.
- Quote: "LLMs initially understand the query, converting multilingual inputs into English for task-solving."

## UNVERIFIED

- **Qin et al. 2023, Cross-lingual Prompting.** Not fetched here; bibliographic data from `experiments/2026-10-02_mid-report-analysis/report/references.bib`. The Part A audit covers it.
- **Hindi ordinal forms (पहली, दूसरी, तीसरी, चौथी; -वाँ/-वीं from about five on).** Web search snippets only (for example https://sublearn.com/learn/hi/grammar/hindi-ordinal-numbers, https://iteachhindi.blogspot.com/2010/05/numbers-part-iv.html), not opened, and the snippets disagree on the exact cut-off and on 6th. Cite a standard Hindi grammar, or have a native speaker state it, before printing.
