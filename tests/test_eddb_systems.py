import pytest
import pandas as pd
from elitetools import eddb
from elitetools.eddb import find_system_by_name, query_systems_by_name, query_nearby_systems, query_systems_by_faction, load_feeds


def setup_module():
        load_feeds()


class TestFindSystemByName:
    def test(self):
        sol_system = find_system_by_name('Sol')
        assert sol_system is not None
        assert sol_system['name'] == 'Sol'
        assert sol_system['needs_permit'] == True

        sd_system = find_system_by_name('Shinrarta Dezhra')
        assert sd_system is not None
        assert sd_system['name'] == 'Shinrarta Dezhra'
        assert sd_system['needs_permit'] == True


    def test_system_not_found(self):
        with pytest.raises(KeyError):
            find_system_by_name('NOT_A_REAL_SYSTEM')


    def test_case_insensitive(self):
        assert (find_system_by_name('sOL')) is not None


class TestQuerySystemsByNames:
    def test(self):
        cs_from_list = query_systems_by_name(['Achenar', 'Alioth', 'Sol'])
        assert len(cs_from_list) == 3
        assert cs_from_list['Achenar']['name'] == 'Achenar'
        assert cs_from_list['Alioth']['name'] == 'Alioth'
        assert cs_from_list['Sol']['name'] == 'Sol'
        assert cs_from_list['Sol']['x'] == 0.0
        assert cs_from_list['Sol']['y'] == 0.0
        assert cs_from_list['Sol']['z'] == 0.0

        cs_from_string = query_systems_by_name('Achenar, Alioth, Sol')
        assert len(cs_from_list) == 3
        assert cs_from_string['Achenar'] == cs_from_list['Achenar']
        assert cs_from_string['Alioth'] == cs_from_list['Alioth']
        assert cs_from_string['Sol'] == cs_from_list['Sol']

        cs_empty = query_systems_by_name([])
        assert len(cs_empty) == 0

    def test_systems_not_found(self):
        with pytest.raises(KeyError):
            query_systems_by_name('NOT_A_SYSTEM')
        with pytest.raises(KeyError):
            query_systems_by_name(['Sol', 'NOT_A_SYSTEM', 'Shinrarta Dezhra'])

    def test_case_insensitive(self):
        cs = query_systems_by_name('AcHeNar, aLIOTH, SOL')
        assert len(cs) == 3


class TestQueryNearbySystems:
    def test(self):
        nearby_systems = query_nearby_systems('Azrael', 20)
        # Nearby systems should not change due to BGS activity, but a major update? Unknown.
        assert len(nearby_systems) == 3
        assert "Dvorsi" in nearby_systems


class TestQuerySystemsByFaction:
    def test(self):
        faction_systems = query_systems_by_faction("The Order of Mobius")
        # A faction is always in at least one system.
        assert len(faction_systems) > 0
        # A faction is always in its home system.
        assert "Azrael" in faction_systems