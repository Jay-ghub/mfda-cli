import importlib
import re
from pathlib import Path

CLI = importlib.import_module("mfda.cli")
DISP = importlib.import_module("mfda.dispatch")


def _call(argv):
    import sys
    from io import StringIO

    buf = StringIO()
    old = sys.stdout
    try:
        sys.stdout = buf
        code = CLI.main(argv)
    finally:
        sys.stdout = old
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


def test_analyze_json_records(tmp_path):
    # numeric + categorical in one file
    p = tmp_path / "users.json"
    p.write_text(
        '[{"id":1,"name":"Ana"},{"id":2,"name":"Bob"},{"id":3,"name":"Chi"}]',
        encoding="utf-8",
    )

    code, out = _call(["analyze", str(p), "--top-k", "2"])
    assert code == 0

    # basic headers
    assert "rows:" in out
    assert "columns:" in out
    assert "numeric:" in out
    assert "categorical:" in out

    # column names show up
    assert "id" in out
    assert "name" in out

    # some stat labels present (don’t over-constrain formatting)
    assert re.search(r"mean", out)


def test_analyze_jsonl_with_lines_flag(tmp_path):
    src = Path("tests/fixtures/tiny_events.jsonl")
    dst = tmp_path / "events.json"  # extension shouldn’t force jsonl; flag should
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    code, out = _call(["analyze", str(dst), "--lines", "--top-k", "2"])
    assert code == 0
    assert "categorical:" in out
    assert "event" in out


def test_analyze_unknown_format_error(tmp_path):
    p = tmp_path / "mystery.data"
    p.write_text("???", encoding="utf-8")

    # sanity: dispatcher can’t detect it
    assert DISP.detect_format(p) is None

    code, out = _call(["analyze", str(p)])
    assert code != 0
    # user-facing message should mention unsupported/unknown format
    assert re.search(r"(?i)unknown|unsupported|format", out)


def test_analyze_no_reader_available(monkeypatch, tmp_path):
    p = tmp_path / "file.csv"
    p.write_text("id,name\n1,A\n", encoding="utf-8")

    # Force the code path
    monkeypatch.setattr(CLI, "detect_format", lambda _: "csv")
    monkeypatch.setattr(CLI, "choose_reader", lambda _fmt: None)

    code, out, err = _call_both(["analyze", str(p)])
    assert code == 2
    assert "No reader available for format" in err


def test_analyze_xlsx_sheet_number(monkeypatch, tmp_path):
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

    # steer format & reader
    monkeypatch.setattr(CLI, "detect_format", lambda _: "xlsx")
    monkeypatch.setattr(
        CLI, "choose_reader", lambda _fmt: type("R", (), {"read": staticmethod(fake_read)})
    )

    # keep analysis simple
    class Rep:
        rows = 1
        columns = 1
        numeric = []
        categorical = []

    monkeypatch.setattr(CLI.analysis, "analyze", lambda recs, top_k: Rep)

    code, out = _call(["analyze", str(p), "--sheet", "2"])
    assert code == 0 and seen.get("sheet") == 2
    assert "rows:" in out and "columns:" in out


def test_analyze_xlsx_sheet_name(monkeypatch, tmp_path):
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

    class Rep:
        rows = 1
        columns = 1
        numeric = []
        categorical = []

    monkeypatch.setattr(CLI.analysis, "analyze", lambda recs, top_k: Rep)

    code, out = _call(["analyze", str(p), "--sheet", "Data"])
    assert code == 0 and seen.get("sheet") == "Data"


def test_analyze_prints_numeric_and_categorical(monkeypatch, tmp_path):
    from importlib import import_module

    CLI = import_module("mfda.cli")

    p = tmp_path / "file.csv"
    p.write_text("id\n1\n", encoding="utf-8")

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

    class Num:
        column = "id"
        count = 1
        nulls = 0
        distinct = 1
        min = 1
        max = 1
        mean = 1.0

    class Cat:
        column = "name"
        count = 1
        nulls = 0
        distinct = 1
        top = [("A", 1)]

    class Rep:
        rows = 1
        columns = 2
        numeric = [Num()]
        categorical = [Cat()]

    monkeypatch.setattr(CLI.analysis, "analyze", lambda recs, top_k: Rep)

    code, out = _call(["analyze", str(p)])
    assert code == 0
    assert "numeric:" in out and "categorical:" in out
    assert "count=" in out and "distinct=" in out  # loop bodies executed
