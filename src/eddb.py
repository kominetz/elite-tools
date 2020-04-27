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
    print("# Populated systems loaded: ", len(feed_data))
    return feed_data


def distance(o_name, d_name):
    o = populated_systems[o_name]
    d = populated_systems[d_name]
    return math.ceil(((d['x'] - o['x']) ** 2 + (d['y'] - o['y']) ** 2 + (d['z'] - o['z']) ** 2) ** 0.5)


def closest_systems(origin, destinations):
    closest_name = origin
    closest_distance = -1
    for destination in destinations:
        destination_distance = distance(origin, destination)
        if closest_distance == -1 or destination_distance < closest_distance:
            closest_name = destination
            closest_distance = destination_distance
    return closest_name


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
                print("%5d ly: %s" % (shortest_length, shortest_route))
    return shortest_route


populated_systems = load_feed(Feeds.POPULATED_SYSTEMS)