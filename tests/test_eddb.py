sys.path.insert(0, '..')
print(sys.path)
import unittest
import os
import sys
from eddb import distance

class TestDistance(unittest.TestCase):
    def test_distance(self):
        a = {'x': 0, 'y': 0, 'z': 0}
        b = {'x': 1, 'y': 1, 'z': 1}
        assert distance(a, b) == round(3 ** 0.5, 1), 'Same start and end point generated non-zero distance.'

    def test_distance_same_points(self):
        a = {'x': 1, 'y': 10, 'z': 0.1}
        b = a
        assert distance(a, b) == 0, 'Same start and end point generated non-zero distance.'


class TestAveragePosition:
    def test_average_position(self):
        assert False
