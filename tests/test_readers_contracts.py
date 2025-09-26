import importlib

import pytest

# List of reader plugin modules to check
READER_MODULES = [
    "mfda.readers.csv_reader",
    "mfda.readers.json_reader",
    "mfda.readers.xlsx_reader",
    "mfda.readers.parquet_reader",
    "mfda.readers.sqlite_reader",
    "mfda.readers.html_reader",
]


@pytest.mark.parametrize("module_name", READER_MODULES)
def test_reader_docstring_present(module_name):
    """Each reader module must exist and contain a non-empty docstring."""
    module = importlib.import_module(module_name)
    assert module.__doc__ is not None
    assert module.__doc__.strip() != ""
