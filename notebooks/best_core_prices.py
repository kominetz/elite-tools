# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
import pandas as pd
from elitetools import eddb
eddb.load_feeds()

# %% [markdown]
## Best Core Prices Around
# Given one or more origin systems and a radius, finds the top five listings by sell price for each core mineral within (radious) light years of the midpoint of the origin systems.
# If radius is zero, then evaluate listings for all populated systems.
# Listings where sell price is less than 'sell_price_upper_average' are ignored.

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

if radius > 0:
    nearby_system_names = eddb.query_nearby_systems(origin, radius)
else:
    nearby_system_names = eddb.populated_systems_df['name'].to_list()
nearby_systems = pd.DataFrame({
        'id': [eddb.populated_systems[system_name]['id'] for system_name in nearby_system_names],
        'System': nearby_system_names,
        'Distance': [eddb.distance(origin, system_name) for system_name in nearby_system_names],
        })

nearby_stations = eddb.station_details[['id', 'name', 'system_id', 'controlling_minor_faction_id']] \
    .rename(columns={'name': 'Station'}) \
    .merge(nearby_systems, how='inner', left_on='system_id', right_on='id') \
    .merge(eddb.faction_details_df[['id', 'name']], how='left', left_on='controlling_minor_faction_id', right_on='id') \
    .rename(columns={'name': 'Minor Faction'})

core_commodities = eddb.commodity_details[eddb.commodity_details['name'] \
    .isin(eddb.core_minerals)] \
    [['id', 'name', 'sell_price_upper_average']] \
    .rename(columns={'name': 'Commodity'})

nearby_core_listings = eddb.commodity_listings.merge(core_commodities, how='inner', left_on='commodity_id', right_on='id') \
    .merge(nearby_stations, how='inner', left_on='station_id', right_on='id_x') \
    .rename(columns = {'sell_price': 'Sell Price', 'demand': 'Demand', 'demand_bracket': 'Bracket'})
nearby_core_listings = nearby_core_listings[nearby_core_listings['Sell Price'] > nearby_core_listings['sell_price_upper_average']] \
    .assign(rnk = nearby_core_listings.groupby('Commodity')['Sell Price'] \
    .rank(method='first', ascending=False)) \
    .query('rnk <= 5') \
    .sort_values('Sell Price', ascending=False) \
    [['Commodity', 'Sell Price', 'Demand', 'Bracket', 'System', 'Station', 'Minor Faction', 'Distance']]
nearby_core_listings

# %%
nearby_core_listings.to_clipboard(index=False)
