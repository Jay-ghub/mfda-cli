import pytest

from mfda import cli


def test_help_root(capsys):
    # --help exits with code 0
    with pytest.raises(SystemExit) as e:
        cli.main(["--help"])
    assert e.value.code == 0
    out, _ = capsys.readouterr()
    assert "usage" in out.lower()
    assert "read" in out
    assert "analyze" in out
    assert "viz" in out
    assert "validate" in out
    assert "report" in out


def test_help_read(capsys):
    with pytest.raises(SystemExit) as e:
        cli.main(["read", "--help"])
    assert e.value.code == 0
    out, _ = capsys.readouterr()
    # Check key parts of the subcommand help
    assert "usage" in out.lower()
    assert "path" in out
    assert "--limit" in out


def test_version(capsys):
    with pytest.raises(SystemExit) as e:
        cli.main(["--version"])
    assert e.value.code == 0
    out, _ = capsys.readouterr()
    assert "mfda" in out
    assert "1.0.0" in out
