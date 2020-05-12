import pytest
from eddb import distance, center

def test_different_points():
    a = {'x': 0, 'y': 0, 'z': 0}
    b = {'x': 1, 'y': 1, 'z': 1}
    assert distance(a, b) == round(3 ** 0.5, 1)
    c = {'x': -1, 'y': -1, 'z': -1}
    assert distance(b,c) == round(12 ** 0.5, 1)

def test_same_points():
    a = {'x': 1, 'y': 10, 'z': 0.1}
    b = a
    assert distance(a, b) == 0
