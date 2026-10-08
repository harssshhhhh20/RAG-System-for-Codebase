# Evaluation harness

Two experiments, both runnable on a laptop.

| Experiment | Script | Question |
|---|---|---|
| Intent routing | `run_router_eval.py` | For a small local LLM, how do keyword rules, the LLM, and rules→LLM hybrids trade accuracy against latency? How much do prompt design and constrained decoding matter? |
| File retrieval | `run_retrieval_eval.py` | Which chunking and retriever find the right file for a codebase question? |

## Setup

```bash
pip install -e ".[dev,eval]"
ollama pull qwen3:4b
```

The router experiment needs only the standard library and a running Ollama server. scikit-learn adds the trained-classifier baseline. For dense retrieval, `sentence-transformers` comes with the main install.

## Router experiment

```bash
python -m eval.run_router_eval --models qwen3:4b --styles zero_shot,definitions,few_shot --decoding constrained --run-name my-run
```

Conditions:

- **Rule profiles.** `full` is every rule SHIVI ships. `precise` drops the broad "question word → qa" and "open/launch/start → automation" heuristics.
- **Prompt styles.**
  - `zero_shot`: SHIVI's original prompt, kept verbatim.
  - `definitions`: adds a one-line definition per label.
  - `few_shot`: definitions plus nine examples that are not in the dataset. The harness refuses to run if any example appears in the data.
- **Decoding.**
  - `constrained`: Ollama structured output with a JSON-schema enum over the labels, and thinking off.
  - `free`: the model's default, including thinking for qwen3. This is what a plain `ChatOllama` call does, and it is very slow, so run it on a subsample with `--per-label 2`.
- **Baseline.** TF-IDF + logistic regression, 5-fold stratified cross-validation.

Every LLM call is appended to `results/router/<run>/predictions/<condition>.jsonl` as soon as it returns. Rerunning the same command resumes an interrupted run. `--analyze-only` recomputes metrics without calling a model.

Hybrid systems are derived, not run separately. For each request, the hybrid uses the rule label if a rule fires and the LLM label otherwise. Its latency is rule time plus LLM time when the LLM was needed. This is exactly what the CLI does.

Outputs per run:

- `env.json`: git commit, dirty flag, hardware, Ollama version, model quantization
- `rules_<profile>.jsonl`, `predictions/*.jsonl`: raw predictions, latency, token counts, raw model output
- `summary.json`, `summary.md`:
  - accuracy with a 95% bootstrap confidence interval, macro-F1 and per-subset accuracy
  - per-label precision, recall and F1, and confusion matrices
  - p50/p95 latency and LLM call rate
  - exact McNemar tests of each hybrid against its fallback alone

To add models, pull them first, then pass a comma-separated list:

```bash
ollama pull qwen3:1.7b
python -m eval.run_router_eval --models qwen3:1.7b,qwen3:4b --run-name size-sweep
```

## Retrieval experiment

```bash
python -m eval.run_retrieval_eval --corpus shivi --run-name my-run
python -m eval.run_retrieval_eval --dense-model "" --run-name lexical-only   # skip embeddings
```

This reports file-level Recall@1/3/5 and MRR for:

- `char` vs `ast` chunking
- BM25, dense, and reciprocal-rank-fusion hybrid retrieval
- each of the above with and without the filename-index shortcut

## Data

See [data/DATASET_CARD.md](data/DATASET_CARD.md). Both datasets are **development sets** with documented biases. Do not report final numbers on them; the card explains what a publishable test set needs.
