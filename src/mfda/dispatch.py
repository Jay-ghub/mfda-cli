"""
File format detection and reader selection utilities for mfda.

Responsibilities:
- Detect the file format of a given path.
- Determine whether the file is compressed or part of an archive.
- Map detected formats to the appropriate reader functions or modules.
- Handle special cases such as `.zip` files containing a single inner path.
"""

import importlib
from pathlib import Path
from types import ModuleType


def detect_format(path: str | Path, hint: str | None = None) -> str | None:
    """
    Detect the file format of the given path.

    Detection order:
    1. Use the provided `hint` if available (overrides other checks).
    2. Otherwise, check the file extension(s).
       - If the last suffix is a compression (.gz or .zip), drop it and use the previous one.
    3. Normalize the extension to lowercase and map to a known logical format.

    Known mappings:
        .csv       -> "csv"
        .tsv       -> "tsv"
        .jsonl     -> "jsonl"
        .json      -> "json"
        .xlsx      -> "xlsx"
        .parquet   -> "parquet"
        .sqlite,
        .db        -> "sqlite"
        .html,
        .htm       -> "html"

    Args:
        path: The filesystem path to the file.
        hint: Optional string that directly specifies the expected format.

    Returns:
        A string representing the detected format (e.g., "csv", "json", "parquet"),
        or None if the format cannot be determined.

    Edge cases:
        - Uppercase extensions are normalized to lowercase.
        - Filenames with multiple dots are handled via Path.suffixes.
        - If there is no extension and no hint, returns None.
    """
    if hint:
        h = hint.lower().strip(".")
        return h

    p = Path(path)
    suffixes = [s.lower() for s in p.suffixes]

    if not suffixes:
        return None

    # Handle compression by dropping last suffix if it's a known compression
    compressions = {".gz", ".zip"}
    if suffixes[-1] in compressions:
        suffixes = suffixes[:-1]

    if not suffixes:
        return None

    ext = suffixes[-1].lstrip(".")

    ext_to_format = {
        "csv": "csv",
        "tsv": "tsv",
        "jsonl": "jsonl",
        "json": "json",
        "xlsx": "xlsx",
        "parquet": "parquet",
        "sqlite": "sqlite",
        "db": "sqlite",
        "html": "html",
        "htm": "html",
    }

    return ext_to_format.get(ext, None)


def choose_reader(fmt: str) -> ModuleType | None:
    """
    Choose the appropriate reader module for the given format.

    Args:
        fmt: The detected file format string (e.g., "csv", "json", "parquet").

    Returns:
        The imported module object corresponding to the given format.
    """
    if not fmt:
        return None
    fmt = fmt.lower()
    readers = {
        "csv": "mfda.readers.csv_reader",
        "tsv": "mfda.readers.csv_reader",  # TSV handled by CSV reader; delimiter policy lives there
        "json": "mfda.readers.json_reader",
        "jsonl": "mfda.readers.json_reader",
        "xlsx": "mfda.readers.xlsx_reader",
        "parquet": "mfda.readers.parquet_reader",
        "sqlite": "mfda.readers.sqlite_reader",
        "html": "mfda.readers.html_reader",
    }

    module_path = readers.get(fmt)
    if module_path is None:
        return None

    return importlib.import_module(module_path)
