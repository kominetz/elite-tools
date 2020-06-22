# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
import pandas as pd
from elitetools import eddb
eddb.load_feeds()


# %%
systems = 'Azrael'  # input("Origin System(s): ") or "Sol"
origin = eddb.center(systems)
radius = 200  # int(input("Radius (ly): ") or 0)
faction = ''  # input("Faction (blank for all): ")
nearby_rt_listings = eddb.best_rt_listings(origin, radius, top_count=3, by_commodity=eddb.core_minerals, min_demand=100)
nearby_rt_listings

# %%
