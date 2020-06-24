import pytest
import os
from elitetools import eddb
from elitetools.eddb import Feeds, feed_cache, load_feed

class TestLoadFeed:
    def test(self):
        pop_sys = load_feed(Feeds.POPULATED_SYSTEMS)
        assert pop_sys is not None
        assert len(pop_sys) == 7