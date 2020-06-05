import pytest
from elitetools.eddb import faction_home_system, player_faction_controlled, minor_faction_ids, minor_faction_names, filter_player_factions, load_feeds


def setup_module():
    load_feeds()


class TestFactionHomeSystem:
    def test(self):
        load_feeds()
        assert "Azrael" == faction_home_system("The Order of Mobius")['name']
        assert "Sol" == faction_home_system("Mother Gaia")['name']
        with pytest.raises(IndexError):
            faction_home_system("I AM A NONSENSE NAME")


class TestPlayFactionControlled:
    def test(self):
        # Subject to change via BGS 
        assert "The Order of Mobius" in player_faction_controlled(["Azrael", "Sol"])


class TestFilterPlayerFactions:
    def test(self):
        # Subject to change via BGS 
        assert "The Order of Mobius" in filter_player_factions(['The Dark Wheel', 'The Order of Mobius'])


class TestMinorFactionIds:
    def test(self):
        assert len(minor_faction_ids("Azrael")) > 0
        # Assumption: TestMinorFactionNames passing means there no need to verify Azrael ID.


class TestMinorFactionNames:
    def test(self):
        assert len(minor_faction_names("Azrael")) > 0
        assert "The Order of Mobius" in minor_faction_names("Azrael")