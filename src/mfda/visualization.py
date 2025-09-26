"""
Save histogram of numeric non-null values; raises if empty

"""

import os
from collections import Counter

import matplotlib.pyplot as plt


# numeric
def save_histogram(
    records: list[dict[str, object]],
    *,
    column: str,
    out_path: str | os.PathLike[str],
    bins: int = 10,
) -> None:
    values = []
    for record in records:
        val = record.get(column)
        if val is None:
            continue
        if isinstance(val, (int, float)):  # noqa: UP038
            values.append(val)
        elif isinstance(val, str):
            try:
                values.append(float(val))  # coerce: convert string -> float
            except ValueError:
                continue
        # empty list
        if not values:
            raise ValueError(f"No numeric data in column {column}")

    # plot
    fig, ax = plt.subplots()
    ax.hist(values, bins=bins)
    # set labels
    ax.set_xlabel(column)
    ax.set_ylabel("Frequency")
    ax.set_title(f"Histogram of {column}")
    # save plot
    fig.savefig(out_path)
    plt.close(fig)


# categorical
def save_bar_counts(
    records: list[dict[str, object]],
    *,
    column: str,
    out_path: str | os.PathLike[str],
    top_k: int = 10,
) -> None:
    values = [rec.get(column) for rec in records if rec.get(column) is not None]

    if not values:
        raise ValueError(f"No categorical data in column {column}")

    freq = Counter(values)
    sorted_items = sorted(freq.items(), key=lambda kv: (-kv[1], str(kv[0])))
    top = sorted_items[:top_k]

    raw_labels, counts = zip(*top, strict=False)
    labels = [str(x) for x in raw_labels]

    # plot
    fig, ax = plt.subplots()
    ax.bar(labels, counts)
    ax.set_xlabel(column)
    ax.set_ylabel("Count")
    ax.set_title(f"Top {top_k} values of {column}")
    fig.savefig(out_path)
    plt.close(fig)
