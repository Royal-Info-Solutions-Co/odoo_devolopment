"""Rotating file logger for the print server."""

import logging
import sys
from logging.handlers import RotatingFileHandler
from config import LOG_FILE, LOG_MAX_BYTES, LOG_BACKUP_COUNT


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        logger.addHandler(handler)
        # Console logging is best-effort only (useful during development). A
        # PyInstaller --noconsole build has no stdout/stderr, so this must never
        # be allowed to break startup — swallow any failure.
        try:
            stream = sys.stderr if sys.stderr is not None else sys.stdout
            if stream is not None:
                console = logging.StreamHandler(stream)
                console.setFormatter(
                    logging.Formatter("[%(levelname)s] %(message)s")
                )
                logger.addHandler(console)
        except Exception:
            pass
    return logger
