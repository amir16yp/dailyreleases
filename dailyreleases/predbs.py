import logging
from datetime import datetime
from typing import NamedTuple, List
from urllib.error import HTTPError, URLError
import mimetypes

from . import cache
from .config import CONFIG, DATA_DIR

logger = logging.getLogger(__name__)

class Pre(NamedTuple):
    dirname: str
    nfo_link: str
    timestamp: datetime

def download_nfo(nfo_link, dirname):
    try:
        r = cache.get(nfo_link)
        content_type = r.content_type
        print(content_type)
        if r.status_code == 200 and content_type:
            extension = mimetypes.guess_extension(content_type)
            if not extension:
                extension = '.nfo'
            nfo_dir = DATA_DIR.joinpath("nfo")
            nfo_dir.mkdir(parents=True, exist_ok=True)  # Create the directory if it doesn't exist
            nfo_filename = nfo_dir.joinpath(f"{dirname}{extension}")
            with open(nfo_filename, "wb") as nfo_file:
                nfo_file.write(r.bytes)
                logger.info(f"Downloaded NFO for {dirname} to {nfo_filename}")
        else:
            logger.warning(f"Failed to download NFO for {dirname}. Status code: {r.status_code}")
    except (HTTPError, URLError) as e:
        logger.warning(f"Failed to download NFO for {dirname}: {e}")


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

    backup_nfos = CONFIG["main"]["backup_nfos"].lower() == "yes"

    for pre in pres.values():
        if backup_nfos:
            logger.info("starting nfo download...")
            download_nfo(pre.nfo_link, pre.dirname)

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

    releases = [
        Pre(
            dirname=rls["dirname"],
            nfo_link=rls["link_href"],
            timestamp=datetime.fromtimestamp(rls["time"]),
        )
        for category in categories
        for page in range(1, num_pages)
        for rls in get_releases_in_category(category, page)
    ]

    # Logging the NFO link
    for release in releases:
        logger.info(f"Release: {release.dirname}, NFO Link: {release.nfo_link}")

    return releases

def get_xrel_p2p() -> List[Pre]:
    logger.debug("Getting P2P pres from xrel.to")

    r = cache.get(
        "https://api.xrel.to/v2/p2p/releases.json",
        params={
            "category_id": "015d9c029",  # game
            "per_page": 100,
        },
    )

    releases = [
        Pre(
            dirname=rls["dirname"],
            nfo_link=rls["link_href"],
            timestamp=datetime.fromtimestamp(rls["pub_time"]),
        )
        for rls in r.json["list"]
    ]

    # Logging the NFO link
    for release in releases:
        logger.info(f"Release: {release.dirname}, NFO Link: {release.nfo_link}")

    return releases

def get_predbde(categories=("GAMES"), num_pages=5) -> List[Pre]:
    logger.debug("Getting pres from predb.net")

    def get_releases_in_category(category, page):
        r = cache.get(
            "https://api.predb.net/",
            params={"type": "section", "q": "GAMES", "page": page},
        )
        return r.json['data']

    releases = [
        Pre(
            dirname=rls["release"],
            nfo_link="http://api.predb.net/nfoimg/{}.png".format(rls["release"]),
            timestamp=datetime.fromtimestamp(float(rls["pretime"])),
        )
        for category in categories
        for page in range(1, num_pages)
        for rls in get_releases_in_category(category, page)
    ]

    # Logging the NFO link
    for release in releases:
        logger.info(f"Release: {release.dirname}, NFO Link: {release.nfo_link}")

    return releases
