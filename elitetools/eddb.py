import itertools
import json
import math
import os.path
import os
import tempfile
import pandas as pd
from datetime import datetime, timezone, timedelta
from enum import Enum

from bs4 import BeautifulSoup
from urllib.request import urlretrieve
from urllib.parse import urlparse
from urllib.request import urlopen


class Feeds(Enum):
    POPULATED_SYSTEMS = 'http://eddb.io/archive/v6/systems_populated.jsonl'
    STATIONS = 'https://eddb.io/archive/v6/stations.jsonl'
    FACTIONS = 'https://eddb.io/archive/v6/factions.jsonl'
    COMMODITIES = 'https://eddb.io/archive/v6/commodities.json'
    MODULES = 'https://eddb.io/archive/v6/modules.json'
    PRICES = 'https://eddb.io/archive/v6/listings.csv'

class Demand(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3

core_minerals = [
    'Low Temperature Diamonds',
    'Alexandrite',
    'Grandidierite',
    'Musgravite',
    'Monazite',
    'Serendibite',
    'Rhodplumsite',
    'Benitoite',
    'Void Opals',
    'Painite',
    'Platinum',
    'Bromellite',
]
# TODO: Move out of main library.
my_engineers = [
    {'system': 'Sirius'},
    {'system': 'Wyrd'},
    {'system': 'Kuk'},
    {'system': 'Alioth'},
    {'system': 'Wolf 397'},
    {'system': 'Leesti'},
    {'system': 'Khun'},
    {'system': 'Laksak'},
    {'system': 'Meene'},
]

homeworld_systems = {
    'Sol': 'Federation', 
    'Shinrarta Dezhra': 'Pilots Federation',
    'Alioth': 'Empire',
    'Achenar': 'Alliance',
}

# TODO: Add Engineer names and upgrade skills with each row being a dict/object.
engineer_systems = sorted([
    'Leesti',
    'Wolf 397',
    'Kuk',
    'Alioth',
    'Khun',
    'Wyrd',
    'Sirius',
    'Laksak',
    'Meene',
    'Muang',
    'Eurybia',
    'Kuwemaki',
    'Achenar',
    'Deciat',
    'Sol',
    'Giryak',
    'Beta-3 Tucani',
    'Arque',
    'Yoru',
    'Shinrarta Dezhra',
    'Los',  # Colonia
    'Tir',  # Colonia
    'Luchtaine',  # Colonia
    'Asura',  # Colonia
    'Shenve',  # Colonia
])

realtime_commodities = [
    {'name': 'Alexandrite', 'type': 'Mineral', 'url': 'https://eddb.io/commodity/349'},
    {'name': 'Benitoite', 'type': 'Mineral', 'url': 'https://eddb.io/commodity/347'},
    {'name': 'Grandidierite', 'type': 'Mineral', 'url': 'https://eddb.io/commodity/348'},
    {'name': 'Low Temperature Diamonds', 'type': 'Mineral', 'url': 'https://eddb.io/commodity/276'},
    {'name': 'Monazite', 'type': 'Mineral', 'url': 'https://eddb.io/commodity/345'},
    {'name': 'Musgravite', 'type': 'Mineral', 'url': 'https://eddb.io/commodity/346'},
    {'name': 'Painite', 'type': 'Mineral', 'url': 'https://eddb.io/commodity/83'},
    {'name': 'Platinum', 'type': 'Metal', 'url': 'https://eddb.io/commodity/46'},
    {'name': 'Rhodplumsite', 'type': 'Mineral', 'url': 'https://eddb.io/commodity/343'},
    {'name': 'Serendibite', 'type': 'Mineral', 'url': 'https://eddb.io/commodity/344'},
    {'name': 'Tritium', 'type': 'Chemical', 'url': 'https://eddb.io/commodity/362'},
    {'name': 'Void Opals', 'type': 'Mineral', 'url': 'https://eddb.io/commodity/350'},
]

SYSTEM_INFLUENCE_RANGE = 20

et_temp_path = os.path.join(tempfile.gettempdir(), 'elite-tools')
os.makedirs(et_temp_path, exist_ok=True)


### FEEDS

commodity_details: pd.DataFrame = None
commodity_listings_eod: pd.DataFrame = None
commodity_listings_rt: pd.DataFrame = None
faction_details: pd.DataFrame = None
populated_systems: pd.DataFrame = None
station_details: pd.DataFrame = None


def scrape_commodity(commodity):
    ''' Given a commodity's name and EDDB URL, extract best sell price listings and return as a list of dicts.
    '''
    listings = []
    with urlopen(commodity['url']) as p:
        page = BeautifulSoup(p, 'html.parser')
    max_sell = page.find(id='table-stations-max-sell')
    for row in max_sell.find_all('tr'):
        fields = row.find_all('td')
        if len(fields) != 7:
            continue  # discard header and malformed rows
        time_fields = fields[6].find_all('span')
        listings.append({
            'commodity_name': commodity['name'],
            'commodity_type': commodity['type'],
            'station_name': fields[0].find('a').get_text(),
            'system_name': fields[1].find('a').get_text(),
            'sell_price': int(fields[2].find('span').get_text().replace(',', '')),
            'demand': int(fields[4].find('span').get_text().replace(',', '')),
            'landing_pad': fields[5].find('span').get_text(),
            'freshness': time_fields[1].get_text(),
        })
    print("%s: %d listings scraped." % (commodity['name'], len(listings)))
    return listings


def load_rt_listings():

    listings = []
    for commodity in realtime_commodities:
        listings.extend(scrape_commodity(commodity))
    return listings


def load_commodity_listings(force_refresh=False):
    ''' specialized feed loader for listings which is the only CSV feed to process
        Looks for a previously-downloaded file and uses it if it's newer than the 
        last tick or downloads regardless if force_refresh is True.
    '''
    cache_filename = urlparse(Feeds.PRICES.value).path[1:].replace("/", "-")
    system_data_path = os.path.join(et_temp_path, cache_filename)
    if os.path.exists(system_data_path) and not force_refresh and fresh_feed(system_data_path):
        print(f'# Found "{system_data_path}".')
    else:
        print(f'# Downloading "{system_data_path}".')
        urlretrieve(Feeds.PRICES.value, system_data_path)
    feed_data = pd.read_csv(system_data_path)
    print(f"# {Feeds.PRICES} records loaded: ", len(feed_data))
    return feed_data


def load_feed(feed, force_refresh=False):
    ''' Given an EDDB JSON data feed, download it and return it as a DataFrame.
        Looks for a previously-downloaded file and uses it if it's newer than the 
        last tick or downloads regardless if force_refresh is True.
    '''
    cache_filename = urlparse(feed.value).path[1:].replace("/", "-")
    system_data_path = os.path.join(et_temp_path, cache_filename)
    if os.path.exists(system_data_path) and not force_refresh and fresh_feed(system_data_path):
        print(f'# Found "{system_data_path}".')
    else:
        print(f'# Downloading "{system_data_path}".')
        urlretrieve(feed.value, system_data_path)

    feed_data = pd.read_json(system_data_path, lines=(feed != Feeds.COMMODITIES))
    print(f"# {feed} records loaded: ", len(feed_data))
    return feed_data


def load_feeds(force_refresh=False):
    ''' Load all feeds from EDDB. Refresh standard feeds and scrapes if stored files
        are older than the refresh policies or if force refresh is specified.
    '''
    global commodity_details, commodity_listings_eod, commodity_listings_rt, faction_details, populated_systems, station_details

    commodity_details = load_feed(Feeds.COMMODITIES, force_refresh)
    commodity_listings_eod = load_commodity_listings()
    faction_details = load_feed(Feeds.FACTIONS, force_refresh)
    faction_details = faction_details.assign(name_index = faction_details['name'].str.lower()).set_index('name_index')
    populated_systems = load_feed(Feeds.POPULATED_SYSTEMS, force_refresh)
    populated_systems = populated_systems.assign(name_index = populated_systems['name'].str.lower()).set_index('name_index')
    station_details = load_feed(Feeds.STATIONS, force_refresh)
    commodity_listings_rt = load_rt_listings()


def fresh_feed(filepath):
    ''' Given a filepath, report true if the file is newer than the estimated last tick.
    ''' 
    ft = datetime.fromtimestamp(os.stat(filepath).st_mtime).astimezone(timezone.utc)
    tt = datetime.now(timezone.utc).replace(hour=15, minute=0, second=0, microsecond=0)
    if tt > datetime.now(timezone.utc):
        tt -= timedelta(days=1)
    return ft > tt


### UTILITY


# Given either two systems names or two system objects, calcuates the distance (ly) between them.
def distance(origin, destination):
    o = find_system_by_name(origin) if isinstance(origin, str) else origin
    d = find_system_by_name(destination) if isinstance(destination, str) else destination
    return round(((d['x'] - o['x']) ** 2 + (d['y'] - o['y']) ** 2 + (d['z'] - o['z']) ** 2) ** 0.5, 1)


# Given an ordered list of systems (aka route), calculate the cumulative distance following the route.
def route_len(route, print_route=False):
    length = 0
    last_system = route[0]
    for next_system in route:
        dist = distance(last_system, next_system)
        length += dist
        if print_route:
            print("%-24s %5d ly  %4d ly" % (next_system, dist, length))
        last_system = next_system
    return length


# Given one or more systems, finds the average non-weighted central position.
def center(systems):
    s_list = [ sn.strip() for sn in systems.split(',') ] if isinstance(systems, str) else systems
    sum_x, sum_y, sum_z = 0, 0, 0
    for s in s_list:
        s_obj = find_system_by_name(s) if isinstance(s, str) else s
        sum_x += s_obj['x']
        sum_y += s_obj['y']
        sum_z += s_obj['z']
    n = len(s_list)
    return {'name': 'Average Position', 'x': sum_x / n, 'y': sum_y / n, 'z': sum_z / n, 'systems': systems}


# Given one or more systems, finds the average position weighted by log10(population).
def population_center(systems):
    s_list = [ sn.strip() for sn in systems.split(',') ] if isinstance(systems, str) else systems
    sum_x, sum_y, sum_z, sum_p = 0, 0, 0, 0
    for s in s_list:
        s_obj = find_system_by_name(s) if isinstance(s, str) else s
        log_pop = math.log10(s_obj['population'])
        sum_x += s_obj['x'] * log_pop
        sum_y += s_obj['y'] * log_pop
        sum_z += s_obj['z'] * log_pop
        sum_p += log_pop
    return {'name': 'Average Populated-Weighted Position', 'x': sum_x / sum_p, 'y': sum_y / sum_p, 'z': sum_z / sum_p, 'systems': systems}


# Given a route (one or more systems), creates a displayable dataframe with leg and cumulative distances from starting system.
def route_to_dataframe(route):
    route_table = []
    length = 0
    last_system = route[0]
    for next_system in route:
        dist = distance(last_system, next_system)
        length += dist
        route_table.append([next_system, dist, length])
        last_system = next_system
    return pd.DataFrame(route_table, columns=['System', 'Leg (ly)', 'Route (ly)'])


# Brute-force calculation of shortest route among waypoints with origin prepended and destination appended if either are provided
def best_route(waypoints, origin, destination, print_choices=False):
    shortest_route = []
    shortest_length = -1
    routes = itertools.permutations(waypoints)
    for waypoints_route in routes:
        route = list(waypoints_route)
        if origin:
            route.insert(0, origin)
        if destination:
            route.append(destination)
        length = route_len(list(route))
        if shortest_length < 0 or length < shortest_length:
            shortest_route = route
            shortest_length = length
            if print_choices:
                print("Picked:  %5d ly: %s" % (shortest_length, shortest_route))
        elif print_choices:
            print("Skipped: %5d ly: %s" % (length, route))
    return shortest_route


### SYSTEMS


def find_system_by_name(system_name = ""):
    ''' Given a valid system name, returns the system as dict.
    '''
    return populated_systems.loc[system_name.lower()]


def query_systems_by_name(system_names):
    ''' Given zero or more valid system names, returns the systems as dicts in a dict keyed by name.
    ''' 
    names = [n.lower() for n in ([s.strip() for s in system_names.split(',')] if isinstance(system_names, str) else system_names)]
    return populated_systems.loc[names].set_index('name', drop=False).T.to_dict()


def query_nearby_systems(origin, radius):
    ''' Given a system and a radius, find all systems within radius including the origin systems
    '''
    if type(origin) == list:
        return set([nearby_system for s in origin for nearby_system in query_nearby_systems(s, radius)])
    else: 
        return [s for s in populated_systems['name'].values if distance(origin, s) <= radius]


def query_systems_by_faction(faction):
    return [s for s in populated_systems['name'].values if system_has_faction(s, faction)]


def system_has_faction(system, faction):
    ''' Tests if a faction controls or is present on a given system.
    '''
    s = find_system_by_name(system) if isinstance(system, str) else system
    f = find_faction_by_name(faction) if isinstance(faction, str) else faction
    return f['id'] in [mpf['minor_faction_id'] for mpf in s['minor_faction_presences']]


### REPORTS ###

# Given a list of systems, create a displayble dataframe of general information about each system.
def system_survey_report(systems, origin='Sol'):
    system_summaries = []
    for n in systems:
        s = find_system_by_name(n)
        d = distance(origin, n)
        system_summaries.append([s['name'], d, s['population'], s['primary_economy'], s['reserve_type']])
    return pd.DataFrame(system_summaries, columns=['Name', 'Distance', 'Population', 'Primary Economy', 'Reserve Level'])


# Given a list of systems, create a displayble dataframe of faction-related information about each system.
def system_faction_report(systems, faction="The Order of Mobius", origin='Azrael'):
    system_summaries = []
    categories = ['Insurgency', 'Control', 'Presence', 'Player Control', 'Player Presence', 'NPC']
    for a_system in systems:
        s = find_system_by_name(a_system) if isinstance(a_system, str) else a_system
        d = distance(origin, a_system)
        cf_name = s['controlling_minor_faction']
        pc_fac = [f for f in filter_player_factions(minor_faction_names(s['name']))]
        states = [x['name'] for x in s['states']]
        cf_state = present_faction_state(s, cf_name)
        cf_inf = cf_state['influence']
        cf_hap = cf_state['happiness_id']
        if cf_name == "The Order of Mobius":
            fac_pri = 0 if len(pc_fac) > 1 else 1
        elif faction in pc_fac:
            fac_pri = 2
        elif cf_name in pc_fac:
            fac_pri = 3
        elif len(pc_fac) > 0:
            fac_pri = 4
        else:
            fac_pri = 5
        system_summaries.append(                  [fac_pri,    categories[fac_pri], s['name'], d,          s['population'], s['primary_economy'], ", ".join(states), cf_hap,      s['security'],    cf_name,               cf_inf,      s['government'], s['allegiance'], ", ".join(pc_fac)])
    return pd.DataFrame(system_summaries, columns=['Priority', 'Category',          'Name',    'Distance', 'Population',    'Primary Economy',    'States',          'Happiness', 'Security Level', 'Controlling Faction', 'Influence', 'Government',    'Allegiance',    'Player Factions Present'])


### FACTIONS


def find_faction_by_name(faction_name):
    return faction_details.loc[faction_name.lower()]


def player_faction_controlled(systems):
    ''' Given a list of systems, returns only any controlling player factions of those systems.
    '''
    return filter_player_factions(set([find_system_by_name(s)['controlling_minor_faction'] for s in systems]))


def filter_player_factions(factions):
    ''' Given a list of factions, returns only the player factions.
    '''
    return set([n for n in factions if find_faction_by_name(n)['is_player_faction']])


def faction_presences(system):
    ''' Given a system name or object, returns the faction presence information (merged with faction_details)
    '''
    s = find_system_by_name(system) if isinstance(system, str) else system
    return pd.DataFrame(s['minor_faction_presences']).merge(faction_details, how='left', left_on='minor_faction_id', right_on='id')


def minor_faction_ids(system):
    ''' Returns faction ids for all factions present in given system.
    '''
    return set(faction_presences(system)['id'].values)


def minor_faction_names(system):
    ''' Returns faction names for all factions present in given system.
    '''
    return set(faction_presences(system)['name'].values)


def present_faction_state(system, faction):
    ''' Returns the faction state object for a faction in a system or None if the faction is not present in that system.
    '''
    s = find_system_by_name(system) if isinstance(system, str) else system
    f_id = (find_faction_by_name(faction) if isinstance(faction, str) else faction)['id']
    for f in s['minor_faction_presences']:
        if f_id == f['minor_faction_id']:
            return f
    return None


def faction_home_system(faction):
    ''' Given a faction name, return the system object of the faction's home system.
    '''
    system_id = faction_details[faction_details['name'] == faction]['home_system_id'].iloc[0]
    return populated_systems[populated_systems['id'] == system_id].iloc[0].to_dict()


##
#
# COMMODITIES AND LISTINGS
#
##

def best_core_prices(origin='Sol', radius=0, by_faction='', top_count=5, by_core_mineral='', min_demand=1000, min_demand_level=Demand.MEDIUM):
    if radius > 0:
        nearby_system_names = query_nearby_systems(origin, radius)
    else:
        # radius = max(eddb.distance(origin, s.strip()) for s in systems.split(","))
        nearby_system_names = populated_systems['name'].to_list()

    nearby_systems = pd.DataFrame({
            'id': [find_system_by_name(system_name)['id'] for system_name in nearby_system_names],
            'System': nearby_system_names,
            'Distance': [distance(origin, system_name) for system_name in nearby_system_names],
            })

    nearby_stations = station_details[['id', 'name', 'system_id', 'controlling_minor_faction_id']] \
        .rename(columns={'name': 'Station'}) \
        .merge(nearby_systems, how='inner', left_on='system_id', right_on='id') \
        .merge(faction_details[['id', 'name']], how='left', left_on='controlling_minor_faction_id', right_on='id') \
        .rename(columns={'name': 'Minor Faction'})
    if by_faction:
        nearby_stations = nearby_stations[nearby_stations['Minor Faction'] == by_faction]

    core_commodities = commodity_details[commodity_details['name'] \
        .isin([cm.strip() for cm in by_core_mineral.split(',')] if by_core_mineral else core_minerals)] \
        [['id', 'name', 'sell_price_upper_average']] \
        .rename(columns={'name': 'Commodity'})

    nearby_core_listings = commodity_listings_eod.merge(core_commodities, how='inner', left_on='commodity_id', right_on='id') \
        .merge(nearby_stations, how='inner', left_on='station_id', right_on='id_x') \
        .rename(columns = {'sell_price': 'Sell Price', 'demand': 'Demand', 'demand_bracket': 'Level'})
    nearby_core_listings = nearby_core_listings[nearby_core_listings['Sell Price'] > nearby_core_listings['sell_price_upper_average']] \
        .query(f'Level >= {min_demand_level.value} and Demand >= {min_demand}') \
        .assign(rnk = nearby_core_listings.groupby('Commodity')['Sell Price'] \
        .rank(method='first', ascending=False)) \
        .query(f'rnk <= {top_count}') \
        .sort_values('Sell Price', ascending=False) \
        .reset_index() \
        [['Commodity', 'Sell Price', 'Demand', 'Level', 'System', 'Station', 'Minor Faction', 'Distance']]
    nearby_core_listings['Level'].replace({1: 'Low', 2: 'Medium', 3: "High"}, inplace=True)
    return nearby_core_listings
