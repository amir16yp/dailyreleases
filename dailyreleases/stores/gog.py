from __future__ import annotations

import logging
from typing import Optional

from .. import util, cache

logger = logging.getLogger(__name__)


def search(query: str) -> Optional[str]:
    logger.debug("Searching GOG for %s", query)
    r = cache.get(
        "https://www.gog.com/games/ajax/filtered",
        params={"search": query, "mediaType": "game", "limit": 5},
    )
    products = {p["title"]: p for p in r.json["products"] if p["isGame"]}

    try:
        best_match = products[
            util.case_insensitive_close_matches(query, products, n=1, cutoff=0.90)[0]
        ]
        logger.debug("Best match is '%s'", best_match)
        return "https://www.gog.com/en/game/{slug}".format(**best_match)
    except IndexError:
        logger.debug("Unable to find %s in GOG search results", query)
        return None
