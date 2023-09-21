"""The cache class is used to interact with the sqlite3 database"""

import logging
import sqlite3
from datetime import timedelta, datetime
from .Response import Response
from .Config import CONFIG
from typing import Set

logger = logging.getLogger(__name__)


class Cache:
    def __init__(self):
        connection = sqlite3.connect(CONFIG.DATA_DIR.joinpath("cache.sqlite"))
        # allow accessing rows by index and case-insensitively by name
        connection.row_factory = sqlite3.Row
        # do not try to decode bytes as utf-8 strings
        connection.text_factory = bytes
        self.connection = connection
        self.cache_time = timedelta(seconds=CONFIG.CONFIG["web"].getint("cache_time"))

    def load_processed(self) -> Set[str]:
        processed = self.connection.execute("SELECT dirname FROM processed"
                                            ).fetchall()
        # Decode dirnames to utf8 or comparsion will be a pain.
        dirnames = {row[0].decode("utf8") for row in processed}
        return dirnames

    def save_processed(self, processed: Set[str]) -> None:
        for dirname in processed:
            self.connection.execute("""
                                    INSERT OR REPLACE INTO processed (dirname)
                                    VALUES (?);
                                    """, (dirname,)
                                    )
        self.connection.commit()

    def setup(self):
        logger.debug("Setting up cache.")
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
            CREATE TABLE IF NOT EXISTS pres (
                id INTEGER PRIMARY KEY,
                dirname TEXT,
                nfo_link TEXT,
                timestamp INTEGER
                );
            """
        )
        self.connection.commit()

    def clean(self, older_than_days=3):
        cutoff_timestamp = (datetime.utcnow() - timedelta(
            days=older_than_days)).timestamp()
        self.connection.execute(
            """
            DELETE FROM requests
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

        if row is not None and datetime.fromtimestamp(row["timestamp"]) > \
                datetime.utcnow() - self.cache_time:
            logger.debug(f"Cache hit: {url}")
            return Response.from_row(row)
        else:
            return None

    def insert_response(self, url: str, response: Response, timestamp):
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

    def insert_pre(self, pre):
        self.connection.execute(
            """
            INSERT OR REPLACE INTO pres(dirname, nfo_link, timestamp)
            VALUES (:url, :response, :timestamp);
            """,
            {
                "dirname": pre.dirname,
                "nfo_link": pre.nfo_link,
                "timestamp": pre.timestamp,
            },
        )
        self.connection.commit()
        return
        