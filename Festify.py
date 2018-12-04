import spotipy
import os
from spotipy.oauth2 import SpotifyClientCredentials

client_credentials_manager = SpotifyClientCredentials(client_id=os.environ['FESTIFY_CLIENT_ID'],
                                                      client_secret=os.environ['FESTIFY_CLIENT_SECRET'])
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)


class Festify:

    @staticmethod
    def create_playlist(playlist_name='Festify - Music Festival', base_64_image=None, results_queue=None):
        if not results_queue or not base_64_image:
            return
