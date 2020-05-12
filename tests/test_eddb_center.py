import pytest
from eddb import distance, center

def test_single_point():
    a = {'x': 1, 'y': 1, 'z': 1}
    b = center([a])
    assert a['x'] == b['x']
    assert a['y'] == b['y']
    assert a['z'] == b['z']


def test_multiple_points():
    a = {'x': -10, 'y': -4, 'z': 0}
    b = {'x': 4, 'y': 1, 'z': -1}
    c = {'x': 3, 'y': 1, 'z': 1}
    d = {'x': 2, 'y': 1, 'z': -1}
    e = {'x': 1, 'y': 1, 'z': 1}
    f = center([a, b, c, d, e])
    assert f['x'] == 0
    assert f['y'] == 0
    assert f['z'] == 0
