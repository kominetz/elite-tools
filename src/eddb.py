import itertools
import json
import math
import os.path
import tempfile
import urllib.request


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


def best_path(origin, destinations):
    shortest_path = []
    shortest_length = -1
    paths = itertools.permutations(destinations)
    for path_tuple in paths:
        path = list(path_tuple)
        path.insert(0, origin)
        path.append(origin)
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


system_data_path = os.path.join(tempfile.gettempdir(), 'systems_populated.jsonl')
if os.path.exists(system_data_path):
    print(f'Using existing system data file "{system_data_path}".')
else:
    urllib.request.urlretrieve('http://eddb.io/archive/v6/systems_populated.jsonl', system_data_path)
    print(f'Downloaded system data as file "{system_data_path}".')

populated_systems = {}
populated_systems_f = open(system_data_path)
for populated_system_r in populated_systems_f:
    pop_sys = json.loads(populated_system_r)
    populated_systems[pop_sys['name']] = pop_sys
populated_systems_f.close()
print("# Populated systems loaded: ", len(populated_systems))
populated_system_names = list(populated_systems.keys())
print()
