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
    def __init__(self, cache: Cache):
        self.cache = cache

    def build_row(self, release: Release):
        # Bold row if Denuvo crack. We're checking this first so as to not actually insert 'DENUVO' as a highlight
        highlights = [
            h for h in release.highlights if h not in ("DENUVO",)
        ]  # avoids modifying original release object
        bold = highlights != release.highlights

        # The rows in the table containing updates will use the full rls_name as the name, while tables
        # containing game and DLC releases will show tags and highlights, as well as the stylized game_name.
        if release.type == ReleaseType.UPDATE:
            name = f"[{release.rls_name}]({release.nfo_link})"
        else:
            tags = " ({})".format(" ".join(release.tags)) if release.tags else ""
            highlights = " **- {}**".format(", ".join(highlights)) if highlights else ""
            name = "[{}{}]({}){}".format(
                util.markdown_escape(release.game_name), tags, release.nfo_link, highlights
            )

        stores = ", ".join(
            f"[{name}]({link})" for name, link in release.store_links.items()
        )

        if release.score == -1:
            reviews = "-"
        else:
            num_reviews_humanized = util.humanize(
                release.num_reviews, precision=1, prefix="dec", suffix=""
            )
            reviews = f"{release.score:.0%} ({num_reviews_humanized})"

        row = (name, release.group, stores, reviews)
        if bold:
            row = tuple(
                f"**{c.replace('**', '')}**" for c in row
            )  # .replace ensures no nested bold, which is unsupported

        return row

    def get_popularity(self, release: Release):
        """
        - The popularity of a game is defined by the number of reviews it has
        on Steam, however:
        We rank RIPs lower than non-RIPs so the same game released as both will
        sort the non-RIP first. Releases with highlights (e.g. PROPER/DENUVO)
        are always ranked highest.
        """
        is_rip = "RIP" in [tag.upper() for tag in release.tags]
        return len(release.highlights), release.num_reviews, not is_rip

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
                        group_order[release.group], self.get_popularity(release)
                    )

                def order(release: Release):
                    return (
                        group_order[release.group],
                        release.group,  # ensure grouping if two groups share group_order
                        self.get_popularity(release),
                    )

                type_releases.sort(key=order, reverse=True)

                post.append(f"| {type} | Group | Store | Score (Reviews) |")
                post.append("|:-|:-|:-|:-|")
                post.extend(
                    "| {} | {} | {} | {} |".format(*self.build_row(rls)) for rls in type_releases
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
        processed = self.cache.load_processed()
        predbs = PREdbs()
        pres = predbs.get_pres()

        releases = parsing.parse_pres(pre for pre in pres if pre.dirname not in processed)

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
