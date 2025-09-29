import importlib
import os
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


def test_viz_histogram_csv(tmp_path):
    out_file = tmp_path / "age_hist.png"
    code, out = _call(
        [
            "viz",
            "tests/fixtures/tiny_customers.csv",
            "--hist",
            "age",
            "--out",
            str(out_file),
        ]
    )
    assert code == 0
    assert out_file.exists()
    assert os.stat(out_file).st_size > 0
    assert re.search(r"(?i)wrote", out)


def test_viz_bar_jsonl_with_lines_flag(tmp_path):
    # Use JSONL content but with .json extension; --lines should force JSONL mode
    src = Path("tests/fixtures/tiny_events.jsonl")
    dst = tmp_path / "events.json"
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    out_file = tmp_path / "event_bar.png"
    code, out = _call(
        [
            "viz",
            str(dst),
            "--lines",
            "--bar",
            "event",
            "--out",
            str(out_file),
            "--top-k",
            "5",
        ]
    )
    assert code == 0
    assert out_file.exists()
    assert os.stat(out_file).st_size > 0
    assert re.search(r"(?i)wrote", out)


def test_viz_invalid_args_both_hist_and_bar(tmp_path):
    out_file = tmp_path / "bad.png"
    code, out = _call(
        [
            "viz",
            "tests/fixtures/tiny_customers.csv",
            "--hist",
            "age",
            "--bar",
            "name",
            "--out",
            str(out_file),
        ]
    )
    assert code != 0
    assert re.search(r"(?i)choose|mutually|either", out)


def test_viz_unknown_format(tmp_path):
    p = tmp_path / "mystery.data"
    p.write_text("???", encoding="utf-8")

    # sanity: dispatcher can't detect it
    assert DISP.detect_format(p) is None

    out_file = tmp_path / "noop.png"
    code, out = _call(
        [
            "viz",
            str(p),
            "--hist",
            "x",
            "--out",
            str(out_file),
        ]
    )
    assert code != 0
    assert re.search(r"(?i)unknown|unsupported|format", out)


def test_viz_requires_option_neither_hist_nor_bar(tmp_path):
    # hits lines 202–203
    out_file = tmp_path / "noop.png"
    code, out = _call(["viz", "tests/fixtures/tiny_customers.csv", "--out", str(out_file)])
    assert code == 2
    assert re.search(r"(?i)must\s+provide\s+--hist\s+or\s+--bar", out)


def test_viz_no_reader_available(monkeypatch, tmp_path):
    # hits lines 223–226
    p = tmp_path / "file.csv"
    p.write_text("id,name\n1,A\n", encoding="utf-8")

    # Force a valid format but no reader
    monkeypatch.setattr(CLI, "detect_format", lambda _: "csv")
    monkeypatch.setattr(CLI, "choose_reader", lambda _fmt: None)

    out_file = tmp_path / "out.png"
    code, out = _call(["viz", str(p), "--hist", "id", "--out", str(out_file)])
    assert code == 2
    assert re.search(r"(?i)no reader available.*csv", out)


def test_viz_known_errors_from_reader(monkeypatch, tmp_path):
    # hits line 252 (FileFormatError/ConfigurationError handler)
    from mfda.errors import FileFormatError

    p = tmp_path / "file.csv"
    p.write_text("id,name\n1,A\n", encoding="utf-8")

    class BoomReader:
        @staticmethod
        def read(path, **kwargs):
            raise FileFormatError("bad format")

    monkeypatch.setattr(CLI, "detect_format", lambda _: "csv")
    monkeypatch.setattr(CLI, "choose_reader", lambda _fmt: BoomReader)

    out_file = tmp_path / "out.png"
    code, out, err = _call_both(["viz", str(p), "--hist", "id", "--out", str(out_file)])
    assert code == 2
    assert "Error:" in err
    assert "bad format" in err


# Optional: exercise XLSX --sheet kwarg conversion (number vs name)
def test_viz_xlsx_sheet_number(monkeypatch, tmp_path):
    seen = {}

    class R:
        @staticmethod
        def read(path, **kw):
            seen.update(kw)

            class T:
                columns = ["A"]
                shape = (1, 1)

                def as_records(self):
                    return [{"A": 1}]

            return T()

    monkeypatch.setattr(CLI, "detect_format", lambda _: "xlsx")
    monkeypatch.setattr(CLI, "choose_reader", lambda _fmt: R)
    # stub out actual image creation
    monkeypatch.setattr(CLI, "save_histogram", lambda recs, column, out_path: None)

    out_file = tmp_path / "h.png"
    code, out = _call(["viz", "wb.xlsx", "--sheet", "2", "--hist", "A", "--out", str(out_file)])
    assert code == 0 and seen.get("sheet") == 2
    assert re.search(r"(?i)wrote histogram", out)


def test_viz_xlsx_sheet_name(monkeypatch, tmp_path):
    seen = {}

    class R:
        @staticmethod
        def read(path, **kw):
            seen.update(kw)

            class T:
                columns = ["A"]
                shape = (1, 1)

                def as_records(self):
                    return [{"A": 1}]

            return T()

    monkeypatch.setattr(CLI, "detect_format", lambda _: "xlsx")
    monkeypatch.setattr(CLI, "choose_reader", lambda _fmt: R)
    monkeypatch.setattr(CLI, "save_bar_counts", lambda recs, column, out_path, top_k: None)

    out_file = tmp_path / "b.png"
    code, out = _call(["viz", "wb.xlsx", "--sheet", "Data", "--bar", "A", "--out", str(out_file)])
    assert code == 0 and seen.get("sheet") == "Data"
    assert re.search(r"(?i)wrote bar chart", out)
