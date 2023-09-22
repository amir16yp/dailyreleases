import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Iterable

from .Pre import Pre
from .stores.StoreHandler import StoreHandler
from .stores.Release import Release, ReleaseType, Platform

logger = logging.getLogger(__name__)


class ParseError(Exception):
    pass


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


def parse_pre(pre: Pre, offline=False) -> Release:
    if re.search("|".join(BLACKLISTED), pre.dirname, flags=re.IGNORECASE):
        raise ParseError("Contains blacklisted word")

    current_timestamp = int(datetime.utcnow().timestamp())
    two_days_ago_timestamp = current_timestamp - (48 * 3600)
    if pre.timestamp < two_days_ago_timestamp:
        raise ParseError("Older than 48 hours")

    logger.info("---")
    logger.info("Parsing: %s", pre.dirname)

    # Extract group name
    rls_name, group = pre.dirname.rsplit("-", maxsplit=1)

    # Find game name by matching until one of the stopwords
    game_name, *stopwords = re.split(
        "[._-]({})".format("|".join(STOPWORDS + TAGS + HIGHLIGHTS)),
        rls_name,
        flags=re.IGNORECASE,
    )

    # Prettify game name by substituting word delimiters with spaces
    game_name = re.sub("[_-]", " ", game_name)
    # Only dots separated by at least two character on either side are substituted to allow titles like "R.O.V.E.R."
    game_name = re.sub("[.](\w{2,})", " \g<1>", game_name)
    game_name = re.sub("(\w{2,})[.]", "\g<1> ", game_name)

    # Some stopwords distinguishes two otherwise identical releases (e.g. x86/x64) - we call these tags
    tags = [
        stopword
        for stopword in stopwords
        if re.match("|".join(TAGS), stopword, flags=re.IGNORECASE)
    ]

    # Some stopwords signify an important piece of information and deserve to be highlighted (e.g. PROPER)
    highlights = [
        stopword
        for stopword in stopwords
        if re.match("|".join(HIGHLIGHTS), stopword, flags=re.IGNORECASE)
    ]

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

    logger.info("Offline: %s %s : %s - %s", platform, rls_type, game_name, group)
    logger.info("Tags: %s. Highlights: %s", tags, highlights)

    release = Release.from_Pre(pre)

    if offline:
        return release

    # Find store links
    storehandler = StoreHandler()
    release.store_links = storehandler.find_store_links(game_name)

    # No store link? Probably software and not a game
    if not release.store_links:
        raise ParseError("No store link: probably software")

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


Releases = Dict[
    Platform, Dict[ReleaseType, List[Release]]
]  # {Windows: {Game: [..], DLC: [..], ..}, Linux: ...}


def parse_pres(pres: Iterable[Pre]) -> Releases:
    releases = {
        platform: {release_type: [] for release_type in ReleaseType}
        for platform in Platform
    }
    for pre in pres:
        try:
            release = parse_pre(pre)
            releases[release.platform][release.type].append(release)
        except ParseError as e:
            logger.info("Skipping %s: %s", pre.dirname, e)

    logger.debug("Parsed releases: %s", releases)
    return releases
