import importlib
import os

import pytest

# require matplotlib for these tests
matplotlib = pytest.importorskip("matplotlib", reason="matplotlib is required for viz tests")

VIZ = importlib.import_module("mfda.visualization")


def test_save_histogram_creates_file(tmp_path):
    records = [{"age": 10}, {"age": 20}, {"age": 20}, {"age": 30}]
    out = tmp_path / "age_hist.png"
    VIZ.save_histogram(records, column="age", out_path=out)
    assert out.exists()
    assert os.stat(out).st_size > 0


def test_save_bar_counts_creates_file(tmp_path):
    records = [{"color": "red"}, {"color": "blue"}, {"color": "red"}]
    out = tmp_path / "color_bar.png"
    VIZ.save_bar_counts(records, column="color", out_path=out, top_k=3)
    assert out.exists()
    assert os.stat(out).st_size > 0
