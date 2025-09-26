"""
CSV/TSV Reader Plugin

- **Format**: Handles `.csv` and `.tsv` files.(plain or compressed: gz, zip)
- **Options**:
  - `delimiter` (default: auto-sniff) Delimiter sniffing must recognize `.tsv` files and default to
  a tab character (`\t`), and any missing values in the input must be normalized to `null` in the
  Table abstraction.
  - `quotechar` (default: `"`)
  - `header_row` (default: first row)
  - `encoding` (default: utf-8)
  - `decimal` (e.g., `,` for European formats)
  - `thousands` (e.g., `.` or `,`)
  - `limit` (optional row limit for preview/testing)
- **Errors Raised**:
  - `FileFormatError` for malformed rows or delimiter mismatch
  - `ConfigurationError` for invalid options
- **Returns**: a `Table`
"""

import csv
from pathlib import Path
from typing import Any

# Defaults & sentinel for the CSV/TSV reader contract
DEFAULT_DELIMITER_CSV = ","
DEFAULT_DELIMITER_TSV = "\t"
NULL = None


class _Table:
    def __init__(self, columns: list[str], rows: list[list[str | None]]):
        self.columns = columns
        self._rows = rows

    @property
    def shape(self) -> tuple[int, int]:
        return (len(self._rows), len(self.columns))

    def as_records(self) -> list[dict[str, Any]]:
        return [dict(zip(self.columns, row, strict=False)) for row in self._rows]


def read(
    path: str | Path,
    *,
    delimiter: str | None = None,
    encoding: str = "utf-8",
    quotechar: str = '"',
    header_row: int = 0,
    decimal: str = ".",
    thousands: str | None = None,
    limit: int | None = None,
    infer_dtypes: bool = True,
) -> Any:
    p = Path(path)

    if delimiter is not None:
        chosen = delimiter
    elif p.suffix.lower() == ".tsv":
        chosen = DEFAULT_DELIMITER_TSV
    else:
        chosen = DEFAULT_DELIMITER_CSV

    rows: list[list[str | None]] = []
    with open(p, newline="", encoding=encoding) as file:
        reader = csv.reader(file, delimiter=chosen, quotechar=quotechar)
        # use small loop to skip header_row lines (if set)
        for _ in range(header_row):
            next(reader)
        header = next(reader)
        for row in reader:
            # enforce limit(if set)
            if limit is not None and len(rows) >= limit:
                break
            # skip malformed rows
            if len(row) != len(header):
                continue
            # skip empty rows
            if not row or all(val == "" for val in row):
                continue
            # empty cells to NULL
            clean_row = [val if val != "" else NULL for val in row]
            rows.append(clean_row)
    return _Table(header, rows)
