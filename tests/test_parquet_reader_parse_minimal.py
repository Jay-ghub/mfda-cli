import importlib
from pathlib import Path

import pytest

pa = pytest.importorskip("pyarrow", reason="pyarrow is required for Parquet tests")
pq = pytest.importorskip("pyarrow.parquet", reason="pyarrow.parquet is required")

PARQ = importlib.import_module("mfda.readers.parquet_reader")


def _write_parquet(path: Path):
    import pyarrow as pa
    import pyarrow.parquet as pq

    tbl = pa.table({"id": [1, 2, 3], "name": ["Ana", "Bob", "Chi"]})
    pq.write_table(tbl, path)


def test_parquet_basic_columns_and_shape(tmp_path: Path):
    p = tmp_path / "tiny.parquet"
    _write_parquet(p)

    t = PARQ.read(p)
    assert hasattr(t, "columns")
    assert hasattr(t, "shape")
    assert callable(t.as_records)
    assert t.columns == ["id", "name"]  # schema order
    assert t.shape == (3, 2)


def test_parquet_subset_columns(tmp_path: Path):
    p = tmp_path / "tiny.parquet"
    _write_parquet(p)

    t = PARQ.read(p, columns=["name"])
    assert t.columns == ["name"]
    assert t.shape == (3, 1)


def test_parquet_limit_rows(tmp_path: Path):
    p = tmp_path / "tiny.parquet"
    _write_parquet(p)

    t = PARQ.read(p, limit=2)
    assert t.shape == (2, 2)
