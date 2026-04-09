"""Package-wide logging configuration."""

import logging
import os
import pathlib
import sys
import tempfile
from typing import Optional

__all__ = [
    "DEFAULT_LOG_PATH",
    "configure_logging",
]

DEFAULT_LOG_PATH = os.path.join(tempfile.gettempdir(), "afmformats.log")


def configure_logging(log_path: Optional[str] = DEFAULT_LOG_PATH,
                      console_logging_level: bool | int = 0) -> str:
    """Ensure afmformats writes debug logs to a file.

    Returns the log path used so CI pipelines can publish it as an artifact.
    """
    path = log_path
    path = str(pathlib.Path(path))
    logger = logging.getLogger("afmformats")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    handler_exists = any(
        isinstance(h, logging.FileHandler)
        and getattr(h, "baseFilename", None) == path
        for h in logger.handlers
    )
    if not handler_exists:
        pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(path, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s: %(message)s"
        )
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        logger.debug("afmformats logging initialized at %s", path)
    if console_logging_level:
        configure_console_logging(console_logging_level)
    return path


def configure_console_logging(level: int = logging.DEBUG) -> None:
    """Mirror afmformats log output to the terminal."""
    logger = logging.getLogger("afmformats")
    handler_exists = any(
        isinstance(h, logging.StreamHandler)
        and not isinstance(h, logging.FileHandler)
        and getattr(h, "stream", None) is sys.stderr
        for h in logger.handlers
    )
    if not handler_exists:
        handler = logging.StreamHandler()
        handler.setLevel(level)
        handler.setFormatter(logging.Formatter(
            "%(levelname)s:%(name)s:%(message)s"))
        logger.addHandler(handler)
