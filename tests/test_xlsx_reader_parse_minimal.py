import importlib
from pathlib import Path

import pytest

openpyxl = pytest.importorskip("openpyxl", reason="openpyxl is required for XLSX tests")

XLSX = importlib.import_module("mfda.readers.xlsx_reader")


def _make_book(tmp_path: Path, name="book.xlsx"):
    """Return (path, workbook) – small helper to create a workbook."""
    from openpyxl import Workbook

    p = tmp_path / name
    wb = Workbook()
    # By default, wb has one active sheet named "Sheet"
    return p, wb


def test_xlsx_read_basic_columns_and_shape(tmp_path: Path):
    p, wb = _make_book(tmp_path)
    ws = wb.active
    ws.title = "Data"
    # Header
    ws.append(["id", "name", "age"])
    # Rows
    ws.append([1, "Ana", 28])
    ws.append([2, "Bob", 31])
    ws.append([3, "Chi", 22])
    wb.save(p)

    t = XLSX.read(p)
    assert hasattr(t, "columns")
    assert hasattr(t, "shape")
    assert callable(t.as_records)
    assert t.columns == ["id", "name", "age"]
    assert t.shape == (3, 3)


def test_xlsx_select_sheet_by_name(tmp_path: Path):
    p, wb = _make_book(tmp_path)
    # Sheet0
    wb.active.append(["skip_me"])
    # Add another sheet with real data
    ws = wb.create_sheet(title="Q1")
    ws.append(["id", "region"])
    ws.append([1, "EU"])
    ws.append([2, "US"])
    wb.save(p)

    t = XLSX.read(p, sheet="Q1")
    assert t.columns == ["id", "region"]
    assert t.shape == (2, 2)


def test_xlsx_header_row_offset(tmp_path: Path):
    p, wb = _make_book(tmp_path)
    ws = wb.active
    # Two junk rows, then header
    ws.append(["junk"])
    ws.append(["more junk"])
    ws.append(["id", "name"])
    ws.append([1, "Ana"])
    ws.append([2, "Bob"])
    wb.save(p)

    t = XLSX.read(p, header_row=2)
    assert t.columns == ["id", "name"]
    assert t.shape == (2, 2)


def test_xlsx_limit_and_missing_cells(tmp_path: Path):
    p, wb = _make_book(tmp_path)
    ws = wb.active
    ws.append(["a", "b"])
    ws.append([1, None])  # missing cell -> should become NULL
    ws.append([2, 3])
    ws.append([4, 5])
    wb.save(p)

    t = XLSX.read(p, limit=2)
    assert t.shape == (2, 2)
    recs = t.as_records()
    assert recs[0]["b"] is XLSX.NULL
