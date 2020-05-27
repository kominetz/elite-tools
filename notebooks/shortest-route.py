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
import eddb
eddb.load_feeds()


# %%
origin = input("Origin: ")


# %%
destination = input("Destination: ")


# %%
waypoints = [wp.strip() for wp in input("Waypoints: ").split(',')]


# %%
eddb.route_to_dataframe(eddb.best_route(waypoints, origin, destination))


