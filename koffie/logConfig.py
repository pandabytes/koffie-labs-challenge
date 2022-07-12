from typing import Any
from pydantic import BaseModel

class LogConfig(BaseModel):
    """ Logging configuration """
    logFormat: str = "%(levelprefix)s %(asctime)s - %(message)s"
    version = 1
    disable_existing_loggers = False
    formatters = {
      "default": {
          "()": "uvicorn.logging.DefaultFormatter",
          "fmt": logFormat,
          "datefmt": "%Y/%m/%d %H:%M:%S",
      },
    }
    handlers = {
      "default": {
          "formatter": "default",
          "class": "logging.StreamHandler",
          "stream": "ext://sys.stdout",
      },
    }
    loggers: dict[str, dict[str, Any]] = {}

    def addLogger(self, loggerName: str, logLevel: int | str):
      """ Add a logger to the configuration. Once a logger is added to the 
          configuration, we can get the logger via the `logging` library.

          Example:
          ```py
          import logging
          from logging.config import dictConfig
          
          loggerName, logConfig = "foo", LogConfig()
          logConfig.addLogger(loggerName, "INFO")

          dictConfig(logConfig.dict())
          logger = logging.getLogger(loggerName)
          ```
      """
      self.loggers[loggerName] = { "handlers": ["default"], "level": logLevel }
