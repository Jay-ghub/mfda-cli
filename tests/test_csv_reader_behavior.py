import importlib


def _mod():
    return importlib.import_module("mfda.readers.csv_reader")


def test_exports_default_delimiters_and_null_policy():
    mod = _mod()

    # defaults must exist
    assert hasattr(mod, "DEFAULT_DELIMITER_CSV")
    assert hasattr(mod, "DEFAULT_DELIMITER_TSV")
    assert hasattr(mod, "NULL")

    # specific policies
    assert mod.DEFAULT_DELIMITER_CSV == ","
    assert mod.DEFAULT_DELIMITER_TSV == "\t"
    assert mod.NULL is None  # single sentinel for missing values


def test_has_read_entrypoint_signature():
    mod = _mod()

    # The reader must expose a callable `read` entrypoint.
    assert hasattr(mod, "read")
    assert callable(mod.read)
