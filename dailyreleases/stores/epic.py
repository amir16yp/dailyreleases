from __future__ import annotations
import requests
from ..util import case_insensitive_close_matches, retry
import logging
from typing import Optional
from epicstore_api import EpicGamesStoreAPI

api = EpicGamesStoreAPI()

logger = logging.getLogger(__name__)

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
                        logger.debug("Best match is '%s'", element["title"])
                        return element["urlSlug"] + '/home'
    except Exception as e:
        print("Error searching in Epic Games Store:", e)
    return None

# if run as a standalone, run a test
#if __name__ == "__main__":
#    print(search("Among Us"))
