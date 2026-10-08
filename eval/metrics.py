"""Classification and latency metrics (stdlib only, so results are easy to audit)."""
import math
import random
from collections import Counter, defaultdict


def accuracy(gold, pred):
    return sum(g == p for g, p in zip(gold, pred)) / len(gold) if gold else 0.0


def per_label_f1(gold, pred, labels):
    scores = {}
    for label in labels:
        tp = sum(g == label and p == label for g, p in zip(gold, pred))
        fp = sum(g != label and p == label for g, p in zip(gold, pred))
        fn = sum(g == label and p != label for g, p in zip(gold, pred))
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        scores[label] = {"precision": precision, "recall": recall, "f1": f1, "support": tp + fn}
    return scores


def macro_f1(gold, pred, labels):
    present = [label for label in labels if label in set(gold)]
    scores = per_label_f1(gold, pred, present)
    return sum(s["f1"] for s in scores.values()) / len(present) if present else 0.0


def confusion(gold, pred):
    """Nested dict gold -> pred -> count. Abstentions appear as 'none'."""
    table = defaultdict(Counter)
    for g, p in zip(gold, pred):
        table[g][p or "none"] += 1
    return {g: dict(c) for g, c in table.items()}


def bootstrap_ci(gold, pred, metric=accuracy, samples=2000, seed=0, alpha=0.05):
    """Percentile bootstrap confidence interval over examples."""
    rng = random.Random(seed)
    n = len(gold)
    values = []
    for _ in range(samples):
        idx = [rng.randrange(n) for _ in range(n)]
        values.append(metric([gold[i] for i in idx], [pred[i] for i in idx]))
    values.sort()
    low = values[int((alpha / 2) * samples)]
    high = values[int((1 - alpha / 2) * samples) - 1]
    return low, high


def mcnemar_exact(gold, pred_a, pred_b):
    """Exact two-sided McNemar test on paired predictions.

    Returns (b, c, p) where b = A right & B wrong, c = A wrong & B right.
    """
    b = sum(pa == g and pb != g for g, pa, pb in zip(gold, pred_a, pred_b))
    c = sum(pa != g and pb == g for g, pa, pb in zip(gold, pred_a, pred_b))
    n = b + c
    if n == 0:
        return b, c, 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return b, c, min(1.0, 2 * tail)


def percentile(values, q):
    """Linear-interpolated percentile, q in [0, 100]."""
    if not values:
        return float("nan")
    ordered = sorted(values)
    position = (len(ordered) - 1) * q / 100
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def latency_summary(values):
    return {
        "mean_s": sum(values) / len(values) if values else float("nan"),
        "p50_s": percentile(values, 50),
        "p95_s": percentile(values, 95),
        "max_s": max(values) if values else float("nan"),
    }
