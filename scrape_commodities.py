from elitetools import *
from bs4 import BeautifulSoup
from enum import Enum
from urllib.request import urlopen

realtime_commodities = [
    {'name': 'Alexandrite', 'type': 'Mineral', 'url': 'https://eddb.io/commodity/349'},
    {'name': 'Benitoite', 'type': 'Mineral', 'url': 'https://eddb.io/commodity/347'},
    {'name': 'Grandidierite', 'type': 'Mineral', 'url': 'https://eddb.io/commodity/348'},
    {'name': 'Low Temperature Diamonds', 'type': 'Mineral', 'url': 'https://eddb.io/commodity/276'},
    {'name': 'Monazite', 'type': 'Mineral', 'url': 'https://eddb.io/commodity/345'},
    {'name': 'Musgravite', 'type': 'Mineral', 'url': 'https://eddb.io/commodity/346'},
    {'name': 'Painite', 'type': 'Mineral', 'url': 'https://eddb.io/commodity/83'},
    {'name': 'Platinum', 'type': 'Metal', 'url': 'https://eddb.io/commodity/46'},
    {'name': 'Rhodplumsite', 'type': 'Mineral', 'url': 'https://eddb.io/commodity/343'},
    {'name': 'Serendibite', 'type': 'Mineral', 'url': 'https://eddb.io/commodity/344'},
    {'name': 'Tritium', 'type': 'Chemical', 'url': 'https://eddb.io/commodity/362'},
    {'name': 'Void Opals', 'type': 'Mineral', 'url': 'https://eddb.io/commodity/350'},
]

def scrape_commodity(commodity):
    ''' Given a commodity's name and EDDB URL, extract best sell price listings and return as a list of dicts.
    '''
    listings = []
    with urlopen(commodity['url']) as p:
        page = BeautifulSoup(p, 'html.parser')
    max_sell = page.find(id='table-stations-max-sell')
    for row in max_sell.find_all('tr'):
        fields = row.find_all('td')
        if len(fields) != 7:
            continue  # discard header and malformed rows
        time_fields = fields[6].find_all('span')
        listings.append({
            'commodity_name': commodity['name'],
            'commodity_type': commodity['type'],
            'station_name': fields[0].find('a').get_text(),
            'system_name': fields[1].find('a').get_text(),
            'sell_price': int(fields[2].find('span').get_text().replace(',', '')),
            'demand': int(fields[4].find('span').get_text().replace(',', '')),
            'landing_pad': fields[5].find('span').get_text(),
            'freshness': time_fields[1].get_text(),
        })
    print("%s: %d listings scraped." % (commodity['name'], len(listings)))
    return listings

all_listings = []
for commodity in realtime_commodities:
    all_listings.extend(scrape_commodity(commodity))
print(all_listings)
print('--- ', len(all_listings))