"""Generator is used to compile functions to generate a reddit post"""

import inspect
import logging
import textwrap
import time
import re
from typing import List
from datetime import datetime, timedelta
from discord_webhook import DiscordWebhook

from . import util
from .RedditHandler import RedditHandler
from .PREdbs import PREdbs
from .Cache import Cache
from .Pre import Pre
from .Config import CONFIG
from .stores.StoreHandler import StoreHandler

logger = logging.getLogger(__name__)


class Generator:
    def __init__(self):
        self.reddit_handler = RedditHandler()
        self.store_handler = StoreHandler()
        self.predb_handler = PREdbs()
        self.cache = Cache()

    def remove_duplicate_lines(self, input_string):
        # Split the input string into lines
        lines = input_string.splitlines()

        # Set to track lines that have been seen
        seen_lines = set()

        # Define exception lines that should be ignored
        exception_lines = ['| :---- | :---- | :---- | :---- |', '&nbsp;', '']

        # List to hold non-duplicate lines
        result_lines = []

        # Count of total duplicate lines removed
        total_duplicates_removed = 0

        # Iterate through each line in the input string
        for line in lines:
            # Strip leading and trailing whitespace
            stripped_line = line.strip()

            # Check if the stripped line is in exception_lines
            if stripped_line in exception_lines:
                result_lines.append(line)
                continue # Skip this line and move to the next iteration

            # Check if the stripped line has been seen before
            if stripped_line in seen_lines:
                total_duplicates_removed += 1  # Increment total duplicates removed count
            else:
                seen_lines.add(stripped_line)  # Add stripped line to seen_lines
                result_lines.append(line)  # Add non-stripped line to result_lines

        logger.debug(f"Removed {total_duplicates_removed} duplicate lines")
        return '\n'.join(result_lines)

    def generate_post(self, pres: List[Pre]) -> str:
        post = []
        update_releases = []
        dlc_releases = []
        game_releases = []

        for pre in pres:
            if pre.release_type == "update":
                update_releases.append(pre)
            elif pre.release_type == "dlc":
                dlc_releases.append(pre)
            elif pre.release_type == "game":
                game_releases.append(pre)

        game_releases = sorted(game_releases, key=lambda pre: pre.group_name)
        update_releases = sorted(update_releases, key=lambda pre: pre.group_name)
        dlc_releases = sorted(dlc_releases, key=lambda pre: pre.group_name)

        if game_releases:
            post.append("| Game | Group | Stores | Review |")
            post.append("| :---- | :---- | :---- | :---- |")
            for pre in game_releases:
                post.append(pre.to_reddit_row())
            post.append("")
            post.append("&nbsp;")
            post.append("")
        if update_releases:
            post.append("| Update | Group | Stores | Reviews |")
            post.append("| :---- | :---- | :---- | :---- |")
            for pre in update_releases:
                post.append(pre.to_reddit_row())
            post.append("")
            post.append("&nbsp;")
            post.append("")
        if dlc_releases:
            post.append("| DLC | Group | Stores | Reviews |")
            post.append("| :---- | :---- | :---- | :---- |")
            for pre in dlc_releases:
                post.append(pre.to_reddit_row())
            post.append("")
            post.append("&nbsp;")
            post.append("")

        if not post:
            logger.warning("Post is empty!")
            post.append("No releases today! :o")

        # Add epilogue
        try:
            post.append("")
            post.append("")
            with CONFIG.DATA_DIR.joinpath("epilogue.txt").open() as file:
                post.extend(line.rstrip() for line in file.readlines())
        except FileNotFoundError:
            logger.info("No epilogue.txt")

        # Convert post list to string
        post_str = "\n".join(post)
        post_str = self.remove_duplicate_lines(post_str)

        logger.debug("Generated post:\n%s", post_str)
        return post_str

    @util.retry(attempts=int(CONFIG.CONFIG['main']['retry']), delay=120)
    def generate(self, discord_post=False, pm_recipients=None) -> None:
        logger.info(
            "-------------------------------------------------------------------------------------------------"
        )
        start_time = time.time()

        pres = self.predb_handler.get_pres()
        relevant_pres = []
        
        for pre in pres:
            if pre.from_today() is True:
                relevant_pres.append(pre)
            elif pre.from_yesterday() is True and self.cache.get_pre_by_dirname(pre.dirname) is None:
                # This branch checks if a pre was missed the day before
                relevant_pres.append(pre)
            else:
                continue

        for pre in relevant_pres:
            self.cache.insert_pre(pre)
            pre.steam_link = self.store_handler.steam.search(pre.game_name)
            pre.gog_link = self.store_handler.gog.search(pre.game_name)
            pre.epic_link = self.store_handler.epic.search(pre.game_name)

            if pre.steam_link is not None:
                match = re.search(r"/(\d+)/?$", pre.steam_link)
                appid = match.group(1)
                bundled_reviews = self.store_handler.steam.get_appreviews(appid)
                if bundled_reviews is not None:
                    positive_reviews, total_reviews = bundled_reviews
                    pre.positive_reviews = positive_reviews
                    pre.total_reviews = total_reviews
                
            
        # The date of the post changes at midday instead of midnight to allow calling script after 00:00
        title = f"Daily Releases ({(datetime.utcnow() - timedelta(hours=12)).strftime('%B %d, %Y')})"

        generated_post = self.generate_post(relevant_pres)
        generated_post_src = textwrap.indent(generated_post, "    ")

        if discord_post:
            # post to discord
            webhook_url = CONFIG.CONFIG["discord"]["webhook_url"]
            webhook = DiscordWebhook(url=webhook_url, content=title)
            webhook.add_file(generated_post.encode(), filename=title + '.txt')
            webhook.execute()
            if CONFIG.CONFIG["reddit"]["enable"] == "no":
                return
            elif CONFIG.CONFIG["reddit"]["enable"] == "yes":
                pass
            else:
                logger.info("reddit is neither disabled nor enabled in config "
                            ", assuming enabled")
            # Post to bot's own subreddit
            bot_subreddit = CONFIG.CONFIG["reddit"]["bot_subreddit"]
            reddit_src_post = self.reddit_handler.submit_post(f"{title} - Source",
                                                              generated_post_src,
                                                              bot_subreddit)
            reddit_post = self.reddit_handler.submit_post(title,
                                                          generated_post,
                                                          bot_subreddit)

            # Manually approve posts since reddit seem to think posts with many links are spam
            reddit_src_post.mod.approve()
            reddit_post.mod.approve()

            if pm_recipients is not None:
                msg = inspect.cleandoc(
                    f"""
                    [Preview]({reddit_post.url})  
                    [Source]({reddit_src_post.url})  
                    """
                )
                for recipient in pm_recipients:
                    self.reddit_handler.send_pm(recipient, title, msg)
        self.cache.clean()
        logger.info("Execution took %s seconds", int(time.time() - start_time))
        logger.info(
            "-------------------------------------------------------------------------------------------------"
        )
