# Citations for the Part A audit

Quotes were taken from the fetched source text. PDFs were read with `pdftotext`; line breaks are removed.

## Qin et al. (2023)

- **Title:** Cross-lingual Prompting: Improving Zero-shot Chain-of-Thought Reasoning across Languages
- **Authors:** Libo Qin, Qiguang Chen, Fuxuan Wei, Shijue Huang, Wanxiang Che
- **Venue:** EMNLP 2023 (main conference)
- **URLs fetched:** https://arxiv.org/abs/2310.14799, https://aclanthology.org/2023.emnlp-main.163.pdf
- **Stage 1 prompt:** "Please act as an expert in multi-lingual understanding in [Source Language Ls]. Request: [Given sentence X] Let's understand the task in [Target Language Lt] step-by-step!"
- **Stage 2 prompt:** "After understanding, you should act as an expert in [Target Task T] in [Target Language Lt]. Let's resolve the task you understand above step-by-step!" and "Finally, you should format your answer as 'Answer: [num]'."
- **Purpose of stage 1:** "the cross-lingual alignment prompting is used to align representations between different languages."
- **Settings:** "The top-p parameter in all processes is set to 1. We select the temperature in Cross-lingual Alignment Prompting from [0, 2] and the temperature in Task-specific Solver Prompting from [0, 1]."
- **Stage-1 solving:** "Preliminary Solution: This strategy indicates that CLP starts preliminary mathematical operations based on comprehension. It may even provide answers during the alignment phase. However, the model's second stage may modify this answer, so it is not the final solution." Table 7 gives it a 54.00% ratio, CLP accuracy 61.11, Native-CoT accuracy 54.63, from 200 sampled items.
- **Reported results (GPT-3.5, MGSM, AVG, Table 1):** Direct 48.6, Native-CoT 51.0, En-CoT 57.8, Translate-En 68.4, CLP 70.6, CLSP 76.7. Languages: bn, de, es, fr, ja, ru, sw, te, th, zh, so no Hindi. "outperforming all baselines with a gain of over 1.8%"; CLSP "6.1% improvements on average accuracy"; single-turn prompting shows "a significant average decrease of 10.4%"; prompt wording "maximum difference of over 4%".
- **CLSP:** "we retain the answers that exhibit a high level of consistency in the inferred reasoning results (f) through a voting mechanism."
- **Used for:** faithfulness table, ordering of CLP and En-CoT, reading of stage-1 solving.

## Qin et al. code

- **Source:** LightChen233/cross-lingual-prompting, `request.py`
- **URLs fetched:** https://github.com/LightChen233/cross-lingual-prompting, https://raw.githubusercontent.com/LightChen233/cross-lingual-prompting/main/request.py
- **Content:** Stage 1 call uses `model="gpt-3.5-turbo", temperature=1, top_p=1`. Stage 2 call uses `model="gpt-3.5-turbo", temperature=0.2, top_p=1`.
- **Used for:** the temperatures in the faithfulness table. The repository file may not be the exact configuration behind every table in the paper.

## Shi et al. (2023)

- **Title:** Language Models are Multilingual Chain-of-Thought Reasoners
- **Authors:** Freda Shi, Mirac Suzgun, Markus Freitag, Xuezhi Wang, Suraj Srivats, Soroush Vosoughi, Hyung Won Chung, Yi Tay, Sebastian Ruder, Denny Zhou, Dipanjan Das, Jason Wei
- **Venue:** arXiv:2210.03057. The fetched arXiv page shows no peer-reviewed venue; the ICLR 2023 listing was not fetched, so confirm the venue before citing it.
- **URLs fetched:** https://arxiv.org/abs/2210.03057, https://arxiv.org/pdf/2210.03057
- **Quote:** "We find that intermediate reasoning steps in English consistently lead to competitive or better results than those written in the native language of the question, suggesting that English chain-of-thought prompting may be a useful baseline for future multilingual reasoning work."
- **Used for:** en-CoT as a baseline and the MGSM benchmark.

## Huang et al. (2023)

- **Title:** Not All Languages Are Created Equal in LLMs: Improving Multilingual Capability by Cross-Lingual-Thought Prompting
- **Authors:** Haoyang Huang, Tianyi Tang, Dongdong Zhang, Wayne Xin Zhao, Ting Song, Yan Xia, Furu Wei
- **Venue:** Findings of EMNLP 2023 (per arXiv listing)
- **URLs fetched:** https://arxiv.org/abs/2305.07004, https://arxiv.org/pdf/2305.07004
- **Quote:** "XLT brings over 10 points of average improvement in arithmetic reasoning and open-domain question-answering tasks."
- **Used for:** size of cross-lingual prompting gains elsewhere. Only the abstract was relied on, because the PDF text extraction was not searchable for details.

## Wendler et al. (2024)

- **Title:** Do Llamas Work in English? On the Latent Language of Multilingual Transformers
- **Authors:** Chris Wendler, Veniamin Veselovsky, Giovanni Monea, Robert West
- **Venue:** arXiv:2402.10588. The fetched page lists no venue; the ACL 2024 listing was not fetched, so confirm before citing it.
- **URLs fetched:** https://arxiv.org/abs/2402.10588, https://arxiv.org/pdf/2402.10588
- **Quote:** "Crucially, our evidence suggests that the abstract 'concept space' lies closer to English than to other languages, which may have important consequences regarding the biases held by multilingual language models." (end of the sentence as printed in the abstract; the extracted line breaks were checked as far as "biases held by mul-")
- **Used for:** motivation only. It studies Llama-2, not Sarvam-105B.

## Zhao et al. (2024)

- **Title:** How do Large Language Models Handle Multilingualism?
- **Authors:** Yiran Zhao, Wenxuan Zhang, Guizhen Chen, Kenji Kawaguchi, Lidong Bing
- **Venue:** NeurIPS 2024
- **URLs fetched:** https://arxiv.org/pdf/2402.18815. The venue and authors come from search results listing https://proceedings.neurips.cc/paper_files/paper/2024/hash/1bd359b32ab8b2a6bbafa1ed2856cf40-Abstract.html, which was not opened.
- **Quote:** "we hypothesize the LLM's multilingual workflow (MWork): LLMs initially understand the query, converting multilingual inputs into English for task-solving. In the intermediate layers, they employ English for reasoning and incorporate multilingual knowledge with self-attention and feed-forward structures, respectively."
- **Used for:** motivation only.

## Mazzia et al. (2026)

- **Title:** Benchmarking Multilingual Temporal Reasoning in LLMs: The Temporal Reasoning Dataset
- **Authors:** Vittorio Mazzia, Sandro Pollastrini, Davide Bernardi, Chiara Rubagotti, Daniele Amberti
- **Venue:** IWSDS 2026
- **URL fetched:** https://aclanthology.org/2026.iwsds-1.19.pdf
- **Quotes:** "Temperature was fixed at 0.0 to enforce deterministic behavior." "Chain-of-thought (CoT) ... prompting was disabled through in-context-learning instructions to measure raw temporal reasoning capacity without external scaffolding." "LLMs show varied responses to both similar and dissimilar insertions."
- **Used for:** temperature choice, distractor design, and the point that TRD does not measure CoT.

## UNVERIFIED

None of the above are unverified as to existence, but three venue details are flagged where they appear: Shi et al. (ICLR 2023), Wendler et al. (ACL 2024) and the NeurIPS proceedings page for Zhao et al. Standard statistical methods (McNemar, Holm, Mantel-Haenszel, Wilson, Benjamini-Hochberg) are used here without a fetched source and should be cited from the mid report's bibliography once that is verified.
