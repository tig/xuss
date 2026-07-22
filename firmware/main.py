"""Boot entry: init + tick. Host-import safe — no machine in this module."""

from config import factory as config_factory, set_param
from defaults import FACE_THEME_DEFAULT, SERIAL_IN_BUDGET, SERIAL_OUT_BUDGET, TICK_SLEEP_MS
from engine import face_mode, make_engine, set_rpm, tick_engine
from face import frame as face_frame
from face import next_theme_index
from inputs import (
    adc_to_rpm,
    chirp_active,
    make_button,
    make_presence,
    tick_button_press,
    tick_presence,
)
from link import LineAssembler, make_stdio_link
from protocol import handle_line, identity_line
from riff import load_riff_bytes, make_riff
from store import load_from_hal, save_to_hal
from version import FW_NAME, FW_VERSION


def init(hal=None, now_ms=0, link=None, riff_data=None):
    cfg = config_factory()
    loaded = load_from_hal(hal)
    if loaded is not None:
        cfg = loaded
    # Never boot into a live instrument path (floating ADC/PIR must not sing)
    cfg["rpm"] = 0
    cfg["knob"] = 0
    cfg["greet"] = 0

    eng = make_engine(now_ms=now_ms)
    # Riff is one-shot in init (not streamed in the tick loop — that interleaved
    # NeoPixel/LCD traffic with DAC and left LEDC humming after).
    if riff_data is None:
        riff_data = _device_or_host_riff(hal)
    riff = make_riff(b"", now_ms=now_ms)  # inactive in tick path

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
        "audio_on": False,
        "theme_idx": int(FACE_THEME_DEFAULT),
        "btn_a": make_button(now_ms),
    }
    if hal is not None and hasattr(hal, "set_backlight"):
        hal.set_backlight(True)
    if hal is not None and hasattr(hal, "park_outputs"):
        hal.park_outputs()
    # Identity first (spec §5)
    _emit(state, identity_line())
    state["identity_sent"] = True
    _paint(state, now_ms)
    # One-shot boot riff, then hard silence (optional; can couple noise if amp is hot)
    try:
        from defaults import BOOT_RIFF_ENABLE

        riff_on = int(BOOT_RIFF_ENABLE) != 0
    except Exception:
        riff_on = True
    if riff_on and riff_data:
        if hasattr(hal, "write_dac_samples"):
            try:
                hal.write_dac_samples(riff_data)
            except Exception:
                pass
        if hasattr(hal, "dac_idle"):
            try:
                hal.dac_idle()
            except Exception:
                pass
    # Triple park after riff — DAC mux on ESP32 can leave the amp hot once
    for _ in range(3):
        if hasattr(hal, "park_outputs"):
            try:
                hal.park_outputs()
            except Exception:
                pass
    try:
        from hal_board import emergency_silence

        emergency_silence()
    except Exception:
        pass
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
    prev_mode = state.get("mode")
    state["mode"] = mode
    identity = "%s %s" % (state["fw_name"], state["fw_version"])
    theme_idx = int(state.get("theme_idx") if state.get("theme_idx") is not None else FACE_THEME_DEFAULT)
    fr = face_frame(elapsed, mode=mode, identity=identity, theme_idx=theme_idx)
    state["last_face"] = fr
    state["led_on"] = bool(fr.get("eyes_open"))
    hal = state.get("hal")
    if hal is None:
        return fr

    # Idle: static side strip; re-paint LCD on wink, theme, and/or marquee motion.
    eye_key = (fr.get("left_open", True), fr.get("right_open", True))
    banner_x = fr.get("banner_x")
    theme_key = fr.get("theme_idx")
    face_changed = (
        mode != prev_mode
        or state.get("_idle_eye_key") != eye_key
        or state.get("_theme_key") != theme_key
        or not state.get("_idle_painted")
    )
    banner_changed = state.get("_banner_x") != banner_x
    if (
        mode == "idle"
        and prev_mode == "idle"
        and state.get("_idle_painted")
        and not face_changed
        and not banner_changed
    ):
        return fr

    prev = state.get("_side_key")
    if mode == "idle":
        side_key = ("idle", theme_key, fr["side"][0] if fr.get("side") else None)
    else:
        side_key = (mode, theme_key, fr.get("eyes_open"), fr["side"][0] if fr.get("side") else None)
    if prev != side_key and hasattr(hal, "set_side_leds"):
        hal.set_side_leds(fr["side"])
        state["_side_key"] = side_key

    if face_changed and hasattr(hal, "show_face"):
        # Full face (eyes/smile/mode) — also draws current banner.
        hal.show_face(fr)
    elif banner_changed and hasattr(hal, "show_banner"):
        # Bar-only update keeps marquee smooth without full LCD thrash.
        hal.show_banner(fr)
    elif banner_changed and hasattr(hal, "show_face"):
        # Host doubles may only implement show_face.
        hal.show_face(fr)

    if mode == "idle":
        state["_idle_painted"] = True
        state["_idle_eye_key"] = eye_key
    else:
        state["_idle_painted"] = False
        state["_idle_eye_key"] = None
    state["_theme_key"] = theme_key
    state["_banner_x"] = banner_x
    return fr


def _drive_edge(state, now_ms=None):
    t = _now(state, now_ms)
    cfg = state["cfg"]
    eng = state["eng"]
    hal = state.get("hal")

    # PIR greet chirp (only if greet=1)
    pres = state["presence"]
    if int(cfg.get("greet") or 0) == 1 and chirp_active(pres, t):
        if hasattr(hal, "set_edge"):
            vol = int(cfg.get("volume") or 0)
            if int(cfg.get("mute") or 0) == 0 and vol > 0:
                hal.set_edge(float(pres.get("chirp_hz") or 880), 50, "voice", volume=vol)
                state["audio_on"] = True
        state["last_hz"] = float(pres.get("chirp_hz") or 0)
        state["_was_chirp"] = True
        return state["last_hz"]

    if state.get("_was_chirp"):
        state["_was_chirp"] = False
        if hasattr(hal, "park_outputs"):
            hal.park_outputs()
        state["audio_on"] = False

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
        # Park only on falling edge of audio — not every idle tick
        if state.get("audio_on"):
            if hasattr(hal, "park_outputs"):
                hal.park_outputs()
            state["audio_on"] = False
    else:
        if hasattr(hal, "set_edge"):
            hal.set_edge(hz, duty, out_route, volume=vol)
        state["audio_on"] = True
    state["last_hz"] = hz
    return hz


def _poll_inputs(state, now_ms=None):
    t = _now(state, now_ms)
    cfg = state["cfg"]
    hal = state.get("hal")

    # Left button (Button A): cycle face/side theme.
    if "btn_a" not in state:
        state["btn_a"] = make_button(t)
    pressed = 0
    if hal is not None and hasattr(hal, "read_button_a"):
        try:
            pressed = 1 if hal.read_button_a() else 0
        except Exception:
            pressed = 0
    if tick_button_press(state["btn_a"], pressed, t):
        state["theme_idx"] = next_theme_index(state.get("theme_idx") or 0)
        # Force full face + side repaint on the next _paint.
        state["_idle_painted"] = False
        state["_side_key"] = None
        state["_theme_key"] = None
        name = None
        try:
            from face import theme_at

            name = theme_at(state["theme_idx"]).get("name")
        except Exception:
            name = str(state["theme_idx"])
        _emit(state, "theme=%s idx=%s" % (name, state["theme_idx"]))

    # Skip PIR work entirely when greet disabled (floating pin cannot peep)
    if int(cfg.get("greet") or 0) != 1:
        return
    pir = 0
    if hal is not None and hasattr(hal, "read_pir"):
        pir = hal.read_pir()
    event = tick_presence(
        state["presence"],
        pir,
        greet_enabled=True,
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
    from hal_board import make_board_hal

    try:
        hal = make_board_hal()
        # Immediate hard silence before anything else
        if hasattr(hal, "park_outputs"):
            hal.park_outputs()
        link = make_stdio_link()
        t0 = hal.ticks_ms() if hasattr(hal, "ticks_ms") else 0
        state = init(hal=hal, now_ms=t0, link=link)
        if hasattr(hal, "park_outputs"):
            hal.park_outputs()

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
            try:
                tick(state)
            except Exception as exc:
                try:
                    print("event=err %s" % exc)
                except Exception:
                    pass
                _park(state)
            sleep_ms = state.get("tick_sleep_ms", TICK_SLEEP_MS)
            if hasattr(hal, "sleep_ms"):
                hal.sleep_ms(sleep_ms)
            else:
                try:
                    import time

                    time.sleep(sleep_ms / 1000.0)
                except ImportError:
                    pass
    except Exception as exc:
        try:
            print("event=fatal %s" % exc)
        except Exception:
            pass
        # last-ditch silence via board HAL only (no machine in main)
        try:
            from hal_board import emergency_silence

            emergency_silence()
        except Exception:
            pass


if __name__ == "__main__":
    main()
