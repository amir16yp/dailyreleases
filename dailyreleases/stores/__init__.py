import logging
import re
from typing import Dict

from .web import web_search
from ..stores import steam, gog, epic

logger = logging.getLogger(__name__)


def find_store_links(game_name: str) -> Dict[str, str]:
    links = {}
    for store, name in ((steam, "Steam"), (gog, "GOG")):
        link = store.search(game_name)
        if link is not None:
            links[name] = link

    epic_link = epic.search(game_name)
    if epic_link is not None:
        links["EGS"] = epic_link

    if links:
        return links
    # If none of those worked, try Googling the game
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
    for link in web_search(f"{game_name} game buy"):
        for store_url, store_name in known_stores.items():
            if re.search(store_url, link, flags=re.IGNORECASE):
                return {store_name: link}

    logger.debug("Unable to find store links for %s", game_name)
    return {}
