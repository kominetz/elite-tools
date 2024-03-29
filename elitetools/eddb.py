import itertools
import json
import logging
import math
import os
import os.path
import tempfile
from datetime import datetime, timedelta, timezone
from enum import Enum
from time import sleep
from urllib.parse import urlparse
from urllib.request import urlopen, urlretrieve

import pandas as pd
from bs4 import BeautifulSoup
import ssl

class Feeds(Enum):
    POPULATED_SYSTEMS = 'https://eddb.io/archive/v6/systems_populated.jsonl'
    STATIONS = 'https://eddb.io/archive/v6/stations.jsonl'
    FACTIONS = 'https://eddb.io/archive/v6/factions.jsonl'
    COMMODITIES = 'https://eddb.io/archive/v6/commodities.json'
    MODULES = 'https://eddb.io/archive/v6/modules.json'
    PRICES = 'https://eddb.io/archive/v6/listings.csv'

class Demand(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3

MINING_RATE_CORE_HOTSPOT = 95          # 70/h primary, 49/hr secondary (half weight)
MINING_RATE_LASER_NOTSPOT = 115
MINING_RATE_LASER_LTD_HOTSPOT = 125
MINING_RATE_LASER_HOTSPOT = 150        # 111/h primary, 81/hr secondary (half weight)

minerals = [
    {'name': 'Alexandrite', 'type': 'Mineral', 'url': 'https://eddb.io/commodity/349', 'mining_rate': MINING_RATE_CORE_HOTSPOT},
    {'name': 'Benitoite', 'type': 'Mineral', 'url': 'https://eddb.io/commodity/347', 'mining_rate': MINING_RATE_CORE_HOTSPOT},
    {'name': 'Bromellite', 'type': 'Mineral', 'url': 'https://eddb.io/commodity/274', 'mining_rate': MINING_RATE_CORE_HOTSPOT},
    {'name': 'Gold', 'type': 'Metal', 'url': 'https://eddb.io/commodity/42', 'mining_rate': MINING_RATE_LASER_NOTSPOT},
    {'name': 'Grandidierite', 'type': 'Mineral', 'url': 'https://eddb.io/commodity/348', 'mining_rate': MINING_RATE_CORE_HOTSPOT},
    {'name': 'Low Temperature Diamonds', 'type': 'Mineral', 'url': 'https://eddb.io/commodity/276', 'mining_rate': MINING_RATE_LASER_LTD_HOTSPOT},
    {'name': 'Monazite', 'type': 'Mineral', 'url': 'https://eddb.io/commodity/345', 'mining_rate': MINING_RATE_CORE_HOTSPOT},
    {'name': 'Musgravite', 'type': 'Mineral', 'url': 'https://eddb.io/commodity/346', 'mining_rate': MINING_RATE_CORE_HOTSPOT},
    {'name': 'Osmium', 'type': 'Metal', 'url': 'https://eddb.io/commodity/97', 'mining_rate': MINING_RATE_LASER_NOTSPOT},
    {'name': 'Painite', 'type': 'Mineral', 'url': 'https://eddb.io/commodity/83', 'mining_rate': MINING_RATE_LASER_HOTSPOT},
    {'name': 'Palladium', 'type': 'Metal', 'url': 'https://eddb.io/commodity/45', 'mining_rate': MINING_RATE_LASER_NOTSPOT},
    {'name': 'Platinum', 'type': 'Metal', 'url': 'https://eddb.io/commodity/46', 'mining_rate': MINING_RATE_LASER_HOTSPOT},
    {'name': 'Rhodplumsite', 'type': 'Mineral', 'url': 'https://eddb.io/commodity/343', 'mining_rate': MINING_RATE_CORE_HOTSPOT},
    {'name': 'Samarium', 'type': 'Metal', 'url': 'https://eddb.io/commodity/275', 'mining_rate': MINING_RATE_LASER_NOTSPOT},
    {'name': 'Serendibite', 'type': 'Mineral', 'url': 'https://eddb.io/commodity/344', 'mining_rate': MINING_RATE_CORE_HOTSPOT},
    {'name': 'Silver', 'type': 'Metal', 'url': 'https://eddb.io/commodity/47', 'mining_rate': MINING_RATE_CORE_HOTSPOT},
    {'name': 'Tritium', 'type': 'Chemical', 'url': 'https://eddb.io/commodity/362', 'mining_rate': MINING_RATE_CORE_HOTSPOT},
    {'name': 'Void Opals', 'type': 'Mineral', 'url': 'https://eddb.io/commodity/350', 'mining_rate': MINING_RATE_CORE_HOTSPOT},
]

minerals_df = pd.DataFrame(minerals)

core_minerals = [
    'Alexandrite',
    'Benitoite',
    'Bromellite',
    'Grandidierite',
    'Low Temperature Diamonds',
    'Monazite',
    'Musgravite',
    'Painite',
    'Platinum',
    'Rhodplumsite',
    'Serendibite',
    'Void Opals',
]

core_only_minerals = [
    'Alexandrite',
    'Benitoite',
    'Grandidierite',
    'Monazite',
    'Musgravite',
    'Rhodplumsite',
    'Serendibite',
    'Void Opals',
]

top_core_minerals = [
    'Alexandrite',
    'Grandidierite',
    'Low Temperature Diamonds',
    'Monazite',
    'Musgravite',
    'Rhodplumsite',
    'Serendibite',
    'Void Opals',
]

top_laser_minerals = [
    'Platinum',
    'Painite',
    'Tritium',
    'Palladium',
    'Gold',
    'Osmium',
    'Silver',
]

top_minerals = top_core_minerals + top_laser_minerals

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

CORE_ENGINEERS = 'Alioth, Muang, Shenve, Sol, Leesti, Khun, Deciat, Kuwemaki, Giryak, Laksak, Eurybia, Shinrarta Dezhra, Sirius, Arque, Meene, Kuk, Wyrd, Beta-3 Tucani, Achenar, Wolf 397, Yoru'
ALL_ENGINEERS = 'Alioth, Muang, Shenve, Sol, Leesti, Khun, Los, Deciat, Kuwemaki, Giryak, Laksak, Eurybia, Shinrarta Dezhra, Sirius, Tir, Luchtaine, Asura, Arque, Meene, Kuk, Wyrd, Beta-3 Tucani, Achenar, Wolf 397, Yoru'

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
    populated_systems = populated_systems[populated_systems['population'] > 0].assign(name_index = populated_systems['name'].str.lower()).set_index('name_index')
    station_details = load_feed(Feeds.STATIONS, force_refresh)
    commodity_listings_rt = load_rt_listings(force_refresh)

    # Calculate or update performance benchmark
    perf_data = commodity_listings_rt[['commodity_name','performance']]
    perf_bench = {}
    for mineral_name in minerals_df['name'].to_list():
        mineral_listings = perf_data.query(f"commodity_name == '{mineral_name}'")
        perf_bench[mineral_name] = mineral_listings['performance'].mean()
    minerals_df['benchmark'] = minerals_df['name'].map(perf_bench)


def fresh_feed(filepath):
    ''' Given a filepath, report true if the file is newer than the estimated last tick.
    ''' 
    ft = datetime.fromtimestamp(os.stat(filepath).st_mtime).astimezone(timezone.utc)
    tt = datetime.now(timezone.utc).replace(hour=15, minute=0, second=0, microsecond=0)
    if tt > datetime.now(timezone.utc):
        tt -= timedelta(days=1)
    return ft > tt


def fresh_scrape(filepath):
    ''' Given a filepath, report true if the file is no more than 1 hour old.
    ''' 
    refresh_after = datetime.fromtimestamp(os.stat(filepath).st_mtime) + timedelta(hours=1)
    return refresh_after > datetime.now()


def load_rt_listings(force_refresh=False):
    ''' Specialized loader for real-time listings scraped from individual EDDB commodity
        pages. If there is a saved file no older than one hour and force_refresh is false,
        loads listings from file. Otherwise scrapes a list of commodity pages, saves
        them to a cache file, and returns a data frame of the listings.
    '''
    rtl_path = rtl_cache(force_refresh)
    rtl_data = pd.read_json(rtl_path, lines=True)
    logging.info(f"# Real-time listing records loaded: ", len(rtl_data))
    return pd.DataFrame(rtl_data)


def rtl_cache(force_refresh=False):
    file_path = os.path.join(et_temp_path, 'scraped_listings.jsonl')
    if os.path.exists(file_path) and not force_refresh and fresh_scrape(file_path):
        logging.debug(f'# Found "{file_path}".')
    else:
        logging.debug(f'# Scraping "{file_path}".')
        listings = []
        for commodity in minerals:
            listings.extend(scrape_commodity(commodity))
        with open(file_path, 'w') as rtl_file:
            for l in listings:
                json.dump(l, rtl_file)
                rtl_file.write('\n')
    return file_path


def load_commodity_listings(force_refresh=False):
    ''' specialized feed loader for listings which is the only CSV feed to process
        Looks for a previously-downloaded file and uses it if it's newer than the 
        last tick or downloads regardless if force_refresh is True.
    '''
    cache_filename = urlparse(Feeds.PRICES.value).path[1:].replace("/", "-")
    system_data_path = os.path.join(et_temp_path, cache_filename)
    if os.path.exists(system_data_path) and not force_refresh and fresh_feed(system_data_path):
        logging.debug(f'# Found "{system_data_path}".')
    else:
        logging.debug(f'# Downloading "{system_data_path}".')
        urlretrieve(Feeds.PRICES.value, system_data_path)
    feed_data = pd.read_csv(system_data_path)
    logging.info(f"# {Feeds.PRICES} records loaded: ", len(feed_data))
    return feed_data


def scrape_commodity(commodity, direction='sell'):
    ''' Given a commodity's name and EDDB URL, extract best sell price listings and return as a list of dicts.
    '''
    listings = []
    page = None
    for retry_period in [1, 5, 10]:
        try:
            with urlopen(commodity['url']) as p:
                page = BeautifulSoup(p, 'html.parser')
                break
        except Exception as e:
            logging.debug(e)
            logging.warning(f"Retrying {commodity['name']} page after {retry_period} sec.")
            sleep(retry_period)

    if page is None:
        raise Exception(f"Cannot load page for commodity {commodity['name']}.")           

    if direction == 'sell':
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
                'performance': int(fields[3].find('span').get_text().replace('%', ''))/100,
                'demand': int(fields[4].find('span').get_text().replace(',', '')),
                'landing_pad': fields[5].find('span').get_text(),
                'as_of_days': float(time_fields[0].get_text().strip("\{\}")) / 86400.0,
                'as_of_text': time_fields[1].get_text(),
            })
        logging.info("# %s: %d sell listings scraped." % (commodity['name'], len(listings)))
    else:
        max_buy = page.find(id='table-stations-max-buy')
        for row in max_buy.find_all('tr'):
            fields = row.find_all('td')
            if len(fields) != 7:
                continue  # discard header and malformed rows
            time_fields = fields[6].find_all('span')
            listings.append({
                'commodity_name': commodity['name'],
                'commodity_type': commodity['type'],
                'station_name': fields[0].find('a').get_text(),
                'system_name': fields[1].find('a').get_text(),
                'buy_price': int(fields[2].find('span').get_text().replace(',', '')),
                'performance': int(fields[3].find('span').get_text().replace('%', ''))/100,
                'supply': int(fields[4].find('span').get_text().replace(',', '')),
                'landing_pad': fields[5].find('span').get_text(),
                'as_of_days': float(time_fields[0].get_text().strip("\{\}")) / 86400.0,
                'as_of_text': time_fields[1].get_text(),
            })
        logging.info("# %s: %d buy listings scraped." % (commodity['name'], len(listings)))
    return listings



def load_feed(feed: Feeds, force_refresh=False):
    ''' Given an EDDB JSON data feed, download it and return it as a DataFrame.
        Looks for a previously-downloaded file and uses it if it's newer than the 
        last tick or downloads regardless if force_refresh is True.
    '''
    feed_path = feed_cache(feed, force_refresh)

    feed_data = pd.read_json(feed_path, lines=(feed != Feeds.COMMODITIES))
    logging.info(f"# {feed} records loaded: ", len(feed_data))
    return feed_data


def feed_cache(feed: Feeds, force_refresh=False):
    ''' Given an EDDB feed, download it if necessary and return the file location.
    '''
    ssl._create_default_https_context = ssl._create_unverified_context
    cache_filename = urlparse(feed.value).path[1:].replace("/", "-")
    file_path = os.path.join(et_temp_path, cache_filename)
    if os.path.exists(file_path) and not force_refresh and fresh_feed(file_path):
        logging.debug(f'# Found "{file_path}".')
    else:
        logging.debug(f'# Downloading "{file_path}".')
        urlretrieve(feed.value, file_path)
    return file_path    


### UTILITY


# Given either two systems names or two system objects, calcuates the distance (ly) between them.
def distance(origin, destination):
    o = find_system_by_name(origin) if isinstance(origin, str) else origin
    d = find_system_by_name(destination) if isinstance(destination, str) else destination
    return round(((d['x'] - o['x']) ** 2 + (d['y'] - o['y']) ** 2 + (d['z'] - o['z']) ** 2) ** 0.5, 1)


# Given an ordered list of systems (aka route), calculate the cumulative distance following the route.
def route_len(route):
    length = 0
    last_system = route[0]
    for next_system in route:
        dist = distance(last_system, next_system)
        length += dist
        logging.debug("%-24s %5d ly  %4d ly" % (next_system, dist, length))
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
    return {'name': 'Average Position', 'x': sum_x / n, 'y': sum_y / n, 'z': sum_z / n}


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
def best_route(waypoints, origin, destination):
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
            logging.debug("Picked:  %5d ly: %s" % (shortest_length, shortest_route))
        else:
            logging.debug("Skipped: %5d ly: %s" % (length, route))
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
    ''' Given one or more origin systems and a radius, return system position objects within radius including the origin systems
    '''
    if type(origin) == list:
        return set([nearby_system for s in origin for nearby_system in query_nearby_systems(s, radius)])
    else: 
        return [s['name'] for s in populated_systems[['name', 'x', 'y', 'z']].to_dict('records') if distance(origin, s) <= radius]


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
    categories = ['Insurgency', 'Control', 'Presence', 'Player Control', 'Player Insurgency', 'Single Player Presence', 'Multiplayer Presence', 'NPC']
    for a_system in systems:
        s = find_system_by_name(a_system) if isinstance(a_system, str) else a_system
        d = distance(origin, a_system)
        cf_name = s['controlling_minor_faction']
        pc_fac = [f for f in filter_player_factions(minor_faction_names(s['name']))]
        states = [x['name'] for x in s['states']]
        cf_state = present_faction_state(s, cf_name)
        cf_inf = cf_state['influence']
        cf_hap = cf_state['happiness_id']
        if cf_name == faction:
            fac_pri = 0 if len(pc_fac) > 1 else 1
        elif faction in pc_fac:
            fac_pri = 2
        elif cf_name in pc_fac:
            fac_pri = 3 if len(pc_fac) == 1 else 4
        elif len(pc_fac) > 0:
            fac_pri = 5 if len(pc_fac) == 1 else 6
        else:
            fac_pri = 7
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

def top_price_mineral_listings(origin='Sol', radius=1000, top_count=10, commodity_count=5, by_commodity=[], min_demand=1000, as_of_days=2.0, large_pad_only=False):
    """ Find top real-time commodity listings by price.
    """
    query_filter = f'demand >= {min_demand} and as_of_days <= {as_of_days} and landing_pad == "L"' if large_pad_only else f'demand >= {min_demand} and as_of_days <= {as_of_days}'
    target_rt_listings = commodity_listings_rt[commodity_listings_rt['commodity_name'].isin(by_commodity)] if len(by_commodity) > 0 else commodity_listings_rt
    nearby_system_names = query_nearby_systems(origin, radius) if radius > 0 else target_rt_listings['system_name'].values
    nearby_systems = pd.DataFrame({
        'system_name': nearby_system_names,
        'Distance': [distance(origin, system_name) for system_name in nearby_system_names],
    })
    nearby_rt_listings = target_rt_listings.merge(nearby_systems, on="system_name")
    filtered_listings = nearby_rt_listings.query(query_filter).sort_values('sell_price', ascending=False)
    ranked_rt_listings = filtered_listings \
        .assign(rnk = nearby_rt_listings.groupby('commodity_name')['sell_price'] \
        .rank(method='first', ascending=False)) \
        .query(f'rnk <= {commodity_count}') \
        .drop_duplicates() \
        .reset_index() \
        [:top_count][['commodity_name', 'sell_price', 'performance', 'demand', 'as_of_text', 'Distance', 'system_name', 'station_name', 'landing_pad']] \
        .rename(columns={'commodity_name': 'Commodity', 'system_name': 'System', 'station_name': 'Station', 'sell_price': 'Sell Price', 'performance': 'Perf', 'demand': 'Demand', 'as_of_text': 'As Of', 'landing_pad': 'Pad'})

    return ranked_rt_listings \
        .style.format({'Perf':'{:+.2f}', 'Distance':'{:.1f} LY'}) \
        .set_properties(subset=['Commodity', 'System', 'Station'], **{'text-align': 'left'}) \
        .set_table_styles([dict(selector = 'th', props=[('text-align', 'left')])])


def top_perf_mineral_listings(origin='Sol', radius=1000, top_count=10, commodity_count=5, by_commodity=[], min_perf=0.0, min_demand=1000, as_of_days=2.0, large_pad_only=False):
    """ Find top real-time commodity listings by price performance (galactic average benchmark).
    """
    query_filter = f'performance >= {min_perf} and demand >= {min_demand} and as_of_days <= {as_of_days} and landing_pad == "L"' if large_pad_only else f'performance >= {min_perf} and demand >= {min_demand} and as_of_days <= {as_of_days}'
    target_rt_listings = commodity_listings_rt[commodity_listings_rt['commodity_name'].isin(by_commodity)] if len(by_commodity) > 0 else commodity_listings_rt
    nearby_system_names = query_nearby_systems(origin, radius) if radius > 0 else target_rt_listings['system_name'].values
    nearby_systems = pd.DataFrame({
        'system_name': nearby_system_names,
        'Distance': [distance(origin, system_name) for system_name in nearby_system_names],
    })
    nearby_rt_listings = target_rt_listings.merge(nearby_systems, on="system_name").merge(minerals_df[['name', 'benchmark']], left_on="commodity_name", right_on="name")
    nearby_rt_listings['active'] = nearby_rt_listings['performance'] - nearby_rt_listings['benchmark']
    filtered_listings = nearby_rt_listings.query(query_filter).sort_values('active', ascending=False)
    ranked_listings = filtered_listings \
        .assign(rnk = filtered_listings.groupby('commodity_name')['active'] \
        .rank(method='first', ascending=False)) \
        .query(f'rnk <= {commodity_count}') \
        .drop_duplicates() \
        .reset_index() \
        [:top_count][['commodity_name', 'sell_price', 'active', 'performance', 'benchmark', 'demand', 'as_of_text', 'Distance', 'system_name', 'station_name', 'landing_pad']] \
        .rename(columns={'commodity_name': 'Commodity', 'system_name': 'System', 'station_name': 'Station', 'sell_price': 'Sell Price', 'performance': 'Perf', 'active': 'Active', 'benchmark': 'Bench', 'demand': 'Demand', 'as_of_text': 'As Of', 'landing_pad': 'Pad'})

    return ranked_listings \
        .style.format({'Active':'{:+.2f}', 'Perf':'{:+.2f}', 'Bench':'{:+.2f}', 'Distance':'{:.1f} LY'}) \
        .set_properties(subset=['Commodity', 'System', 'Station'], **{'text-align': 'left'}) \
        .set_table_styles([dict(selector = 'th', props=[('text-align', 'left')])])


def top_score_mineral_listings(origin='Sol', radius=1000, top_count=10, commodity_count=5, by_commodity=[], min_score=0.0, min_demand=1000, as_of_days=2.0, large_pad_only=False):
    """ Find top real-time commodity listings by score accounting for mining rates (core v. laser).
    """
    query_filter = f'landing_pad == "L" and demand >= {min_demand} and as_of_days <= {as_of_days}' if large_pad_only else f'demand >= {min_demand} and as_of_days <= {as_of_days}'
    target_rt_listings = commodity_listings_rt[commodity_listings_rt['commodity_name'].isin(by_commodity)] if len(by_commodity) > 0 else commodity_listings_rt
    nearby_system_names = query_nearby_systems(origin, radius) if radius > 0 else target_rt_listings['system_name'].values
    nearby_systems = pd.DataFrame({
        'system_name': nearby_system_names,
        'Distance': [distance(origin, system_name) for system_name in nearby_system_names],
    })
    nearby_listings = target_rt_listings.merge(nearby_systems, on="system_name")
    filtered_listings = nearby_listings.query(query_filter)
    scored_listings = filtered_listings \
        .merge(minerals_df[['name', 'mining_rate']], left_on='commodity_name', right_on='name') \
        .assign(Score = lambda l: round(l['sell_price'] * l['mining_rate'] / 1000000)) \
        .query(f'Score >= {min_score}') \
        .sort_values('Score', ascending=False)
    ranked_listings = scored_listings \
        .assign(rnk = scored_listings.groupby('commodity_name')['Score'] \
        .rank(method='first', ascending=False)) \
        .query(f'rnk <= {commodity_count}') \
        .drop_duplicates() \
        .reset_index() \
        [:top_count][['commodity_name', 'sell_price', 'performance', 'demand', 'as_of_text', 'Distance', 'system_name', 'station_name', 'landing_pad', 'Score']] \
        .rename(columns={'commodity_name': 'Commodity', 'system_name': 'System', 'station_name': 'Station', 'sell_price': 'Sell Price', 'performance': 'Perf', 'demand': 'Demand', 'as_of_text': 'As Of', 'landing_pad': 'Pad'})

    return ranked_listings \
        .style.format({'Perf':'{:+.2f}', 'Distance':'{:.1f} LY', 'Score': '{:.1f}'}) \
        .set_properties(subset=['Commodity', 'System', 'Station'], **{'text-align': 'left'}) \
        .set_table_styles([dict(selector = 'th', props=[('text-align', 'left')])])


def commodity_sources_nearby(origin_name, commodity_names, minimum_supply=100, top_count=5):
    ''' Given a starting point and a list of commodities, find the five closet sources for each commodity,
        then group them by system and station.
    '''
    origin = find_system_by_name(origin_name)
    commodities = commodity_details[commodity_details['name'].isin(commodity_names)][['id', 'name']] \
        .rename(columns={'name': 'commodity', 'id': 'commodity_id'})

    listings = commodity_listings_eod.merge(commodities, on='commodity_id') \
        [['station_id', 'commodity', 'supply', 'buy_price']] \
        .query(f'supply > {minimum_supply}') \
        .drop_duplicates()

    listings_with_locations = listings.merge(station_details[['id', 'name', 'system_id', 'max_landing_pad_size', 'distance_to_star']] \
        .rename(columns={'id': 'station_id', 'name': 'station', 'max_landing_pad_size': 'Pad Size', 'distance_to_star': 'Sublight'}), on='station_id') \
        .merge(populated_systems[['id', 'name', 'x', 'y', 'z']] \
        .rename(columns={'id': 'system_id', 'name': 'system'}), on='system_id') \
        .drop(columns=['station_id', 'system_id'])

    dist_listings = listings_with_locations.assign(distance = lambda x: distance(origin, x))

    listings_ranked = dist_listings.assign(rnk = dist_listings.groupby('commodity')['distance'] \
            .rank(method='first', ascending=True)) \
            .query(f'rnk <= {top_count}') \
            .sort_values(by=['distance', 'commodity', 'station'], ascending=[True, True, True]) \
            .drop_duplicates() \
            .reset_index() \
            .drop(columns=['x', 'y', 'z', 'index', 'rnk'])

    listings_grouped = listings_ranked.sort_values(by=['distance', 'system', 'Sublight', 'station', 'commodity']) \
        .set_index(['system', 'station', 'commodity'])

    return listings_grouped


def filter_hge_states(states):
    hge_states = ["Boom", "Civil Unrest", "Civil War", "Investment", "Outbreak", "War"]
    return "/".join(sorted([x['name'] for x in states if x['name'] in hge_states]))

def query_nearby_hge(origin="Sol", radius=25, min_pop=1, state_count=0):
    nearby_system_names = query_nearby_systems(origin, radius)
    nearby_systems = pd.DataFrame({
        'name': nearby_system_names,
        'Distance': [distance(origin, system_name) for system_name in nearby_system_names],
    }) \
    .merge(populated_systems[['name', 'population', 'primary_economy', 'security', 'allegiance', 'states']], on='name')
    nearby_systems = nearby_systems.assign(hge_states = [filter_hge_states(s) for s in nearby_systems.states])
    nearby_systems.loc[(nearby_systems.allegiance == 'Federation') & (nearby_systems.hge_states == ''), 'hge_states'] = "Federation"
    nearby_systems.loc[(nearby_systems.allegiance == 'Empire')     & (nearby_systems.hge_states == ''), 'hge_states'] = "Empire"
    nearby_systems = nearby_systems.query(f'population >= {min_pop}')
    if state_count > 0:
        nearby_systems = nearby_systems.assign(rnk = nearby_systems.groupby('hge_states')['Distance'] \
            .rank(method='first', ascending=True)) \
            .query(f'rnk <= {state_count}')
    return nearby_systems[nearby_systems.hge_states > ''][['Distance', 'name', 'population', 'primary_economy', 'security', 'hge_states']].sort_values('Distance').reset_index(drop=True)
