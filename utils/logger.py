"""
Logging utility — sets up a consistent logger for all modules.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler


def setup_logger(name: str, log_file: str = "bot.log", level: int = logging.INFO) -> logging.Logger:
    """
    Create and return a named logger with both console and rotating file handlers.

    Args:
        name:     Logger name (usually the module name).
        log_file: Path to the log file.
        level:    Logging level (default: INFO).

    Returns:
        Configured Logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding duplicate handlers on repeated calls
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    logger.addHandler(console_handler)

    # Rotating file handler (5 MB per file, keep 3 backups)
    try:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)
    except OSError:
        # If the log file can't be created (e.g. read-only FS), continue with console only
        logger.warning("Could not create log file. Logging to console only.")

    return logger
