"""Parameter store — completeness contract (spec §7). Host-importable."""

from defaults import (
    DEFAULTS_EXEMPT,
    DUTY_PCT,
    DUTY_PCT_MAX,
    DUTY_PCT_MIN,
    GREET,
    KNOB,
    MUTE,
    RING_TEETH,
    RING_TEETH_MAX,
    RING_TEETH_MIN,
    ROUTE,
    RPM_DEFAULT,
    RPM_MAX,
    RPM_MIN,
    TELEMETRY_HZ,
    TELEMETRY_HZ_MAX,
    TELEMETRY_HZ_MIN,
    VOLUME,
    VOLUME_MAX,
    VOLUME_MIN,
)

_ROUTES = ("voice", "tach", "both")


def factory():
    return {
        "ring_teeth": RING_TEETH,
        "rpm": RPM_DEFAULT,
        "duty_pct": DUTY_PCT,
        "route": ROUTE,
        "volume": VOLUME,
        "greet": GREET,
        "knob": KNOB,
        "mute": MUTE,
        "telemetry_hz": TELEMETRY_HZ,
    }


def validate(key, value):
    """Return (ok, coerced_or_error_string)."""
    if key == "ring_teeth":
        v = int(value)
        if v < RING_TEETH_MIN or v > RING_TEETH_MAX:
            return False, "range"
        return True, v
    if key == "rpm":
        v = int(value)
        if v < RPM_MIN or v > RPM_MAX:
            return False, "range"
        return True, v
    if key == "duty_pct":
        v = int(value)
        if v < DUTY_PCT_MIN or v > DUTY_PCT_MAX:
            return False, "range"
        return True, v
    if key == "route":
        s = str(value)
        if s not in _ROUTES:
            return False, "enum"
        return True, s
    if key == "volume":
        v = int(value)
        if v < VOLUME_MIN or v > VOLUME_MAX:
            return False, "range"
        return True, v
    if key in ("greet", "knob", "mute"):
        v = int(value)
        if v not in (0, 1):
            return False, "range"
        return True, v
    if key == "telemetry_hz":
        v = int(value)
        if v < TELEMETRY_HZ_MIN or v > TELEMETRY_HZ_MAX:
            return False, "range"
        return True, v
    return False, "unknown"


def get_param(cfg, key):
    if key not in cfg:
        raise KeyError(key)
    return cfg[key]


def set_param(cfg, key, value):
    ok, result = validate(key, value)
    if not ok:
        return False, result
    cfg[key] = result
    return True, result


def apply_defaults(cfg):
    """Restore factory values except DEFAULTS_EXEMPT keys (mute)."""
    fresh = factory()
    for key in DEFAULTS_EXEMPT:
        if key in cfg:
            fresh[key] = cfg[key]
    cfg.clear()
    cfg.update(fresh)
    return cfg
