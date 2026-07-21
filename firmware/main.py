"""Boot entry: init + tick. Host-import safe — no machine in this module.

Device starts the loop only when executed as __main__ (MicroPython boot).
Host tests import init / tick and inject a fake HAL.

L0 visible: idle face on IPS + side LED chase (time-based).
"""

from config import factory as config_factory
from defaults import TICK_SLEEP_MS
from face import frame as face_frame
from version import FW_NAME, FW_VERSION


def init(hal=None, now_ms=0):
    cfg = config_factory()
    state = {
        "hal": hal,
        "fw_name": FW_NAME,
        "fw_version": FW_VERSION,
        "tick_count": 0,
        "tick_sleep_ms": TICK_SLEEP_MS,
        "cfg": cfg,
        "mode": "idle",
        "t0_ms": int(now_ms),
        "last_face": None,
        "led_on": False,
    }
    # Identity first (spec §5) — on link when serial protocol lands; for L0 we
    # stamp state and paint face immediately so the device is visibly alive.
    if hal is not None:
        if hasattr(hal, "set_backlight"):
            hal.set_backlight(True)
        _paint(state, now_ms)
    return state


def _now(state, now_ms=None):
    if now_ms is not None:
        return int(now_ms)
    hal = state.get("hal")
    if hal is not None and hasattr(hal, "ticks_ms"):
        return int(hal.ticks_ms())
    return 0


def _paint(state, now_ms=None):
    t = _now(state, now_ms)
    elapsed = t - int(state.get("t0_ms", 0))
    if elapsed < 0:
        elapsed = 0
    identity = "%s %s" % (state["fw_name"], state["fw_version"])
    fr = face_frame(elapsed, mode=state.get("mode", "idle"), identity=identity)
    state["last_face"] = fr
    state["led_on"] = bool(fr.get("eyes_open"))
    hal = state.get("hal")
    if hal is None:
        return fr
    if hasattr(hal, "set_side_leds"):
        hal.set_side_leds(fr["side"])
    if hasattr(hal, "show_face"):
        hal.show_face(fr)
    return fr


def tick(state, now_ms=None):
    state["tick_count"] = state["tick_count"] + 1
    _paint(state, now_ms)
    return state


def main():
    from hal_board import make_board_hal

    hal = make_board_hal()
    # Prefer device clock for t0 so patterns are wall-time based
    t0 = hal.ticks_ms() if hasattr(hal, "ticks_ms") else 0
    state = init(hal=hal, now_ms=t0)
    # Soft serial identity (best-effort; does not block face)
    try:
        print("fw_name=%s fw_version=%s" % (FW_NAME, FW_VERSION))
    except Exception:
        pass
    while True:
        tick(state)
        sleep_ms = state.get("tick_sleep_ms", TICK_SLEEP_MS)
        if hasattr(hal, "sleep_ms"):
            hal.sleep_ms(sleep_ms)
        else:
            try:
                import time

                time.sleep(sleep_ms / 1000.0)
            except ImportError:
                pass


if __name__ == "__main__":
    main()
