import pytest

from mynotes.utils.codescan import scan_line_modules


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
    result = scan_line_modules(line)
    assert result == expected
