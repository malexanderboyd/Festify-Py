import spotipy
import os
from spotipy.oauth2 import SpotifyClientCredentials

client_credentials_manager = SpotifyClientCredentials(client_id=os.environ['FESTIFY_CLIENT_ID'],
                                                      client_secret=os.environ['FESTIFY_CLIENT_SECRET'])
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)


class Festify:

    @staticmethod
    def create_playlist(playlist_id, playlist_name='Festify - Music Festival', base_64_image=None, access_token=None, results_queue=None):
        if not results_queue or not base_64_image or not access_token:
            return results_queue.put((playlist_id, -1, 'Invalid arguments'))

        print(f'Generating {playlist_name}, id: {playlist_id}')

        results_queue.put((playlist_id, 1, None))

    # refresh_token = response_data["refresh_token"]
    # token_type = response_data["token_type"]
    # expires_in = response_data["expires_in"]

    # Auth Step 6: Use the access token to access Spotify API
    # authorization_header = {"Authorization": "Bearer {}".format(access_token)}
