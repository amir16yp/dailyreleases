"""Inherited by multiple classes to avoid code redundancy"""

import requests
import logging
from typing import List
from urllib.error import HTTPError

from .Config import CONFIG

logger = logging.getLogger(__name__)


class APIHelper():
    def __init__(self):
        pass

    def send_request(self, url: str, parameters: dict = None):
        # Sends a get-request to the api_url with the parameters.
        try:
            response = requests.get(url, params=parameters)
            response.raise_for_status()

            return response
        except Exception as e:
            logger.exception(e)
            logger.warning("Failed to send request.")
            return None

    def web_search(self, query: str) -> List[str]:
        logger.debug("Searching Google for %s", query)
        try:
            google_api = "https://www.googleapis.com/customsearch/v1"
            params = {
                    "key": CONFIG.CONFIG["google"]["key"],
                    "cx": CONFIG.CONFIG["google"]["cx"],
                    "q": query,
                    }
            r = self.send_request(google_api, params)
            if r is None:
                return []
            else:
                return [result["link"] for result in r.json()["items"]]
        except (KeyError, HTTPError) as e:
            logger.exception(e)
            logger.warning("Google search failed (probably rate-limited)")
            return []
