import logging
from datetime import time, datetime, timedelta
from time import sleep
from discord_webhook import DiscordWebhook

from .stores.StoreHandler import StoreHandler
from . import __version__
from .Config import CONFIG
from .Generator import Generator

logger = logging.getLogger(__name__)


class DiscordLogHandler(logging.Handler):
    def emit(self, record):
        log_msg = self.format(record)
        webhook = DiscordWebhook(url=CONFIG.CONFIG["discord"]
                                 ["debug_webhook_url"],
                                 content=log_msg)
        webhook.execute()


class Main:
    def __init__(self):
        self.generator = Generator()
        
    def run_midnight_mode(self):
        storehandler = StoreHandler()
        while True:
            try:
                now = datetime.now()
                midnight = datetime.combine(now + timedelta(days=1), time.min)
                until_midnight = midnight - now
                logger.info(f"Waiting {until_midnight} until midnight..")
                sleep(until_midnight.total_seconds())
                storehandler.epic.load_offerid_json()
                self.generator.generate(
                    discord_post=True,
                    pm_recipients=CONFIG.CONFIG["reddit"]
                    ["notify_users"].split(",")
                )
            except Exception as e:
                logger.exception(e)
            except KeyboardInterrupt:
                print("Exiting (KeyboardInterrupt)")
                break

    def run_immediate_mode(self):
        self.generator.generate(
            discord_post=True,
            pm_recipients=CONFIG.CONFIG["reddit"]["notify_users"].split(",")
            )

    def run_test_mode(self):
        self.generator.generate(discord_post=False)

    def run_main(self):
        try:
            print(f"Starting Daily Releases Bot v{__version__}")
            mode = CONFIG.CONFIG["main"]["mode"]
            if CONFIG.CONFIG['discord']['enable_debughook'] == 'yes':
                logger.info("Enabling discord webhook debug log.")
                logging.getLogger().addHandler(DiscordLogHandler())
            else:
                logger.info("Set enable_debughook to 'yes' if discord debug "
                            "log is needed.")
            logger.info(f"Running in mode: {mode}")
            if mode == "test":
                self.run_test_mode()
            if mode == "immediately":
                self.run_immediate_mode()
            if mode == "midnight":
                self.run_midnight_mode()
        except Exception as e:
            logger.exception(e)
            raise e
