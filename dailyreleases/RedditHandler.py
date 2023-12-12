"""Used to handle actions for Reddit"""

import logging
import re
import praw
from praw.models import Submission
from .Config import CONFIG

logger = logging.getLogger(__name__)


class RedditHandler:
    def __init__(self):
        self.praw_handler = praw.Reddit(**CONFIG.CONFIG["reddit"])

    def submit_post(self, title: str, text: str, subreddit: str) -> Submission:
        logger.info("Submitting post to r/%s", subreddit)
        return self.praw_handler.subreddit(subreddit).submit(title, text)

    def get_previous_daily_post(self, subreddit: str) -> Submission:
        logger.info("Getting previous daily post from r/%s", subreddit)
        posts = self.praw_handler.subreddit(subreddit).search(
            'title:"daily releases"', sort="new", syntax="lucene",
            time_filter="week")
        return next(p for p in posts if re.search(
            r"daily release.*[(].* \d\d\d\d[)]", p.title, flags=re.IGNORECASE))
