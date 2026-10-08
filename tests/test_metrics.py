import math

from eval import metrics


def test_accuracy_and_f1():
    gold = ["a", "a", "b", "b"]
    pred = ["a", "b", "b", "b"]
    assert metrics.accuracy(gold, pred) == 0.75
    scores = metrics.per_label_f1(gold, pred, ["a", "b"])
    assert scores["a"]["precision"] == 1.0 and scores["a"]["recall"] == 0.5
    assert math.isclose(metrics.macro_f1(gold, pred, ["a", "b"]), (2 / 3 + 0.8) / 2)


def test_none_predictions_count_as_wrong():
    assert metrics.accuracy(["a"], [None]) == 0.0
    assert metrics.confusion(["a"], [None]) == {"a": {"none": 1}}


def test_mcnemar():
    gold = ["a"] * 10
    a = ["a"] * 10
    b = ["a"] * 2 + ["x"] * 8
    hits_a, hits_b, p = metrics.mcnemar_exact(gold, a, b)
    assert (hits_a, hits_b) == (8, 0)
    assert math.isclose(p, 2 / 2 ** 8)
    assert metrics.mcnemar_exact(gold, a, a)[2] == 1.0


def test_percentile():
    assert metrics.percentile([1, 2, 3, 4], 50) == 2.5
    assert metrics.percentile([5], 95) == 5


def test_bootstrap_is_deterministic():
    gold = ["a", "b"] * 20
    pred = ["a", "a"] * 20
    low, high = metrics.bootstrap_ci(gold, pred, samples=200)
    assert low <= 0.5 <= high
    assert metrics.bootstrap_ci(gold, pred, samples=200) == (low, high)
