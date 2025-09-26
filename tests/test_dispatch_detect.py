import types

import pytest

# Import only the function names you’re testing, not their internals.
from mfda.dispatch import choose_reader, detect_format


@pytest.mark.parametrize(
    "path,expected",
    [
        ("file.csv", "csv"),
        ("file.tsv", "tsv"),
        ("file.jsonl", "jsonl"),
        ("archive.csv.gz", "csv"),  # gzip should unwrap
    ],
)
def test_detect_format_by_extension_and_compression(path, expected):
    """detect_format should infer format from extension or compression wrapper."""
    assert detect_format(path) == expected


def test_detect_format_hint_overrides_everything():
    """If a hint is provided, it wins even if extension suggests otherwise."""
    assert detect_format("data", hint="xlsx") == "xlsx"


def test_choose_reader_returns_callable_or_module():
    """choose_reader should return something usable (a callable or module)."""
    reader = choose_reader("csv")
    assert callable(reader) or isinstance(reader, types.ModuleType)
