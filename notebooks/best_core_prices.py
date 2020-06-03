# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
import pandas as pd
from elitetools import eddb
eddb.load_feeds()

# %% [markdown]
## Best Core Prices Around
# Given one or more origin systems and a radius, finds the top five listings by sell price for each core mineral within (radious) light years of the midpoint of the origin systems.
# Listings are further restricted to only include high demand markets with a demand of at least 1000t.
# If radius is zero, then evaluate listings for all populated systems.
# Listings where sell price is less than 'sell_price_upper_average' are ignored.

# %%
systems = input("Origin System(s): ") or "Sol"
origin = eddb.center(systems)
origin

# %%
radius = int(input("Radius (ly): ") or 0)
radius

# %%
faction = input("Faction (blank for all): ")
faction

# %%
nearby_core_listings = eddb.best_core_prices(origin, radius, by_faction=faction)
nearby_core_listings.to_clipboard(index=False)
nearby_core_listings
