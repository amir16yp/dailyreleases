import logging
from datetime import datetime
from typing import NamedTuple, List
from urllib.error import HTTPError, URLError

from . import cache

logger = logging.getLogger(__name__)


class Pre(NamedTuple):
    dirname: str
    nfo_link: str
    timestamp: datetime


def get_pres() -> List[Pre]:
    logger.info("Getting pres from predbs")

    # PreDBs in order of preference
    predbs = (get_xrel, get_xrel_p2p, get_predbde)
    pres = {}
    for get in reversed(predbs):
        try:
            pres.update(
                (p.dirname, p) for p in get()
            )  # override duplicate dirnames in later iterations
        except (HTTPError, URLError) as e:
            logger.error(e)
            logger.warning("Connection to predb failed, skipping..")

    return list(pres.values())


def get_xrel(categories=("CRACKED", "UPDATE"), num_pages=2) -> List[Pre]:
    logger.debug("Getting pres from xrel.to")

    def get_releases_in_category(category, page):
        r = cache.get(
            "https://api.xrel.to/v2/release/browse_category.json",
            params={
                "category_name": category,
                "ext_info_type": "game",
                "per_page": 100,
                "page": page,
            },
        )
        return r.json["list"]

    return [
        Pre(
            dirname=rls["dirname"],
            nfo_link=rls["link_href"],
            timestamp=datetime.fromtimestamp(rls["time"]),
        )
        for category in categories
        for page in range(1, num_pages)
        for rls in get_releases_in_category(category, page)
    ]


def get_xrel_p2p() -> List[Pre]:
    logger.debug("Getting P2P pres from xrel.to")

    r = cache.get(
        "https://api.xrel.to/v2/p2p/releases.json",
        params={
            "category_id": "015d9c029",  # game
            "per_page": 100,
        },
    )

    return [
        Pre(
            dirname=rls["dirname"],
            nfo_link=rls["link_href"],
            timestamp=datetime.fromtimestamp(rls["pub_time"]),
        )
        for rls in r.json["list"]
    ]


def get_predbde(categories=("GAMES", "0DAY"), num_pages=5) -> List[Pre]:
    logger.debug("Getting pres from predb.de")

    def get_releases_in_category(category, page):
        r = cache.get(
            "https://predb.de/api/",
            params={"type": "section", "q": category, "page": page},
        )
        return r.json["data"]

    return [
        Pre(
            dirname=rls["release"],
            nfo_link="https://predb.de/rls/{}".format(rls["release"]),
            timestamp=datetime.fromtimestamp(float(rls["pretime"])),
        )
        for category in categories
        for page in range(1, num_pages)
        for rls in get_releases_in_category(category, page)
    ]
