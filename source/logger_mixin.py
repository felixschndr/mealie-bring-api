import logging
import os
import sys


class LoggerMixin:
    def __init__(self):
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        logging.basicConfig(
            stream=sys.stdout,
            format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
            encoding="utf-8",
            level=log_level,
        )
        self.log = logging.getLogger(self.__class__.__name__)

        logging.getLogger("asyncio").setLevel(logging.INFO)
        # Disable Flask log messages
        logging.getLogger("werkzeug").setLevel(logging.WARNING)
