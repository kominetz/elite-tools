# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %% Change working directory from the workspace root to the ipynb file location. Turn this addition off with the DataScience.changeDirOnImportExport setting
# ms-python.python added
import os
try:
	os.chdir(os.path.join(os.getcwd(), 'notebooks'))
	print(os.getcwd())
except:
	pass
# %%
import pandas as pd
from elitetools import eddb
eddb.load_feeds()


# %%
faction = "The Order of Mobius"
origin = eddb.faction_home_system(faction)
core_systems = set(eddb.query_systems_by_faction(faction))
extended_systems = set([inf_s for core_s in core_systems for inf_s in eddb.query_nearby_systems(core_s, eddb.SYSTEM_INFLUENCE_RANGE)])


# %%



# %%
faction_report = eddb.system_faction_report(extended_systems, faction, origin).sort_values(by=['Priority', 'Name'], ascending=[True, True])
faction_report.to_clipboard()
faction_report


# %%
faction_stats = {}
#cpf = eddb.player_faction_controlled(extended_systems, faction, origin)
for s_name in extended_systems:
    s = eddb.populated_systems[s_name]
    cf_name = s['controlling_minor_faction']
    if cf_name in eddb.player_faction_names:
        if cf_name not in faction_stats.keys():
            faction_stats[cf_name] = {'name': cf_name, 'control': 0, 'presence': 0}
        faction_stats[cf_name]['control'] += 1
    for f in s['minor_faction_presences']:
        f_name = eddb.faction_names_by_id[f['minor_faction_id']]
        if f_name in eddb.player_faction_names:
            if f_name not in faction_stats.keys():
                faction_stats[f_name] = {'name': f_name, 'control': 0, 'presence': 0}
            if f_name != cf_name:
                faction_stats[f_name]['presence'] += 1

pd.DataFrame.from_dict(faction_stats.values()).set_index('name').sort_values(by=['control', 'presence', 'name'], ascending=[False, False, True])


