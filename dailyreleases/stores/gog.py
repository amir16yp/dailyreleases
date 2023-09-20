from __future__ import annotations
import logging

from .. import util
from ..APIHelper import APIHelper

logger = logging.getLogger(__name__)


class GOG(APIHelper):
    def __init__(self):
        self.games_api = "https://www.gog.com/games/ajax/filtered"

    def search(self, query: str):
        parameters = {"search": query, "mediaType": "game", "limit": 5}
        r = self.send_request(self.games_api, parameters)
        products = {p["title"]: p for p in r.json()["products"] if p["isGame"]}

        try:
            best_match = products[
                util.case_insensitive_close_matches(query, products, n=1,
                                                    cutoff=0.90)[0]
            ]
            logger.debug("Best match is '%s'", best_match)
            return "https://www.gog.com/en/game/{slug}".format(**best_match)
        except IndexError:
            logger.debug("Unable to find %s in GOG search results", query)
            return None
