import importlib
import json
import re

CLI = importlib.import_module("mfda.cli")
DISP = importlib.import_module("mfda.dispatch")


def _call(argv):
    import sys
    from io import StringIO

    buf = StringIO()
    old = sys.stdout
    try:
        sys.stdout = buf
        code = CLI.main(argv)
    finally:
        sys.stdout = old
    return code, buf.getvalue()


def test_validate_csv_inline_schema(tmp_path):
    p = tmp_path / "tiny.csv"
    p.write_text("id,name\n1,Ana\n2,\n3,Chi\n", encoding="utf-8")
    schema = {"name": {"required": True}, "id": {"unique": True}}
    sfile = tmp_path / "schema.json"
    sfile.write_text(json.dumps(schema), encoding="utf-8")

    code, out = _call(["validate", str(p), "--schema", str(sfile)])
    assert code == 0
    assert "rows:" in out and "columns:" in out
    # Should mention at least the missing_required code
    assert re.search(r"missing_required", out)


def test_validate_unknown_format(tmp_path):
    p = tmp_path / "mystery.data"
    p.write_text("???", encoding="utf-8")
    assert DISP.detect_format(p) is None

    code, out = _call(["validate", str(p)])
    assert code != 0
    assert re.search(r"(?i)unknown|unsupported|format", out)
