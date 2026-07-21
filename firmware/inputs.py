"""ANGLE knob + PIR presence logic. Host-importable."""

from defaults import (
    KNOB_ADC_MAX,
    KNOB_ADC_MIN,
    KNOB_RPM_MAX,
    KNOB_RPM_MIN,
    PIR_GREET_CHIRP_MS,
    PIR_GREET_HZ,
    PIR_QUIET_MS,
)


def adc_to_rpm(raw):
    """Map ADC reading to rpm (linear)."""
    lo = int(KNOB_ADC_MIN)
    hi = int(KNOB_ADC_MAX)
    r = int(raw)
    if r < lo:
        r = lo
    if r > hi:
        r = hi
    span = hi - lo if hi > lo else 1
    rpm_span = int(KNOB_RPM_MAX) - int(KNOB_RPM_MIN)
    return int(KNOB_RPM_MIN) + (r - lo) * rpm_span // span


def make_presence(now_ms=0):
    return {
        "pir_raw": 0,
        "human": False,
        "armed": True,  # ready for next approach after quiet
        "last_human_ms": 0,
        "greeted": False,
        "greet_until_ms": 0,
        "chirp_hz": 0,
    }


def tick_presence(pres, pir_raw, greet_enabled, instrument_busy, now_ms):
    """Update presence; return event 'greet' once per approach or None.

    Never greets twice for one approach; never interrupts instrument run.
    """
    now = int(now_ms)
    human = int(pir_raw) != 0
    pres["pir_raw"] = 1 if human else 0
    event = None

    if human:
        if not pres.get("human"):
            # rising edge of presence
            if (
                greet_enabled
                and pres.get("armed")
                and not instrument_busy
                and not pres.get("greeted")
            ):
                pres["greeted"] = True
                pres["armed"] = False
                pres["greet_until_ms"] = now + int(PIR_GREET_CHIRP_MS)
                pres["chirp_hz"] = int(PIR_GREET_HZ)
                event = "greet"
        pres["human"] = True
        pres["last_human_ms"] = now
    else:
        was = pres.get("human")
        pres["human"] = False
        if was:
            # left — re-arm after quiet window from last sighting
            pass
        quiet = now - int(pres.get("last_human_ms") or 0)
        if quiet >= int(PIR_QUIET_MS):
            pres["armed"] = True
            pres["greeted"] = False

    if pres.get("greet_until_ms") and now >= int(pres["greet_until_ms"]):
        pres["greet_until_ms"] = 0
        pres["chirp_hz"] = 0

    return event


def chirp_active(pres, now_ms):
    return int(pres.get("chirp_hz") or 0) > 0 and int(now_ms) < int(
        pres.get("greet_until_ms") or 0
    )
