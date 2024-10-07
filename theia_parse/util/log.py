import os

from dotenv import load_dotenv
from loguru import logger
from tqdm import tqdm


load_dotenv()

log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
is_debug = True if log_level in ["DEBUG", "TRACE"] else False
logger.remove(0)
logger.add(
    lambda msg: tqdm.write(msg, end=""),
    colorize=True,
    format=(
        "{time} <light-blue>[{thread.name} | {module}]</light-blue> "
        "<level>{level}</level> {message}"
    ),
    level=log_level,
    backtrace=True,
    diagnose=is_debug,
    filter=lambda record: record["extra"].get("name") == "theia-parse",
)


class LogFactory:
    @staticmethod
    def get_logger():
        """
        Provides a logger with the given name and a preconfigured formatter.
        :return: logger instance
        """
        return logger.bind(name="theia-parse")
