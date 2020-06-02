# %%
import yaml

with open('./docs/commodities_by_type.yaml') as f:
    commodities_by_type = yaml.safe_load(f)

with open('./docs/economies_import_export.yaml') as f:
    economies_import_export = yaml.safe_load(f)

# %%
print(economies_import_export.keys())


# %%
commodities = []
[commodities.append(y) for x in commodities_by_type.values() for y in x]
commodities.sort()
commodities

# %%
import pandas as pd
commodities_import_export = {}
def add_relation(commodity, side, economy):
    global commodities_import_export
    if commodity not in commodities_import_export:
        commodities_import_export[commodity] = { 'imported_by': [], 'exported_by': []}
    commodities_import_export[commodity][side].append(economy)

[add_relation(commodity, ('imported_by' if side == 'imports' else 'exported_by'), economy) \
    for economy in economies_import_export \
        for side in economies_import_export[economy] \
            for commodity in economies_import_export[economy][side]]

# %%
print(yaml.dump(commodities_import_export))

# %%
