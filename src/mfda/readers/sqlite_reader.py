"""
SQLite Reader Plugin

- **Format**: Handles `.sqlite` or `.db` files. Reads tables or results of SQL queries.
- **Options**:
  - `table` (name of table to read; required if no query)
  - `query` (SQL string; mutually exclusive with table)
  - `limit` (optional row limit)
- **Errors Raised**:
  - `FileFormatError` if database file is invalid
  - `ConfigurationError` if query/table options conflict
- **Returns**: a `Table` (see core model docs)
"""

import sqlite3
from pathlib import Path
from typing import Any

from mfda.errors import ConfigurationError

NULL = None


class _Table:
    def __init__(self, columns: list[str], records: list[dict[str, Any]]) -> None:
        self.columns = columns
        self._records = records

    @property
    def shape(self) -> tuple[int, int]:
        return (len(self._records), len(self.columns))

    def as_records(self) -> list[dict[str, Any]]:
        return self._records


def read(
    path: str | Path,
    *,
    table: str | None = None,
    query: str | None = None,
    limit: int | None = None,
) -> _Table:
    with sqlite3.connect(path) as conn:
        cursor = conn.cursor()

        # raise Errors when both or neither are provided
        if table and query:
            raise ConfigurationError("Provide either table or query, not both")

        if not table and not query:
            raise ConfigurationError("Provide either table or query, not neither")

        # build SQL
        if table:
            sql = f"SELECT * FROM {table}"  # noqa: S608
            if limit is not None:
                sql += " LIMIT ?"
                cursor.execute(sql, (limit,))
            else:
                cursor.execute(sql)
            rows = cursor.fetchall()
        else:
            assert query is not None
            cursor.execute(query)
            rows = cursor.fetchall()
            if limit is not None:
                rows = rows[:limit]

        # get cols
        columns = [d[0] for d in cursor.description]

        # normalize rows
        normalized_rows = []
        for row in rows:
            clean_row = [NULL if val is None else val for val in row]
            normalized_rows.append(clean_row)

        # build records
        records = [dict(zip(columns, row, strict=False)) for row in normalized_rows]

        return _Table(columns, records)
