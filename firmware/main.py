"""Boot entry: init + tick. Host-import safe — no machine in this module.

L1 path: identity line, line protocol, edge engine, dead-man, escape hatch.
Face + side LEDs stay time-based.
"""

from config import factory as config_factory
from defaults import SERIAL_IN_BUDGET, SERIAL_OUT_BUDGET, TICK_SLEEP_MS
from engine import face_mode, make_engine, tick_engine
from face import frame as face_frame
from link import LineAssembler, make_stdio_link
from protocol import handle_line, identity_line
from version import FW_NAME, FW_VERSION


def init(hal=None, now_ms=0, link=None):
    cfg = config_factory()
    eng = make_engine(now_ms=now_ms)
    state = {
        "hal": hal,
        "link": link,
        "lines": LineAssembler(),
        "fw_name": FW_NAME,
        "fw_version": FW_VERSION,
        "tick_count": 0,
        "tick_sleep_ms": TICK_SLEEP_MS,
        "cfg": cfg,
        "eng": eng,
        "mode": "idle",
        "t0_ms": int(now_ms),
        "last_face": None,
        "led_on": False,
        "exit_repl": False,
        "do_reboot": False,
        "save_requested": False,
        "identity_sent": False,
    }
    if hal is not None and hasattr(hal, "set_backlight"):
        hal.set_backlight(True)
    # Identity first on the link (spec §5)
    _emit(state, identity_line())
    state["identity_sent"] = True
    _paint(state, now_ms)
    _drive_edge(state, now_ms)
    return state


def _emit(state, line):
    link = state.get("link")
    if link is not None and hasattr(link, "write_line"):
        link.write_line(line)


def _emit_budget(state, lines):
    """Egress capped per tick (character budget)."""
    budget = int(SERIAL_OUT_BUDGET)
    for line in lines:
        s = str(line)
        cost = len(s) + 1
        if cost > budget:
            # still send a truncated err if possible
            if budget > 8:
                _emit(state, s[: budget - 1])
            break
        _emit(state, s)
        budget -= cost


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
    mode = face_mode(state["eng"], state["cfg"])
    state["mode"] = mode
    identity = "%s %s" % (state["fw_name"], state["fw_version"])
    fr = face_frame(elapsed, mode=mode, identity=identity)
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


def _drive_edge(state, now_ms=None):
    t = _now(state, now_ms)
    cfg = state["cfg"]
    eng = state["eng"]
    hz, duty, route, event = tick_engine(eng, cfg, t)
    if event == "deadman":
        _emit(state, "event=deadman")
    if event == "profile_done":
        _emit(state, "event=profile_done")
        try:
            from config import set_param

            set_param(cfg, "rpm", 0)
        except Exception:
            cfg["rpm"] = 0

    # mute / volume 0 park voice only; tach duty stays honest mark-space
    out_route = route
    vol = int(cfg.get("volume") or 0)
    if int(cfg.get("mute") or 0) == 1 or vol <= 0:
        if route == "voice":
            hz = 0.0
        elif route == "both":
            out_route = "tach"

    hal = state.get("hal")
    if hal is None:
        state["last_hz"] = hz
        return hz

    if hasattr(hal, "set_edge"):
        # volume is amplitude on the voice sink, never a thinner duty cycle
        hal.set_edge(hz if hz > 0 else 0, duty, out_route, volume=vol)
    elif hz <= 0 and hasattr(hal, "park_outputs"):
        hal.park_outputs()
    state["last_hz"] = hz
    return hz


def _poll_serial(state, now_ms=None):
    link = state.get("link")
    if link is None or not hasattr(link, "read_budget"):
        return
    t = _now(state, now_ms)
    chunk = link.read_budget(SERIAL_IN_BUDGET)
    lines = state["lines"].push(chunk)
    for line in lines:
        responses = handle_line(state, line, t)
        _emit_budget(state, responses)
        if state.get("exit_repl") or state.get("do_reboot"):
            break


def tick(state, now_ms=None):
    state["tick_count"] = state["tick_count"] + 1
    t = _now(state, now_ms)
    _poll_serial(state, t)
    if state.get("exit_repl") or state.get("do_reboot"):
        _park(state)
        # Restore interrupt char immediately so mpremote/silico can reclaim CDC
        if state.get("exit_repl"):
            try:
                import micropython

                micropython.kbd_intr(3)
            except Exception:
                pass
        return state
    _drive_edge(state, t)
    _paint(state, t)
    # telemetry only when host enables it (default 0 = silence)
    hz_tel = int(state["cfg"].get("telemetry_hz") or 0)
    if hz_tel > 0:
        # emit about hz_tel times per second based on wall time
        period = max(1, 1000 // hz_tel)
        last = int(state.get("_tel_ms") or 0)
        if t - last >= period:
            state["_tel_ms"] = t
            eng = state["eng"]
            _emit(
                state,
                "rpm=%s hz=%s mode=%s"
                % (eng.get("active_rpm", 0), int(state.get("last_hz") or 0), state.get("mode")),
            )
    return state


def _park(state):
    hal = state.get("hal")
    if hal is not None and hasattr(hal, "park_outputs"):
        hal.park_outputs()
    try:
        from engine import stop

        stop(state["eng"])
    except Exception:
        pass


def feed_line(state, line, now_ms=None):
    """Host-test helper: inject one command line."""
    t = _now(state, now_ms)
    link = state.get("link")
    if link is not None and hasattr(link, "feed_line"):
        link.feed_line(line)
        _poll_serial(state, t)
    else:
        responses = handle_line(state, line, t)
        _emit_budget(state, responses)
    return state


def main():
    from hal_board import make_board_hal

    hal = make_board_hal()
    link = make_stdio_link()
    t0 = hal.ticks_ms() if hasattr(hal, "ticks_ms") else 0
    state = init(hal=hal, now_ms=t0, link=link)

    while True:
        if state.get("exit_repl"):
            _park(state)
            # restore default Ctrl-C interrupt if available
            try:
                import micropython

                micropython.kbd_intr(3)
            except Exception:
                pass
            break
        if state.get("do_reboot"):
            _park(state)
            if hasattr(hal, "reboot"):
                hal.reboot()
            break
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
