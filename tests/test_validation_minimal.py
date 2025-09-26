import importlib

VAL = importlib.import_module("mfda.validation")


def _count_issues(rep: "VAL.ValidationReport", code: str, column: str | None = None) -> int:
    return sum(1 for i in rep.issues if i.code == code and (column is None or i.column == column))


def test_required_missing_detected():
    records = [
        {"id": 1, "name": "Ana"},
        {"id": 2},  # name missing
        {"id": 3, "name": "Chi"},
    ]
    schema = {"name": {"required": True}}
    rep = VAL.validate(records, schema)

    assert rep.row_count == 3
    assert rep.column_count >= 2
    assert _count_issues(rep, "missing_required", "name") == 1


def test_unique_duplicate_detected():
    records = [
        {"id": 1, "name": "Ana"},
        {"id": 1, "name": "Bob"},  # duplicate id
        {"id": 2, "name": "Chi"},
    ]
    schema = {"id": {"unique": True}}
    rep = VAL.validate(records, schema)

    assert _count_issues(rep, "duplicate", "id") == 1


def test_numeric_range_detected():
    records = [
        {"age": 10},
        {"age": 999},  # too high
        {"age": 20},
        {"age": -5},  # too low
    ]
    schema = {"age": {"min": 0, "max": 120}}
    rep = VAL.validate(records, schema)

    assert _count_issues(rep, "out_of_range", "age") == 2


def test_integration_with_csv_reader(tmp_path):
    import importlib

    CSV = importlib.import_module("mfda.readers.csv_reader")

    p = tmp_path / "tiny.csv"
    p.write_text("id,name\n1,Ana\n2,\n3,Chi\n", encoding="utf-8")
    table = CSV.read(p)
    records = table.as_records()

    schema = {"name": {"required": True}, "id": {"unique": True}}
    rep = VAL.validate(records, schema)

    # row 2 has missing name, no duplicate ids here
    assert _count_issues(rep, "missing_required", "name") == 1
    assert _count_issues(rep, "duplicate", "id") == 0
