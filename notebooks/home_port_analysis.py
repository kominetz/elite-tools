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
origin = input("Home System: ")


# %%
core_systems = eddb.query_nearby_systems(origin, eddb.SYSTEM_INFLUENCE_RANGE)
extended_systems = eddb.query_nearby_systems(core_systems, eddb.SYSTEM_INFLUENCE_RANGE)
system_summaries = eddb.system_survey_report(extended_systems, origin)
system_summaries.sort_values(by='Distance')
system_summaries.to_clipboard(header=None, index=False)
system_summaries


