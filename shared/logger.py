"""Minimal structured logger for AgriNegotiator."""

import logging
import sys


def get_logger(name: str = "agrinegotiator") -> logging.Logger:
    """Return a logger with a consistent format; idempotent."""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger  # already configured

    logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)s %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    )
    handler.setFormatter(fmt)
    logger.addHandler(handler)

    return logger


# Default module-level logger
log = get_logger()
