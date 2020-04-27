import eddb

origin_systems = ['EngrCOG', 'Beta Comae Berenices', 'Sol', 'Shinrarta Dezhra']
engineer_systems = {
    'Sirius',
    'Wyrd',
    'Kuk',
    'Alioth',
    'Wolf 397',
    'Leesti',
    'Khun',
    'Laksak',
    'Meene',
}
destination_systems = engineer_systems.copy()
destination_systems.remove('Laksak')
destination_systems.remove('Meene')

x_pos = 0.0
y_pos = 0.0
z_pos = 0.0
for p in engineer_systems:
    x_pos += eddb.populated_systems[p]['x']
    y_pos += eddb.populated_systems[p]['y']
    z_pos += eddb.populated_systems[p]['z']
x_pos /= len(engineer_systems)
y_pos /= len(engineer_systems)
z_pos /= len(engineer_systems)

print(f"ENGINEER CENTER OF GRAVITY: ({x_pos}, {y_pos}, {z_pos})")
eddb.populated_systems["EngrCOG"] = {'name': "EngrCOG", 'x': x_pos, 'y': y_pos, 'z': z_pos}
name = eddb.closest("EngrCOG", eddb.populated_systems.keys())
dist = eddb.distance('EngrCOG', name)
print(f"SYSTEM CLOSEST TO EngrCOG: {name} ({dist} ly)")
print()

for o in origin_systems:
    print(f"-- ORIGIN SYSTEM: {o} --")
    print()
    print("Distance to Engineers")
    for d in sorted(engineer_systems):
        print("%-16s: %4d ly" % (d, eddb.distance(o, d)))
    print()
    print("Best Path Through Destinations")
    eddb.resolve_path(eddb.best_path(list(destination_systems), origin=o, destination=o), True)
    print()
