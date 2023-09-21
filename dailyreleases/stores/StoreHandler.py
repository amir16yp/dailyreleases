from ..APIHelper import APIHelper
from .Steam import Steam
from .GOG import GOG
from .Epic import Epic
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class StoreHandler(APIHelper):
    def __init__(self):
        self.steam = Steam()
        self.gog = GOG()
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

        return links
