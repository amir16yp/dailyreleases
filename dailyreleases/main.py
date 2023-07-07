import logging
from datetime import time, datetime, timedelta
from time import sleep

import prawcore

from . import __version__, reddit
from .config import CONFIG
from .generation import generate

logger = logging.getLogger(__name__)


def listen_inbox() -> None:
    logger.info("Listening on reddit inbox stream")
    authorized_users = CONFIG["reddit"]["authorized_users"].split(",")

    while True:
        try:
            for message in reddit.praw.inbox.stream():
                if message.author in authorized_users:
                    generate(post=True, pm_recipients=(message.author.name,))
                else:
                    logger.info(
                        "Discarding PM from %s: not authorized user", message.author
                    )
                message.mark_read()  # mark message read last so we can retry after potential fatal errors
        except prawcore.PrawcoreException as e:
            logger.warning("PrawcoreException: %s", e)
            logger.info("Restarting inbox listener..")
        except KeyboardInterrupt:
            print("Exiting (KeyboardInterrupt)")
            break


def at_midnight() -> None:
    while True:
        try:
            now = datetime.now()
            midnight = datetime.combine(now + timedelta(days=1), time.min)
            until_midnight = midnight - now
            logger.info(f"Waiting {until_midnight} until midnight..")
            sleep(until_midnight.total_seconds())
            generate(
                post=True, pm_recipients=CONFIG["reddit"]["notify_users"].split(",")
            )
        except Exception as e:
            logger.exception(e)
        except KeyboardInterrupt:
            print("Exiting (KeyboardInterrupt)")
            break


def main() -> None:
    try:
        print(f"Starting Daily Releases Bot v{__version__}")
        mode = CONFIG["main"]["mode"]
        logger.info("Mode is %s", mode)

        if mode == "test":
            generate(post=False)
        if mode == "immediately":
            generate(
                post=True, pm_recipients=CONFIG["reddit"]["notify_users"].split(",")
            )
        if mode == "midnight":
            at_midnight()
        if mode == "reply":
            listen_inbox()
    except Exception as e:
        logger.exception(e)
        raise e


if __name__ == "__main__":
    main()
