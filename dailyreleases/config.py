import configparser
import logging
import logging.config
import shutil
from pathlib import Path
from json import dumps

logger = logging.getLogger(__name__)

PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG_FILE = PACKAGE_ROOT.joinpath("config.ini.default")
DATA_DIR = Path.home().joinpath(".dailyreleases")
CONFIG_FILE = DATA_DIR.joinpath("config.ini")


def read_config() -> configparser.ConfigParser:
    """
    Read and return config file. Copies default config template to data dir if it doesn't already exists.
    """
    if not CONFIG_FILE.exists():
        DATA_DIR.mkdir(exist_ok=True)
        shutil.copyfile(DEFAULT_CONFIG_FILE, CONFIG_FILE)

        print("Please customize", CONFIG_FILE)
        exit()

    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)

    return config


CONFIG = read_config()
CONFIG_DICT = {s:dict(CONFIG.items(s)) for s in CONFIG.sections()}
logger.info("USING CONFIG:\n" + dumps(CONFIG_DICT, indent=2))

def logging_config(file, level, backup_count) -> dict:
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


def initialize_logging(config: configparser.ConfigParser = CONFIG) -> None:
    """
    Set up logging.
    """
    file = DATA_DIR.joinpath("logs/main.log")
    level = config["logging"]["level"]
    backup_count = config["logging"].getint("backup_count")

    file.parent.mkdir(exist_ok=True)
    logging.config.dictConfig(logging_config(file, level, backup_count))

    logger.info("Logging level is %s", level)
    logger.info("Logging to %s - backup count is %s", file, backup_count)


initialize_logging()
