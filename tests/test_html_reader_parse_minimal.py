import importlib
from pathlib import Path

import pytest

bs4 = pytest.importorskip("bs4", reason="beautifulsoup4 is required for HTML tests")

HTML = importlib.import_module("mfda.readers.html_reader")


def _write_html(path: Path, tables: list[str]) -> None:
    html = "<html><body>" + "".join(tables) + "</body></html>"
    path.write_text(html, encoding="utf-8")


def test_html_basic_columns_and_shape(tmp_path: Path):
    p = tmp_path / "one.html"
    table = """
    <table>
      <tr><th>id</th><th>name</th><th>age</th></tr>
      <tr><td>1</td><td>Ana</td><td>28</td></tr>
      <tr><td>2</td><td>Bob</td><td>31</td></tr>
      <tr><td>3</td><td>Chi</td><td>22</td></tr>
    </table>
    """
    _write_html(p, [table])

    t = HTML.read(p)
    assert t.columns == ["id", "name", "age"]
    assert t.shape == (3, 3)


def test_html_select_table_by_index(tmp_path: Path):
    p = tmp_path / "multi.html"
    t1 = """<table><tr><th>a</th></tr><tr><td>x</td></tr></table>"""
    t2 = """<table><tr><th>id</th><th>region</th></tr><tr><td>1</td><td>EU</td></tr></table>"""
    _write_html(p, [t1, t2])

    t = HTML.read(p, table_index=1)
    assert t.columns == ["id", "region"]
    assert t.shape == (1, 2)


def test_html_header_row_offset_and_limit(tmp_path: Path):
    p = tmp_path / "hdr.html"
    table = """
    <table>
      <tr><td>junk</td></tr>
      <tr><td>more</td></tr>
      <tr><th>id</th><th>name</th></tr>
      <tr><td>1</td><td>Ana</td></tr>
      <tr><td>2</td><td>Bob</td></tr>
    </table>
    """
    _write_html(p, [table])

    t = HTML.read(p, header_row=2, limit=1)
    assert t.columns == ["id", "name"]
    assert t.shape == (1, 2)


def test_html_missing_cells_to_NULL(tmp_path: Path):
    p = tmp_path / "na.html"
    table = """
    <table>
      <tr><th>a</th><th>b</th></tr>
      <tr><td>1</td><td></td></tr>
    </table>
    """
    _write_html(p, [table])

    t = HTML.read(p)
    recs = t.as_records()
    assert recs[0]["b"] is HTML.NULL
