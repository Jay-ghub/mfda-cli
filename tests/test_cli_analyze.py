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
