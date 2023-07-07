from __future__ import annotations

import logging
import re
from typing import TypeVar, Optional, Tuple

from bs4 import BeautifulSoup

from .. import util, cache

logger = logging.getLogger(__name__)

AppID = TypeVar("AppID", int, str)


def appdetails(appid: AppID) -> dict:
    r = cache.get(
        "https://store.steampowered.com/api/appdetails", params={"appids": appid}
    )
    return r.json[str(appid)]["data"]


def packagedetails(appid: AppID) -> dict:
    r = cache.get(
        "https://store.steampowered.com/api/packagedetails",
        params={"packageids": appid},
    )
    return r.json[str(appid)]["data"]


def appreviews(appid: AppID) -> dict:
    r = cache.get(
        f"https://store.steampowered.com/appreviews/{appid}",
        params={
            "start_date": -1,
            "end_date": -1,
            "filter": "summary",
            "language": "all",
            "purchase_type": "all",
            "json": 1,
        },
    )
    return r.json["query_summary"]


def reviews(appid: AppID) -> Tuple[int, int]:
    app_review = appreviews(appid)

    if app_review["total_reviews"] == 0:
        return -1, -1

    positive = app_review["total_positive"] / app_review["total_reviews"]
    return positive, app_review["total_reviews"]


def eula(appid: AppID) -> str:
    r = cache.get(f"https://store.steampowered.com//eula/{appid}_eula_0")
    soup = BeautifulSoup(r.text, "html.parser").find(id="eula_content")
    if soup is not None:
        return soup.text
    return ""


def search(query: str) -> Optional[str]:
    logger.debug("Searching Steam store for %s", query)
    r = cache.get(
        "https://store.steampowered.com/search/suggest",
        params={"term": query, "f": "json", "cc": "US", "l": "english"},
    )

    # Reverse results to make the first one take precedence over later ones if multiple results have the same name.
    # E.g. "Wolfenstein II: The New Colossus" has both international and german version under the same name.
    items = {item["name"]: item for item in reversed(r.json)}

    try:
        best_match = items[
            util.case_insensitive_close_matches(query, items, n=1, cutoff=0.90)[0]
        ]
        logger.debug("Best match is '%s'", best_match)
        type_to_slug = {"game": "app", "dlc": "app", "bundle": "bundle"}
        slug = type_to_slug.get(best_match["type"], best_match["type"])
        return f"https://store.steampowered.com/{slug}/{best_match['id']}"
    except IndexError:
        logger.debug("Unable to find %s in Steam search results", query)
        return None


def update_info(release: Release) -> None:
    logger.debug("Getting information about game using Steam API")
    link = release.store_links["Steam"]
    link_type, appid = re.search("(app|sub|bundle)(?:/)([0-9]+)", link).groups()

    if link_type == "bundle":
        logger.debug(
            "Steam link is to bundle: not utilizing API"
        )  # Steam has no public API for bundles
        return

    # If the link is a package on Steam (e.g. game + dlc), we need to find the base game of the package
    if link_type == "sub":
        package_details = packagedetails(appid)

        # Set game name to package name (e.g. 'Fallout New Vegas Ultimate' instead of 'Fallout New Vegas')
        release.game_name = package_details["name"]

        # Use the "base game" of the package as the basis for further computation.
        # We guesstimate the base game as the most popular app (i.e. the one with most reviews) among the first three
        package_appids = [app["id"] for app in package_details["apps"][:3]]
        package_apps_details = [appdetails(appid) for appid in package_appids]
        details = max(
            package_apps_details, key=lambda app: reviews(app["steam_appid"])[1]
        )
        appid = details["steam_appid"]

    # Otherwise, if the release is a single game on Steam
    else:
        details = appdetails(appid)
        release.game_name = details["name"]

    # Now that we have a single Steam game to represent the release, use it to improve the information
    release.score, release.num_reviews = reviews(appid)

    # DLC releases don't always contain the word "dlc" (e.g. 'Fallout New Vegas: Dead Money'), so some DLCs get
    # mislabeled as games during offline parsing. We can use Steam's API to get the correct type, but if the release was
    # already deemed an update, keep it as such, because an update to a DLC is an update.
    if details["type"] == "dlc" and release.type != "Update":
        release.type = "DLC"

    # Add highlight if "denuvo" occurs in Steam's DRM notice or potential 3rd-party EULA
    if (
        "denuvo" in details.get("drm_notice", "").lower()
        or "denuvo" in eula(appid).lower()
    ):
        logger.info(
            "'denuvo' found in Steam DRM-notice/EULA; adding 'DENUVO' to highlights"
        )
        release.highlights.append("DENUVO")
