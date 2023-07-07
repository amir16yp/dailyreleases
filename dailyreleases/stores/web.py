import logging
from typing import List
from urllib.error import HTTPError

from .. import cache
from ..config import CONFIG

logger = logging.getLogger(__name__)


def web_search(query: str) -> List[str]:
    logger.debug("Searching Google for %s", query)
    try:
        r = cache.get(
            "https://www.googleapis.com/customsearch/v1",
            params={
                "key": CONFIG["google"]["key"],
                "cx": CONFIG["google"]["cx"],
                "q": query,
            },
        )
        return [result["link"] for result in r.json["items"]]
    except (KeyError, HTTPError) as e:
        logger.exception(e)
        logger.warning("Google search failed (probably rate-limited)")
        return []
