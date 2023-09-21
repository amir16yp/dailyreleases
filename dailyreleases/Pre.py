"""Class representing a PRE"""

from datetime import datetime


class Pre:
    def __init__(self, dirname: str, nfo_link: str, timestamp: int):
        self.dirname = dirname
        self.nfo_link = nfo_link
        self.timestamp = timestamp

    @classmethod
    def from_row(cls, row):
        pre = cls(
            dirname=row["dirname"],
            nfo_link=row["nfo_link"],
            timestamp=row["timestamp"]
        )
        return pre

    def from_today(self):
        timestamp_datetime = datetime.utcfromtimestamp(self.timestamp)
        today_date = datetime.now().date()
        if timestamp_datetime.date() == today_date:
            return True
        else:
            return False
