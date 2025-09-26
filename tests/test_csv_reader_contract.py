import importlib

import pytest


def test_csv_reader_module_exists_and_has_docstring():
    """The CSV reader module must exist and have a non-empty docstring."""
    module = importlib.import_module("mfda.readers.csv_reader")
    assert module is not None
    assert module.__doc__ is not None
    assert module.__doc__.strip() != ""


@pytest.mark.parametrize("section", ["Format", "Options", "Errors", "Returns", "compressed"])
def test_csv_reader_docstring_mentions_sections(section):
    """The CSV reader module docstring must mention required sections."""
    module = importlib.import_module("mfda.readers.csv_reader")
    doc = module.__doc__ or ""
    assert section in doc
