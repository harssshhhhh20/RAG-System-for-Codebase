# Rules First? Intent Routing for Developer Assistants on Small Local LLMs

*Working draft. Numbers marked **[pilot]** come from the development set and must be replaced with held-out test-set results before submission. See "Path to submission" at the end.*

## Abstract (template)

Local-first assistants route each user request to a tool, such as editing a file, managing tasks or answering a question from an indexed codebase. A common design puts cheap keyword rules in front of an LLM classifier. We study this design on a laptop-class machine (Apple M2, 8 GB) with a 4B-parameter model served by Ollama. On **[N]** requests over nine intents, we compare:

- keyword rules
- an LLM under three prompt styles and two decoding modes
- a small trained classifier
- rules→fallback hybrids

We find that **[headline 1: e.g. the model's default "thinking" decoding costs X s per request for Y accuracy, while schema-constrained decoding takes Z s]**, that **[headline 2: label definitions and few-shot examples raise accuracy from A to B]**, and that **[headline 3: high-coverage rules lower the accuracy of a strong fallback; only high-precision rules help]**. We release the dataset, the harness and the assistant.

## 1. Introduction

- **Setting.** Developer assistants that run fully on device for privacy and cost: no cloud calls, consumer hardware, 1–8B models.
- **Problem.** Routing is on the critical path of every request. Large models route well but are slow locally. Rules are instant but brittle.
- **Gap.** Prior routing work routes between models to save cost (e.g. RouteLLM). Intent-detection benchmarks (CLINC150, BANKING77) assume a trained classifier and plenty of data. Neither measures the rules-first pattern that hobbyist and production agents actually ship, under local latency budgets.
- **Research questions:**
  - **RQ1.** How do rules, a small local LLM and a lightweight trained classifier compare in accuracy and latency?
  - **RQ2.** How much do prompt design (zero-shot, label definitions, few-shot) and decoding (free/thinking vs. schema-constrained) change LLM routing accuracy and latency?
  - **RQ3.** When does putting rules in front of a fallback help, and when does it hurt? How does this depend on rule precision vs. coverage?
- **Contributions:**
  1. A labeled routing dataset with canonical, paraphrase and adversarial (keyword-trap) subsets.
  2. A reproducible harness: resumable runs, environment capture, bootstrap confidence intervals, McNemar tests.
  3. An empirical study answering RQ1–RQ3.
  4. Practical guidance: gate rules on precision, constrain decoding, and give the model label definitions.

## 2. Related work (verify every reference before citing)

- **Retrieval-augmented generation.** Lewis et al., 2020 (NeurIPS), "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks".
- **Model routing.** Ong et al., 2024, "RouteLLM: Learning to Route LLMs with Preference Data" (arXiv:2406.18665).
- **Intent detection benchmarks:**
  - Larson et al., 2019 (EMNLP-IJCNLP), CLINC150 / out-of-scope intent detection.
  - Casanueva et al., 2020 (NLP4ConvAI), BANKING77.
- **Constrained / structured decoding:**
  - Willard & Louf, 2023, "Efficient Guided Generation for Large Language Models" (arXiv:2307.09702).
  - Tam et al., 2024, "Let Me Speak Freely? A Study on the Impact of Format Restrictions on Performance of Large Language Models" (arXiv:2408.02442).
- **Small reasoning models.** Qwen Team, 2025, "Qwen3 Technical Report" (arXiv:2505.09388).
- **Statistical comparison of classifiers.** McNemar, 1947 (Psychometrika); Dietterich, 1998 (Neural Computation).
- **Code retrieval** (for the secondary study):
  - BM25: Robertson & Zaragoza, 2009.
  - Reciprocal rank fusion: Cormack et al., 2009 (SIGIR).
  - BGE-M3: Chen et al., 2024 (arXiv:2402.03216).

## 3. System

SHIVI is a terminal assistant with nine intents:

- **automation**: open apps and URLs
- **memory**: personal facts
- **code**: show, run, edit, review or explain a file
- **task**, **project**: to-do and project tracking
- **qa**: RAG over indexed sources
- **source**: register folders to index
- **ingest**: rebuild the index
- **planner**: what to work on next

Routing (`shivi/router.py`) applies ordered deterministic rules, then falls back to an Ollama model. The fallback uses JSON-schema-constrained decoding over the label set. Figure 1: request → rules → (fallback) → handler.

## 4. Experimental setup

- **Data.**
  - Development set: 340 requests (`eval/data/router_dev.jsonl`), split into canonical 108, paraphrase 153 and hard 79.
  - Test set: **[TODO: ≥500 requests from independent participants, double-annotated, Cohen's κ reported]**.
- **Systems:**
  - rules[full] and rules[precise]
  - LLM (qwen3:4b, Q4_K_M) × {zero_shot, definitions, few_shot} × {constrained, free}
  - TF-IDF + logistic regression (5-fold CV)
  - hybrid[rules + each fallback]
- **Model sweep.** **[TODO: qwen3 0.6B / 1.7B / 4B / 8B and one non-Qwen family of similar size]**.
- **Hardware.** Apple M2, 8 GB unified memory, Ollama 0.33.2. The exact environment is recorded per run in `env.json`.
- **Metrics:**
  - accuracy with a 95% percentile bootstrap CI (2,000 resamples) and macro-F1
  - accuracy per subset
  - p50/p95 latency (warm model; load time excluded via a warm-up call) and LLM call rate
  - paired exact McNemar test for each hybrid against its fallback alone

## 5. Results [pilot]

Development set (n = 340), qwen3:4b Q4_K_M on Apple M2 8 GB. Full table: `results/router/pilot-qwen3-4b/summary.md`.

| System | Acc [95% CI] | Macro-F1 | Hard subset | LLM calls | p50 / p95 latency |
|---|---|---|---|---|---|
| Rules (full) | 0.491 [0.438, 0.544] | 0.587 | 0.532 | 0 | <0.1 ms |
| LLM zero-shot (original prompt) | 0.526 [0.471, 0.582] | 0.480 | 0.481 | 1.00 | 1.35 / 2.01 s |
| LLM + label definitions | 0.906 [0.876, 0.935] | 0.901 | 0.835 | 1.00 | 1.20 / 1.89 s |
| LLM + definitions + few-shot | **0.950** [0.926, 0.974] | **0.950** | **0.899** | 1.00 | 1.09 / 1.49 s |
| TF-IDF + LR (5-fold CV) | 0.926 [0.897, 0.953] | 0.925 | 0.873 | 0 | 0.8 ms |
| Rules (full) → few-shot LLM | 0.882 [0.847, 0.918] | 0.886 | 0.772 | 0.41 | 0.00 / 1.40 s |
| Rules (precise) → few-shot LLM | 0.932 [0.906, 0.959] | 0.932 | 0.861 | 0.60 | 0.65 / 1.46 s |

**RQ1.** The full rules are perfect on canonical commands (1.000) but fail on paraphrases (0.111). They fire on 59% of requests with only 0.83 precision. A cross-validated TF-IDF classifier reaches 0.926 at under 1 ms, which is a strong baseline that any LLM router must beat. *(Caveat: templated canonical items inflate this.)*

**RQ2.** Prompt design dominates. Adding one-line label definitions lifts accuracy from 0.526 to 0.906. Adding nine out-of-set examples lifts it further to 0.950, and latency does not rise (p50 1.09 s, p95 1.49 s). Schema-constrained decoding makes each call about 10 output tokens. Without it, the same model at default settings spent about 1,100 tokens and 164 s on a single request in a probe, and answered wrongly *Free-decoding subsample* (first 2 items per label, all canonical; n = 18):

| Decoding | Accuracy | Mean output tokens | p50 / p95 latency |
|---|---|---|---|
| free (default thinking) | 12/18 | 1,136 | 67.8 / 286.4 s |
| constrained, same prompt | 10/18 | 10 | about 1.3 s |

That is roughly 50× slower for a gain of 2 items, which is within noise at this n. Warm-up alone took 143 s. The subsample contains only canonical commands, so it says nothing about paraphrases..

**RQ3.** Rules in front of a good fallback **hurt**:

- With full rules in front of the few-shot LLM, accuracy falls from 0.950 to 0.882 (McNemar: 10 hybrid-only vs. 33 LLM-only correct, p = 6.1e-4).
- The same happens with the TF-IDF fallback (p = 4.7e-4).
- In front of the weak zero-shot LLM, rules help (0.526 to 0.665, p = 4.3e-7).
- The high-precision profile (coverage 0.40, precision 0.93) removes most of the damage. Against the few-shot LLM: 0.932 vs. 0.950, p = 0.15, not significant. It still skips the LLM on 40% of requests.

The benefit of a rule layer therefore depends on the fallback's quality relative to the rules' *precision*, not their coverage.

**Error analysis (few-shot LLM, 17 errors).** 11 of the 17 are *topic-vs-action* confusions: a question about a subsystem gets that subsystem's label. Examples: "where are tasks stored?" → task, "describe the memory system" → memory, "how do sources get ingested?" → ingest. Most of the rest involve a misleading keyword ("i need to remember to write docs" → memory). Zero-shot errors are systematic instead: memory→qa (23), planner→task (21), automation→qa/code/task (34).

## 6. Discussion

- **Why do high-coverage rules hurt?** The broad "starts with a question word → qa" rule captures questions about tasks, projects, sources and plans. Its errors cannot be corrected downstream, because the fallback never sees those requests.
- **Precision matters more than coverage.** Gating rules on measured precision (e.g. ≥ 0.95 on development data) is a cheap, principled design rule.
- **Constrained decoding is a latency feature, not just a formatting feature.** For thinking models it removes hundreds of reasoning tokens per request.
- **Threats to validity:**
  - one author wrote both the rules and the development set
  - English only, single turn
  - one hardware platform
  - Ollama version and quantization effects
  - the TF-IDF baseline is inflated by templated canonical items under cross-validation

## 7. Secondary study: file retrieval for codebase questions [pilot]

36 questions over the 19-file `shivi/` package, BM25 only (dense retrieval pending installation of `sentence-transformers`). Results: `results/retrieval/pilot-lexical/summary.md`.

| Chunking / retriever | R@1 | R@3 | R@5 | MRR |
|---|---|---|---|---|
| char-500 / BM25 | 0.625 | 0.819 | 0.917 | 0.778 |
| char-500 / BM25 + filename index | 0.653 | 0.819 | 0.917 | 0.797 |
| AST / BM25 | 0.625 | 0.861 | 0.944 | 0.778 |
| AST / BM25 + filename index | 0.653 | 0.861 | 0.944 | 0.796 |

The corpus is too small and the questions too close to the code's own wording to draw conclusions. This only validates the harness.

## Path to submission

1. **Held-out test set.** Recruit 10–20 developers. Give them short scenario cards, collect ≥ 500 requests, double-annotate, and report κ.
2. **Freeze before testing.** Freeze rules, prompts and few-shot examples, then run the test set once.
3. **Model sweep.** At least three sizes and two model families. Report memory footprint as well as latency.
4. **Second hardware platform.** E.g. an x86 laptop without a GPU.
5. **Calibrated rule gating.** Promote a rule only if its development precision clears a threshold, then report the coverage/accuracy trade-off curve on test.
6. **Write-up targets.** A workshop on efficient or on-device NLP, or on LLMs for software engineering. Tool or demo tracks at SE/NLP conferences are a second option. Post a preprint first.
