import pytest
from elitetools.eddb import distance, center, population_center


class TestCenter:
    def test_single_point(self):
        a = {'x': 1, 'y': 1, 'z': 1}
        b = center([a])
        assert a['x'] == b['x']
        assert a['y'] == b['y']
        assert a['z'] == b['z']


    def test_multiple_points(self):
        # Test 1
        a = {'x': 10, 'y': -1, 'z': 0.1}
        b = {'x': 20, 'y': -2, 'z': 0.2}
        c = {'x': 30, 'y': -3, 'z': 0.3}
        d = {'x': 40, 'y': -4, 'z': 0.4}
        e = center([a, b, c, d])
        assert e['x'] == 25
        assert e['y'] == -2.5
        assert e['z'] == 0.25
        # Test 2
        f = {'x': 10, 'y': 20, 'z': 30}
        g = {'x': -1, 'y': -2, 'z': -3}
        h = {'x': 0.1, 'y': 0.2, 'z': 0.3}
        i = {'x': 0, 'y': 0, 'z': 0}
        j = center([f, g, h, i])
        assert j['x'] == 9.1/4
        assert j['y'] == 18.2/4
        assert j['z'] == 27.3/4
        # Test 3
        a = {'x': -10, 'y': -4, 'z': 0}
        b = {'x': 4, 'y': 1, 'z': -1}
        c = {'x': 3, 'y': 1, 'z': 1}
        d = {'x': 2, 'y': 1, 'z': -1}
        e = {'x': 1, 'y': 1, 'z': 1}
        f = center([a, b, c, d, e])
        assert f['x'] == 0
        assert f['y'] == 0
        assert f['z'] == 0


class TestPopulationCenter:
    def test_single_point(self):
        a = {'x': 1, 'y': 1, 'z': 1, 'population': 1000000}
        b = population_center([a])
        assert a['x'] == b['x']
        assert a['y'] == b['y']
        assert a['z'] == b['z']


    def test_multiple_points_same_weights(self):
        # Test 1
        a = {'x': 10, 'y': -1, 'z': 0.1, 'population': 1000000}
        b = {'x': 20, 'y': -2, 'z': 0.2, 'population': 1000000}
        c = {'x': 30, 'y': -3, 'z': 0.3, 'population': 1000000}
        d = {'x': 40, 'y': -4, 'z': 0.4, 'population': 1000000}
        e = population_center([a, b, c, d])
        assert e['x'] == 25
        assert e['y'] == -2.5
        assert e['z'] == 0.25
        # Test 2
        f = {'x': 10, 'y': 20, 'z': 30, 'population': 10000}
        g = {'x': -1, 'y': -2, 'z': -3, 'population': 1000}
        h = {'x': 0.1, 'y': 0.2, 'z': 0.3, 'population': 100}
        i = {'x': 0, 'y': 0, 'z': 0, 'population': 10}
        j = population_center([f, g, h, i])
        assert j['x'] == ( 40 - 3 + 0.2) / 10
        assert j['y'] == ( 80 - 6 + 0.4) / 10
        assert j['z'] == (120 - 9 + 0.6) / 10
        # Test 3
        a = {'x': -10, 'y': -4, 'z': 0, 'population': 1000000}
        b = {'x': 4, 'y': 1, 'z': -1, 'population': 1000000}
        c = {'x': 3, 'y': 1, 'z': 1, 'population': 1000000}
        d = {'x': 2, 'y': 1, 'z': -1, 'population': 1000000}
        e = {'x': 1, 'y': 1, 'z': 1, 'population': 1000000}
        f = population_center([a, b, c, d, e])
        assert f['x'] == 0
        assert f['y'] == 0
        assert f['z'] == 0


class TestDistance:
    def test_different_points(self):
        a = {'x': 0, 'y': 0, 'z': 0}
        b = {'x': 1, 'y': 1, 'z': 1}
        assert distance(a, b) == round(3 ** 0.5, 1)
        c = {'x': -1, 'y': -1, 'z': -1}
        assert distance(b,c) == round(12 ** 0.5, 1)

    def test_same_points(self):
        a = {'x': 1, 'y': 10, 'z': 0.1}
        b = a
        assert distance(a, b) == 0
