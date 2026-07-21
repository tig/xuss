"""Live edge engine — profiles, dead-man, route. Host-importable."""

from defaults import DEADMAN_MS, EDGE_HZ_MAX, EDGE_HZ_MIN, PROFILES
from edge import profile_rpm_at, profile_steps, profile_total_ms, rpm_to_hz


def make_engine(now_ms=0):
    return {
        "profile_name": None,
        "profile_steps": None,
        "profile_t0": 0,
        "active_rpm": 0,
        "forcing": False,
        "last_host_ms": int(now_ms),
        "last_hz": 0.0,
        "parked_reason": None,
    }


def touch_host(eng, now_ms):
    eng["last_host_ms"] = int(now_ms)


def stop(eng):
    eng["profile_name"] = None
    eng["profile_steps"] = None
    eng["profile_t0"] = 0
    eng["active_rpm"] = 0
    eng["forcing"] = False
    eng["last_hz"] = 0.0


def set_rpm(eng, rpm, now_ms):
    touch_host(eng, now_ms)
    eng["profile_name"] = None
    eng["profile_steps"] = None
    eng["active_rpm"] = int(rpm)
    eng["forcing"] = int(rpm) > 0
    eng["parked_reason"] = None


def start_profile(eng, name, now_ms):
    steps = profile_steps(name, PROFILES)
    touch_host(eng, now_ms)
    eng["profile_name"] = name
    eng["profile_steps"] = steps
    eng["profile_t0"] = int(now_ms)
    eng["active_rpm"] = int(steps[0][0]) if steps else 0
    eng["forcing"] = True
    eng["parked_reason"] = None


def face_mode(eng, cfg):
    if eng.get("parked_reason") == "deadman":
        return "idle"
    rpm = int(eng.get("active_rpm") or 0)
    if rpm <= 0 and not eng.get("forcing"):
        return "idle"
    route = cfg.get("route", "voice")
    if route == "tach":
        return "driving"
    if route == "both":
        return "driving"
    return "singing"


def _clamp_hz(hz):
    if hz <= 0:
        return 0.0
    if hz < EDGE_HZ_MIN:
        return float(EDGE_HZ_MIN)
    if hz > EDGE_HZ_MAX:
        return float(EDGE_HZ_MAX)
    return float(hz)


def tick_engine(eng, cfg, now_ms):
    """Advance profile/dead-man. Returns (hz, duty_pct, route, event_or_None)."""
    now = int(now_ms)
    event = None

    # Profile sampling
    steps = eng.get("profile_steps")
    if steps is not None:
        elapsed = now - int(eng.get("profile_t0") or 0)
        total = profile_total_ms(steps)
        if elapsed >= total:
            stop(eng)
            event = "profile_done"
        else:
            eng["active_rpm"] = profile_rpm_at(steps, elapsed)
            eng["forcing"] = True

    # Dead-man on DUT-touching activity
    route = cfg.get("route", "voice")
    touches_dut = eng.get("forcing") and route in ("tach", "both")
    if touches_dut:
        silent = now - int(eng.get("last_host_ms") or 0)
        if silent > int(DEADMAN_MS):
            stop(eng)
            eng["parked_reason"] = "deadman"
            event = "deadman"
            return 0.0, int(cfg.get("duty_pct", 50)), route, event

    rpm = int(eng.get("active_rpm") or 0)
    if rpm <= 0:
        eng["forcing"] = bool(steps is not None)
        eng["last_hz"] = 0.0
        return 0.0, int(cfg.get("duty_pct", 50)), route, event

    hz = _clamp_hz(rpm_to_hz(rpm, cfg.get("ring_teeth", 130)))
    eng["last_hz"] = hz
    eng["forcing"] = True
    duty = int(cfg.get("duty_pct", 50))
    return hz, duty, route, event
