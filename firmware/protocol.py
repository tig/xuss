"""ASCII line protocol (spec §7). Host-importable."""

from config import apply_defaults, get_param, set_param
from defaults import PROFILES, SERIAL_ERR_MAX
from engine import set_rpm, start_profile, stop, touch_host
from version import FW_NAME, FW_VERSION


def identity_line():
    return "fw_name=%s fw_version=%s" % (FW_NAME, FW_VERSION)


def _err(msg):
    s = "err=%s" % msg
    if len(s) > SERIAL_ERR_MAX:
        s = s[:SERIAL_ERR_MAX]
    return s


def _ok(msg="ok"):
    return msg


def handle_line(state, line, now_ms):
    """Dispatch one command line. Returns list of response lines.

    Side effects: may set state['exit_repl'], state['do_reboot'], mutate eng/cfg.
    """
    eng = state["eng"]
    cfg = state["cfg"]
    touch_host(eng, now_ms)

    if line is None:
        return [_err("line")]

    text = line.strip()
    if not text:
        return []

    # Ctrl-C is data (0x03), not an interrupt — ignore as empty
    if text == "\x03":
        return []

    parts = text.split()
    cmd = parts[0].lower()

    if cmd == "identity":
        return [identity_line()]

    if cmd == "get":
        if len(parts) == 1:
            # dump all
            keys = sorted(cfg.keys())
            return ["%s=%s" % (k, cfg[k]) for k in keys]
        key = parts[1]
        try:
            return ["%s=%s" % (key, get_param(cfg, key))]
        except KeyError:
            return [_err("unknown")]

    if cmd == "set":
        if len(parts) < 3:
            return [_err("syntax")]
        key = parts[1]
        value = parts[2]
        ok, result = set_param(cfg, key, value)
        if not ok:
            return [_err(str(result))]
        # live rpm via set
        if key == "rpm":
            set_rpm(eng, int(result), now_ms)
        return ["%s=%s" % (key, result)]

    if cmd == "defaults":
        apply_defaults(cfg)
        stop(eng)
        return [_ok("defaults")]

    if cmd == "save":
        # main performs store.save_to_hal and emits save=ok|fail
        state["save_requested"] = True
        return []

    if cmd == "rpm":
        if len(parts) < 2:
            return ["rpm=%s" % cfg.get("rpm", 0)]
        ok, result = set_param(cfg, "rpm", parts[1])
        if not ok:
            return [_err(str(result))]
        set_rpm(eng, int(result), now_ms)
        return ["rpm=%s" % result]

    if cmd == "route":
        if len(parts) < 2:
            return ["route=%s" % cfg.get("route")]
        ok, result = set_param(cfg, "route", parts[1])
        if not ok:
            return [_err(str(result))]
        return ["route=%s" % result]

    if cmd == "stop":
        stop(eng)
        ok, _ = set_param(cfg, "rpm", 0)
        return [_ok("stop")]

    if cmd == "sing":
        if len(parts) < 2:
            return [_err("syntax")]
        name = parts[1]
        if name not in PROFILES:
            return [_err("profile")]
        set_param(cfg, "route", "voice")
        start_profile(eng, name, now_ms)
        return ["sing=%s" % name]

    if cmd == "run":
        if len(parts) < 2:
            return [_err("syntax")]
        name = parts[1]
        if name not in PROFILES:
            return [_err("profile")]
        set_param(cfg, "route", "tach")
        start_profile(eng, name, now_ms)
        # announce DUT actuation (spec §5)
        return ["run=%s" % name, "actuate=tach"]

    if cmd == "repl":
        state["exit_repl"] = True
        return [_ok("repl")]

    if cmd == "reboot":
        state["do_reboot"] = True
        return [_ok("reboot")]

    return [_err("cmd")]
