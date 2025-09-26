import importlib
from pathlib import Path

JSONR = importlib.import_module("mfda.readers.json_reader")


def test_json_records_array_columns_and_shape():
    table = JSONR.read(Path("tests/fixtures/tiny_users.json"))
    assert hasattr(table, "columns")
    assert hasattr(table, "shape")
    assert callable(table.as_records)
    assert table.columns == ["id", "name"]
    assert table.shape == (3, 2)


def test_jsonl_mode_by_extension():
    table = JSONR.read(Path("tests/fixtures/tiny_events.jsonl"))
    assert table.columns == ["event", "ts"]
    assert table.shape == (3, 2)


def test_jsonl_mode_forced_with_flag_on_json():
    # Even though the file is .json, lines=True should force JSONL mode
    p = Path("tests/fixtures/tiny_events.jsonl")
    tmp = p.with_suffix(".json")  # copy to .json so extension wouldn't trigger JSONL
    tmp.write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
    try:
        table = JSONR.read(tmp, lines=True)
        assert table.columns == ["event", "ts"]
        assert table.shape == (3, 2)
    finally:
        if tmp.exists():
            tmp.unlink()


def test_missing_keys_become_NULL():
    table = JSONR.read(Path("tests/fixtures/tiny_users_missing.json"))
    records = table.as_records()
    # Middle record had no "name" -> NULL
    assert records[1]["name"] is JSONR.NULL


def test_limit_applies_to_rows_only():
    t = JSONR.read(Path("tests/fixtures/tiny_users.json"), limit=2)
    assert t.shape == (2, 2)
