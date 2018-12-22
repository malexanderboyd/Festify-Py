import math

import requests
import os
import json

api_key = os.environ['SONGKICK_API_KEY']

api_url = 'https://api.songkick.com/api/3.0/'

events_path = 'events.json'


with open('city-ids.json', 'r') as city_ids_file:
    city_ids = json.load(city_ids_file)


festivals_map = {}
for city_name, city_id in city_ids.items():
    print(f'{city_name}')
    events_params = {
    'apikey': api_key,
    'type': 'Festival',
    'location': f'sk:{city_id}',
    'per_page': 50
    }
    festivals = requests.get(api_url + events_path, params=events_params)

    festivals = festivals.json()

    results_page = festivals.get('resultsPage', None)

    if not results_page:
        continue

    page_idx = results_page.get('page', None)
    total_entries = results_page.get('totalEntries', None)

    required_pages = math.ceil(total_entries / 50)

    for event in results_page.get('results', {}).get('event', []):
        event_id = event.get('id', None)
        event_name = event.get('displayName', None)

        if not event_id or not event_name:
            continue

        festivals_map[event_name] = event_id

    while page_idx < required_pages:
        page_idx += 1
        events_params['page'] = page_idx
        festivals = requests.get(api_url + events_path, params=events_params)

        festivals = festivals.json()

        results_page = festivals.get('resultsPage', None)
        page_idx = results_page.get('page', None)
        for event in results_page.get('results', {}).get('event', []):
            event_id = event.get('id', None)
            event_name = event.get('displayName', None)

            if not event_id or not event_name:
                continue

            festivals_map[event_name] = event_id

with open('festival-ids.json', 'w') as festival_ids_file:
    festival_ids_file.write(json.dumps(festivals_map))
