import os
import copy
import logging
from typing import Text


class Settings:
    def __init__(self, **kwargs):
        environ = copy.deepcopy(os.environ)
        environ.update(**kwargs)

        # General
        self.APP_NAME: Text = environ.get("APP_NAME", "wiki-retrieval-service")
        self.APP_VERSION: Text = environ.get("APP_VERSION", "0.1.0")
        self.APP_TIMEZONE: Text = environ.get("APP_TIMEZONE", "Asia/Taipei")

        # Logging Config
        self.APP_LOGGER_NAME: Text = environ.get("APP_LOGGER_NAME", "sanic.root")
        self.LOG_DIR: Text = "log"
        self.LOG_ACCESS_FILENAME: Text = environ.get(
            "LOG_ACCESS_FILENAME", "access.log"
        )
        self.LOG_ERROR_FILENAME: Text = environ.get("LOG_ERROR_FILENAME", "error.log")
        self.LOG_SERVICE_FILENAME: Text = environ.get(
            "LOG_SERVICE_FILENAME", "service.log"
        )

        # OpenAI Config
        self.OPENAI_API_KEY = environ.get("OPENAI_API_KEY")


settings = Settings()

logger = logging.getLogger(settings.APP_LOGGER_NAME)
