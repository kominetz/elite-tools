import pytest
from eddb import faction_home_system, load_feeds

class TestFactionHomeSystem:
    def test(self):
        load_feeds()
        assert "Azrael" == faction_home_system("The Order of Mobius")['name']
        assert "Sol" == faction_home_system("Mother Gaia")['name']
        with pytest.raises(IndexError):
            faction_home_system("I AM A NONSENSE NAME")