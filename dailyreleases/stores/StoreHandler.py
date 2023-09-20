from ..APIHelper import APIHelper
from .Steam import Steam
from .GOG import GOG
from .Epic import Epic
from typing import Dict
import re
import logging

logger = logging.getLogger(__name__)


class StoreHandler(APIHelper):
    def __init__(self):
        self.steam = Steam()
        self.gog =  GOG()
        self.epic = Epic()
        
    def find_store_links(self, game_name: str) -> Dict[str, str]:
        links = {}
        
        # Find store links from specific stores
        steam_link = self.steam.search(game_name)
        if steam_link:
            links["Steam"] = steam_link
        
        gog_link = self.gog.search(game_name)
        if gog_link:
            links["GOG"] = gog_link
        
        epic_link = self.epic.search(game_name)
        if epic_link:
            links["EGS"] = epic_link

        # If specific store links were found, return them
        if links:
            return links

        known_stores = {
            "store.steampowered.com/(app|sub|bundle)": "Steam",  # order doesn't matter
            "gog.com/game": "GOG",
            "ea.com": "EA",
            "ubi(soft)?.com": "Ubisoft",
            "www.microsoft.com/.*p": "Microsoft Store",
            "store.epicgames.com": "Epic Games",
            "itch.io": "Itch.io",
            "bigfishgames.com/games": "Big Fish Games",
            "gamejolt.com": "Game Jolt",
            "alawar.com": "Alawar",
            "wildtangent.com": "WildTangent Games",
        }

        # Multiple store links are sometimes returned, but we believe in Google's algorithm and choose the first one
        for link in self.web_search(f"{game_name} game buy"):
            for store_url, store_name in known_stores.items():
                if re.search(store_url, link, flags=re.IGNORECASE):
                    return {store_name: link}

        logger.debug("Unable to find store links for %s", game_name)
        return {}
