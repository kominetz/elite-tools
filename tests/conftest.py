import os
import pytest
from elitetools import eddb
from elitetools.eddb import Feeds

def mock_feed_cache(feed: Feeds, force_refresh=False):
    if feed == Feeds.POPULATED_SYSTEMS:
        return os.path.join('.', 'tests', 'data', 'populated_systems.jsonl' )
    elif feed == Feeds.COMMODITIES:
        return os.path.join('.', 'tests', 'data', 'commodities.json' )
    elif feed == Feeds.FACTIONS:
        return os.path.join('.', 'tests', 'data', 'factions.jsonl' )
    elif feed == Feeds.MODULES:
        return os.path.join('.', 'tests', 'data', 'modules.jsonl' )
    elif feed == Feeds.PRICES:
        return os.path.join('.', 'tests', 'data', 'listings.csv' )
    elif feed == Feeds.STATIONS:
        return os.path.join('.', 'tests', 'data', 'stations.jsonl' )
    else:
        raise KeyError(f"Illegal Feeds argument: {feed}")


def mock_rtl_cache(force_refresh=False):
    return os.path.join('.', 'tests', 'data', 'scraped_listings.jsonl' )
    

@pytest.fixture(scope='module', autouse=True)
def mock_feeds():
    ''' Return contrived data files for testing feeds.
    '''
    eddb.feed_cache = mock_feed_cache
    eddb.rtl_cache = mock_rtl_cache
