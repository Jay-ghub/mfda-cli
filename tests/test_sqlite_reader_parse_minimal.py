import importlib
import sqlite3
from pathlib import Path

import pytest

SQL = importlib.import_module("mfda.readers.sqlite_reader")


def _make_db(path: Path):
    con = sqlite3.connect(path)
    cur = con.cursor()
    cur.execute("create table users (id integer, name text, age integer)")
    cur.executemany(
        "insert into users (id, name, age) values (?, ?, ?)",
        [(1, "Ana", 28), (2, "Bob", 31), (3, None, 22)],  # name NULL in row 3
    )
    con.commit()
    con.close()


def test_sqlite_read_table_basic(tmp_path: Path):
    p = tmp_path / "tiny.db"
    _make_db(p)

    t = SQL.read(p, table="users")
    assert hasattr(t, "columns")
    assert hasattr(t, "shape")
    assert callable(t.as_records)
    assert t.columns == ["id", "name", "age"]
    assert t.shape == (3, 3)
    recs = t.as_records()
    assert recs[2]["name"] is SQL.NULL  # normalized missing


def test_sqlite_read_query(tmp_path: Path):
    p = tmp_path / "tiny.db"
    _make_db(p)

    t = SQL.read(p, query="select name, id from users order by id")
    assert t.columns == ["name", "id"]
    assert t.shape == (3, 2)


def test_sqlite_limit(tmp_path: Path):
    p = tmp_path / "tiny.db"
    _make_db(p)

    t = SQL.read(p, table="users", limit=2)
    assert t.shape == (2, 3)


def test_sqlite_table_and_query_conflict(tmp_path: Path):
    p = tmp_path / "tiny.db"
    _make_db(p)

    from mfda.errors import ConfigurationError

    with pytest.raises(ConfigurationError):
        SQL.read(p, table="users", query="select * from users")
