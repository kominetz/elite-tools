import itertools
import json
import math
import os.path
import tempfile
import pandas as pd

from urllib.request import urlretrieve
from enum import Enum
from urllib.parse import urlparse


class Feeds(Enum):
    POPULATED_SYSTEMS = 'http://eddb.io/archive/v6/systems_populated.jsonl'
    STATIONS = 'https://eddb.io/archive/v6/stations.jsonl'
    FACTIONS = 'https://eddb.io/archive/v6/factions.jsonl'
    COMMODITIES = 'https://eddb.io/archive/v6/commodities.json'
    MODULES = 'https://eddb.io/archive/v6/modules.json'

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

SYSTEM_INFLUENCE_RANGE = 20

et_temp_path = os.path.join(tempfile.gettempdir(), 'elite-tools')
os.makedirs(et_temp_path, exist_ok=True)

populated_systems = {}
station_details = {}
faction_details = {}
faction_names_by_id = {}
player_faction_names = {}


### FEEDS


def load_feed(feed, force_refresh=False, refresh_interval=7):
    # TODO: If cache file is older than refresh_interval, refresh the cache.
    cache_filename = urlparse(feed.value).path[1:].replace("/", "-")
    system_data_path = os.path.join(et_temp_path, cache_filename)
    if os.path.exists(system_data_path) and not force_refresh:
        print(f'Using existing file "{system_data_path}" for {feed}.')
    else:
        urlretrieve(feed.value, system_data_path)
        print(f'Downloaded {feed} as file "{system_data_path}".')

    feed_data = {}
    feed_file = open(system_data_path)
    for system_record in feed_file:
        pop_sys = json.loads(system_record)
        feed_data[pop_sys['name']] = pop_sys
    feed_file.close()
    print(f"# {feed} records loaded: ", len(feed_data))
    return feed_data


def load_feed_dataframe(feed, force_refresh=False):
    et_temp_path = os.path.join(tempfile.gettempdir(), 'elite-tools')
    os.makedirs(et_temp_path, exist_ok=True)
    cache_filename = urlparse(feed.value).path[1:].replace("/", "-")
    system_data_path = os.path.join(et_temp_path, cache_filename)
    if os.path.exists(system_data_path) and not force_refresh:
        print(f'Using existing file "{system_data_path}" for {feed}.')
    else:
        urlretrieve(feed.value, system_data_path)
        print(f'Downloaded {feed} as file "{system_data_path}".')

    feed_data = []
    feed_file = open(system_data_path)
    for system_record in feed_file:
        pop_sys = json.loads(system_record)
        feed_data.append(pop_sys)
    feed_file.close()
    print(f"# {feed} records df-loaded: ", len(feed_data))
    return pd.DataFrame.from_dict(feed_data)


### UTILITY

def distance(origin, destination):
    o = populated_systems[origin] if isinstance(origin, str) else origin
    d = populated_systems[destination] if isinstance(destination, str) else destination
    return round(((d['x'] - o['x']) ** 2 + (d['y'] - o['y']) ** 2 + (d['z'] - o['z']) ** 2) ** 0.5, 1)


def average_position(system_names):
    if isinstance(system_names, str):
        system_names = [ sn.strip() for sn in system_names.split(',') ]
    sum_x, sum_y, sum_z = 0, 0, 0
    n = len(system_names)
    for name in system_names:
        s = populated_systems[name]
        sum_x += s['x']
        sum_y += s['y']
        sum_z += s['z']
    return {'name': 'Average Position', 'x': sum_x / n, 'y': sum_y / n, 'z': sum_z / n, 'system_names': system_names}


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


def closest_systems(origin, destinations):
    closest_name = origin
    closest_distance = -1
    for destination in destinations:
        destination_distance = distance(origin, destination)
        if closest_distance == -1 or destination_distance < closest_distance:
            closest_name = destination
            closest_distance = destination_distance
    return closest_name


def query_nearby_systems(origin, radius):
    if type(origin) == list:
        return set([nearby_system for s in origin for nearby_system in query_nearby_systems(s, radius)])
    else: 
        return [s for s in populated_systems.keys() if distance(origin, s) <= radius]


def query_systems_by_faction(faction):
    return [s for s in populated_systems.keys() if system_has_faction(s, faction)]


def system_has_faction(system, faction):
    return populated_systems[system]['controlling_minor_faction'] == faction or faction_details[faction]['id'] in minor_faction_ids(system)


def system_states(system):
    return ", ".join([s['name'] for s in system['states']])


def nearby_systems(origin, radius):  # Deprecated, assuming that's a thing in python
    return [s for s in populated_systems if distance(origin, s) <= radius]


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


# DEPRECATED
# TODO: Replace calls with system_survey_data() and remove this wrapper.
def summarize_systems(systems, origin='Sol'):
    return system_survey_summary(systems, origin)


def system_survey_summary(systems, origin='Sol'):
    system_summaries = []
    for n in systems:
        s = populated_systems[n]
        d = distance(origin, n)
        system_summaries.append([s['name'], d, s['population'], s['government'], s['allegiance'], s['security'], s['primary_economy'], s['controlling_minor_faction'], s['reserve_type']])
    return pd.DataFrame(system_summaries, columns=['Name', 'Distance', 'Population', 'Government', 'Allegiance', 'Security Level', 'Primary Economy', 'Controlling Faction', 'Reserve Level'])


# DEPRECATE
# TODO: Replace calls with system_faction_data() and remove this wrapper.
def summarize_faction_systems(systems, origin='Sol'):
    return system_faction_summary(systems, origin)


def system_faction_summary(systems, origin='Sol'):
    system_summaries = []
    categories = ['Insurgency', 'Control', 'Presence', 'Player Control', 'Player Presence', 'NPC']
    for n in systems:
        s = populated_systems[n]
        d = distance(origin, n)
        cf_name = s['controlling_minor_faction']
        pc_fac = [f for f in filter_player_factions(minor_faction_names(s['name']))]
        states = [x['name'] for x in s['states']]
        cf_state = get_faction_state(s, cf_name)
        cf_inf = cf_state['influence']
        cf_hap = cf_state['happiness_id']
        if cf_name == "The Order of Mobius":
            fac_pri = 0 if len(pc_fac) > 1 else 1
        elif "The Order of Mobius" in pc_fac:
            fac_pri = 2
        elif cf_name in pc_fac:
            fac_pri = 3
        elif len(pc_fac) > 0:
            fac_pri = 4
        else:
            fac_pri = 5
        system_summaries.append([fac_pri, categories[fac_pri], s['name'], d, cf_name, cf_hap, cf_inf, ", ".join(pc_fac), ", ".join(states), s['population'], s['government'], s['allegiance'], s['security'], s['primary_economy']])
    return pd.DataFrame(system_summaries, columns=['Priority', 'Category', 'Name', 'Distance', 'Controlling Faction', 'Happiness', 'Influence', 'Player Factions Present', 'States', 'Population', 'Government', 'Allegiance', 'Security Level', 'Primary Economy']).set_index('Priority','Name')


def get_faction_state(system, faction_name):
    for f in system['minor_faction_presences']:
        if faction_details[faction_name]['id'] == f['minor_faction_id']:
            return f
    return None


def influenced_systems(system_name):
    direct_inf_systems = query_nearby_systems(system_name, SYSTEM_INFLUENCE_RANGE)
    indirect_inf_systems = [query_nearby_systems(s, SYSTEM_INFLUENCE_RANGE) for s in direct_inf_systems]
    print(len(indirect_inf_systems), len(set([x for x in indirect_inf_systems])))


### FACTIONS


def controlling_player_factions(systems):
    return filter_player_factions(set([populated_systems[s]['controlling_minor_faction'] for s in systems]))


def system_player_factions(system):
    return [faction_names_by_id[f['minor_faction_id']] for f_pres in populated_systems[system]['minor_faction_presences'] for f in f_pres if f['is_player_faction']]


def present_player_factions(systems):
    mfp = [mfp for s in systems for mfp in populated_systems[s]['minor_faction_presences']]
    minor_faction_ids = set([f['minor_faction_id'] for f in mfp])
    minor_factions = set([f['name'] for f in faction_details.values() if int(f['id']) in minor_faction_ids])
    return filter_player_factions(minor_factions)


def filter_player_factions(factions):
    return set([n for n in factions if faction_details[n]['is_player_faction']])


def minor_faction_ids(system):
     return set(s['minor_faction_id'] for s in populated_systems[system]['minor_faction_presences'])


def minor_faction_names(system):
     return [faction_names_by_id[s['minor_faction_id']] for s in populated_systems[system]['minor_faction_presences']]


### INITIALIZATION ###

#  Originally feeds loaded in main. Moved to function so cache/feed settings could be controlled before the module took any actions.
def load_feeds(force_refresh=False):
    global populated_systems, station_details, faction_details, faction_names_by_id, player_faction_names
    print(force_refresh)

    populated_systems = load_feed(Feeds.POPULATED_SYSTEMS, force_refresh)
    station_details = load_feed(Feeds.STATIONS, force_refresh)
    faction_details = load_feed(Feeds.FACTIONS, force_refresh)

    faction_names_by_id = {}
    player_faction_names = set()
    for f in faction_details.values():
        faction_names_by_id[f['id']] = f['name']
        if f['is_player_faction']:
            player_faction_names.add(f['name'])
    # factions_dataframe = load_feed_dataframe(Feeds.FACTIONS)

# Simulates original behavior, required until all notebooks can be updated to explicitly call load_feeds().
