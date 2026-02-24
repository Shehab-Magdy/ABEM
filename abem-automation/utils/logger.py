"""
Centralised logging utility for the automation framework.

Features:
- Coloured console output (INFO+)
- Full DEBUG file log written to reports/test_run.log
- One logger instance per name (no duplicate handlers on re-import)
- Thread-safe (standard logging module guarantees this)

Usage:
    from utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Starting test…")
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# ── Colour codes for terminal output ──────────────────────────────────────────

_RESET   = "\033[0m"
_COLOURS = {
    "DEBUG":    "\033[36m",   # cyan
    "INFO":     "\033[32m",   # green
    "WARNING":  "\033[33m",   # yellow
    "ERROR":    "\033[31m",   # red
    "CRITICAL": "\033[35m",   # magenta
}


class _ColouredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        colour = _COLOURS.get(record.levelname, _RESET)
        record.levelname = f"{colour}{record.levelname:<8}{_RESET}"
        return super().format(record)


# ── Public API ─────────────────────────────────────────────────────────────────

_LOG_DIR = Path("reports")
_LOG_FILE = _LOG_DIR / "test_run.log"
_ROOT_LOGGER_CONFIGURED = False


def _configure_root() -> None:
    global _ROOT_LOGGER_CONFIGURED
    if _ROOT_LOGGER_CONFIGURED:
        return

    _LOG_DIR.mkdir(exist_ok=True)
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # Console — INFO and above, with colour
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(
        _ColouredFormatter(
            fmt="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    root.addHandler(console)

    # File — DEBUG and above, plain text
    file_handler = logging.FileHandler(_LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter(
            fmt="[%(asctime)s] %(levelname)-8s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root.addHandler(file_handler)

    _ROOT_LOGGER_CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a named logger, configuring the root logger on first call."""
    _configure_root()
    return logging.getLogger(name)
