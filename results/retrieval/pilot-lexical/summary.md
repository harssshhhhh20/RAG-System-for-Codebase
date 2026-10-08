# Retrieval results (36 questions, 6 name a file; 19 corpus files)

| Chunker/retriever | chunks | R@1 | R@3 | R@5 | MRR | MRR (no file named) |
|---|---|---|---|---|---|---|
| char/bm25 | 142 | 0.625 | 0.819 | 0.917 | 0.778 | 0.756 |
| char/bm25+filename | 142 | 0.653 | 0.819 | 0.917 | 0.797 | 0.756 |
| ast/bm25 | 115 | 0.625 | 0.861 | 0.944 | 0.778 | 0.755 |
| ast/bm25+filename | 115 | 0.653 | 0.861 | 0.944 | 0.796 | 0.755 |
