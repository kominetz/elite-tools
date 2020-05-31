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
reference_system = input("Reference System: ")


# %%
systems = [wp.strip() for wp in input("Systems to summarize: ").split(',')]


# %%
system_summaries = eddb.system_survey_report(systems, reference_system)
system_summaries.sort_values(by='Name')


# %%
system_summaries.to_clipboard(header=None, index=False)


