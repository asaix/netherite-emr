# Citations for Part B

Every entry was fetched during this audit on 2026-10-31. Quotes are copied from the fetched text. arXiv HTML and PDF text was extracted locally, so line breaks and some symbols are normalised.

## The PDF's "[verify]" list

### Bogdan et al. 2025, Thought Anchors

- **Full reference:** Paul C. Bogdan, Uzay Macar, Neel Nanda, Arthur Conmy. 2025. *Thought Anchors: Which LLM Reasoning Steps Matter?* arXiv:2506.19143 (v1 23 Jun 2025, v4 27 Oct 2025). The arXiv page lists no venue.
- **URL fetched:** https://arxiv.org/abs/2506.19143, https://arxiv.org/html/2506.19143
- **PDF entry:** correct.
- **Supports the on-policy resampling method:** "We repeatedly resample reasoning traces from the start of each sentence. Based on resampling data, we can quantify the counterfactual impact of each sentence on the likelihood of any final answer."
- **Where we depart from it:**
  - They use far more samples: "generating 100 rollouts both without sentence Si ... and another distribution with sentence Si". We use 7 per arm.
  - They filter resamples: "The problem with resampling importance is that if Ti is identical or similar to Si then we do not get much information about whether Si is important or not." Our P arm has no such filter, and 57.8% of Hindi P rollouts mention the distractor anyway. This is the direct prior-work basis for the dilution argument against reading M - P as the effect of the mention.
  - They use both outcomes: "For each selected problem, we generated one correct and one incorrect reasoning trace". We use wrong traces only.
  - They study reasoning models with long thinking traces (average 144.2 sentences). Ours is thinking-off CoT.

### Macar et al. 2026, Thought Branches

- **Full reference:** Uzay Macar, Paul C. Bogdan, Senthooran Rajamanoharan, Neel Nanda. *Thought Branches: Interpreting LLM Reasoning Requires Resampling.* ICLR 2026 poster. arXiv:2510.27484 (v1 31 Oct 2025, v2 13 Apr 2026).
- **URL fetched:** https://arxiv.org/abs/2510.27484, https://arxiv.org/html/2510.27484, https://iclr.cc/virtual/2026/poster/10008605
- **PDF entry:** correct, including the venue. The arXiv page itself lists no venue; the ICLR virtual site lists the poster (Thursday 23 April 2026) with these four authors. Name all four rather than "et al." where the style allows. A search snippet suggested the ICLR slides add Arthur Conmy; I did not confirm that, and the poster page and arXiv both list four.
- **Supports "models regenerate removed content":** "Reasoning models often regenerate key ideas post-edit: a sentence removed at position i may resurface at position j≥i." Also: "Models may utter a statement later if it is omitted or they can negate earlier steps."
- **Supports "hand edits are off-policy and can trigger repair":** "Artificial interventions can understate or distort causal influence in decision-making scenarios by inducing distribution shift and triggering error correction." And the definition: "An intervention is off-policy if the model would not plausibly produce it itself (e.g., a handwritten sentence or one taken from a different context)."
- **Supports the need for many samples:** "We argue that studying a single sample is inadequate for understanding causal influence and the underlying computation."
- **Limits on the PDF's use. The sentence "that it tends to repair (Macar et al., 2026)" needs narrowing:**
  1. The comparison is in decision tasks: "We find that off-policy interventions yield small and unstable effects compared to resampling in decision-making tasks."
  2. Their off-policy experiments insert sentences. Removal is studied by resampling with a resilience metric. They did not hand-delete sentences as Experiment 1 does.
  3. Their MATH appendix points the other way for tasks closer to ours: "handwritten interventions show stronger local effects in math problems compared to blackmail scenarios", and "the relative effectiveness of on-policy versus off-policy interventions may vary by domain, with mathematical reasoning showing greater receptivity to structured external corrections." In their Table 5 (MATH), handwritten edits have the lowest no-effect rate (9.2%) and the highest plan-shift rate (64.7%), against 12.6% and 55.1% for resampled.
  4. So the README's "That matches Thought Branches" is not established for date arithmetic.
- **Supports the Q arm and the prefix limitation.** The Q arm is their transplantation design: "generate a CoT for a question while a hint is presented and then transplant portions of said CoT into a model prompted with the same question but without any hint." They find that "A hint's effects are (i) subtle, (ii) diffuse, and (iii) cumulative", which is the prior-work reason to expect the pre-k prefix can carry distractor influence. They describe this as "a form of causal mediation analysis", and the same logic says Q - P is a partial effect.
- **Supports a filtered analysis:** counterfactual++ importance "measures the causal impact when a sentence's semantic content is completely absent from the entire trace." Our exploratory M minus P(no-mention rollouts) comparison is a crude analogue, without their repeated resampling.

### Lanham et al. 2023

- **Full reference:** Tamera Lanham, Anna Chen, Ansh Radhakrishnan, Benoit Steiner, Carson Denison, Danny Hernandez, Dustin Li, Esin Durmus, Evan Hubinger, Jackson Kernion, Kamilė Lukošiūtė, Karina Nguyen, Newton Cheng, Nicholas Joseph, Nicholas Schiefer, Oliver Rausch, Robin Larson, Sam McCandlish, Sandipan Kundu, Saurav Kadavath, Shannon Yang, Thomas Henighan, Timothy Maxwell, Timothy Telleen-Lawton, Tristan Hume, Zac Hatfield-Dodds, Jared Kaplan, Jan Brauner, Samuel R. Bowman, Ethan Perez. 2023. *Measuring Faithfulness in Chain-of-Thought Reasoning.* arXiv:2307.13702.
- **URL fetched:** https://arxiv.org/abs/2307.13702, https://arxiv.org/html/2307.13702
- **PDF entry:** correct.
- **Supports intervening on CoT to test causal role:** "We investigate hypotheses for how CoT reasoning may be unfaithful, by examining how the model predictions change when we intervene on the CoT (e.g., by adding mistakes or paraphrasing it)."
- **Precedent for continuing an edited trace:** "Adding Mistakes: Have a language model add a mistake somewhere in the original CoT and then regenerate the rest of the CoT." This is the closest precedent for Experiment 1, with insertion in place of deletion.
- **Precedent for cutting a trace:** "Early Answering: Truncate the original CoT before answering."

### Yang et al. 2025

- **Full reference:** Sohee Yang, Sang-Woo Lee, Nora Kassner, Daniela Gottesman, Sebastian Riedel, Mor Geva. 2025. *How Well Can Reasoning Models Identify and Recover from Unhelpful Thoughts?* Findings of EMNLP 2025. arXiv:2506.10979.
- **URL fetched:** https://arxiv.org/abs/2506.10979, https://arxiv.org/pdf/2506.10979
- **PDF entry:** incomplete. Add the venue from the arXiv comment ("Findings of EMNLP 2025").
- **Supports harm from written irrelevant content:** "models are effective at identifying most unhelpful thoughts but struggle to recover from the same thoughts". Also: "Models tend to naively continue the line of reasoning of the injected irrelevant thoughts".
- **Caution:** this cuts against any general "models repair edits" reading, so it should not be cited alongside Macar et al. for repair. It fits M - P < 0. Their injections are whole thoughts placed in the thinking block of reasoning models. Ours is the model's own one-sentence mention in thinking-off CoT.

## Named in the brief and the merge note

### Turpin et al. 2023

- **Full reference:** Miles Turpin, Julian Michael, Ethan Perez, Samuel R. Bowman. 2023. *Language Models Don't Always Say What They Think: Unfaithful Explanations in Chain-of-Thought Prompting.* NeurIPS 2023. arXiv:2305.04388.
- **URL fetched:** https://arxiv.org/abs/2305.04388, https://arxiv.org/pdf/2305.04388
- **Supports "reading a trace is not enough" in both directions:** "CoT explanations can systematically misrepresent the true reason for a model's prediction." Biasing features are ones "which models systematically fail to mention in their explanations."
- **Use in Part B:** this is why the 81% of Hindi wrong answers with no pre-answer mention are out of scope but not exonerated. A distractor can matter without a mention, so Part B cannot say what share of all errors it causes.

### Shi et al. 2023 (GSM-IC)

- **Full reference:** Freda Shi, Xinyun Chen, Kanishka Misra, Nathan Scales, David Dohan, Ed Chi, Nathanael Schärli, Denny Zhou. 2023. *Large Language Models Can Be Easily Distracted by Irrelevant Context.* ICML 2023. arXiv:2302.00093.
- **URL fetched:** https://arxiv.org/abs/2302.00093, https://arxiv.org/pdf/2302.00093
- **Supports the distractor premise:** "the model performance is dramatically decreased when irrelevant information is included."
- **Note:** Part C's "Shi et al., 2023" is a different paper on multilingual CoT. Keep the "2023a" distinction, and add this entry to the reference list.

### Qin et al. 2023

- **Full reference:** Libo Qin, Qiguang Chen, Fuxuan Wei, Shijue Huang, Wanxiang Che. 2023. *Cross-lingual Prompting: Improving Zero-shot Chain-of-Thought Reasoning across Languages.* EMNLP 2023. arXiv:2310.14799.
- **URL fetched:** https://arxiv.org/abs/2310.14799 (via export.arxiv.org)
- **PDF entry:** correct. The arXiv comment reads "Accepted at EMNLP2023 Main Conference". Part A uses it, Part B does not.

## Added by this audit

### Tian and Pearl 2000

- **Full reference:** Jin Tian, Judea Pearl. *Probabilities of Causation: Bounds and Identification.* UAI 2000, pages 589-598. arXiv:1301.3898. Venue and pages come from a search result for the ML Anthology record (https://mlanthology.org/uai/2000/tian2000uai-probabilities), which I did not open directly.
- **URL fetched:** https://arxiv.org/abs/1301.3898, https://arxiv.org/pdf/1301.3898
- **Supports the excess fraction wording:** the excess-risk-ratio is "often misnamed as the attributable fraction", because "ERR invokes purely statistical relationships, hence it cannot in itself serve to measure attribution, unless fortified with some causal assumptions."
- **Supports the lower-bound reading:** "the point estimates that Pearl obtained under the assumption of monotonicity ... constitute valid lower bounds when monotonicity is not assumed."
- **Use:** (P wrong - Q wrong) / P wrong is the ERR. Randomised arm assignment supplies exogeneity. Monotonicity is doubtful here because some distractors help (for example "22 तारीख ...", Q - P -4.6), so "one in eleven" is a lower bound on how often the distractor was necessary, within the conditions of the contrast.

### Pearl 2001

- **Full reference:** Judea Pearl. *Direct and Indirect Effects.* UAI 2001, pages 411-420. arXiv:1301.2300. Venue and pages come from a search result for the ML Anthology record (https://mlanthology.org/uai/2001/pearl2001uai-direct), which I did not open directly.
- **URL fetched:** https://arxiv.org/abs/1301.2300, https://arxiv.org/pdf/1301.2300
- **Supports the estimand language:** "The direct effect of one event on another can be defined and measured by holding constant all intermediate variables between the two." The paper separates this controlled effect from the natural effect, and shows that indirect effects "cannot be isolated by holding certain variables constant."
- **Use:** Q - P holds the pre-k text constant but leaves the later text free. It is therefore neither a total effect (for k > 0) nor a direct effect with respect to later mentions. A difference of such contrasts does not decompose into "through the question" and "through the mention".

## Non-paper sources

- **Sarvam chat template:** https://huggingface.co/sarvamai/sarvam-105b-fp8/raw/main/chat_template.jinja, fetched 2026-10-31. Confirms no default system prompt, `<|nothink|>` appended to the user turn when `enable_thinking` is false, and assistant turns rendered as `<think></think>` followed by a newline and the stripped content. This is the current file, for the `sarvam-105b-fp8` repo named in `gpu/template_check.py`. I did not fetch the version served from the RedHatAI repo, and the run's template-check log is not in the repository.

## UNVERIFIED

None of the works above. Two items cited inside Macar et al. (Bigelow et al. 2024, Wang et al. 2025) were not fetched and are not relied on here.
