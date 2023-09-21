"""Generator is used to compile functions to generate a reddit post"""

import inspect
import logging
import textwrap
import time
from collections import defaultdict
from datetime import datetime, timedelta
from discord_webhook import DiscordWebhook

from . import util, reddit, parsing
from .PREdbs import PREdbs
from .Cache import Cache
from .Config import CONFIG
from .parsing import Releases, Release, ReleaseType

logger = logging.getLogger(__name__)


class Generator:
    def __init__(self):
        self.cache = Cache()
        self.cache.setup()


    def generate_post(self, releases: Releases) -> str:
        post = []
        for platform, platform_releases in releases.items():
            # Skip if platform doesn't contain any releases in any of the three release type categories
            if sum(len(pr) for pr in platform_releases.values()) == 0:
                continue

            post.append(f"# {platform}")
            for type, type_releases in platform_releases.items():
                if not type_releases:
                    continue

                # Releases in the tables are grouped by release group, and the groups are ordered according to the most
                # popular game within the group. Games are sorted by popularity internally in the groups as well.
                group_order = defaultdict(lambda: (0, -1, False))
                for release in type_releases:
                    group_order[release.group] = max(
                        group_order[release.group], release.get_popularity()
                    )

                def order(release: Release):
                    return (
                        group_order[release.group],
                        release.group,  # ensure grouping if two groups share group_order
                        release.get_popularity(),
                    )

                type_releases.sort(key=order, reverse=True)

                post.append(f"| {type} | Group | Store | Score (Reviews) |")
                post.append("|:-|:-|:-|:-|")
                post.extend(
                    "| {} | {} | {} | {} |".format(*rls.build_row()) for rls in type_releases
                )

                post.append("")
                post.append("&nbsp;")
                post.append("")

            post.append("")
            post.append("")

        if not post:
            logger.warning("Post is empty!")
            post.append("No releases today! :o")

        # Add epilogue
        try:
            with CONFIG.DATA_DIR.joinpath("epilogue.txt").open() as file:
                post.extend(line.rstrip() for line in file.readlines())
        except FileNotFoundError:
            logger.info("No epilogue.txt")

        # Convert post list to string
        post_str = "\n".join(post)

        logger.debug("Generated post:\n%s", post_str)
        return post_str

    @util.retry(attempts=int(CONFIG.CONFIG['main']['retry']), delay=120)
    def generate(self, post=False, pm_recipients=None) -> None:
        logger.info(
            "-------------------------------------------------------------------------------------------------"
        )
        start_time = time.time()
        #processed = self.cache.load_processed()
        predbs = PREdbs()
        pres = predbs.get_pres()

        #releases = parsing.parse_pres(pre for pre in pres if pre.dirname not in processed)
        releases = parsing.parse_pres(pre for pre in pres if pre.is_today() is True)

        # The date of the post changes at midday instead of midnight to allow calling script after 00:00
        title = f"Daily Releases ({(datetime.utcnow() - timedelta(hours=12)).strftime('%B %d, %Y')})"

        generated_post = self.generate_post(releases)
        generated_post_src = textwrap.indent(generated_post, "    ")
        self.cache.save_processed({p.dirname for p in pres})

        if post:
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
                logger.info("reddit is neither disabled nor enabled in config, assuming enabled")
            # Post to bot's own subreddit
            bot_subreddit = CONFIG.CONFIG["reddit"]["bot_subreddit"]
            reddit_src_post = reddit.submit_post(f"{title} - Source", generated_post_src, bot_subreddit)
            reddit_post = reddit.submit_post(title, generated_post, bot_subreddit)

            # Manually approve posts since reddit seem to think posts with many links are spam
            reddit_src_post.mod.approve()
            reddit_post.mod.approve()

            # We only need to save the latest pres since older ones will never show up again
            self.cache.save_processed(p.dirname for p in pres)

            if pm_recipients is not None:
                msg = inspect.cleandoc(
                    f"""
                    [Preview]({reddit_post.url})  
                    [Source]({reddit_src_post.url})  
                    """
                )
                for recipient in pm_recipients:
                    reddit.send_pm(recipient, title, msg)

        self.cache.clean()
        logger.info("Execution took %s seconds", int(time.time() - start_time))
        logger.info(
            "-------------------------------------------------------------------------------------------------"
        )
