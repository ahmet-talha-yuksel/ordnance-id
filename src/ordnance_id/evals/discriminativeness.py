"""Distribution-free descriptive measures for observation features."""

import math
from collections import Counter
from collections.abc import Hashable, Sequence


def mutual_information(values: Sequence[Hashable], labels: Sequence[Hashable]) -> float:
    """Compute empirical mutual information in nats."""

    if len(values) != len(labels):
        raise ValueError("values and labels must have equal length")
    if not values:
        return 0.0
    joint = Counter(zip(values, labels, strict=True))
    value_counts, label_counts = Counter(values), Counter(labels)
    total = len(values)
    return sum(
        count / total
        * math.log((count * total) / (value_counts[value] * label_counts[label]))
        for (value, label), count in joint.items()
    )


def total_variation(left: Counter[Hashable], right: Counter[Hashable]) -> float:
    """Compute total variation distance between empirical categorical distributions."""

    if not left.total() or not right.total():
        return 0.0
    return 0.5 * sum(
        abs(left[value] / left.total() - right[value] / right.total())
        for value in set(left) | set(right)
    )


def interval_overlap(left: tuple[float, float], right: tuple[float, float]) -> float:
    """Measure IQR intersection over union on [0, 1]."""

    intersection = max(0.0, min(left[1], right[1]) - max(left[0], right[0]))
    union = max(left[1], right[1]) - min(left[0], right[0])
    if union == 0:
        return 1.0 if left == right else 0.0
    return intersection / union
