"""Class representing a PRE"""

from typing import NamedTuple
from datetime import datetime


class Pre(NamedTuple):
    dirname: str
    nfo_link: str
    timestamp: datetime
