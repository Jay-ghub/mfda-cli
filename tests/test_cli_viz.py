import importlib
import os
import re
from pathlib import Path

import pytest

# Skip these tests cleanly if matplotlib isn't available
matplotlib = pytest.importorskip("matplotlib", reason="matplotlib is required for viz CLI tests")

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
