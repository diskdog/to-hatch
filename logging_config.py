"""Logging configuration using the Python standard library.
 
Sets up a single stream handler on the root logger with a concise,
timestamped format suitable for development and demo use.
"""
 
from __future__ import annotations
 
import logging
import sys
 
 
def configure_logging(level: int = logging.INFO) -> None:
    """Configure the root logger.
 
    Args:
        level: Minimum log level to emit. Defaults to ``logging.INFO``.
    """
    root = logging.getLogger()
    root.setLevel(level)
 
    # Avoid duplicate handlers if called more than once (e.g. under reload).
    if root.handlers:
        return
 
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root.addHandler(handler)
 
 
def get_logger(name: str) -> logging.Logger:
    """Return a module-level logger.
 
    Args:
        name: Logger name, typically ``__name__``.
 
    Returns:
        A configured :class:`logging.Logger` instance.
    """
    return logging.getLogger(name)