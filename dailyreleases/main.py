import logging
from datetime import time, datetime, timedelta
from time import sleep
from discord_webhook import DiscordWebhook
import prawcore

from .stores import StoreHandler
from . import __version__, reddit
from .Config import CONFIG
from .Generator import Generator
from .Cache import Cache

logger = logging.getLogger(__name__)
cache = Cache()
cache.setup()
generator = Generator(cache)

debug_discord_webhook_url = CONFIG.CONFIG["discord"]["debug_webhook_url"]

class DiscordLogHandler(logging.Handler):
    def emit(self, record):
        log_msg = self.format(record)
        webhook = DiscordWebhook(url=debug_discord_webhook_url, content=log_msg)
        response = webhook.execute()

def listen_inbox() -> None:
    logger.info("Listening on reddit inbox stream")
    authorized_users = CONFIG["reddit"]["authorized_users"].split(",")

    while True:
        try:
            for message in reddit.praw.inbox.stream():
                if message.author in authorized_users:
                    generator.generate(post=True, pm_recipients=(message.author.name,))
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
    storehandler = StoreHandler()
    while True:
        try:
            now = datetime.now()
            midnight = datetime.combine(now + timedelta(days=1), time.min)
            until_midnight = midnight - now
            logger.info(f"Waiting {until_midnight} until midnight..")
            sleep(until_midnight.total_seconds())
            storehandler.epic.load_offerid_json()
            generator.generate(
                post=True, pm_recipients=CONFIG.CONFIG["reddit"]["notify_users"].split(",")
            )
        except Exception as e:
            logger.exception(e)
        except KeyboardInterrupt:
            print("Exiting (KeyboardInterrupt)")
            break


def main():
    try:
        print(f"Starting Daily Releases Bot v{__version__}")
        mode = CONFIG.CONFIG["main"]["mode"]
        if CONFIG.CONFIG['discord']['enable_debughook'] == 'yes':
            logger.info("Enabling discord webhook debug log")
            logging.getLogger().addHandler(DiscordLogHandler())
        else:
            logger.info("Set enable_debughook to 'yes' if discord debug log is needed.")
        logger.info("Mode is %s", mode)
        if mode == "test":
            generator.generate(post=False)
        if mode == "immediately":
            generator.generate(
                post=True, pm_recipients=CONFIG.CONFIG["reddit"]["notify_users"].split(",")
            )
        if mode == "midnight":
            at_midnight()
        if mode == "reply":
            listen_inbox()
    except Exception as e:
        logger.exception(e)
        raise e
