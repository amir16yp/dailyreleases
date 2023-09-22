from .. import util
from enum import Enum
from typing import Dict, List
from datetime import datetime
import re
import logging
from .StoreHandler import StoreHandler

logger = logging.getLogger(__name__)


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
        timestamp: int,
        rls_name: str,
        group: str,
        game_name: str,
        type: ReleaseType,
        platform: Platform,
        store_links: Dict[str, str] = None,
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
        self.score = score
        self.num_reviews = num_reviews

    @classmethod
    def from_Pre(cls, pre):

        logger.info("---")
        logger.info("Parsing: %s", pre.dirname)

        # Extract group name
        rls_name, group = pre.dirname.rsplit("-", maxsplit=1)
        group = pre.group_name

        # Prettify game name by substituting word delimiters with spaces
        game_name = re.sub("[_-]", " ", rls_name)
        # Only dots separated by at least two character on either side are substituted to allow titles like "R.O.V.E.R."
        game_name = re.sub("[.](\w{2,})", " \g<1>", game_name)
        game_name = re.sub("(\w{2,})[.]", "\g<1> ", game_name)

        # Find platform
        if re.search("mac[._-]?os[._-]?x?", rls_name, flags=re.IGNORECASE):
            platform = Platform.OSX
        elif re.search("linux", rls_name, flags=re.IGNORECASE):
            platform = Platform.LINUX
        else:
            platform = Platform.WINDOWS

        # Find release type (Game/DLC/Update)
        # Order of the if-statements is important: Update trumps DLC because an update to a DLC is an update, not a DLC!
        if re.search(
            "update|v[0-9]|addon|Crack[._-]?fix|DIR[._-]?FIX|build[._-]?[0-9]+",
            rls_name,
            flags=re.IGNORECASE,
        ):
            rls_type = ReleaseType.UPDATE
        elif re.search(
            "(?<!incl[._-])dlc", rls_name, flags=re.IGNORECASE
        ):  # 'Incl.DLC' isn't a DLC-release
            rls_type = ReleaseType.DLC
        else:
            rls_type = ReleaseType.GAME

        release = cls(
            dirname=pre.dirname,
            nfo_link=pre.nfo_link,
            timestamp=pre.timestamp,
            rls_name=rls_name,
            group=group,
            game_name=game_name,
            type=rls_type,
            platform=platform,
        )


        # Find store links
        storehandler = StoreHandler()
        release.store_links = storehandler.find_store_links(game_name)

        # If one of the store links we found is to Steam, use their API to get (better) information about the game.
        if "Steam" in release.store_links:
            try:
                storehandler.steam.update_info(release)
            except Exception as e:  # a lot of stuff can go wrong with Steam's API, better catch everything
                logger.error(
                    "Failed to update release info using Steam's API on %s", release
                )
                logger.exception(e)

        logger.info(
            "Final  : %s %s : %s - %s  :  %s",
            release.platform,
            release.type,
            release.game_name,
            release.group,
            release,
        )
        return release
        

    def build_row(self) -> str:
        # The rows in the table containing updates will use the full rls_name as the name, while tables
        # containing game and DLC releases will show tags and highlights, as well as the stylized game_name.
        if self.type == ReleaseType.UPDATE:
            name = f"[{self.rls_name}]({self.nfo_link})"
        else:
            name = "[{}{}]({}){}".format(
                util.markdown_escape(self.game_name), self.nfo_link
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

        return row

    def get_popularity(self):
        return tuple()
