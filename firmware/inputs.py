"""ANGLE knob + PIR presence logic. Host-importable."""

from defaults import (
    KNOB_ADC_MAX,
    KNOB_ADC_MIN,
    KNOB_RPM_MAX,
    KNOB_RPM_MIN,
    PIR_BOOT_GRACE_MS,
    PIR_DEBOUNCE_TICKS,
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
        "pir_high_count": 0,
        "human": False,
        "armed": True,
        "last_human_ms": 0,
        "greeted": False,
        "greet_until_ms": 0,
        "chirp_hz": 0,
        "t0_ms": int(now_ms),
    }


def tick_presence(pres, pir_raw, greet_enabled, instrument_busy, now_ms):
    """Update presence; return event 'greet' once per approach or None.

    Never greets twice for one approach; never interrupts instrument run.
    Debounced + boot-grace so a floating pin cannot peep-loop.
    """
    now = int(now_ms)
    event = None

    # Boot grace: ignore PIR entirely
    t0 = int(pres.get("t0_ms") or 0)
    if now - t0 < int(PIR_BOOT_GRACE_MS):
        pres["pir_raw"] = 0
        pres["pir_high_count"] = 0
        return None

    # Debounce: need N consecutive highs
    if int(pir_raw) != 0:
        pres["pir_high_count"] = int(pres.get("pir_high_count") or 0) + 1
    else:
        pres["pir_high_count"] = 0
    human = int(pres["pir_high_count"]) >= int(PIR_DEBOUNCE_TICKS)
    pres["pir_raw"] = 1 if human else 0

    if human:
        if not pres.get("human"):
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
        pres["human"] = False
        quiet = now - int(pres.get("last_human_ms") or 0)
        # only re-arm after we have seen a human at least once (last_human_ms > 0)
        if int(pres.get("last_human_ms") or 0) > 0 and quiet >= int(PIR_QUIET_MS):
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
