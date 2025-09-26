import importlib
from pathlib import Path

CSV = importlib.import_module("mfda.readers.csv_reader")


def test_csv_read_basic_columns_and_shape():
    table = CSV.read(Path("tests/fixtures/tiny_customers.csv"))
    assert hasattr(table, "columns")
    assert hasattr(table, "shape")
    assert callable(table.as_records)
    assert table.columns == ["id", "name", "age"]
    assert table.shape == (3, 3)


def test_tsv_default_delimiter_is_tab():
    table = CSV.read(Path("tests/fixtures/tiny_customers.tsv"))
    assert table.columns == ["id", "name", "age"]
    assert table.shape == (3, 3)


def test_delimiter_override_semicolon():
    table = CSV.read(
        Path("tests/fixtures/tiny_decimals.csv"),
        delimiter=";",  # override
    )
    assert table.columns == ["id", "price", "qty"]
    assert table.shape == (2, 3)


def test_missing_values_normalized_to_NULL(tmp_path):
    # Create a tiny CSV with an empty field -> should become NULL
    p = tmp_path / "na.csv"
    p.write_text("a,b\n1,\n", encoding="utf-8")
    table = CSV.read(p)
    records = table.as_records()
    assert len(records) == 1
    # second column should be the module's NULL sentinel
    assert records[0]["b"] is CSV.NULL
