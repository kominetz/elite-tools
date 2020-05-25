# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
import eddb
eddb.load_feeds()


# %%
systems = input("Origin System(s): ")
origin = eddb.center(systems)
origin


# %%
radius = int(input("Radius (ly): "))
if radius == 0:
    radius = max(eddb.distance(origin, s.strip()) for s in systems.split(","))
radius


# %%
nearby_system_names = eddb.query_nearby_systems(origin, radius)
nearby_system_ids = [ eddb.populated_systems[sys]['id'] for sys in nearby_system_names ]
stations = [station for station in eddb.station_details.values() if station['system_id'] in nearby_system_ids ]
[ station['name'] for station in stations ]

# %%
station_ids = [ station['id'] for station in stations ]
prices = eddb.load_prices()

# %%
nearby_prices = prices[prices['station_id'].isin(station_ids)]
print(len(nearby_prices))

# %%
commodities = eddb.load_feed_df(eddb.Feeds.COMMODITIES)


# %%
commodity_ids = commodities[commodities['name'].isin(eddb.core_minerals)]['id'].values
print(commodity_ids)

# %%
nearby_core_prices = nearby_prices[nearby_prices['commodity_id'].isin(commodity_ids)]
print(len(nearby_core_prices))

# %%
station_details = eddb.load_feed_df(eddb.Feeds.STATIONS)

# %%
nearby_core_prices.iloc[0]

# %%
