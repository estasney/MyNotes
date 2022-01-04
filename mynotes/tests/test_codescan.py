import pytest
from collections import namedtuple
from mynotes.export.preprocess.codescan import ExtractModuleUsage
FakeNbCell = namedtuple("FakeNbCell", "cell_type, source")

@pytest.mark.parametrize(
    "line, expected",
    [
        ("import pandas as pd", ["pandas"]),  # aliased
        ("import collections", ["collections"]),
        ("from collections import Counter", ["collections"]),  # from
        ("from some.package import module", ["some"]),  # dotted
        ("import operator, collections", ["operator", "collections"]),  # comma
        ("from operator import (eq, getitem)", ["operator"]),  # parentheses
        ("import pandas as pd, numpy as np", ["pandas", "numpy"]),  # multiple aliases
        ("# import numpy", []),
    ],  # commented out import)
)
def test_line_scans(line, expected):
    proc = ExtractModuleUsage()
    cell_line = FakeNbCell("code", line)
    result = proc.preprocess_cell(cell_line, {"mynotes": {"modules": []}}, 0)[1]
    assert result == {"mynotes": {"modules": expected}}
