from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logger(log_path: str) -> logging.Logger:
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    logger = logging.getLogger("obrbr")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False
    
    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    
    fh = RotatingFileHandler(log_path, maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(fmt)
    
    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger