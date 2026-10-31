# Citations for the LR audit

Quotes come from the page or PDF fetched during this audit. An entry marked `UNVERIFIED` was not read at its source.

## Chain-of-thought faithfulness

**Turpin, Michael, Perez, Bowman (2023).** Language Models Don't Always Say What They Think: Unfaithful Explanations in Chain-of-Thought Prompting. NeurIPS 2023 (per the arXiv comment). https://arxiv.org/abs/2305.04388
Quote: "CoT explanations can systematically misrepresent the true reason for a model's prediction."
Use: a trace is not established as the process behind the answer, so divergence between traces cannot be read as divergence in the computation.

**Lanham et al. (2023).** Measuring Faithfulness in Chain-of-Thought Reasoning. arXiv:2307.13702. https://arxiv.org/abs/2307.13702
Quote: "examining how the model predictions change when we intervene on the CoT (e.g., by adding mistakes or paraphrasing it)"; "Models show large variation across tasks in how strongly they condition on the CoT."
Use: their design intervenes on the trace, and ours only observes. The task heterogeneity they report matches our per-task slopes, though on a different question.

**Zhao, Liu, Schütze, Hedderich (2025).** A Comprehensive Evaluation of Multilingual Chain-of-Thought Reasoning: Performance, Consistency, and Faithfulness Across Languages. arXiv:2510.09555. https://arxiv.org/abs/2510.09555
Quote: "we assess crosslingual consistency of thinking traces by interchanging them between languages"; they "adapt perturbation-based techniques -- i.e., truncation and error injection -- to probe the faithfulness".
Use: closest prior work. They test consistency by swapping traces, an intervention, where we compare trace strings. A search result lists it as Findings of EACL 2026; I read only the arXiv page, so check the venue before citing it.

## Edit distance and reasoning sequences

**Levenshtein (1966).** Binary codes capable of correcting deletions, insertions, and reversals. Soviet Physics Doklady (English translation; Russian original in Doklady Akademii Nauk SSSR, 1965). `UNVERIFIED` at the primary source. Secondary source fetched: NIST Dictionary of Algorithms and Data Structures, https://xlinux.nist.gov/dads/HTML/Levenshtein.html
Quote from NIST: "The smallest number of insertions, deletions, and substitutions required to change one string or tree into another."
Use: base metric. Our cost for partial dates (0.5) and the normalisation by the longer length are our own departures.

**Dai, Li, Zhou, Hu (2024).** Beyond Imitation: Learning Key Reasoning Steps from Dual Chain-of-Thoughts in Reasoning Distillation. arXiv:2405.19737. https://arxiv.org/abs/2405.19737
Quote: "apply the minimum edit distance algorithm on the dual CoTs data to locate these key steps".
Use: precedent for edit distance over CoT pairs. They use it to locate pivotal steps in distillation, not as a predictor of correctness, and their pairs are constructed to differ in conclusion.

**Xie, Orel, Thareja et al. (2025).** FinChain: A Symbolic Benchmark for Verifiable Chain-of-Thought Financial Reasoning. arXiv:2506.02515. https://arxiv.org/abs/2506.02515
Close paraphrase: ChainEval is "a dynamic alignment measure" that scores final-answer correctness and step-level reasoning consistency.
Use: precedent for step alignment that keeps answer scoring and step scoring as separate components, which is what RDS fails to do. The abstract page does not state the alignment algorithm.

**Lee, Park, Sim, Bae (2025).** Rewarding Structural Conformance of Reasoning using Process Mining. arXiv:2510.25065. https://arxiv.org/abs/2510.25065
Quote: "TACReward aggregates stepwise structural deviations between teacher and policy reasoning using process mining techniques."
Use: precedent for scoring structure separately from outcome, as our op-type view does. The abstract does not discuss edit distance.

I found no prior work that regresses cross-lingual correctness disagreement on an edit distance over parsed reasoning steps. That is a statement about my searches, not proof that none exists.

## Regression methods

**Cameron and Miller (2015).** A Practitioner's Guide to Cluster-Robust Inference. Journal of Human Resources 50(2). PDF fetched: https://escholarship.org/content/qt1jq5d0pq/qt1jq5d0pq.pdf
Quote: "failure to control for this within-cluster error correlation can lead to using standard errors that are too small, with consequent overly-narrow confidence intervals, overly-large t-statistics, and over-rejection of true null hypotheses."
Quote on the bootstrap: a "pairs cluster bootstrap that, like the CRVE, gives a consistent estimate of V[β̂] when errors are clustered."
Use: clustered SEs in the logits, and cluster bootstrap for rates, AUC and fixed-effect ORs. Section VII.C covers logit.

**Chamberlain (1980).** Analysis of Covariance with Qualitative Data. Review of Economic Studies 47(1), 225-238. Abstract page fetched: https://ideas.repec.org/a/oup/restud/v47y1980i1p225-238..html
Quote: "Instead a conditional likelihood function is maximized, conditional on sufficient statistics for the incidental parameters."; "In the logit case, a standard conditional logit program can be used."
Use: the question fixed-effects model. Only questions whose outcome varies across distractor variants contribute.

**Mood (2010).** Logistic Regression: Why We Cannot Do What We Think We Can Do, and What We Can Do About It. European Sociological Review (DOI 10.1093/esr/jcp006; the fetched copy is the 2009 advance-access version, volume details from search results). PDF fetched: https://academicweb.nd.edu/~rwilliam/ndonly/readings/CDA/BinaryOutcomes/Logistic%20regression%20-%20Why%20we%20cannot%20do%20what%20we%20think%20we%20can%20do.pdf
Quote: "we cannot compare log-odds ratios or odds ratios for similar models across groups, samples, or time points, or across models with different independent variables in a sample."; "AME expresses the average effect of x1 on P(y = 1)."
Use: why ORs across modes and token views are not directly comparable, why we report AME and per-SD scales, and why the AME is close to equal across OFF rows with and without controls (23.96 and 24.02).

**Peduzzi, Concato, Kemper, Holford, Feinstein (1996).** A simulation study of the number of events per variable in logistic regression analysis. J Clin Epidemiol 49(12), 1373-9. https://pubmed.ncbi.nlm.nih.gov/8970487/
Quote: "For EPV values less than 10, however, the regression coefficients were biased."; "low EPV can lead to major problems."
Use: the ON adjusted model has 2.1 events per parameter.

**Ogawa and Tomo (2023).** On the existence of Firth's modified estimates in logistic regression models. arXiv:2304.07484. PDF fetched: https://arxiv.org/pdf/2304.07484v1
Quote: "Firth's modified estimator is widely used to address the issue of data separation, which results in the nonexistence of the maximum likelihood estimate."
Use: secondary source for the Firth fit in the ON models.

**Heinze and Schemper (2002).** A solution to the problem of separation in logistic regression. Statistics in Medicine 21(16), 2409-2419. `UNVERIFIED`: publisher, aggregator and BibSonomy pages failed or returned bot challenges. The reference details are confirmed in the reference list of Ogawa and Tomo. A search summary says it prefers profile penalised likelihood intervals over Wald; I could not confirm that at the source, so check it before citing.

**Firth (1993).** Bias reduction of maximum likelihood estimates. Biometrika 80(1), 27-38. `UNVERIFIED`: reference details taken from Ogawa and Tomo only.

**Liang and Zeger (1986).** Longitudinal data analysis using generalized linear models. Biometrika 73(1), 13-22. `UNVERIFIED`: the Johns Hopkins PDF returned HTTP 403 and the Bohrium page returned a bot challenge. Seen in search snippets only. Cameron and Miller is the verified substitute for clustered inference.
