# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
import pandas as pd
import eddb
eddb.load_feeds()
station_details = eddb.load_feed_df(eddb.Feeds.STATIONS)
commodities = eddb.load_feed_df(eddb.Feeds.COMMODITIES)
prices = eddb.load_prices()

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
nearby_systems = pd.DataFrame({
        'id': [eddb.populated_systems[system_name]['id'] for system_name in nearby_system_names],
        'System': nearby_system_names,
        'Distance': [eddb.distance(origin, system_name) for system_name in nearby_system_names],
        })
nearby_stations = station_details[['id', 'name', 'system_id', 'controlling_minor_faction_id']].rename(columns={'name': 'Station'}).merge(nearby_systems, how='inner', left_on='system_id', right_on='id').merge(eddb.faction_details_df[['id', 'name']], how='left', left_on='controlling_minor_faction_id', right_on='id').rename(columns={'name': 'Minor Faction'})
nearby_prices = prices.merge(nearby_stations, how='inner', left_on='station_id', right_on='id_x')
core_commodities = commodities[commodities['name'].isin(eddb.core_minerals)][['id', 'name', 'sell_price_upper_average']].rename(columns={'name': 'Commodity'})
nearby_core_prices = core_commodities.merge(nearby_prices, how='inner', left_on='id', right_on='commodity_id')
#ncp_details = nearby_core_prices[nearby_core_prices['demand_bracket'] > 1]
ncp_details = nearby_core_prices[nearby_core_prices['sell_price'] > nearby_core_prices['sell_price_upper_average']]
ncp_details = ncp_details.rename(columns = {
    'sell_price': 'Sell Price', 
    'demand': 'Demand',
    'demand_bracket': 'Bracket',
})
ncp_details = ncp_details.assign(rnk = ncp_details.groupby('Commodity')['Sell Price'].rank(method='first', ascending=False)).query('rnk <= 5').sort_values('Sell Price', ascending=False)
ncp_details = ncp_details[[
    'Commodity', 
    'Sell Price', 
    'Demand', 
    'Bracket', 
    'System', 
    'Station', 
    'Minor Faction', 
    'Distance']]
ncp_details

# %%
ncp_details.to_clipboard(index=False)