"""Retrieval experiment: which chunking + retriever finds the right file?

Example (from the repo root):

    python -m eval.run_retrieval_eval --corpus shivi --run-name pilot

Compares, at the file level (a hit = any chunk from a gold file):
  chunkers:   char  (fixed 500-char windows, 100 overlap; SHIVI's original)
              ast   (one chunk per top-level function/class for Python,
                     char windows for everything else)
  retrievers: bm25, dense (optional, sentence-transformers), and
              hybrid (reciprocal rank fusion of bm25 + dense)
  shortcut:   + filename index lookup when the question names a file

Metrics: Recall@1/3/5 and MRR over files.
"""
import argparse
import ast
import json
import math
import os
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from eval.run_router_eval import git_state, hardware  # noqa: E402
from shivi.fileops import extract_file_name  # noqa: E402
from shivi.ingest import IGNORE_DIRS, SUPPORTED_TEXT_FILES  # noqa: E402

DEFAULT_QUESTIONS = REPO_ROOT / "eval" / "data" / "retrieval_dev.jsonl"
RESULTS_DIR = REPO_ROOT / "results" / "retrieval"
EXCLUDE_PARTS = {"eval", "tests", "results", "paper", "dist"}


# --- corpus and chunking -------------------------------------------------

def load_corpus(root):
    files = {}
    for directory, dirs, names in os.walk(root):
        dirs[:] = sorted(
            d for d in dirs
            if d not in IGNORE_DIRS and not d.startswith(".") and d not in EXCLUDE_PARTS
            and not d.endswith(".egg-info")
        )
        for name in sorted(names):
            if name.startswith(".") or not name.endswith(SUPPORTED_TEXT_FILES):
                continue
            path = os.path.join(directory, name)
            relative = os.path.relpath(path, root)
            try:
                files[relative] = Path(path).read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
    return files


def char_chunks(text, size=500, overlap=100):
    if not text:
        return []
    step = size - overlap
    return [text[i:i + size] for i in range(0, max(1, len(text) - overlap), step)]


def ast_chunks(text, path):
    """Top-level functions/classes become chunks; module code between them too."""
    if not path.endswith(".py"):
        return char_chunks(text)
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return char_chunks(text)
    lines = text.splitlines(keepends=True)
    chunks, cursor = [], 0
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        start = (node.decorator_list[0].lineno if node.decorator_list else node.lineno) - 1
        if start > cursor:
            chunks.append("".join(lines[cursor:start]))
        chunks.append("".join(lines[start:node.end_lineno]))
        cursor = node.end_lineno
    chunks.append("".join(lines[cursor:]))
    out = []
    for chunk in chunks:
        if not chunk.strip():
            continue
        # Very long definitions are windowed so no chunk dwarfs the others.
        out.extend(char_chunks(chunk, size=2000, overlap=200) if len(chunk) > 2000 else [chunk])
    return out


CHUNKERS = {
    "char": lambda text, path: char_chunks(text),
    "ast": ast_chunks,
}


def build_chunks(files, chunker):
    chunks = []
    for path, text in files.items():
        for piece in CHUNKERS[chunker](text, path):
            # Prefix the path so retrievers can match on file names, as a
            # real index would via metadata.
            chunks.append({"file": path, "text": f"{path}\n{piece}"})
    return chunks


# --- retrievers ----------------------------------------------------------

TOKEN = re.compile(r"[a-z0-9]+")


def tokenize(text):
    """Lowercase word tokens; snake_case and camelCase are split too."""
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    return TOKEN.findall(text.lower().replace("_", " "))


class BM25:
    def __init__(self, documents, k1=1.5, b=0.75):
        self.k1, self.b = k1, b
        self.docs = [Counter(tokenize(d)) for d in documents]
        self.lengths = [sum(d.values()) for d in self.docs]
        self.avg = sum(self.lengths) / max(1, len(self.lengths))
        df = Counter(term for doc in self.docs for term in doc)
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def scores(self, query):
        terms = tokenize(query)
        out = []
        for doc, length in zip(self.docs, self.lengths):
            score = 0.0
            for term in terms:
                tf = doc.get(term)
                if tf:
                    norm = tf + self.k1 * (1 - self.b + self.b * length / self.avg)
                    score += self.idf[term] * tf * (self.k1 + 1) / norm
            out.append(score)
        return out


class Dense:
    def __init__(self, documents, model_name):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)
        self.vectors = self.model.encode(documents, normalize_embeddings=True,
                                         show_progress_bar=False)

    def scores(self, query):
        vector = self.model.encode([query], normalize_embeddings=True)[0]
        return list(self.vectors @ vector)


def rank_files(chunks, chunk_scores):
    """File score = best chunk score. Returns files best first."""
    best = {}
    for chunk, score in zip(chunks, chunk_scores):
        if score > best.get(chunk["file"], float("-inf")):
            best[chunk["file"]] = score
    return [f for f, _ in sorted(best.items(), key=lambda item: -item[1])]


def rrf(*rankings, k=60):
    fused = defaultdict(float)
    for ranking in rankings:
        for position, item in enumerate(ranking):
            fused[item] += 1 / (k + position + 1)
    return [item for item, _ in sorted(fused.items(), key=lambda item: -item[1])]


def filename_shortcut(question, ranking, files):
    """Move files named in the question to the front (SHIVI's filename index)."""
    reference = extract_file_name(question)
    if not reference:
        return ranking
    name = os.path.basename(reference).lower()
    named = [f for f in files if os.path.basename(f).lower() == name]
    return named + [f for f in ranking if f not in named]


# --- evaluation ----------------------------------------------------------

def file_metrics(ranking, gold, ks=(1, 3, 5)):
    result = {f"recall@{k}": len(set(ranking[:k]) & gold) / len(gold) for k in ks}
    reciprocal = 0.0
    for position, item in enumerate(ranking, start=1):
        if item in gold:
            reciprocal = 1 / position
            break
    result["mrr"] = reciprocal
    return result


def mean_metrics(per_question):
    keys = per_question[0].keys()
    return {k: sum(q[k] for q in per_question) / len(per_question) for k in keys}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--corpus", default=str(REPO_ROOT / "shivi"),
                        help="directory to index; gold paths are relative to it")
    parser.add_argument("--questions", default=str(DEFAULT_QUESTIONS))
    parser.add_argument("--dense-model", default="BAAI/bge-m3",
                        help="sentence-transformers model; pass '' to skip dense retrieval")
    parser.add_argument("--run-name", default=time.strftime("%Y%m%d-%H%M%S"))
    args = parser.parse_args()

    files = load_corpus(args.corpus)
    with open(args.questions, encoding="utf-8") as f:
        questions = [json.loads(line) for line in f if line.strip()]
    missing = {g for q in questions for g in q["gold_files"]} - set(files)
    if missing:
        raise SystemExit(f"Gold files not in corpus: {sorted(missing)}")

    results, per_question_log = {}, []
    for chunker in CHUNKERS:
        chunks = build_chunks(files, chunker)
        texts = [c["text"] for c in chunks]
        retrievers = {"bm25": BM25(texts)}
        if args.dense_model:
            try:
                retrievers["dense"] = Dense(texts, args.dense_model)
            except ImportError:
                print("sentence-transformers not installed; skipping dense retrieval")
        rankings = defaultdict(list)
        for q in questions:
            per = {name: rank_files(chunks, r.scores(q["question"])) for name, r in retrievers.items()}
            if "dense" in per:
                per["hybrid_rrf"] = rrf(per["bm25"], per["dense"])
            for name in list(per):
                per[f"{name}+filename"] = filename_shortcut(q["question"], per[name], files)
            for name, ranking in per.items():
                rankings[name].append(ranking)
        for name, ranked in rankings.items():
            system = f"{chunker}/{name}"
            scores = [file_metrics(r, set(q["gold_files"])) for r, q in zip(ranked, questions)]
            results[system] = {
                "chunks": len(chunks),
                "all": mean_metrics(scores),
                "names_file": mean_metrics([s for s, q in zip(scores, questions) if extract_file_name(q["question"])] or [scores[0]]),
                "no_file_named": mean_metrics([s for s, q in zip(scores, questions) if not extract_file_name(q["question"])] or [scores[0]]),
            }
            for q, r, s in zip(questions, ranked, scores):
                per_question_log.append({"system": system, "id": q["id"], "top5": r[:5], **s})

    run_dir = RESULTS_DIR / args.run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    env = {"args": vars(args), "git": git_state(), "hardware": hardware(),
           "corpus_files": len(files), "questions": len(questions)}
    (run_dir / "env.json").write_text(json.dumps(env, indent=2))
    (run_dir / "summary.json").write_text(json.dumps(results, indent=2))
    with open(run_dir / "per_question.jsonl", "w") as f:
        for row in per_question_log:
            f.write(json.dumps(row) + "\n")

    named = sum(bool(extract_file_name(q["question"])) for q in questions)
    lines = [f"# Retrieval results ({len(questions)} questions, {named} name a file; "
             f"{len(files)} corpus files)", "",
             "| Chunker/retriever | chunks | R@1 | R@3 | R@5 | MRR | MRR (no file named) |",
             "|---|---|---|---|---|---|---|"]
    for system, r in results.items():
        a = r["all"]
        lines.append(f"| {system} | {r['chunks']} | {a['recall@1']:.3f} | {a['recall@3']:.3f} | "
                     f"{a['recall@5']:.3f} | {a['mrr']:.3f} | {r['no_file_named']['mrr']:.3f} |")
    text = "\n".join(lines) + "\n"
    (run_dir / "summary.md").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
