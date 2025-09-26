from mfda.dispatch import choose_reader, detect_format


def test_detect_format_uppercase_extension():
    assert detect_format("DATA.CSV") == "csv"


def test_detect_format_hint_strips_dot():
    assert detect_format("whatever", hint=".jsonl") == "jsonl"


def test_detect_format_unknown_returns_none():
    assert detect_format("file.unknown") is None


def test_choose_reader_empty_returns_none():
    assert choose_reader("") is None
