import itertools
import sys
import threading
import time


class Spinner:
    """Simple terminal spinner on stderr (disabled when verbose mode is on)."""

    _FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

    def __init__(self, message: str = "Thinking", *, enabled: bool = True):
        self._message = message
        self._enabled = enabled
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def set_message(self, message: str) -> None:
        self._message = message

    def __enter__(self) -> "Spinner":
        if self._enabled:
            self._stop.clear()
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
        return self

    def __exit__(self, *_args) -> None:
        if not self._enabled:
            return
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1)
        self._clear_line()

    def _clear_line(self) -> None:
        sys.stderr.write("\r\033[K")
        sys.stderr.flush()

    def _run(self) -> None:
        for frame in itertools.cycle(self._FRAMES):
            if self._stop.is_set():
                break
            sys.stderr.write(f"\r\033[K{self._message} {frame}")
            sys.stderr.flush()
            time.sleep(0.08)
