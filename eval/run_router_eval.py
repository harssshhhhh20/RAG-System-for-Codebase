"""Router experiment: rules vs. LLM vs. hybrid intent classification.

Example (from the repo root):

    python -m eval.run_router_eval --models qwen3:4b \
        --styles zero_shot,definitions,few_shot --run-name pilot

Every LLM call is written to disk as it happens, so an interrupted run
resumes where it stopped. Re-running with --analyze-only recomputes all
metrics from the saved predictions without calling any model.

Hybrid systems are derived from the rule and LLM-only predictions: for
each request, hybrid = rule label if a rule fires, else the LLM label;
hybrid latency = rule time + (LLM time if the LLM was needed). This is
exactly what the CLI does, and avoids running the LLM twice.
"""
import argparse
import json
import os
import platform
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from eval import metrics  # noqa: E402
from shivi import ollama_client, router  # noqa: E402

DEFAULT_DATA = REPO_ROOT / "eval" / "data" / "router_dev.jsonl"
RESULTS_DIR = REPO_ROOT / "results" / "router"


def load_dataset(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def check_few_shot_leakage(rows):
    texts = {row["text"].lower().strip() for row in rows}
    leaked = [text for text, _ in router.FEW_SHOT_EXAMPLES if text.lower() in texts]
    if leaked:
        raise SystemExit(f"Few-shot examples overlap the evaluation data: {leaked}")


def stratified_subset(rows, per_label):
    taken, out = Counter(), []
    for row in rows:
        if taken[row["label"]] < per_label:
            taken[row["label"]] += 1
            out.append(row)
    return out


def condition_name(model, style, decoding):
    return f"{model.replace(':', '-').replace('/', '-')}__{style}__{decoding}"


def git_state():
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True
        ).strip()
        dirty = bool(subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=REPO_ROOT, text=True
        ).strip())
        return {"commit": commit, "dirty": dirty}
    except (OSError, subprocess.CalledProcessError):
        return {}


def hardware():
    info = {"platform": platform.platform(), "machine": platform.machine(),
            "python": sys.version.split()[0]}
    if sys.platform == "darwin":
        for key, name in (("cpu", "machdep.cpu.brand_string"), ("ram_bytes", "hw.memsize")):
            try:
                info[key] = subprocess.check_output(["sysctl", "-n", name], text=True).strip()
            except (OSError, subprocess.CalledProcessError):
                pass
    return info


def record_environment(run_dir, args, models):
    env = {
        "started": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "args": vars(args),
        "git": git_state(),
        "hardware": hardware(),
    }
    try:
        env["ollama_version"] = ollama_client.version()
        env["models"] = {}
        for model in models:
            details = ollama_client.show(model)
            env["models"][model] = {
                "details": details.get("details"),
                "modified_at": details.get("modified_at"),
            }
    except OSError as e:
        env["ollama_error"] = str(e)
    (run_dir / "env.json").write_text(json.dumps(env, indent=2))


def run_rules(rows, run_dir):
    for profile in router.RULE_PROFILES:
        with open(run_dir / f"rules_{profile}.jsonl", "w", encoding="utf-8") as f:
            for row in rows:
                start = time.perf_counter()
                label = router.rule_route(row["text"], profile=profile)
                latency = time.perf_counter() - start
                f.write(json.dumps({"id": row["id"], "pred": label, "latency_s": latency}) + "\n")


def load_predictions(path):
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return {item["id"]: item for item in map(json.loads, f)}


def run_llm(rows, run_dir, model, style, decoding, warmup=True):
    path = run_dir / "predictions" / f"{condition_name(model, style, decoding)}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    done = load_predictions(path)
    todo = [row for row in rows if row["id"] not in done]
    print(f"\n== {path.stem}: {len(done)} done, {len(todo)} to go")
    if not todo:
        return
    if warmup:
        # First call loads the model into memory; keep it out of the numbers.
        _, meta = router.llm_route("warm up", model, style=style,
                                   constrained=decoding == "constrained")
        print(f"   warm-up {meta['latency_s']:.1f}s")
    constrained = decoding == "constrained"
    with open(path, "a", encoding="utf-8") as f:
        for number, row in enumerate(todo, start=1):
            try:
                label, meta = router.llm_route(
                    row["text"], model, style=style, constrained=constrained,
                    think=False if constrained else None,
                    num_predict=None if constrained else 4096,
                )
            except OSError as e:
                print(f"   {row['id']}: request failed ({e}); rerun to resume")
                return
            item = {"id": row["id"], "pred": label, **meta}
            f.write(json.dumps(item) + "\n")
            f.flush()
            mark = "ok" if label == row["label"] else f"MISS ({label})"
            print(f"   [{number}/{len(todo)}] {meta['latency_s']:5.2f}s {row['label']:<10} {mark}")


def sklearn_baseline(rows, folds=5, seed=0):
    """TF-IDF + logistic regression, cross-validated (needs scikit-learn)."""
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import StratifiedKFold
        from sklearn.pipeline import make_pipeline, make_union
    except ImportError:
        return None
    texts = [row["text"] for row in rows]
    labels = [row["label"] for row in rows]
    preds = [None] * len(rows)
    latencies = [0.0] * len(rows)
    splitter = StratifiedKFold(n_splits=folds, shuffle=True, random_state=seed)
    for train, test in splitter.split(texts, labels):
        model = make_pipeline(
            make_union(
                TfidfVectorizer(analyzer="word", ngram_range=(1, 2)),
                TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5)),
            ),
            LogisticRegression(max_iter=2000, C=10),
        )
        model.fit([texts[i] for i in train], [labels[i] for i in train])
        for i in test:
            start = time.perf_counter()
            preds[i] = model.predict([texts[i]])[0]
            latencies[i] = time.perf_counter() - start
    return {row["id"]: {"pred": p, "latency_s": t} for row, p, t in zip(rows, preds, latencies)}


def evaluate(name, rows, preds, latencies, llm_calls=None):
    gold = [row["label"] for row in rows]
    labels = list(router.LABELS)
    result = {
        "system": name,
        "n": len(rows),
        "accuracy": metrics.accuracy(gold, preds),
        "accuracy_ci95": metrics.bootstrap_ci(gold, preds),
        "macro_f1": metrics.macro_f1(gold, preds, labels),
        "per_subset_accuracy": {
            subset: metrics.accuracy(
                [g for g, r in zip(gold, rows) if r["subset"] == subset],
                [p for p, r in zip(preds, rows) if r["subset"] == subset],
            )
            for subset in sorted({row["subset"] for row in rows})
        },
        "per_label": metrics.per_label_f1(gold, preds, labels),
        "latency": metrics.latency_summary(latencies),
        "confusion": metrics.confusion(gold, preds),
    }
    if llm_calls is not None:
        result["llm_call_rate"] = sum(llm_calls) / len(llm_calls)
    return result


def analyze(rows, run_dir, include_sklearn=True):
    by_id = {row["id"]: row for row in rows}
    gold = [row["label"] for row in rows]
    systems = {}
    preds_for = {}

    rules = {
        profile: load_predictions(run_dir / f"rules_{profile}.jsonl")
        for profile in router.RULE_PROFILES
    }
    for profile, table in rules.items():
        name = f"rules[{profile}]"
        preds = [table[row["id"]]["pred"] for row in rows]
        lat = [table[row["id"]]["latency_s"] for row in rows]
        fired = [p is not None for p in preds]
        systems[name] = evaluate(name, rows, preds, lat, [0] * len(rows))
        systems[name]["coverage"] = sum(fired) / len(rows)
        systems[name]["precision_when_fired"] = (
            sum(p == g for p, g, f in zip(preds, gold, fired) if f) / max(1, sum(fired))
        )
        preds_for[name] = preds

    def add_hybrids(base_name, subset, base_preds, base_lat):
        for profile, table in rules.items():
            hybrid_preds, hybrid_lat, calls = [], [], []
            for row, bp, bl in zip(subset, base_preds, base_lat):
                rule = table[row["id"]]
                if rule["pred"] is not None:
                    hybrid_preds.append(rule["pred"])
                    hybrid_lat.append(rule["latency_s"])
                    calls.append(0)
                else:
                    hybrid_preds.append(bp)
                    hybrid_lat.append(rule["latency_s"] + bl)
                    calls.append(1)
            name = f"hybrid[{profile}+{base_name}]"
            systems[name] = evaluate(name, subset, hybrid_preds, hybrid_lat, calls)
            if len(subset) == len(rows):
                preds_for[name] = (base_name, hybrid_preds)

    for path in sorted((run_dir / "predictions").glob("*.jsonl")):
        llm = load_predictions(path)
        subset = [row for row in rows if row["id"] in llm]
        if not subset:
            continue
        name = path.stem
        preds = [llm[row["id"]]["pred"] for row in subset]
        lat = [llm[row["id"]]["latency_s"] for row in subset]
        systems[name] = evaluate(name, subset, preds, lat, [1] * len(subset))
        systems[name]["parse_failures"] = sum(p is None for p in preds)
        output_tokens = [llm[row["id"]].get("output_tokens") or 0 for row in subset]
        systems[name]["mean_output_tokens"] = sum(output_tokens) / len(output_tokens)
        if len(subset) == len(rows):
            preds_for[name] = preds
        add_hybrids(name, subset, preds, lat)

    if include_sklearn:
        clf = sklearn_baseline(rows)
        if clf:
            name = "tfidf_logreg_cv5"
            preds = [clf[row["id"]]["pred"] for row in rows]
            lat = [clf[row["id"]]["latency_s"] for row in rows]
            systems[name] = evaluate(name, rows, preds, lat, [0] * len(rows))
            preds_for[name] = preds
            add_hybrids(name, rows, preds, lat)

    # Paired significance: each hybrid vs. its fallback used alone.
    tests = {}
    for name, value in preds_for.items():
        if isinstance(value, tuple):
            base, hybrid_preds = value
            b, c, p = metrics.mcnemar_exact(gold, hybrid_preds, preds_for[base])
            tests[f"{name} vs {base}"] = {"hybrid_only_right": b, "base_only_right": c, "p_value": p}

    summary = {"n": len(rows), "systems": systems, "mcnemar": tests}
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    (run_dir / "summary.md").write_text(render_markdown(summary))
    print("\n" + render_markdown(summary))
    return summary


def render_markdown(summary):
    lines = [
        f"# Router results (n = {summary['n']})",
        "",
        "| System | n | Acc | 95% CI | Macro-F1 | canonical | paraphrase | hard | LLM calls | p50 s | p95 s |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for name, s in summary["systems"].items():
        sub = s["per_subset_accuracy"]
        ci = s["accuracy_ci95"]
        lines.append(
            f"| {name} | {s['n']} | {s['accuracy']:.3f} | {ci[0]:.3f}-{ci[1]:.3f} | {s['macro_f1']:.3f} | "
            f"{sub.get('canonical', float('nan')):.3f} | {sub.get('paraphrase', float('nan')):.3f} | "
            f"{sub.get('hard', float('nan')):.3f} | {s.get('llm_call_rate', 0):.2f} | "
            f"{s['latency']['p50_s']:.4f} | {s['latency']['p95_s']:.4f} |"
        )
    for name, s in summary["systems"].items():
        if "coverage" in s:
            lines += ["", f"{name}: coverage {s['coverage']:.3f}, precision when a rule fires "
                          f"{s['precision_when_fired']:.3f}"]
    if summary["mcnemar"]:
        lines += ["", "## Paired McNemar tests", "",
                  "| Comparison | hybrid-only correct | base-only correct | p |", "|---|---|---|---|"]
        for name, t in summary["mcnemar"].items():
            lines.append(f"| {name} | {t['hybrid_only_right']} | {t['base_only_right']} | {t['p_value']:.4g} |")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", default=str(DEFAULT_DATA))
    parser.add_argument("--models", default="qwen3:4b", help="comma-separated Ollama models")
    parser.add_argument("--styles", default="zero_shot,definitions,few_shot")
    parser.add_argument("--decoding", default="constrained",
                        help="comma-separated: constrained (JSON schema) and/or free (model default, incl. thinking)")
    parser.add_argument("--per-label", type=int, default=None,
                        help="evaluate only the first N items per label (for slow conditions)")
    parser.add_argument("--run-name", default=time.strftime("%Y%m%d-%H%M%S"))
    parser.add_argument("--analyze-only", action="store_true")
    parser.add_argument("--no-sklearn", action="store_true")
    args = parser.parse_args()

    rows = load_dataset(args.data)
    check_few_shot_leakage(rows)
    run_dir = RESULTS_DIR / args.run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    models = [m for m in args.models.split(",") if m]

    if not args.analyze_only:
        if not (run_dir / "env.json").exists():
            record_environment(run_dir, args, models)
        run_rules(rows, run_dir)
        llm_rows = stratified_subset(rows, args.per_label) if args.per_label else rows
        for model in models:
            for decoding in args.decoding.split(","):
                for style in args.styles.split(","):
                    run_llm(llm_rows, run_dir, model, style, decoding)

    analyze(rows, run_dir, include_sklearn=not args.no_sklearn)


if __name__ == "__main__":
    main()
