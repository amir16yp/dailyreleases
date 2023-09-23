from __future__ import annotations

import logging
import re
from typing import TypeVar, Optional
from bs4 import BeautifulSoup

from .. import util
from ..APIHelper import APIHelper

logger = logging.getLogger(__name__)

AppID = TypeVar("AppID", int, str)


class Steam(APIHelper):
    def __init__(self):
        self.packagedetails_api = "https://store.steampowered.com/api/appdetails"
        self.appreview_api = "https://store.steampowered.com/appreviews/"
        self.eula_api = "https://store.steampowered.com//eula/"
        self.search_api = "https://store.steampowered.com/search/suggest"

    def get_appdetails(self, appid: str) -> dict:
        r = self.send_request(
            "https://store.steampowered.com/api/appdetails",
            {"appids": appid}
        )
        try:
            return r.json()[str(appid)]["data"]

        except KeyError:
            logger.exception("Could not retrieve Steam appdetails.")
            return dict()

    def get_packagedetails(self, appid: AppID) -> dict:
        r = self.send_request(self.packagedetails_api, {"packageids": appid})
        return r.json()[str(appid)]["data"]

    def get_appreviews(self, appid: str) -> tuple:
        params = {
                "start_date": -1,
                "end_date": -1,
                "filter": "summary",
                "language": "all",
                "purchase_type": "all",
                "json": 1,
                }
        try:
            api_url = f"{self.appreview_api}{appid}"
            response = self.send_request(api_url, params)
            response_data = response.json()
            if "query_summary" in response_data:
                summary = response_data["query_summary"]
                positive_reviews = summary["total_positive"]
                total_reviews = summary["total_reviews"]
                return positive_reviews, total_reviews
            else:
                return None
        except Exception as e:
            logger.exception(f"Could not retrieve app reviews. {e}")
            return None

    def get_eula(self, appid: AppID) -> str:
        r = self.send_request(f"{self.eula_api}{appid}_eula_0")
        soup = BeautifulSoup(r.text, "html.parser").find(id="eula_content")
        if soup is not None:
            return soup.text
        return ""

    def get_appid(self, game_name: str) -> str:
        logger.debug("Searching Steam store for %s", game_name)
        response = self.send_request(
            f"{self.search_api}",
            {"term": game_name, "f": "json", "cc": "US", "l": "english"}
            ).json()
        if not response:
            return None

        return response[0].get("id")

    def search(self, query: str) -> Optional[str]:
        logger.debug("Searching Steam store for %s", query)
        r = self.send_request(
            f"{self.search_api}",
            {"term": query, "f": "json", "cc": "US", "l": "english"}
            )

    # Reverse results to make the first one take precedence over later ones if multiple results have the same name.
    # E.g. "Wolfenstein II: The New Colossus" has both international and german version under the same name.
        items = {item["name"]: item for item in reversed(r.json())}

        try:
            best_match = items[
                util.case_insensitive_close_matches(query, items, n=1,
                                                    cutoff=0.90)[0]
                ]
            logger.debug("Best match is '%s'", best_match)
            type_to_slug = {"game": "app", "dlc": "app", "bundle": "bundle"}
            slug = type_to_slug.get(best_match["type"], best_match["type"])
            return f"https://store.steampowered.com/{slug}/{best_match['id']}"
        except IndexError:
            logger.debug("Unable to find %s in Steam search results", query)
            return None
