from __future__ import annotations

import logging
import os
from pathlib import Path

_LOG_PATH_ENV = "SPECIFY_LOG_PATH"
_DEBUG_ENV = "SPECIFY_DEBUG"
_DEFAULT_LOG = Path.home() / ".claude" / "specify.log"

_FMT = "[%(asctime)s] [%(levelname)s] %(message)s"
_DATEFMT = "%Y-%m-%dT%H:%M:%S"

_logger: logging.Logger | None = None


def get_logger() -> logging.Logger:
    global _logger
    if _logger is not None:
        return _logger

    logger = logging.getLogger("specify")
    logger.handlers.clear()
    logger.propagate = False

    if not os.environ.get(_DEBUG_ENV):
        logger.addHandler(logging.NullHandler())
        _logger = logger
        return _logger

    log_path = Path(os.environ.get(_LOG_PATH_ENV, _DEFAULT_LOG))
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
        handler.setFormatter(logging.Formatter(_FMT, datefmt=_DATEFMT))
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
    except OSError:
        logger.addHandler(logging.NullHandler())

    _logger = logger
    return _logger


def reset() -> None:
    """Reset cached logger — for use in tests only."""
    global _logger
    if _logger is not None:
        for h in _logger.handlers[:]:
            h.close()
            _logger.removeHandler(h)
    _logger = None
