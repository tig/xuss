"""Boot entry: init + tick. Host-import safe — no machine in this module."""

from config import factory as config_factory, set_param
from defaults import SERIAL_IN_BUDGET, SERIAL_OUT_BUDGET, TICK_SLEEP_MS
from engine import face_mode, make_engine, set_rpm, tick_engine
from face import frame as face_frame
from inputs import adc_to_rpm, chirp_active, make_presence, tick_presence
from link import LineAssembler, make_stdio_link
from protocol import handle_line, identity_line
from riff import load_riff_bytes, make_riff, riff_advance, riff_done, riff_samples_for_tick
from store import load_from_hal, save_to_hal
from version import FW_NAME, FW_VERSION


def init(hal=None, now_ms=0, link=None, riff_data=None):
    cfg = config_factory()
    loaded = load_from_hal(hal)
    if loaded is not None:
        cfg = loaded

    eng = make_engine(now_ms=now_ms)
    if riff_data is None:
        riff_data = _device_or_host_riff(hal)
    riff = make_riff(riff_data, now_ms=now_ms)

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
        "presence": make_presence(now_ms),
        "riff": riff,
        "mode": "idle",
        "t0_ms": int(now_ms),
        "last_face": None,
        "led_on": False,
        "exit_repl": False,
        "do_reboot": False,
        "save_requested": False,
        "identity_sent": False,
        "last_hz": 0.0,
    }
    if hal is not None and hasattr(hal, "set_backlight"):
        hal.set_backlight(True)
    # Identity first (spec §5) — before riff blocks chunks
    _emit(state, identity_line())
    state["identity_sent"] = True
    _paint(state, now_ms)
    return state


def _device_or_host_riff(hal):
    # Device file
    if hal is not None and hasattr(hal, "read_text"):
        # binary: prefer open via read if available
        pass
    try:
        from defaults import BOOT_RIFF_PATH

        with open(BOOT_RIFF_PATH, "rb") as f:
            return f.read()
    except Exception:
        pass
    return load_riff_bytes()


def _emit(state, line):
    link = state.get("link")
    if link is not None and hasattr(link, "write_line"):
        link.write_line(line)


def _emit_budget(state, lines):
    budget = int(SERIAL_OUT_BUDGET)
    for line in lines:
        s = str(line)
        cost = len(s) + 1
        if cost > budget:
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


def _instrument_busy(state):
    eng = state["eng"]
    if eng.get("forcing") and int(eng.get("active_rpm") or 0) > 0:
        return True
    if eng.get("profile_steps") is not None:
        return True
    return False


def _paint(state, now_ms=None):
    t = _now(state, now_ms)
    elapsed = t - int(state.get("t0_ms", 0))
    if elapsed < 0:
        elapsed = 0
    mode = face_mode(state["eng"], state["cfg"])
    if not riff_done(state.get("riff")):
        mode = "singing"
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
    hal = state.get("hal")

    # Boot riff owns the speaker until done (serial still polled in tick)
    if not riff_done(state.get("riff")):
        n = riff_samples_for_tick(state["riff"], state.get("tick_sleep_ms", TICK_SLEEP_MS))
        still = riff_advance(state["riff"], n, hal=hal)
        if not still and hasattr(hal, "park_outputs"):
            # hard silence after riff — no residual LEDC buzz
            hal.park_outputs()
        state["last_hz"] = 0.0
        state["_was_chirp"] = False
        return 0.0

    # PIR greet chirp (short) when not instrument-busy
    pres = state["presence"]
    if chirp_active(pres, t):
        if hasattr(hal, "set_edge"):
            vol = int(cfg.get("volume") or 0)
            if int(cfg.get("mute") or 0) == 0 and vol > 0:
                hal.set_edge(float(pres.get("chirp_hz") or 880), 50, "voice", volume=vol)
        state["last_hz"] = float(pres.get("chirp_hz") or 0)
        state["_was_chirp"] = True
        return state["last_hz"]

    # Chirp just ended: park so we do not leave 880 Hz PWM running
    if state.get("_was_chirp"):
        state["_was_chirp"] = False
        if hasattr(hal, "park_outputs"):
            hal.park_outputs()

    # ANGLE knob live rpm only when enabled
    if int(cfg.get("knob") or 0) == 1 and hal is not None and hasattr(hal, "read_angle_raw"):
        raw = hal.read_angle_raw()
        rpm = adc_to_rpm(raw)
        set_param(cfg, "rpm", rpm)
        set_rpm(eng, rpm, t)

    hz, duty, route, event = tick_engine(eng, cfg, t)
    if event == "deadman":
        _emit(state, "event=deadman")
    if event == "profile_done":
        _emit(state, "event=profile_done")
        set_param(cfg, "rpm", 0)

    out_route = route
    vol = int(cfg.get("volume") or 0)
    if int(cfg.get("mute") or 0) == 1 or vol <= 0:
        if route == "voice":
            hz = 0.0
        elif route == "both":
            out_route = "tach"

    if hz <= 0:
        if hasattr(hal, "park_outputs"):
            hal.park_outputs()
        elif hasattr(hal, "set_edge"):
            hal.set_edge(0, duty, out_route, volume=vol)
    elif hasattr(hal, "set_edge"):
        hal.set_edge(hz, duty, out_route, volume=vol)
    state["last_hz"] = hz
    return hz


def _poll_inputs(state, now_ms=None):
    t = _now(state, now_ms)
    # No PIR while boot riff is still playing
    if not riff_done(state.get("riff")):
        return
    hal = state.get("hal")
    cfg = state["cfg"]
    pir = 0
    if hal is not None and hasattr(hal, "read_pir"):
        pir = hal.read_pir()
    event = tick_presence(
        state["presence"],
        pir,
        greet_enabled=int(cfg.get("greet") or 0) == 1,
        instrument_busy=_instrument_busy(state),
        now_ms=t,
    )
    if event == "greet":
        _emit(state, "event=greet")


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
        if state.get("save_requested"):
            state["save_requested"] = False
            if save_to_hal(state.get("hal"), state["cfg"]):
                _emit(state, "save=ok")
            else:
                _emit(state, "save=fail")
        if state.get("exit_repl") or state.get("do_reboot"):
            break


def tick(state, now_ms=None):
    state["tick_count"] = state["tick_count"] + 1
    t = _now(state, now_ms)
    _poll_serial(state, t)
    if state.get("exit_repl") or state.get("do_reboot"):
        _park(state)
        if state.get("exit_repl"):
            try:
                import micropython

                micropython.kbd_intr(3)
            except Exception:
                pass
        return state
    _poll_inputs(state, t)
    _drive_edge(state, t)
    _paint(state, t)
    hz_tel = int(state["cfg"].get("telemetry_hz") or 0)
    if hz_tel > 0:
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
    t = _now(state, now_ms)
    link = state.get("link")
    if link is not None and hasattr(link, "feed_line"):
        link.feed_line(line)
        _poll_serial(state, t)
    else:
        responses = handle_line(state, line, t)
        _emit_budget(state, responses)
        if state.get("save_requested"):
            state["save_requested"] = False
            if save_to_hal(state.get("hal"), state["cfg"]):
                _emit(state, "save=ok")
            else:
                _emit(state, "save=fail")
    return state


def main():
    from defaults import BOOT_RIFF_PATH
    from hal_board import make_board_hal

    # Ensure riff file name alias if only host name present
    try:
        import uos as os  # type: ignore
    except ImportError:
        import os  # type: ignore
    try:
        if BOOT_RIFF_PATH not in os.listdir() and "boot-riff.u8.raw" in os.listdir():
            # no rename required if we open both in loader
            pass
    except Exception:
        pass

    hal = make_board_hal()
    link = make_stdio_link()
    t0 = hal.ticks_ms() if hasattr(hal, "ticks_ms") else 0
    state = init(hal=hal, now_ms=t0, link=link)

    while True:
        if state.get("exit_repl"):
            _park(state)
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
        # While riff plays, sample chunks already used wall time; keep loop snappy
        if not riff_done(state.get("riff")):
            sleep_ms = 5
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
