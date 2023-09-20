from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List
from datetime import datetime


class ReleaseType(str, Enum):
    GAME = "Game"
    UPDATE = "Update"
    DLC = "DLC"

    def __str__(self) -> str:
        return self.value


class Platform(str, Enum):
    WINDOWS = "Windows"
    OSX = "Mac OSX"
    LINUX = "Linux"

    def __str__(self) -> str:
        return self.value


@dataclass
class Release:
    dirname: str
    nfo_link: str
    timestamp: datetime
    rls_name: str  # dirname without group
    group: str
    game_name: str
    type: ReleaseType
    platform: Platform
    store_links: Dict[str, str] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    highlights: List[str] = field(default_factory=list)
    score: int = (
        -1
    )
    # score and number of reviews is -1 by default; updated if the game is on Steam
    num_reviews: int = -1
