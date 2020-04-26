import itertools, json, math, os, tempfile, urllib.request

files_to_cache = {
    'systems_populated.jsonl': 'http://eddb.io/archive/v6/systems_populated.jsonl',
    'stations.jsonl':          'https://eddb.io/archive/v6/stations.jsonl',
    'factions.jsonl':          'https://eddb.io/archive/v6/factions.jsonl',
    'commodities.json':        'https://eddb.io/archive/v6/commodities.json',
    'modules.json':            'https://eddb.io/archive/v6/modules.json',
}
et_temp_path = os.path.join(tempfile.gettempdir(), 'elite-tools')
os.makedirs(et_temp_path, exist_ok=True)

for et_filename in files_to_cache.keys():
    et_file_path = os.path.join(et_temp_path, et_filename)
    if os.path.exists(et_file_path):
       print(f'Using existing data file "{et_file_path}".')
    else:
        urllib.request.urlretrieve(files_to_cache[et_filename], et_file_path)
        print(f'Downloaded data as file "{et_file_path}".')
