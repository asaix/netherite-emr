# Citations

Quotes and paraphrases come from the fetched pages through the WebFetch tool, which summarises pages and caps quote length. Check wording against the source before quoting in the paper. All fetches were made on 2026-10-31.

## Fetched

**1. Marchisio, Ko, Berard, Dehaze, Ruder (2024).** Understanding and Mitigating Language Confusion in LLMs. EMNLP 2024, pp. 6653-6677. https://aclanthology.org/2024.emnlp-main.380/
Quote: "their inability to consistently generate text in a user's desired language". Paraphrase: a benchmark over 15 languages tests how often models answer in the wrong language; few-shot prompting, multilingual fine-tuning and preference tuning help only partly.
Use: frames the Devanagari non-compliance as an output-language failure. Departure: they measure wrong language, we measure wrong script and mixing under an explicit instruction.

**2. Khanuja, Dandapat, Srinivasan, Sitaram, Choudhury (2020).** GLUECoS: An Evaluation Benchmark for Code-Switched NLP. ACL 2020, pp. 3575-3585. https://aclanthology.org/2020.acl-main.329/
Quote: "Code-switching is the use of more than one language in the same conversation or utterance." Paraphrase: English-Hindi and English-Spanish benchmark over language identification, POS tagging, NER, sentiment, question answering and NLI.
Use: source of the code-switching definition and evidence that Hindi-English is a benchmarked pair. Departure: code-mixed input, no reasoning traces.

**3. Aguilar, Kar, Solorio (2020).** LinCE: A Centralized Benchmark for Linguistic Code-switching Evaluation. LREC 2020, pp. 1803-1813. https://aclanthology.org/2020.lrec-1.223/
Quote: "combines eleven corpora covering four different code-switched language pairs". Paraphrase: pairs include Hindi-English; tasks are language identification, NER, POS tagging and sentiment.
Use: as above. Departure: classification and tagging, no reasoning.

**4. Shankar, Jyothi, Bhattacharyya (2024).** In-context Mixing (ICM): Code-mixed Prompts for Multilingual LLMs. ACL 2024, pp. 4162-4176. https://aclanthology.org/2024.acl-long.228/
Quote: "intra-sententially code-mixed by randomly swapping content words in the target languages with their English translations". Paraphrase: gains on disfluency correction, grammar correction and text simplification, largest for low-resource languages. The fetched page does not mention chain-of-thought.
Use: shows code-mixing can help when it is in few-shot input. **Correction:** the mid-report sentence "code-mixed few-shot examples add to CoT gains" is not supported by the fetched abstract page. Check the PDF before keeping it.

**5. Husain, Dabre, Kumar, Gala, Jayakumar, Puduppully, Kunchukuttan (2024).** RomanSetu: Efficiently unlocking multilingual capabilities of Large Language Models via Romanization. arXiv:2401.14280, listed as accepted to ACL 2024. https://arxiv.org/abs/2401.14280
Quotes: "reduces token fertility by 2x-4x"; "matches or outperforms native script representation". The abstract page does not name Hindi.
Use: the expectation that romanisation could help. Departure: they pretrain and instruction-tune a model on romanised text; Sarvam-105B was not, as far as this project knows, and our traces are unprompted choices.

**6. Khullar, Desai, Malviya, Dalmia, Shi (2025).** Script Gap: Evaluating LLM Triage on Indian Languages in Native vs Roman Scripts in a Real World Setting. arXiv:2512.10780. https://arxiv.org/html/2512.10780v1
Quotes: "F1 scores trailing those of native scripts by 5-12 points"; "this performance gap by scripts is not due to a failure in clinical reasoning".
Use: romanised input can cost accuracy. Departure: romanised input on classification; ours is romanised output on arithmetic reasoning.

**7. Winata, Anugraha, Irawan, et al. (2026).** Can Large Language Models Understand, Reason About, and Generate Code-Switched Text? arXiv:2601.07153, preprint. https://arxiv.org/html/2601.07153
Quotes: "an average performance degradation of approximately 11% under code-switching conditions"; Hindi-English mixing is "predominantly written in the Latin script"; "many model generations include Devanagari script within mixed text"; no consistent pattern that an LLM "reliably generates code-switched text exclusively in the Latin script".
Use: closest external support for the script non-compliance finding, and the best fetched source for Section 1's claim about how Hinglish is written. It does not give a user count.

**8. Das, Parmar, Ramnath, Verma (2026).** Indi-RomCoM: Code-Mixed Benchmark for Evaluating LLMs on Romanized Indic-English Instructions. arXiv:2606.30790, preprint, submitted 29 June 2026. https://arxiv.org/abs/2606.30790 and https://arxiv.org/html/2606.30790
Quotes: "LLMs consistently underperform on RCM instructions"; "reasoning tasks suffer less degradation than detection tasks"; Register Defection Rate "tracks the proportion of model outputs that incorrectly revert to standard English text"; "RDR rises with CM intensity across nearly all models". Reported figures: Sarvam-30B accuracy 64.2% at baseline to 56.1% at 75% code-mixing, RDR 26.1%.
Use: nearest neighbour on a related Sarvam model. Departure: romanised input instructions, different model, and not specifically date and time arithmetic.

**9. Tam, Wu, Chiu, Lin, Chen, Lee (2025).** Language Matters: How Do Multilingual Input and Reasoning Paths Affect Large Reasoning Models? arXiv:2505.17407. https://arxiv.org/abs/2505.17407
Quotes: "When constrained to reason in the same language as the input"; "LRMs tend to default to reasoning in high-resource languages (e.g., English)". Paraphrase: performance declines under that constraint, especially for low-resource languages; high-resource reasoning generally preserves it.
Use: prior support for reasoning language mattering. Departure: search results describe control by prefilling thinking tokens, a stronger manipulation than our instruction. I confirmed that method only from a search snippet, not the fetched page.

**10. Qi, Chen, Xiong, Fernandez, Bitterman, Bisazza (2025).** When Models Reason in Your Language: Controlling Thinking Language Comes at the Cost of Accuracy. Findings of EMNLP 2025, pp. 20279-20296. https://aclanthology.org/2025.findings-emnlp.1103/
Quote: "reduces answer accuracy, exposing an important trade-off".
Use: prior evidence that imposing a thinking language costs accuracy, which is the same family as the Hinglish instruction effect and an alternative to a Hindi-specific reading.

**11. Qin, Chen, Wei, Huang, Che (2023).** Cross-lingual Prompting: Improving Zero-shot Chain-of-Thought Reasoning across Languages. EMNLP 2023, pp. 2695-2709. https://aclanthology.org/2023.emnlp-main.163/
Quote: "aiming to improve zero-shot CoT reasoning across languages".
Use: prior for separating understanding from reasoning, relevant to the read-versus-reason split.

**12. Shi, Suzgun, Freitag, Wang, Srivats, Vosoughi, Chung, Tay, Ruder, Zhou, Das, Wei (2022).** Language Models are Multilingual Chain-of-Thought Reasoners. arXiv:2210.03057. https://ar5iv.labs.arxiv.org/html/2210.03057 and https://arxiv.org/abs/2210.03057
Quotes: EN-CoT is "the chain of thought in English (EN-CoT), regardless of the problem language"; EN-CoT "consistently achieves competitive or better performance than reasoning in the native language of the question". Figures: 51.3% vs 48.1% on PaLM-540B.
Use: source of the en-CoT condition. The effect here (+23 points) is far larger than their 3 to 5 points. Venue not confirmed: the project bib points to OpenReview, which blocked the fetch with a browser check.

**13. Yang, Chai (2025).** CodeMixBench: Evaluating Code-Mixing Capabilities of LLMs Across 18 Languages. EMNLP 2025, pp. 2139-2169. https://aclanthology.org/2025.emnlp-main.109/
Quote: "a comprehensive benchmark covering eight tasks, including three specific to LLMs and five traditional NLP tasks". The fetched page does not say whether Hindi-English or romanised text is included.
Use: general code-mixing benchmark only.

**14. Gupta, Bhogal, Ghosh (2024).** Code-Mixer Ya Nahi: Novel Approaches to Measuring Multilingual LLMs' Code-Mixing Capabilities. arXiv:2410.11079. https://arxiv.org/abs/2410.11079
Quote: "Rule-Based Prompting shows promise in generating unique code-mixed sentences".
Use: background on prompting for code-mixed output, the closest to our output-side instruction. Not reasoning.

**15. Shi, Chen, Misra, Scales, Dohan, Chi, Scharli, Zhou (2023).** Large Language Models Can Be Easily Distracted by Irrelevant Context. ICML 2023, PMLR 202, pp. 31210-31227. https://proceedings.mlr.press/v202/shi23a.html
Only metadata was read. Use: background for distractor conditions, title-level only.

## UNVERIFIED

- **Social, economic, and demographic factors drive the emergence of Hinglish code-mixing on social media.** Humanities and Social Sciences Communications, 2024. https://www.nature.com/articles/s41599-024-03058-6 The fetch redirected to a login. A search snippet says most users prefer romanised script. Do not cite until read.
- **"Over 34% of users prefer Hinglish" (IIT Delhi study, press coverage).** Search snippet only, secondary source. Do not cite.
- **Milestone Localization Hinglish report.** Commercial survey, search snippet only. Do not cite.
- **Prefill method in Tam et al. and "reasoning hub" wording.** Search snippet only; the fetched abstract does not use "hub".

## Search outcome

I searched for chain-of-thought traces written in Hinglish and found no study that measures accuracy under that manipulation. The nearest work tests romanised or code-mixed input (Indi-RomCoM, Winata et al.). This is one search session, so state it as "we did not find", not "none exists".
