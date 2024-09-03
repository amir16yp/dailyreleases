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
        try:
            response = requests.get(url, params=parameters)
            response.raise_for_status()

            return response
        except Exception as e:
            logger.exception(e)
            logger.warning("Failed to send request.")
            return None
