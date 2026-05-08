import ctypes
import time

# Windows Virtual Key codes
_KEY_MAP: dict[str, int] = {
    "ctrl": 0x11, "lctrl": 0xA2, "rctrl": 0xA3,
    "alt": 0x12,  "lalt": 0xA4,  "ralt": 0xA5,
    "shift": 0x10,
    "scroll_lock": 0x91,
    "pause_break": 0x13,
    "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73,
    "f5": 0x74, "f6": 0x75, "f7": 0x76, "f8": 0x77,
    "f9": 0x78, "f10": 0x79, "f11": 0x7A, "f12": 0x7B,
}


class _POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


def _key_vk(name: str) -> int | None:
    return _KEY_MAP.get(name.lower().strip())


def _is_held(vk: int) -> bool:
    return bool(ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000)


def _cursor_pos() -> tuple[int, int]:
    pt = _POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return (pt.x, pt.y)


class PauseManager:
    def __init__(
        self,
        pause_key: str = "ctrl",
        mouse_pause_on_start: bool = False,
        mouse_pause_seconds: float = 3.0,
        mouse_pause_toggle_key: str = "scroll_lock",
    ) -> None:
        self._pause_vk = _key_vk(pause_key)
        self._toggle_vk = _key_vk(mouse_pause_toggle_key)
        self._mouse_pause_enabled = mouse_pause_on_start
        self._mouse_pause_seconds = mouse_pause_seconds

        self._last_pos = _cursor_pos()
        self._last_move_time: float = 0.0
        self._toggle_was_held = False
        self._was_paused = False

    def is_paused(self) -> bool:
        # --- key-hold pause ---
        if self._pause_vk and _is_held(self._pause_vk):
            self._report(True, "key held")
            return True

        # --- toggle mouse-move-pause mode ---
        if self._toggle_vk:
            held = _is_held(self._toggle_vk)
            if held and not self._toggle_was_held:
                self._mouse_pause_enabled = not self._mouse_pause_enabled
                state = "ON" if self._mouse_pause_enabled else "OFF"
                print(f"[eve-gate-logger] Mouse-move pause: {state}")
            self._toggle_was_held = held

        # --- mouse-move pause ---
        if self._mouse_pause_enabled:
            pos = _cursor_pos()
            if pos != self._last_pos:
                self._last_pos = pos
                self._last_move_time = time.monotonic()
            if self._last_move_time and time.monotonic() - self._last_move_time < self._mouse_pause_seconds:
                self._report(True, "mouse moving")
                return True

        self._report(False, "")
        return False

    def _report(self, paused: bool, reason: str) -> None:
        if paused and not self._was_paused:
            print(f"[eve-gate-logger] Scanning paused ({reason})")
        elif not paused and self._was_paused:
            print("[eve-gate-logger] Scanning resumed")
        self._was_paused = paused
