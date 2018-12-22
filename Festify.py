from typing import Dict, List
from calendar import month_name as MONTH_NAMES
from calendar import month_abbr as MONTH_ABBR
from urllib.parse import urlencode

import spotipy
import os
import dataclasses
import re
import requests

ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
UPLOADS_DIR = os.path.join(ROOT_DIR, 'uploads')
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.join(ROOT_DIR, 'GCP_KEY.json')


@dataclasses.dataclass
class CreateRequest:
    '''Class for keeping track of create playlist requests'''
    id: str
    name: str
    base_64_image: str
    access_token: str
    result: Dict = dataclasses.field(default_factory=dict)


class Festify:

    @staticmethod
    def _is_valid_month(word):
        """
        :param word: word that may be a valid month name depending on locale
        :return: True if the word is a valid month name or a month abbreviation, else False
        """
        if not word:
            return False

        return word.title() in MONTH_NAMES or word.title() in MONTH_ABBR

    @staticmethod
    def _is_valid_year(word):
        """
        :param word: word that may contain a valid year (####, 1970, etc)
        :return: the year that was found if word is a valid year, or False
        """
        if not word:
            return False

        year_pattern = '^[0-9]{4}$'
        year_regex = re.compile(year_pattern)
        match = year_regex.match(word)

        return match.group(0) if match is not None else False

    @staticmethod
    def create_playlist(playlist_id, playlist_name='Festify - Music Festival', base_64_image=None, access_token=None,
                        results_queue=None):
        if not results_queue or not base_64_image or not access_token:
            return results_queue.put((playlist_id, -1, 'Invalid arguments'))

        print(f'Generating {playlist_name}, id: {playlist_id}')

        create_request = CreateRequest(id=playlist_id, name=playlist_name, base_64_image=base_64_image,
                                       access_token=access_token)

        create_result = Festify._create_playlist(create_request)

        results_queue.put(create_result)

        exit(0)

    @staticmethod
    def _create_playlist(create_request: CreateRequest) -> CreateRequest:
        print(create_request)
        # Imports the Google Cloud client library
        from google.cloud import vision
        # Instantiates a client
        client = vision.ImageAnnotatorClient()

        spotify_client = spotipy.Spotify(auth=create_request.access_token)

        image_path = os.path.join(UPLOADS_DIR, create_request.base_64_image)

        with open(image_path, 'rb') as image_file:
            content = image_file.read()

        image = vision.types.Image(content=content)

        try:
            response = client.text_detection(image=image)
            texts = response.text_annotations
        except Exception as e:
            print(e)
            return create_request
        finally:
            os.remove(image_path)

        extracted_texts = [text.description.strip() for text in texts[1:]]

        extracted_texts_str = ' '.join(extracted_texts)

        results = Festify.process(extracted_texts, extracted_texts_str)

        return create_request

    @staticmethod
    def process(extracted_texts: List[str], extracted_texts_str: str) -> Dict:
        if not extracted_texts or not extracted_texts_str:
            return {}

        festival_name = Festify._get_festival_name(extracted_texts)

    @staticmethod
    def _is_festival(search_term: str) -> bool:
        if not search_term:
            return False


    @staticmethod
    def _get_festival_name(extracted_texts: List[str]) -> str:
        common_abbrev = [
            'festival', 'fest', 'music'
        ]
        target_idx = -1

        for term in common_abbrev:
            if term in extracted_texts:
                target_idx = extracted_texts.index(term)
                break

        if not target_idx == -1:
            pass

        for idx in range(len(extracted_texts)):
            for sub_idx in reversed(range(1, 5)):
                end = idx + sub_idx
                if idx + sub_idx > len(extracted_texts):
                    continue
                sub_group = extracted_texts[idx:end]

                sub_group_str = ' '.join(sub_group)

                confident = Festify._is_festival(sub_group_str)

                if confident:
                    return sub_group_str

    # refresh_token = response_data["refresh_token"]
    # token_type = response_data["token_type"]
    # expires_in = response_data["expires_in"]

    # Auth Step 6: Use the access token to access Spotify API
    # authorization_header = {"Authorization": "Bearer {}".format(access_token)}
