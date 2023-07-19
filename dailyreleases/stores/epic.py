from __future__ import annotations
import requests
from ..util import case_insensitive_close_matches, retry
from ..config import CONFIG
import logging
from typing import Optional
from epicstore_api import EpicGamesStoreAPI
from json import dumps, loads
api = EpicGamesStoreAPI()

logger = logging.getLogger(__name__)

offerid_json = {}

@retry()
def load_offerid_json():
    global offerid_json
    egs_offerid_url = CONFIG['main']['egs_offeridapi_url']
    logger.debug("Loading EGS offerid defintions from " + egs_offerid_url)
    offerid_txt = requests.get(egs_offerid_url).content.decode()
    offerid_json = loads(offerid_txt)

@retry()
def get_epic_games_data(query: str):
    search_json = api.fetch_store_games(keywords=query)
    return search_json

def search(game_name: str) -> Optional[str]:
    try:
        logger.debug("Searching Epic Games Store for %s", game_name)
        data = get_epic_games_data(game_name)
        if "data" in data and "Catalog" in data["data"]:
            elements = data["data"]["Catalog"]["searchStore"]["elements"]
            matches = case_insensitive_close_matches(
                game_name, [element["title"] for element in elements]
            )
            for match in matches:
                for element in elements:
                    if element["title"].lower() == match.lower():
                        if offerid_json == {}:
                            load_offerid_json()
                        url = "https://store.epicgames.com/en-US/p/" + offerid_json[element['id']]
                        logger.debug("Best match is '%s' '%s'", element["title"], url)
                        return url
    except Exception as e:
        print("Error searching in Epic Games Store:", e)
    return None

