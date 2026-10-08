# Router results (n = 340)

| System | n | Acc | 95% CI | Macro-F1 | canonical | paraphrase | hard | LLM calls | p50 s | p95 s |
|---|---|---|---|---|---|---|---|---|---|---|
| rules[full] | 340 | 0.491 | 0.438-0.544 | 0.587 | 1.000 | 0.111 | 0.532 | 0.00 | 0.0000 | 0.0000 |
| rules[precise] | 340 | 0.374 | 0.318-0.424 | 0.463 | 0.741 | 0.111 | 0.380 | 0.00 | 0.0000 | 0.0000 |
| qwen3-4b__definitions__constrained | 340 | 0.906 | 0.876-0.935 | 0.901 | 0.954 | 0.908 | 0.835 | 1.00 | 1.2024 | 1.8872 |
| hybrid[full+qwen3-4b__definitions__constrained] | 340 | 0.853 | 0.818-0.888 | 0.854 | 1.000 | 0.804 | 0.747 | 0.41 | 0.0000 | 1.6073 |
| hybrid[precise+qwen3-4b__definitions__constrained] | 340 | 0.894 | 0.862-0.926 | 0.888 | 0.944 | 0.895 | 0.823 | 0.60 | 0.5798 | 1.7973 |
| qwen3-4b__few_shot__constrained | 340 | 0.950 | 0.926-0.974 | 0.950 | 0.972 | 0.961 | 0.899 | 1.00 | 1.0902 | 1.4895 |
| hybrid[full+qwen3-4b__few_shot__constrained] | 340 | 0.882 | 0.847-0.918 | 0.886 | 1.000 | 0.856 | 0.772 | 0.41 | 0.0000 | 1.4044 |
| hybrid[precise+qwen3-4b__few_shot__constrained] | 340 | 0.932 | 0.906-0.959 | 0.932 | 0.963 | 0.948 | 0.861 | 0.60 | 0.6544 | 1.4579 |
| qwen3-4b__zero_shot__constrained | 340 | 0.526 | 0.471-0.582 | 0.480 | 0.611 | 0.490 | 0.481 | 1.00 | 1.3477 | 2.0126 |
| hybrid[full+qwen3-4b__zero_shot__constrained] | 340 | 0.665 | 0.615-0.718 | 0.662 | 1.000 | 0.458 | 0.608 | 0.41 | 0.0000 | 1.5745 |
| hybrid[precise+qwen3-4b__zero_shot__constrained] | 340 | 0.629 | 0.576-0.682 | 0.606 | 0.843 | 0.503 | 0.582 | 0.60 | 1.1915 | 1.6578 |
| qwen3-4b__zero_shot__free | 18 | 0.667 | 0.444-0.889 | 0.585 | 0.667 | nan | nan | 1.00 | 67.7818 | 286.4429 |
| hybrid[full+qwen3-4b__zero_shot__free] | 18 | 1.000 | 1.000-1.000 | 1.000 | 1.000 | nan | nan | 0.00 | 0.0000 | 0.0000 |
| hybrid[precise+qwen3-4b__zero_shot__free] | 18 | 0.778 | 0.556-0.944 | 0.689 | 0.778 | nan | nan | 0.22 | 0.0000 | 69.6020 |
| tfidf_logreg_cv5 | 340 | 0.926 | 0.897-0.953 | 0.925 | 0.981 | 0.915 | 0.873 | 0.00 | 0.0009 | 0.0016 |
| hybrid[full+tfidf_logreg_cv5] | 340 | 0.862 | 0.824-0.900 | 0.863 | 1.000 | 0.824 | 0.747 | 0.41 | 0.0000 | 0.0014 |
| hybrid[precise+tfidf_logreg_cv5] | 340 | 0.915 | 0.882-0.944 | 0.914 | 0.981 | 0.902 | 0.848 | 0.60 | 0.0008 | 0.0014 |

rules[full]: coverage 0.594, precision when a rule fires 0.827

rules[precise]: coverage 0.403, precision when a rule fires 0.927

## Paired McNemar tests

| Comparison | hybrid-only correct | base-only correct | p |
|---|---|---|---|
| hybrid[full+qwen3-4b__definitions__constrained] vs qwen3-4b__definitions__constrained | 15 | 33 | 0.01328 |
| hybrid[precise+qwen3-4b__definitions__constrained] vs qwen3-4b__definitions__constrained | 5 | 9 | 0.424 |
| hybrid[full+qwen3-4b__few_shot__constrained] vs qwen3-4b__few_shot__constrained | 10 | 33 | 0.0006061 |
| hybrid[precise+qwen3-4b__few_shot__constrained] vs qwen3-4b__few_shot__constrained | 3 | 9 | 0.146 |
| hybrid[full+qwen3-4b__zero_shot__constrained] vs qwen3-4b__zero_shot__constrained | 67 | 20 | 4.305e-07 |
| hybrid[precise+qwen3-4b__zero_shot__constrained] vs qwen3-4b__zero_shot__constrained | 40 | 5 | 7.878e-08 |
| hybrid[full+tfidf_logreg_cv5] vs tfidf_logreg_cv5 | 8 | 30 | 0.000472 |
| hybrid[precise+tfidf_logreg_cv5] vs tfidf_logreg_cv5 | 3 | 7 | 0.3438 |
