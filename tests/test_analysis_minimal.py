import importlib

AN = importlib.import_module("mfda.analysis")


def _by_col_numeric(report: "AN.AnalysisReport", name: str) -> "AN.NumericSummary | None":
    for s in report.numeric:
        if s.column == name:
            return s
    return None


def _by_col_categorical(report: "AN.AnalysisReport", name: str) -> "AN.CategoricalSummary | None":
    for s in report.categorical:
        if s.column == name:
            return s
    return None


def test_numeric_summary_simple():
    records = [
        {"age": 10},
        {"age": None},
        {"age": 20},
        {"age": 30},
    ]
    rep = AN.analyze(records)

    s = _by_col_numeric(rep, "age")
    assert rep.rows == 4
    assert s is not None
    assert s.count == 3
    assert s.nulls == 1
    assert s.distinct == 3
    assert s.min == 10
    assert s.max == 30
    assert s.mean == 20.0


def test_categorical_topk_with_ties_and_nulls():
    records = [
        {"color": "red"},
        {"color": "blue"},
        {"color": "blue"},
        {"color": None},
        {"color": "green"},
        {"color": "red"},
    ]
    rep = AN.analyze(records, top_k=2)

    s = _by_col_categorical(rep, "color")
    assert s is not None
    assert s.count == 5  # exclude the one None
    assert s.nulls == 1
    assert s.distinct == 3
    # top-k sorted by freq DESC, then value ASC for ties
    assert s.top == [("blue", 2), ("red", 2)]


def test_mixed_types_numeric_and_categorical_split():
    records = [
        {"age": 10, "name": "Ana"},
        {"age": 20, "name": "Bob"},
        {"age": None, "name": "Chi"},
    ]
    rep = AN.analyze(records)

    assert _by_col_numeric(rep, "age") is not None
    assert _by_col_categorical(rep, "name") is not None
