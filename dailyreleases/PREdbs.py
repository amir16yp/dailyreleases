"""This class is used to query different PREdb APIs"""

import logging
from typing import List
from urllib.error import HTTPError, URLError
import mimetypes

from .Pre import Pre
from .Config import CONFIG
from .APIHelper import APIHelper

logger = logging.getLogger(__name__)


class PREdbs(APIHelper):
    def __init__(self):
        self.xrel_scene_api = "https://api.xrel.to/v2/release/browse_category.json"
        self.xrel_p2p_api = "https://api.xrel.to/v2/p2p/releases.json"
        self.predb_api = "https://api.predb.net/"

    def download_nfo(self, nfo_link: str, dirname: str, data_dir: str):
        try:
            r = self.send_request(nfo_link)
            content_type = r.content_type
            if r.status_code == 200 and content_type:
                extension = mimetypes.guess_extension(content_type)
                if not extension:
                    extension = '.nfo'
                nfo_dir = data_dir.joinpath("nfo")
                # Create the directory if it doesn't exist
                nfo_dir.mkdir(parents=True, exist_ok=True)
                nfo_filename = nfo_dir.joinpath(f"{dirname}{extension}")
                with open(nfo_filename, "wb") as nfo_file:
                    nfo_file.write(r.bytes)
                    logger.info(f"Downloaded NFO for {dirname} to "
                                f"{nfo_filename}")
            else:
                logger.warning(f"Failed to download NFO for {dirname}. "
                               f"Status code: {r.status_code}")
        except (HTTPError, URLError) as e:
            logger.warning(f"Failed to download NFO for {dirname}: {e}")

    def get_xrel_scene(self, categories=("CRACKED", "UPDATE")) -> List[Pre]:
        logger.debug("Getting PREs from xrel.to")

        xrel_releases = []

        for category in categories:
            parameters = {
                "category_name": category,
                "ext_info_type": "game",
                "per_page": 100,
                "page": 1,
                }
            release_list = self.send_request(self.xrel_scene_api,
                                             parameters)
            if release_list is not None:
                release_list = release_list.json().get("list")
            else:
                logger.error("Release list could not be retrieved.")
                continue

            for release_info in release_list:
                dirname = release_info["dirname"]
                nfo_link = release_info["link_href"]
                group = release_info["group_name"]
                timestamp = release_info["time"]
                xrel_releases.append(Pre(dirname, nfo_link, group, timestamp))
                logger.info(f"Release {dirname}, NFO: {nfo_link}")

        return xrel_releases

    def get_xrel_p2p(self) -> List[Pre]:
        logger.debug("Getting P2P pres from xrel.to")

        xrel_releases = []

        parameters = {
            "category_id": "015d9c029",  # game
            "per_page": 100
                      }
        release_list = self.send_request(self.xrel_p2p_api, parameters)
        if release_list is not None:
            release_list = release_list.json().get("list")
        else:
            logger.error("Release list could not be retrieved.")
            return xrel_releases

        for release_info in release_list:
            # pprint(release_info)
            dirname = release_info["dirname"]
            nfo_link = release_info["link_href"]
            if "group" in release_info.keys():
                if "name" in release_info['group'].keys():
                    group = release_info["group"]["name"]
            timestamp = release_info["pub_time"]
            xrel_releases.append(Pre(dirname, nfo_link, group, timestamp))
            logger.info(f"Release {dirname}, NFO: {nfo_link}")

        return xrel_releases

    def get_predbde(self) -> List[Pre]:
        logger.debug("Getting pres from predb.net")
        # Today and yesterday in case any were missed.
        built_api = f"{self.predb_api}?section=GAMES&date=today&date=yesterday"

        predb_releases = []

        response = self.send_request(built_api)
        if response is None:
            return predb_releases
        elif response.json().get("results") == 0:
            return predb_releases

        response = response.json()
        for rls in response.get("data"):
            dirname = rls["release"]
            nfo_link = "http://api.predb.net/nfoimg/{}.png".format(rls["release"])
            group = rls["group"]
            timestamp = rls["pretime"]
            predb_releases.append(Pre(dirname, nfo_link, group, timestamp))
            logger.info(f"Release: {dirname}, NFO Link: {nfo_link}")

        return predb_releases

    def get_pres(self) -> List[Pre]:
        logger.info("Getting pres from predbs")

        # PreDBs in order of preference
        predbs = [self.get_xrel_scene, self.get_xrel_p2p, self.get_predbde]
        pres = dict()

        for get_func in reversed(predbs):
            try:
                releases = get_func()
                # override duplicate dirnames in later iterations
                pres.update((pre.dirname, pre) for pre in releases)
            except (HTTPError, URLError) as e:
                logger.error(e)
                logger.warning("Connection to predb failed, skipping..")

        if CONFIG.CONFIG["main"]["backup_nfos"].lower() == "yes":
            logger.info("starting nfo download...")
            for pre in pres.values():
                self.download_nfo(pre.nfo_link, pre.dirname)

        return list(pres.values())
