from __future__ import annotations
from result import Ok, Err
import pytest

from configpile import types

def test_default_types():
    assert types.integer.parse('345') == Ok(345)
    assert types.integer.parse('qwe').is_err()

def test_separated_by():
    assert types.integer.separated_by(',').parse('3,4,56') == Ok([3,4,56])
