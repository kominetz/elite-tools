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
from elitetools import eddb
eddb.load_feeds()


# %%
systems = input("Systems: ")
origin = eddb.center(systems)


# %%
radius = int(input("Radius (ly): "))
if radius == 0:
    radius = max(eddb.distance(origin, s.strip()) for s in systems.split(","))
radius


# %%
nearby_systems = eddb.query_nearby_systems(origin, radius)
system_summaries = eddb.system_survey_report(nearby_systems, origin)
system_summaries


# %%
system_summaries.to_clipboard(header=None, index=False)


