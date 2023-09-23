"""Class representing a PRE"""

from datetime import datetime, timedelta
import re

STOPWORDS = (
    "update",
    "v[0-9]+",
    "build[._-]?[0-9]+",
    "iNTERNAL",
    "incl",
    "Standalone",
    "Multilanguage",
    "DLC",
    "DLC[._-]?Unlocker",
    "Steam[._-]?Edition",
    "GOG",
    "mac[._-]?os[._-]?x?",
    "linux",
)

TAGS = (
    "Hotfix",
    "Crack[._-]?fix",
    "Dir[._-]?fix",
    "MULTI[._-]?[0-9]+",
    "x(?:86|64)",
    "(?:86|64)[._-]?bit",
    "RIP",
    "REPACK",
    "German",
    "Czech",
    "Russian",
    "Korean",
    "Italian",
    "Swedish",
    "Danish",
    "French",
    "Slovak",
)

HIGHLIGHTS = (
    "PROPER",
    "READNFO",
)

BLACKLISTED = (
    "Keygen",
    "Keymaker",
    "[._-]3DS",
    "[._-]NSW",
    "[._-]PS4",
    "[._-]PSP",
    "[._-]Wii",
    "[._-]WiiU",
    "x264",
    "720p",
    "1080p",
    "eBook",
    "TUTORIAL",
    "Debian",
    "Ubuntu",
    "Fedora",
    "openSUSE",
    "jQuery",
    "CSS" "ASP[._-]NET",
    "Windows[._-]Server",
    "Lynda",
    "OREILLY" "Wintellectnow",
    "3ds[._-]?Max",
    "For[._-]Maya",
    "Cinema4D",
)


class Pre:
    def __init__(self, dirname: str, nfo_link: str, group_name: str,
                 timestamp: int):
        self.dirname = dirname
        self.game_name = self.format_dirname()
        self.nfo_link = nfo_link
        self.group_name = group_name
        self.timestamp = timestamp
        self.positive_reviews: int = 0
        self.total_reviews: int = 0
        self.steam_link = None
        self.gog_link = None
        self.epic_link = None

        if re.search("update|addon|Crack[._-]?fix|DIR[._-]?FIX|build[._-]?[0-9]+",
                     dirname,
                     flags=re.IGNORECASE,):
            self.release_type = "update"
        elif re.search(
            "(?<!incl[._-])dlc", dirname, flags=re.IGNORECASE
        ):  # 'Incl.DLC' isn't a DLC-release
            self.release_type = "dlc"
        else:
            self.release_type = "game"

    @classmethod
    def from_row(cls, row):
        pre = cls(
            dirname=row["dirname"],
            nfo_link=row["nfo_link"],
            group_name=row["group_name"],
            timestamp=row["timestamp"]
        )
        return pre

    def format_dirname(self) -> str:
        hyphen_index = self.dirname.find("-")
        rls_name = self.dirname[:hyphen_index]
        game_name, *stopwords = re.split(
            r"[._-]({})".format("|".join(STOPWORDS + TAGS + HIGHLIGHTS)),
            rls_name,
            flags=re.IGNORECASE,
            )

        # Prettify game name by substituting word delimiters with spaces
        game_name = re.sub("[_-]", " ", game_name)
        # Only dots separated by at least two character on either side are substituted to allow titles like "R.O.V.E.R."
        game_name = re.sub(r"[.](\w{2,})", r" \g<1>", game_name)
        game_name = re.sub(r"(\w{2,})[.]", r"\g<1> ", game_name)

        return game_name

    def from_today(self) -> bool:
        timestamp_datetime = datetime.utcfromtimestamp(self.timestamp)
        today_date = datetime.now().date()
        if timestamp_datetime.date() == today_date:
            return True
        else:
            return False

    def from_yesterday(self) -> bool:
        timestamp_datetime = datetime.utcfromtimestamp(self.timestamp)
        yesterday_date = datetime.now().date() - timedelta(days=1)
        if timestamp_datetime.date() == yesterday_date:
            return True
        else:
            return False
    
    def to_reddit_row(self):
        stores = []
        if self.steam_link is not None:
            stores.append("[Steam](self.steam_link)")
        if self.gog_link is not None:
            stores.append("[GOG](self.gog_link)")
        if self.epic_link is not None:
            stores.append("[Epic](self.epic_link)")

        stores_formatted = ", ".join(stores)

        # Review ratio is only calculated using Steam reviews.
        if not self.steam_link:
            review_formatted = "-"
        elif self.positive_reviews == 0 or self.total_reviews == 0:
            review_formatted = "-"
        else:
            ratio = self.positive_reviews / self.total_reviews
            if self.total_reviews >= 1000:
                review_formatted = f"{ratio * 100:.2f}% ({self.total_reviews / 1000:.1f}k)"
            else:
                review_formatted = f"{ratio * 100:.2f}% ({self.positive_reviews})"

        if self.release_type == "game":
            row = f"| {self.game_name} | {self.group_name} | {stores_formatted} | {review_formatted} |"
        else:
            row = f"| {self.dirname} | {self.group_name} | {stores_formatted} | {review_formatted} |"

        return row
