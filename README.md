# Elite Dangerous Tools #

Tools and Utilities about Elite Dangerous

## Overview ##

* python
  * eddb.py -- python module for manipulating feeds from eddb. Required by notebooks.
  * refresh_caches.py -- forces a refresh of the eddb module's feed cachces
* notebooks
  * nearby_systems -- Given one or more systems and a radius, calculate the midpoint of those systems and find all systems within radius (ly) of the midpoint. Copies results to clipboard.
  * home_port_analysis -- Given a system, find all populated systems within 20 ly of that system, then all the systems within 20ly of those systems. Copies results to clipboard.
  * player_faction_analysis -- Given a faction, find all worlds where that faction is present, all worlds with 20 ly of those systems, and determine player faction involvement in those systems.
  * shortest_route -- Given a list of systems, and optionally starting and end points, calculate the shortest route among those systems. *WARNING!* Brute force approach takes N! where N = # of systems.
  * system_summaries -- Given a list of systems, create a summary table of those systems and copy it to the clipboard.
  * expansion_analysis *(PLANNED)* -- Given a list of systems, find the nearest three targets for expansion for each system. Copies results to clipboard.
  * best_core_prices -- Given an origin and a radius, find the best five sell prices for each core mineral within the sphere. Includes the distance from origin.
