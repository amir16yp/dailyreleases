"""The cache class is used to interact with the sqlite3 database"""

import logging
import sqlite3
from datetime import timedelta, datetime

from .Response import Response
from .Pre import Pre
from .Config import CONFIG


logger = logging.getLogger(__name__)


class Cache:
    def __init__(self):
        connection = sqlite3.connect(CONFIG.DATA_DIR.joinpath("cache.sqlite"))
        # allow accessing rows by index and case-insensitively by name
        connection.row_factory = sqlite3.Row
        self.connection = connection
        self.cache_time = timedelta(seconds=CONFIG.CONFIG["web"].getint(
            "cache_time"))

    def setup(self):
        logger.debug("Setting up cache.")
        # TODO: table requests obsolete?
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS
            requests (id INTEGER PRIMARY KEY,
                      url TEXT UNIQUE NOT NULL,
                      response BLOB NOT NULL,
                      timestamp INTEGER NOT NULL);
            """
        )
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS
            pres (id INTEGER PRIMARY KEY,
                  dirname TEXT,
                  nfo_link TEXT,
                  group_name TEXT,
                  timestamp INTEGER);
            """
        )
        self.connection.commit()

    def clean(self, older_than_days=3):
        # Removes PREs from Cache that are older than specified days
        cutoff_timestamp = (datetime.utcnow() - timedelta(
            days=older_than_days)).timestamp()
        self.connection.execute(
            """
            DELETE FROM pres
            WHERE timestamp < :cutoff;
            """,
            {
                "cutoff": cutoff_timestamp,
            },
        )
        self.connection.commit()
        self.connection.executescript("VACUUM;")

    def get_response_by_url(self, url: str) -> Response:
        row = self.connection.execute(
            """
            SELECT response, timestamp
            FROM requests
            WHERE url = :url;
            """,
            {"url": url},
        ).fetchone()

        if row is not None:
            logger.debug(f"Cache hit: {url}")
            return Response.from_row(row)
        else:
            return None

    def get_pre_by_dirname(self, dirname: str) -> Pre:
        row = self.connection.execute(
            """
            SELECT dirname, nfo_link, group_name, timestamp
            FROM pres
            WHERE dirname = :dirname;
            """,
            {"dirname": dirname},
        ).fetchone()

        if row is not None:
            logger.debug(f"Cache hit: {dirname}")
            return Pre.from_row(row)
        else:
            return None

    def insert_response(self, url: str, response: Response, timestamp: int):
        self.connection.execute(
            """
            INSERT OR REPLACE INTO requests(url, response, timestamp)
            VALUES (:url, :response, :timestamp);
            """,
            {
                "url": url,
                "response": response.content,
                "timestamp": timestamp,
            },
        )
        self.connection.commit()
        return

    def insert_pre(self, pre: Pre):
        self.connection.execute(
            """
            INSERT OR REPLACE INTO pres(dirname, nfo_link, group_name, timestamp)
            VALUES (:dirname, :nfo_link, :group_name, :timestamp);
            """,
            {
                "dirname": pre.dirname,
                "nfo_link": pre.nfo_link,
                "group_name": pre.group_name,
                "timestamp": pre.timestamp,
            },
        )
        self.connection.commit()
        return
