# Citations

Every URL below was fetched during this audit, except where marked `UNVERIFIED` or "metadata only". Quotes come from the fetched text. PDF text extraction can alter line breaks.

## Design-basis papers

**Mazzia, Pollastrini, Bernardi, Rubagotti, Amberti. 2026. Benchmarking Multilingual Temporal Reasoning in LLMs: The Temporal Reasoning Dataset. Proceedings of the 16th International Workshop on Spoken Dialogue System Technology, 168-181.** https://aclanthology.org/2026.iwsds-1.19.pdf
- CoT is left open: "Chain-of-thought (CoT) ... prompting was disabled through in-context-learning instructions ... leaving the exploration of CoT's impact on temporal reasoning performance for future research."
- Scoring: "Format compliance rates were consistently above 99% across all models when using the strict output instructions, with format errors counted as incorrect responses in our evaluation."
- Stability: "memorization-based tasks demonstrate more stable performance patterns across difficulty levels."
- Distractors: "the average performance impact of insertions is small but consistently with a negative average." Day of week: "absolute performance drops of up to 10-22 percentage points."
- Table 5 gives hours 1-4 to 32-64. The code draws from 0 to the maximum.
- Hindi: in Tables 6-7, Hindi date recurrence is 0.00 to 0.36 for every model listed, with 0.36 for both Claude 3.5 Sonnet versions.
- Justifies: tasks, levels, sentences, temperature 0. We depart in: prompts, CoT, and the full language x level x insertion crossing.

**Kojima, Gu, Reid, Matsuo, Iwasawa. 2022. Large Language Models are Zero-Shot Reasoners. NeurIPS 35, 22199-22213.** https://arxiv.org/pdf/2205.11916
- "by simply adding 'Let's think step by step' before each answer"; "increasing the accuracy on MultiArith from 17.7% to 78.7% and GSM8K from 10.4% to 40.7%."
- Justifies: zero-shot CoT without examples. We depart: no trigger sentence, a language instruction, and one prompt instead of "Two-stage prompting".

**Shi, Chen, Misra, Scales, Dohan, Chi, Schärli, Zhou. 2023. Large Language Models Can Be Easily Distracted by Irrelevant Context. ICML, PMLR 202, 31210-31227.** https://arxiv.org/pdf/2302.00093
- "add to it one irrelevant sentence, while making sure that it does not affect the solution"; "In-topic sentences are closely related to the topic of the original problem, whereas off-topic sentences are about a different topic."
- Justifies: one prepended sentence, related vs unrelated. We depart: TRD's fixed pool, no role-name or number-range factors, and at least one sentence that does affect interpretation.

**Mirzadeh, Alizadeh-Vahid, Shahrokhi, Tuzel, Bengio, Farajtabar. 2025. GSM-Symbolic. ICLR.** https://arxiv.org/pdf/2410.05229
- "LLMs exhibit noticeable variance when responding to different instantiations of the same question"; "By adding seemingly relevant but ultimately irrelevant information to problems, we demonstrate substantial performance drops (up to 65%) across all state-of-the-art models."
- Justifies: concern with sentence-level variance. We depart: CoT on/off contrast, and a single sentence draw per question.

**Sprague, Yin, Rodriguez, Jiang, Wadhwa, Singhal, Zhao, Ye, Mahowald, Durrett. 2025. To CoT or not to CoT? ICLR.** https://arxiv.org/pdf/2409.12183
- "meta-analysis covering over 100 papers using CoT and ran our own evaluations of 20 datasets across 14 models"; improvements from CoT come mainly "from math and symbolic reasoning."
- Justifies: the prediction that CoT helps date arithmetic. Hindi date subtraction is a counterexample in this model.

**Liu, Geng, Wu, Sucholutsky, Lombrozo, Griffiths. 2025. Mind Your Step (by Step). ICML, PMLR 267, 38489-38517.** https://proceedings.mlr.press/v267/liu25t.html
- "In three of these tasks, state-of-the-art models exhibit significant performance drop-offs with CoT." Close paraphrase of the abstract, read through a fetch tool that limits quotes: six tasks, three with significant drops (up to 36.3 points, o1-preview vs GPT-4o), others mixed. The full PDF was not obtained.
- Justifies: CoT can lower accuracy. The mid-report wording needs correcting: not all six.

**Berg-Kirkpatrick, Burkett, Klein. 2012. An Empirical Investigation of Statistical Significance in NLP. EMNLP-CoNLL, 995-1005.** https://aclanthology.org/D12-1091.pdf
- "We use the paired bootstrap"; asks how well "the standard i.i.d. notion of significance" holds where "future distributions are neither independent nor identically distributed."
- Justifies: paired bootstrap. Resampling whole questions as clusters is our extension, and they use b = 10^6.

**Dror, Baumer, Shlomov, Reichart. 2018. The Hitchhiker's Guide to Testing Statistical Significance in NLP. ACL, 1383-1392.** https://aclanthology.org/P18-1128.pdf
- Lists McNemar's test and the paired bootstrap among tests for NLP evaluation (close paraphrase).

**Shi et al. 2023. Language Models are Multilingual Chain-of-Thought Reasoners. ICLR.** https://arxiv.org/pdf/2210.03057
- "intermediate reasoning steps in English consistently lead to competitive or better results than those written in the native language of the question."

**Qin, Chen, Wei, Huang, Che. 2023. Cross-lingual Prompting. EMNLP, 2695-2709.** https://aclanthology.org/2023.emnlp-main.163.pdf
- "Please act as an expert in multi-lingual understanding in Chinese."; "you should format your answer as 'Answer: [num]'."

## Statistics papers I could not read

**McNemar 1947. Psychometrika 12(2), 153-157. doi:10.1007/BF02295996.** Metadata confirmed at https://api.crossref.org/works/10.1007/BF02295996. Search results describe two approaches to judging a difference between correlated proportions, one equivalent to chi-square. Full text blocked: `UNVERIFIED` for any specific quote.

**Mantel and Haenszel 1959. JNCI 22(4), 719-748. doi:10.1093/jnci/22.4.719.** Title confirmed at https://api.crossref.org/works/10.1093/jnci/22.4.719. A search-engine summary describes chi-square tests extended to stratified data and a summary relative risk. The hosted PDF refused connection: `UNVERIFIED` for any specific quote.

**Simpson 1951. JRSS B 13(2), 238-241. doi:10.1111/j.2517-6161.1951.tb00088.x.** Metadata confirmed at https://api.crossref.org/works/10.1111/j.2517-6161.1951.tb00088.x. A search summary, relying on secondary sources, says conditional odds ratios of 1.2 with a marginal of 1.0, and non-collapsibility. A search result's alternative DOI (`tb00558`) does not exist in Crossref; the bib's DOI is right. Hosted PDF refused connection: `UNVERIFIED` for any specific quote.

**Holm 1979.** `UNVERIFIED`. JSTOR returned a challenge page.

## Not fetched, suggested only

The argument that treating stimuli as fixed effects overstates generality is commonly credited to Clark (1973), "The language-as-fixed-effect fallacy". `UNVERIFIED`: I did not fetch it, so don't cite it without checking.

## All 39 mid-report `references.bib` entries

"Fetched" here confirms bibliographic details, and for the design-basis papers above, content too. For other entries I did not check how the mid report describes them.

| Key | URL | Status | Note |
|---|---|---|---|
| `mazzia-etal-2026-benchmarking` | https://aclanthology.org/2026.iwsds-1.19/ | fetched | Read in full. Anthology author order and venue match the bib; the PDF's own text says 'Systems Technology'. |
| `shi-etal-2023-mgsm` | https://arxiv.org/pdf/2210.03057 | fetched | OpenReview blocked automated fetch; title confirmed from the arXiv PDF. |
| `shi-etal-2023-distracted` | https://proceedings.mlr.press/v202/shi23a.html | fetched | Title and pages match the fetched page. Mid-report characterisation not checked. |
| `qin-etal-2023-cross` | https://aclanthology.org/2023.emnlp-main.163/ | fetched | PDF fetched; prompts in config/prompt.yaml follow it. |
| `wei-etal-2022-chain` | https://proceedings.neurips.cc/paper_files/paper/2022/hash/9d5609613524ecf4f15af0f7b31abca4-Abstract-Conference.html | fetched | Title and pages match the fetched page. Mid-report characterisation not checked. |
| `turpin-etal-2023-unfaithful` | https://proceedings.neurips.cc/paper_files/paper/2023/hash/ed3fea9033a80fea1376299fa7863f4a-Abstract-Conference.html | fetched | Bib lacks pages; source gives 74952-74965. |
| `sarvam-2026-models` | https://www.sarvam.ai/blogs/sarvam-30b-105b | fetched | Page title is 'Open-sourcing Sarvam 30B & 105B models', dated 2026-03-06; bib title differs slightly. Page confirms a Mixture-of-Experts backbone and a training budget weighted to 10 Indian languages. |
| `mcnemar-1947-note` | https://doi.org/10.1007/BF02295996 | metadata only | Crossref metadata only; Springer page blocked automated fetch. |
| `holm-1979-simple` | https://www.jstor.org/stable/4615733 | UNVERIFIED | JSTOR returned a challenge page; not confirmed. UNVERIFIED. |
| `mantel-haenszel-1959-statistical` | https://doi.org/10.1093/jnci/22.4.719 | metadata only | Crossref metadata and a search-engine abstract only; OUP blocked fetch. Pages from bibliographic records. |
| `simpson-1951-interpretation` | https://doi.org/10.1111/j.2517-6161.1951.tb00088.x | metadata only | Crossref confirms title, volume, pages and the bib's DOI. Text not read. |
| `berg-kirkpatrick-etal-2012-empirical` | https://aclanthology.org/D12-1091/ | fetched | Title and pages match the fetched page. Mid-report characterisation not checked. |
| `dror-etal-2018-hitchhikers` | https://aclanthology.org/P18-1128/ | fetched | Title and pages match the fetched page. Mid-report characterisation not checked. |
| `huang-chang-2023-towards` | https://aclanthology.org/2023.findings-acl.67/ | fetched | Title and pages match the fetched page. Mid-report characterisation not checked. |
| `huang-etal-2023-languages` | https://aclanthology.org/2023.findings-emnlp.826/ | fetched | Title and pages match the fetched page. Mid-report characterisation not checked. |
| `lai-nissim-2024-mcot` | https://aclanthology.org/2024.acl-long.649/ | fetched | Title and pages match the fetched page. Mid-report characterisation not checked. |
| `qi-etal-2025-models` | https://aclanthology.org/2025.findings-emnlp.1103/ | fetched | Title and pages match the fetched page. Mid-report characterisation not checked. |
| `wendler-etal-2024-llamas` | https://aclanthology.org/2024.acl-long.820/ | fetched | Title and pages match the fetched page. Mid-report characterisation not checked. |
| `marchisio-etal-2024-understanding` | https://aclanthology.org/2024.emnlp-main.380/ | fetched | Title and pages match the fetched page. Mid-report characterisation not checked. |
| `tan-etal-2023-towards` | https://aclanthology.org/2023.acl-long.828/ | fetched | Title and pages match the fetched page. Mid-report characterisation not checked. |
| `wei-etal-2023-menatqa` | https://aclanthology.org/2023.findings-emnlp.100/ | fetched | Title and pages match the fetched page. Mid-report characterisation not checked. |
| `wang-zhao-2024-tram` | https://aclanthology.org/2024.findings-acl.382/ | fetched | Title and pages match the fetched page. Mid-report characterisation not checked. |
| `chu-etal-2024-timebench` | https://aclanthology.org/2024.acl-long.66/ | fetched | Title and pages match the fetched page. Mid-report characterisation not checked. |
| `khanuja-etal-2020-gluecos` | https://aclanthology.org/2020.acl-main.329/ | fetched | Title and pages match the fetched page. Mid-report characterisation not checked. |
| `aguilar-etal-2020-lince` | https://aclanthology.org/2020.lrec-1.223/ | fetched | Title and pages match the fetched page. Mid-report characterisation not checked. |
| `shankar-etal-2024-context` | https://aclanthology.org/2024.acl-long.228/ | fetched | Title and pages match the fetched page. Mid-report characterisation not checked. |
| `yang-chai-2025-codemixbench` | https://aclanthology.org/2025.emnlp-main.109/ | fetched | Title and pages match the fetched page. Mid-report characterisation not checked. |
| `prasad-etal-2023-receval` | https://aclanthology.org/2023.emnlp-main.622/ | fetched | Title and pages match the fetched page. Mid-report characterisation not checked. |
| `kojima2022large` | https://proceedings.neurips.cc/paper_files/paper/2022/hash/8bb0d291acd4acf06ef112099c16f326-Abstract-Conference.html | fetched | Title and pages match the fetched page. Mid-report characterisation not checked. |
| `wang2023selfconsistency` | https://arxiv.org/pdf/2203.11171 | fetched | OpenReview blocked; arXiv PDF confirms title and '+17.9%' on GSM8K. |
| `sprague2025cot` | https://arxiv.org/pdf/2409.12183 | fetched | ICLR PDF returned no title tag; arXiv version read. |
| `liu2025mind` | https://proceedings.mlr.press/v267/liu25t.html | fetched | Title and pages match the fetched page. Mid-report characterisation not checked. |
| `mirzadeh2025gsmsymbolic` | https://arxiv.org/pdf/2410.05229 | fetched | OpenReview blocked; arXiv PDF read. |
| `zhao2024handle` | https://neurips.cc/virtual/2024/poster/94375 | fetched | Poster page title matches; content not read. |
| `chen2021timeqa` | https://datasets-benchmarks-proceedings.neurips.cc/paper/2021/hash/1f0e3dad99908345f7439f8ffabdffc4-Abstract-round2.html | fetched | Title and pages match the fetched page. Mid-report characterisation not checked. |
| `fatemi2025test` | https://proceedings.iclr.cc/paper_files/paper/2025/hash/eb7295a8bc613b375726659c2ecd6f14-Abstract-Conference.html | fetched | Bib lacks pages; source gives 94426-94447. |
| `golovneva2023roscoe` | https://arxiv.org/pdf/2212.07919 | fetched | OpenReview blocked; title confirmed from arXiv PDF. |
| `yong2025crosslingual` | https://arxiv.org/abs/2505.05408 | fetched | Title and authors match arXiv abstract page. |
| `levenshtein1966binary` | none | UNVERIFIED | No URL in bib; not fetched. UNVERIFIED. |
