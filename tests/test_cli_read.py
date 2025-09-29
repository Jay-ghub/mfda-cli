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


def _call_both(argv):
    import sys
    from io import StringIO

    out, err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = out, err
        code = CLI.main(argv)
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    return code, out.getvalue(), err.getvalue()


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


def test_read_errors_on_unknown_format(monkeypatch, tmp_path):
    p = tmp_path / "file.unknown"
    p.write_text("dummy", encoding="utf-8")

    # Ensure detect_format returns None (just in case)
    assert DISP.detect_format(p) is None

    code, out = _call(["read", str(p)])
    assert code != 0
    assert re.search(r"(?i)unknown|unsupported|format", out)


def test_read_no_reader_available(monkeypatch, tmp_path):
    p = tmp_path / "file.csv"
    p.write_text("id,name\n1,a\n", encoding="utf-8")

    # Force detect_format -> "csv"
    monkeypatch.setattr(CLI, "detect_format", lambda _: "csv")
    # Force choose_reader -> None
    monkeypatch.setattr(CLI, "choose_reader", lambda _fmt: None)

    # Capture stdout and stderr
    import sys
    from io import StringIO

    out, err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = out, err
        code = CLI.main(["read", str(p)])
    finally:
        sys.stdout, sys.stderr = old_out, old_err

    assert code == 2
    assert "No reader available for format" in err.getvalue()


def test_read_sets_lines_kwarg_for_json(monkeypatch, tmp_path):
    p = tmp_path / "events.json"
    p.write_text('{"a": 1}\n{"a": 2}\n', encoding="utf-8")  # content doesn't matter here

    seen = {}

    def fake_read(path, **kw):
        seen.update(kw)

        class T:
            columns = ["a"]
            shape = (2, 1)

            def as_records(self):
                return [{"a": 1}, {"a": 2}]

        return T()

    monkeypatch.setattr(CLI, "detect_format", lambda _: "json")
    monkeypatch.setattr(
        CLI, "choose_reader", lambda _fmt: type("R", (), {"read": staticmethod(fake_read)})
    )

    code, out = _call(["read", str(p), "--lines", "--limit", "2"])
    assert code == 0
    assert seen.get("lines") is True
    assert "columns:" in out and "shape:" in out


def test_read_sets_lines_kwarg_for_jsonl(monkeypatch, tmp_path):
    p = tmp_path / "events.jsonl"
    p.write_text('{"a": 1}\n{"a": 2}\n', encoding="utf-8")  # content doesn't matter here

    seen = {}

    def fake_read(path, **kw):
        seen.update(kw)

        class T:
            columns = ["a"]
            shape = (2, 1)

            def as_records(self):
                return [{"a": 1}, {"a": 2}]

        return T()

    monkeypatch.setattr(CLI, "detect_format", lambda _: "jsonl")
    monkeypatch.setattr(
        CLI, "choose_reader", lambda _fmt: type("R", (), {"read": staticmethod(fake_read)})
    )

    code, out = _call(["read", str(p), "--lines", "--limit", "2"])
    assert code == 0
    assert seen.get("lines") is True
    assert "columns:" in out and "shape:" in out


def test_read_xlsx_sheet_number(monkeypatch, tmp_path):
    p = tmp_path / "wb.xlsx"
    p.write_bytes(b"fake")
    seen = {}

    def fake_read(path, **kw):
        seen.update(kw)

        class T:
            columns = ["A"]
            shape = (1, 1)

            def as_records(self):
                return [{"A": 1}]

        return T()

    monkeypatch.setattr(CLI, "detect_format", lambda _: "xlsx")
    monkeypatch.setattr(
        CLI, "choose_reader", lambda _fmt: type("R", (), {"read": staticmethod(fake_read)})
    )

    code, out = _call(["read", str(p), "--sheet", "2"])
    assert code == 0
    assert seen.get("sheet") == 2
    assert "columns:" in out and "shape:" in out


def test_read_xlsx_sheet_name(monkeypatch, tmp_path):
    p = tmp_path / "wb.xlsx"
    p.write_bytes(b"fake")
    seen = {}

    def fake_read(path, **kw):
        seen.update(kw)

        class T:
            columns = ["A"]
            shape = (1, 1)

            def as_records(self):
                return [{"A": 1}]

        return T()

    monkeypatch.setattr(CLI, "detect_format", lambda _: "xlsx")
    monkeypatch.setattr(
        CLI, "choose_reader", lambda _fmt: type("R", (), {"read": staticmethod(fake_read)})
    )

    code, out = _call(["read", str(p), "--sheet", "Data"])
    assert code == 0
    assert seen.get("sheet") == "Data"


def test_read_preview_truncates_to_available_records(monkeypatch, tmp_path):
    p = tmp_path / "x.csv"
    p.write_text("id\n", encoding="utf-8")

    def fake_read(path, **kw):
        class T:
            columns = ["id"]
            shape = (1, 1)

            def as_records(self):
                return [{"id": 1}]

        return T()

    monkeypatch.setattr(CLI, "detect_format", lambda _: "csv")
    monkeypatch.setattr(
        CLI, "choose_reader", lambda _fmt: type("R", (), {"read": staticmethod(fake_read)})
    )

    code, out = _call(["read", str(p), "--limit", "5"])
    assert code == 0
    # only one record printed despite limit 5
    assert out.count("{") == 1
