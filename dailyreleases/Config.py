"""Custom config class to collect important configurations"""

import configparser
import logging
import logging.config
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


class Config:
    def __init__(self):
        self.PACKAGE_ROOT = Path(__file__).resolve().parent
        self.DEFAULT_CONFIG_FILE = self.PACKAGE_ROOT.joinpath("config.ini.default")
        self.DATA_DIR = Path.home().joinpath(".dailyreleases")
        self.CONFIG_FILE = self.DATA_DIR.joinpath("config.ini")
        self.CONFIG = self.read_config()

    def read_config(self) -> configparser:
        """
        Read and return config file. Copies default config template to data dir
        if it doesn't already exists.
        """
        if not self.CONFIG_FILE.exists():
            self.DATA_DIR.mkdir(exist_ok=True)
            shutil.copyfile(self.DEFAULT_CONFIG_FILE, self.CONFIG_FILE)

            print("Please customize", self.CONFIG_FILE)
            exit()

        config = configparser.ConfigParser()
        config.read(self.CONFIG_FILE)
        return config

    def logging_config(self, file, level, backup_count) -> dict:
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s [%(levelname)-7s] %(name)s:%(funcName)s - %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                    "formatter": "standard",
                    "level": level,
                },
                "file": {
                    "class": "logging.handlers.TimedRotatingFileHandler",
                    "when": "midnight",
                    "backupCount": backup_count,
                    "filename": file,
                    "encoding": "utf-8",
                    "formatter": "standard",
                    "level": level,
                },
            },
            "loggers": {"dailyreleases": {"level": level}},
            "root": {"handlers": ["console", "file"], "level": "WARNING"},
        }

    def initialize_logging(self):
        config = self.read_config()
        file = self.DATA_DIR.joinpath("logs/main.log")

        level = config["logging"]["level"]
        backup_count = config["logging"].getint("backup_count")
        file.parent.mkdir(exist_ok=True)
        logging.config.dictConfig(self.logging_config(file, level,
                                                      backup_count))
        logger.info("Logging level is %s", level)


CONFIG = Config()
CONFIG.initialize_logging()
