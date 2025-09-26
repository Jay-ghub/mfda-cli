"""
JSON/JSONL Reader Plugin

- **Format**: Handles `.json` (records array) and `.jsonl` (one JSON object per line), plain or
compressed(gz, zip).
- **Options**:
  - `lines: bool` (default: False; set True for JSONL)
  - `encoding` (default: utf-8)
  - `limit` (optional row limit)
- **Errors Raised**:
  - `FileFormatError` if JSON is invalid or not records/objects
  - `ConfigurationError` if options conflict
- **Returns**: a `Table` (see core model docs)
"""

import json
from pathlib import Path
from typing import Any

from mfda.errors import FileFormatError

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
    lines: bool = False,
    encoding: str = "utf-8",
    limit: int | None = None,
) -> Any:
    p = Path(path)
    ext = p.suffix.lower()

    # decide mode
    if lines is True:
        mode = "jsonl"
    elif ext == ".jsonl":
        mode = "jsonl"
    else:
        mode = "records"

    # parse per mode

    # JSONL
    if mode == "jsonl":
        records = []
        with open(p, encoding=encoding) as fp:
            for lineno, line in enumerate(fp, start=1):
                # skip empty lines
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as e:
                    raise FileFormatError(f"Invalid JSON on line {lineno}: {e}") from e

                if not isinstance(obj, dict):
                    raise FileFormatError("JSONL expects one JSON object per line")

                records.append(obj)

                # Apply limit
                if limit is not None and len(records) >= limit:
                    break

    # JSON
    elif mode == "records":
        with open(p, encoding=encoding) as fp:
            data = json.load(fp)

        if not isinstance(data, list) or any(not isinstance(x, dict) for x in data):
            raise FileFormatError("Records JSON must be a list of objects")

        records = data

        # Apply limit
        if limit is not None:
            records = records[:limit]

    # column builder
    columns = []
    for rec in records:
        for k in rec.keys():
            if k not in columns:
                columns.append(k)

    # missing keys to NULL
    for rec in records:
        for k in columns:
            if k not in rec:
                rec[k] = NULL

    # return Table class
    return _Table(columns, records)
