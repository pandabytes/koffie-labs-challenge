from typing import Any
from pydantic import BaseModel

class LogConfig(BaseModel):
    """Logging configuration"""
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
      self.loggers[loggerName] = { "handlers": ["default"], "level": logLevel }
