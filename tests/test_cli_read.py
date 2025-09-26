import importlib
import re
from pathlib import Path

CLI = importlib.import_module("mfda.cli")
DISP = importlib.import_module("mfda.dispatch")


def _call(argv):
    # Call your main() with argv and capture printed output
    import sys
    from io import StringIO

    buf = StringIO()
    old_out = sys.stdout
    try:
        sys.stdout = buf
        code = CLI.main(argv)
    finally:
        sys.stdout = old_out
    return code, buf.getvalue()


def test_read_csv_preview_columns_shape(tmp_path):
    # Reuse your existing CSV fixture
    csv_path = Path("tests/fixtures/tiny_customers.csv")
    code, out = _call(["read", str(csv_path), "--limit", "2"])

    assert code == 0
    assert "columns:" in out
    assert "shape:" in out
    # be tolerant to spacing
    assert re.search(r"columns:\s*\[.*id.*name.*age.*\]", out)
    assert re.search(r"shape:\s*\(2,\s*3\)", out)
    # records preview should include at least 1 row
    assert "records:" in out


def test_read_format_override_on_unknown_extension(tmp_path):
    # Copy CSV to a .data file to force override need
    src = Path("tests/fixtures/tiny_customers.csv")
    dst = tmp_path / "mystery.data"
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    code, out = _call(["read", str(dst), "--format", "csv", "--limit", "1"])
    assert code == 0
    assert "columns:" in out
    assert re.search(r"shape:\s*\(1,\s*3\)", out)


def test_read_jsonl_lines_flag(tmp_path):
    # Use JSONL content but with .json extension: lines flag must force JSONL mode
    src = Path("tests/fixtures/tiny_events.jsonl")
    dst = tmp_path / "events.json"
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    code, out = _call(["read", str(dst), "--lines", "--limit", "2"])
    assert code == 0
    assert "columns:" in out
    assert re.search(r"shape:\s*\(2,\s*2\)", out)


def test_read_errors_on_unknown_format(tmp_path, monkeypatch):
    p = tmp_path / "file.unknown"
    p.write_text("dummy", encoding="utf-8")

    # Ensure detect_format returns None (just in case)
    assert DISP.detect_format(p) is None

    code, out = _call(["read", str(p)])
    assert code != 0
    assert re.search(r"(?i)unknown|unsupported|format", out)
