
import json
import logging
import sqlite3
import time
from collections import defaultdict
from datetime import timedelta, datetime
from typing import Mapping, Optional
import urllib.parse

import requests  # Import the 'requests' library

from .config import DATA_DIR, CONFIG

logger = logging.getLogger(__name__)

connection = sqlite3.connect(DATA_DIR.joinpath("cache.sqlite"))
connection.row_factory = (
    sqlite3.Row
)  # allow accessing rows by index and case-insensitively by name
connection.text_factory = bytes  # do not try to decode bytes as utf-8 strings

DEFAULT_CACHE_TIME = timedelta(seconds=CONFIG["web"].getint("cache_time"))
logger.info("Default cache time is %s", DEFAULT_CACHE_TIME)


class Response:
    def __init__(self, bytes: bytes = None, status_code: int = None, content_type: str = None) -> None:
        self.bytes = bytes
        #self.text = self.bytes.decode()  # TODO: Detect encoding
        self.status_code = status_code
        self.content_type = content_type
    @property
    def json(self):
        return json.loads(self.bytes)


def setup():
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS
        requests (id INTEGER PRIMARY KEY,
                  url TEXT UNIQUE NOT NULL,
                  response BLOB NOT NULL,
                  timestamp INTEGER NOT NULL);
        """
    )


def clean(older_than=timedelta(days=3)):
    connection.execute(
        """
        DELETE FROM requests
        WHERE timestamp < :cutoff;
        """,
        {
            "cutoff": (datetime.utcnow() - older_than).timestamp(),
        },
    )
    connection.commit()
    connection.executescript("VACUUM;")


last_request = defaultdict(float)


def get(
    url: str,
    params: Mapping = None,
    cache_time: timedelta = DEFAULT_CACHE_TIME,
    ratelimit: Optional[float] = 1,
    *args,
    **kwargs
) -> Response:
    """
    Sends a GET request, caching the result for cache_time. If 'ratelimit' is supplied, requests are rate limited at the
    host-level to this number of requests per second.
    """
    if params is not None:
        url += "?" + urllib.parse.urlencode(params)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:65.0) Gecko/20100101 Firefox/65.0"
    }

    # logger.debug("Get %s", url)

    row = connection.execute(
        """
        SELECT response, timestamp
        FROM requests
        WHERE url = :url;
        """,
        {"url": url},
    ).fetchone()

    if (
        row is not None
        and datetime.fromtimestamp(row["timestamp"]) > datetime.utcnow() - cache_time
    ):
        # logger.debug("Cache hit: %s", url)
        return Response(row["response"])

    # logger.debug("Cache miss: %s", url)
    if ratelimit is not None:
        min_interval = 1 / ratelimit
        elapsed = time.time() - last_request[url]
        wait = min_interval - elapsed
        if wait > 0:
            # logger.debug("Rate-limited for %ss", round(wait, 2))
            time.sleep(wait)

    response = requests.get(url, headers=headers, *args, **kwargs)  # Use requests.get to send the request

    last_request[url] = time.time()
    connection.execute(
        """
        INSERT OR REPLACE INTO requests(url, response, timestamp)
        VALUES (:url, :response, :timestamp);
        """,
        {
            "url": url,
            "response": response.content,
            "timestamp": datetime.utcnow().timestamp(),
        },
    )
    connection.commit()
    return Response(bytes=response.content, status_code=response.status_code, content_type=response.headers.get("content-type"))


setup()
