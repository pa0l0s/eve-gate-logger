import logging
import os
import sys
import traceback
from logging.handlers import RotatingFileHandler

_LOG_FILE = "eve-gate-logger.log"


def _log_path() -> str:
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, _LOG_FILE)


def setup() -> None:
    """Configure root logger: WARNING+ to rotating file, INFO+ to console."""
    path = _log_path()

    file_handler = RotatingFileHandler(
        path, maxBytes=1 * 1024 * 1024, backupCount=2, encoding="utf-8"
    )
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s [%(module)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter("%(message)s"))

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(file_handler)
    root.addHandler(console_handler)

    # Catch unhandled exceptions and write them to the log file
    def _excepthook(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        logging.critical("Unhandled exception:\n%s", msg)
        print(f"\n[eve-gate-logger] Crashed — details saved to {path}")

    sys.excepthook = _excepthook
    logging.info(f"[eve-gate-logger] Log file: {path}")
