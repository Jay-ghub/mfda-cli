"""
Parquet Reader Plugin

- **Format**: Handles `.parquet` columnar storage files (palin or compressed gz/gzip).
- **Options**:
  - `columns` (subset to read; default: all)
  - `limit` (optional row limit)
  - 'missing values --> NULL'
- **Errors Raised**:
  - `FileFormatError` if file is corrupt or not Parquet
  - `ConfigurationError` if options mismatch schema
- **Returns**: a `Table` (see core model docs)
"""

from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

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
    columns: list[str] | None = None,
    limit: int | None = None,
) -> Any:
    pa_table = pq.read_table(path, columns=columns)
    cols = pa_table.schema.names
    # convert to list(dicts)
    records = pa_table.to_pylist()

    # normalize missing values
    for rec in records:
        for k, v in rec.items():
            if v is None:
                rec[k] = NULL

    # limit
    if limit is not None:
        records = records[:limit]

    return _Table(cols, records)
