from .. import util
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


class Release:
    def __init__(
        self,
        dirname: str,
        nfo_link: str,
        timestamp: datetime,
        rls_name: str,
        group: str,
        game_name: str,
        type: ReleaseType,
        platform: Platform,
        store_links: Dict[str, str] = None,
        tags: List[str] = None,
        highlights: List[str] = None,
        score: int = -1,
        num_reviews: int = -1,
    ):
        self.dirname = dirname
        self.nfo_link = nfo_link
        self.timestamp = timestamp
        self.rls_name = rls_name
        self.group = group
        self.game_name = game_name
        self.type = type
        self.platform = platform
        self.store_links = store_links or {}
        self.tags = tags or []
        self.highlights = highlights or []
        self.score = score
        self.num_reviews = num_reviews

    def build_row(self) -> str:
        # Bold row if Denuvo crack. We're checking this first so as to not actually insert 'DENUVO' as a highlight
        highlights = [
            h for h in self.highlights if h not in ("DENUVO",)
        ]  # avoids modifying original release object
        bold = highlights != self.highlights

        # The rows in the table containing updates will use the full rls_name as the name, while tables
        # containing game and DLC releases will show tags and highlights, as well as the stylized game_name.
        if self.type == ReleaseType.UPDATE:
            name = f"[{self.rls_name}]({self.nfo_link})"
        else:
            tags = " ({})".format(" ".join(self.tags)) if self.tags else ""
            highlights = " **- {}**".format(", ".join(highlights)) if highlights else ""
            name = "[{}{}]({}){}".format(
                util.markdown_escape(self.game_name), tags, self.nfo_link, highlights
            )

        stores = ", ".join(
            f"[{name}]({link})" for name, link in self.store_links.items()
        )

        if self.score == -1:
            reviews = "-"
        else:
            num_reviews_humanized = util.humanize(
                self.num_reviews, precision=1, prefix="dec", suffix=""
            )
            reviews = f"{self.score:.0%} ({num_reviews_humanized})"

        row = (name, self.group, stores, reviews)
        if bold:
            row = tuple(
                f"**{c.replace('**', '')}**" for c in row
            )  # .replace ensures no nested bold, which is unsupported

        return row

    def get_popularity(self):
        """
        - The popularity of a game is defined by the number of reviews it has
        on Steam, however:
        We rank RIPs lower than non-RIPs so the same game released as both will
        sort the non-RIP first. Releases with highlights (e.g. PROPER/DENUVO)
        are always ranked highest.
        """
        is_rip = "RIP" in [tag.upper() for tag in self.tags]
        return len(self.highlights), self.num_reviews, not is_rip
