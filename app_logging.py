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


class _LazyFileHandler(logging.Handler):
    """Creates the log file only when the first record is actually emitted."""

    def __init__(self, path: str) -> None:
        super().__init__(level=logging.WARNING)
        self._path = path
        self._real: RotatingFileHandler | None = None

    def _ensure(self) -> RotatingFileHandler:
        if self._real is None:
            self._real = RotatingFileHandler(
                self._path, maxBytes=1 * 1024 * 1024, backupCount=2, encoding="utf-8"
            )
            self._real.setFormatter(logging.Formatter(
                "%(asctime)s %(levelname)s [%(module)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            ))
        return self._real

    def emit(self, record: logging.LogRecord) -> None:
        self._ensure().emit(record)

    def close(self) -> None:
        if self._real:
            self._real.close()
        super().close()


def setup() -> None:
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter("%(message)s"))

    path = _log_path()
    file_handler = _LazyFileHandler(path)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(file_handler)
    root.addHandler(console_handler)

    def _excepthook(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        logging.critical("Unhandled exception:\n%s", msg)
        print(f"\n[eve-gate-logger] Crashed — details saved to {path}")

    sys.excepthook = _excepthook
