import importlib

# Import the CLI module once so we can monkeypatch its symbols directly
CLI = importlib.import_module("mfda.cli")


def _call(argv):
    """Capture only stdout (for normal prints)."""
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
    """Capture both stdout and stderr (for error handlers)."""
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


def test_report_hist_requires_hist_out(tmp_path):
    # Covers the precheck: --hist requires --hist-out
    out_md = tmp_path / "r.md"
    code, out = _call(
        [
            "report",
            "tests/fixtures/tiny_customers.csv",
            "--out",
            str(out_md),
            "--hist",
            "age",
        ]
    )
    assert code == 2
    assert "--hist requires --hist-out" in out


def test_report_bar_requires_bar_out(tmp_path):
    # Covers the precheck: --bar requires --bar-out
    out_md = tmp_path / "r.md"
    code, out = _call(
        [
            "report",
            "tests/fixtures/tiny_customers.csv",
            "--out",
            str(out_md),
            "--bar",
            "name",
        ]
    )
    assert code == 2
    assert "--bar requires --bar-out" in out


def test_report_no_schema_with_charts(monkeypatch, tmp_path):
    """
    Happy path with NO schema (prints 'No schema provided...'), both charts stubbed.
    Hits: detect->reader->read, analyze, validate(empty), chart writes, and markdown writing.
    """
    rmd = tmp_path / "r.md"
    hist = tmp_path / "h.png"
    bar = tmp_path / "b.png"

    # Force a predictable reader
    class R:
        @staticmethod
        def read(path, **kw):
            class T:
                columns = ["n"]
                shape = (2, 1)

                def as_records(self):
                    return [{"n": 1}, {"n": 2}]

            return T()

    monkeypatch.setattr(CLI, "detect_format", lambda _: "csv")
    monkeypatch.setattr(CLI, "choose_reader", lambda _fmt: R)

    # Controlled analysis + validation
    class Num:
        column = "n"
        count = 2
        nulls = 0
        distinct = 2
        min = 1
        max = 2
        mean = 1.5

    class Rep:
        rows = 2
        columns = 1
        numeric = [Num()]
        categorical = []

    class VRep:
        issues = []

    monkeypatch.setattr(CLI.analysis, "analyze", lambda recs, top_k: Rep)
    monkeypatch.setattr(CLI.validation, "validate", lambda recs, schema: VRep)

    # Stub chart writers (no matplotlib dependency)
    monkeypatch.setattr(CLI, "save_histogram", lambda *a, **k: None)
    monkeypatch.setattr(CLI, "save_bar_counts", lambda *a, **k: None)

    code, out = _call(
        [
            "report",
            "tests/fixtures/tiny_customers.csv",
            "--out",
            str(rmd),
            "--hist",
            "n",
            "--hist-out",
            str(hist),
            "--bar",
            "n",
            "--bar-out",
            str(bar),
            "--top-k",
            "3",
        ]
    )
    assert code == 0
    # The CLI prints this when no schema is provided
    assert "No schema provided, skipping rule checks." in out

    text = rmd.read_text("utf-8")
    assert "Report for" in text
    assert "## Overview" in text
    assert "## Numeric columns" in text
    assert "Histogram for `n`" in text
    assert "Bar chart for `n`" in text


def test_report_with_schema_and_issues(monkeypatch, tmp_path):
    """
    Happy path WITH schema and non-empty issues — exercises the issues loop.
    """
    rmd = tmp_path / "r.md"
    sfile = tmp_path / "schema.json"
    sfile.write_text('{"rules":[1]}', encoding="utf-8")

    class R:
        @staticmethod
        def read(path, **kw):
            class T:
                columns = ["a"]
                shape = (1, 1)

                def as_records(self):
                    return [{"a": None}]

            return T()

    monkeypatch.setattr(CLI, "detect_format", lambda _: "csv")
    monkeypatch.setattr(CLI, "choose_reader", lambda _fmt: R)

    class Rep:
        rows = 1
        columns = 1
        numeric = []
        categorical = []

    class Issue:
        code = "E1"
        column = "a"
        count = 1
        examples = [{"a": None}]

    class VRep:
        issues = [Issue()]

    monkeypatch.setattr(CLI.analysis, "analyze", lambda *a, **k: Rep)
    monkeypatch.setattr(CLI.validation, "validate", lambda *a, **k: VRep)

    code, _out = _call(["report", "x.csv", "--out", str(rmd), "--schema", str(sfile)])
    assert code == 0

    txt = rmd.read_text("utf-8")
    assert "Validation issues" in txt
    assert "code=E1" in txt
    assert "column=a" in txt


def test_report_error_handlers(monkeypatch, tmp_path):
    """
    Cover both the known-error branch (ConfigurationError/FileFormatError -> return 2)
    and the unexpected-error branch (generic Exception -> return 1).
    We'll do two subcases separately for clarity.
    """
    from mfda.errors import ConfigurationError

    # ---- Known error from reader.read() -> exit code 2, stderr "Error: ..."
    class RBad:
        @staticmethod
        def read(*a, **k):
            raise ConfigurationError("bad cfg")

    monkeypatch.setattr(CLI, "detect_format", lambda _: "csv")
    monkeypatch.setattr(CLI, "choose_reader", lambda _fmt: RBad)

    code, out, err = _call_both(["report", "x.csv", "--out", str(tmp_path / "r1.md")])
    assert code == 2
    assert "Error:" in err and "bad cfg" in err

    # ---- Unexpected error later (e.g., analysis blows up) -> exit code 1,
    # stderr "Unexpected error: ..."
    class RGood:
        @staticmethod
        def read(*a, **k):
            class T:
                columns = ["a"]
                shape = (1, 1)

                def as_records(self):
                    return [{"a": 1}]

            return T()

    monkeypatch.setattr(CLI, "choose_reader", lambda _fmt: RGood)
    # Make analyze raise a generic exception
    monkeypatch.setattr(
        CLI.analysis, "analyze", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
    )

    code, out, err = _call_both(["report", "x.csv", "--out", str(tmp_path / "r2.md")])
    assert code == 1
    assert "Unexpected error:" in err
