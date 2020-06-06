import pytest

from elitetools.eddb import (faction_home_system, filter_player_factions,
                             find_faction_by_name, load_feeds,
                             minor_faction_ids, minor_faction_names,
                             player_faction_controlled, present_faction_state,
                             system_has_faction)


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
        assert "The Order of Mobius" in player_faction_controlled(
            ["Azrael", "Sol"])


class TestFilterPlayerFactions:
    def test(self):
        # Subject to change via BGS
        pf = filter_player_factions(
            ['Labour of Azrael', 'The Order of Mobius'])
        assert pf is not None
        assert len(pf) == 1
        assert "The Order of Mobius" in pf
        assert "Labour of Azrael" not in pf


class TestMinorFactionIds:
    def test(self):
        assert len(minor_faction_ids("Azrael")) > 0
        # Assumption: TestMinorFactionNames passing means there no need to verify Azrael ID.


class TestMinorFactionNames:
    def test(self):
        assert len(minor_faction_names("Azrael")) > 0
        assert "The Order of Mobius" in minor_faction_names("Azrael")


class TestFindFactionByName:
    def test(self):
        faction = find_faction_by_name('The Order of Mobius')
        assert faction['name'] == 'The Order of Mobius'

    def test_case_insensitive(self):
        faction = find_faction_by_name('the ORDER oF Mobius')
        assert faction['name'] == 'The Order of Mobius'


class TestSystemHasFaction:
    def test(self):
        assert system_has_faction("Azrael", "The Order of Mobius")
        assert system_has_faction('Azrael', 'Labour of Azrael')

    def test_case_insensitive(self):
        assert system_has_faction("AZRAEL", "THE order oF Mobius")


class TestPresentFactionState:
    def test(self):
        assert present_faction_state(
            'Azrael', 'The Order of Mobius') is not None
        assert present_faction_state('Azrael', 'Mother Gaia') is None


    def test_not_a_faction(self):
        with pytest.raises(KeyError):
            assert present_faction_state('Azrael', 'NOT_A_REAL_FACTION') is None

