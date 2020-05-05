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

engineers = [
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

def load_feed(feed):
    et_temp_path = os.path.join(tempfile.gettempdir(), 'elite-tools')
    os.makedirs(et_temp_path, exist_ok=True)
    cache_filename = urlparse(feed.value).path[1:].replace("/", "-")
    system_data_path = os.path.join(et_temp_path, cache_filename)
    if os.path.exists(system_data_path):
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
    return [s for s in populated_systems.keys() if distance(origin, s) <= radius]


def query_systems_by_faction(faction):
    faction_id = factions[faction]['id']
    return [s for s in populated_systems.keys() if system_has_faction(s, faction)]


def system_has_faction(system, faction):
    return populated_systems[system]['controlling_minor_faction'] == faction or factions[faction]['id'] in minor_faction_ids(system)


def minor_faction_ids(system):
     return set(s['minor_faction_id'] for s in populated_systems[system]['minor_faction_presences'])


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


def summarize_systems(systems, origin='Sol'):
    system_summaries = []
    for n in systems:
        s = populated_systems[n]
        d = distance(origin, n)
        system_summaries.append([s['name'], d, s['population'], s['government'], s['allegiance'], s['security'], s['primary_economy'], s['controlling_minor_faction'], s['reserve_type']])
    return pd.DataFrame(system_summaries, columns=['Name', 'Distance', 'Population', 'Government', 'Allegiance', 'Security Level', 'Primary Economy', 'Controlling Faction', 'Reserve Level'])
        

def summarize_faction_systems(systems, origin='Sol'):
    system_summaries = []
    for n in systems:
        s = populated_systems[n]
        d = distance(origin, n)
        system_summaries.append([s['name'], d, s['controlling_minor_faction'], system_states(s), s['population'], s['government'], s['allegiance'], s['security'], s['primary_economy'], s['reserve_type']])
    return pd.DataFrame(system_summaries, columns=['Name', 'Distance', 'Controlling Faction', 'States', 'Population', 'Government', 'Allegiance', 'Security Level', 'Primary Economy', 'Reserve Level'])


populated_systems = load_feed(Feeds.POPULATED_SYSTEMS)
factions = load_feed(Feeds.FACTIONS)
