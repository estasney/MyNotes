from unittest import TestCase
from mynotes.utils.codescan import scan_line

test_cases = [
    ("import pandas as pd", ["pandas"]),  # aliased
    ("import collections", ["collections"]),
    ("from collections import Counter", ["collections"]),  # from
    ('from some.package import module', ['some.package']),  # dotted
    ("import operator, collections", ["operator", "collections"]),  # comma
    ("from operator import (eq, getitem)", ["operator"]),  # parentheses
    ("import pandas as pd, numpy as np", ["pandas", "numpy"]),  # multiple aliases
    ("# import numpy", [])  # commented out import
    ]


class Test(TestCase):
    def test_scan_line(self):
        for given, expected in test_cases:
            result = scan_line(given)
            self.assertEqual(result, expected)
