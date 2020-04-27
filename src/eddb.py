import itertools
import json
import math
import os.path
import tempfile

from urllib.request import urlretrieve
from enum import Enum
from urllib.parse import urlparse


class Feeds(Enum):
    POPULATED_SYSTEMS = 'http://eddb.io/archive/v6/systems_populated.jsonl'
    STATIONS = 'https://eddb.io/archive/v6/stations.jsonl'
    FACTIONS = 'https://eddb.io/archive/v6/factions.jsonl'
    COMMODITIES = 'https://eddb.io/archive/v6/commodities.json'
    MODULES = 'https://eddb.io/archive/v6/modules.json'


def distance(o_name, d_name):
    o = populated_systems[o_name]
    d = populated_systems[d_name]
    return math.ceil(((d['x'] - o['x']) ** 2 + (d['y'] - o['y']) ** 2 + (d['z'] - o['z']) ** 2) ** 0.5)


def closest_path(origin, destinations):
    calculated_path = []
    d_last = origin
    d_remaining = destinations.copy()
    subtotal_distance = 0
    while len(d_remaining) > 0:
        d_next = closest(d_last, d_remaining)
        leg_distance = distance(d_last, d_next)
        calculated_path.append({'name': d_next, 'distance': leg_distance})
        d_last = d_next
        d_remaining.discard(d_last)
        subtotal_distance += leg_distance
    return calculated_path, subtotal_distance


def resolve_path(path, print_path=False):
    length = 0
    last_system = path[0]
    for next_system in path:
        dist = distance(last_system, next_system)
        length += dist
        if print_path:
            print("%-24s %5d ly  %4d ly" % (next_system, dist, length))
        last_system = next_system
    return length


def best_path(waypoints, origin, destination):
    shortest_path = []
    shortest_length = -1
    paths = itertools.permutations(waypoints)
    for path_tuple in paths:
        path = list(path_tuple)
        if origin:
            path.insert(0, origin)
        if destination:
            path.append(destination)
        length = resolve_path(list(path))
        if shortest_length < 0 or length < shortest_length:
            shortest_path = path
            shortest_length = length
            # print("%5d ly: %s" % (shortest_length, shortest_path))
    return shortest_path


def closest(origin, destinations):
    closest_name = origin
    closest_distance = -1
    for destination in destinations:
        destination_distance = distance(origin, destination)
        if closest_distance == -1 or destination_distance < closest_distance:
            closest_name = destination
            closest_distance = destination_distance
    return closest_name


def load_feed(feed):
    et_temp_path = os.path.join(tempfile.gettempdir(), 'elite-tools')
    os.makedirs(et_temp_path, exist_ok=True)
    cache_filename = urlparse(feed.value).path[1:].replace("/", "-")
    system_data_path = os.path.join(et_temp_path, cache_filename)
    if os.path.exists(system_data_path):
        print(f'Using existing file "{system_data_path}" for {feed}.')
    else:
        urlretrieve(feed.value, system_data_path)
        print(f'Downloaded {feed} feed as file "{system_data_path}".')

    feed_data = {}
    feed_file = open(system_data_path)
    for system_record in feed_file:
        pop_sys = json.loads(system_record)
        feed_data[pop_sys['name']] = pop_sys
    feed_file.close()
    print("# Populated systems loaded: ", len(feed_data))
    return feed_data


populated_systems = load_feed(Feeds.POPULATED_SYSTEMS)
