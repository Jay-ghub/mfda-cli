"""
Reader Plugins Package

This package provides modular file readers for different formats.
Each reader plugin is responsible for:

1. Detecting and loading its supported file format.
2. Normalizing data into the core `Table` abstraction.
3. Raising clear errors (`FileFormatError`, `ConfigurationError`).

Available plugins:

- csv_reader    — CSV/TSV (delimiter-sniffing, compressed)
- json_reader   — JSON/JSONL
- xlsx_reader   — Excel spreadsheets (.xlsx)
- parquet_reader — Parquet columnar files
- sqlite_reader — SQLite database tables or queries
- html_reader   — HTML tables

Each module contains only a **contract docstring** at this stage.
Implementation will follow in later steps.
"""

# Placeholder imports (to be activated once implementations exist)
# from . import csv_reader
# from . import json_reader
# from . import xlsx_reader
# from . import parquet_reader
# from . import sqlite_reader
# from . import html_reader
