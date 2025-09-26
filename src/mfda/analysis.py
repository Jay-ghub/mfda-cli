"""
Analysis layer

Computes small, deterministic summaries:
- Numeric columns: count, nulls, distinct, min, max, mean
- Categorical columns: count, nulls, distinct, top-k (by frequency desc, then value asc)

Notes:
- Null policy: treat missing/None as nulls and exclude them from numeric stats.
- Distinct excludes nulls.
- Top-k ties broken by value (ascending).
"""

from collections import Counter
from dataclasses import dataclass
from typing import Any


@dataclass
class NumericSummary:
    column: str
    count: int  # non-null count
    nulls: int
    distinct: int  # excluding nulls
    min: float | int
    max: float | int
    mean: float


@dataclass
class CategoricalSummary:
    column: str
    count: int  # non-null count
    nulls: int
    distinct: int  # excluding nulls
    top: list[tuple[str, int]]  # sorted by freq desc, then value asc


@dataclass
class AnalysisReport:
    rows: int
    columns: int
    numeric: list[NumericSummary]
    categorical: list[CategoricalSummary]


def analyze(
    records: list[dict[str, Any]],
    *,
    top_k: int = 3,
) -> AnalysisReport:
    rows = len(records)
    columns = len({k for r in records for k in r})

    numeric_stats = []
    categorical_stats = []

    all_columns = {k for r in records for k in r}
    for col in all_columns:
        values = [r.get(col) for r in records]
        non_null = [v for v in values if v is not None]

        if all(isinstance(v, (int, float)) for v in non_null):  # noqa: UP038
            # numeric branch
            count = len(non_null)
            nulls = rows - count
            distinct = len(set(non_null))
            if count > 0:
                min_val = min(non_null)
                max_val = max(non_null)
                mean = sum(non_null) / count
            else:
                min_val = max_val = mean = None
            numeric_stats.append(
                NumericSummary(col, count, nulls, distinct, min_val, max_val, mean)
            )

        else:
            # categorical branch
            count = len(non_null)
            nulls = rows - count
            distinct = len(set(non_null))
            freq = Counter(non_null)
            sorted_items = sorted(freq.items(), key=lambda kv: (-kv[1], str(kv[0])))
            top = sorted_items[:top_k]
            categorical_stats.append(CategoricalSummary(col, count, nulls, distinct, top))

    return AnalysisReport(
        rows=rows, columns=columns, numeric=numeric_stats, categorical=categorical_stats
    )
