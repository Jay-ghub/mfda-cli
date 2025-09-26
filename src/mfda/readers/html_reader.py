"""
HTML Table Reader Plugin

- **Format**: Handles `.html` pages or fragments containing <table> elements.
- **Options**:
  - `table_index` (which <table> to read; default: first)
  - `header_row` (row index for headers; default: first row)
  - `limit` (optional row limit)
- **Errors Raised**:
  - `FileFormatError` if HTML is malformed or no table found
  - `ConfigurationError` if table index is invalid
- **Returns**: a `Table` (see core model docs)
"""

from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup
from bs4.element import Tag

from mfda.errors import FileFormatError

NULL = None


class _Table:
    def __init__(self, columns: list[str], rows: list[list[Any]]) -> None:
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
    table_index: int = 0,
    header_row: int = 0,
    encoding: str = "utf-8",
    limit: int | None = None,
) -> _Table:
    with open(path, encoding=encoding) as f:
        soup = BeautifulSoup(f.read(), "html.parser")

        # collect table tags
        tables = soup.find_all("table")
        if table_index >= len(tables) or table_index < 0:
            raise FileFormatError(f"No such table: {table_index}")

        table = tables[table_index]
        # Narrow to Tag before using Tag methods
        assert isinstance(table, Tag), "Expected a <table> Tag"

        # rows
        row_nodes = table.find_all("tr")
        rows: list[Tag] = []
        for node in row_nodes:
            assert isinstance(node, Tag), "Expected <tr> Tag"
            rows.append(node)

        # skip header_row (but don't underflow)
        skip = min(header_row, len(rows))
        for _ in range(skip):
            rows.pop(0)

        if not rows:
            raise FileFormatError("No header row available after skipping header_row")

        # header
        first_row = rows.pop(0)
        assert isinstance(first_row, Tag), "Expected header <tr> Tag"
        header_nodes = first_row.find_all(["th", "td"])
        header_cells: list[Tag] = []
        for cell in header_nodes:
            assert isinstance(cell, Tag), "Expected <th>/<td> Tag"
            header_cells.append(cell)
        columns = [cell.get_text(strip=True) for cell in header_cells]

        # data rows
        records: list[list[Any]] = []
        for tr in rows:
            assert isinstance(tr, Tag), "Expected data <tr> Tag"
            cell_nodes = tr.find_all(["td", "th"])

            cells: list[str] = []
            for td in cell_nodes:
                assert isinstance(td, Tag), "Expected <td>/<th> Tag"
                cells.append(td.get_text(strip=True))

            # skip ragged rows
            if len(cells) != len(columns):
                continue

            clean_row = [NULL if val == "" else val for val in cells]
            records.append(clean_row)

            # enforce limit
            if limit is not None and len(records) >= limit:
                break

        return _Table(columns, records)
