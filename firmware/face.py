"""Face choreography — time-based patterns only (spec §4). No hardware."""

from banner import banner_text, banner_x
from defaults import (
    FACE_BLINK_MS,
    FACE_BLINK_PERIOD_MS,
    FACE_CHASE_BRIGHT,
    FACE_CHASE_MS,
    FACE_DRIVE_COLOR,
    FACE_EYE_COLOR,
    FACE_IDLE_DIM,
    FACE_IDLE_SIDE_ON,
    FACE_SING_COLOR,
    FACE_WINK_EYE,
    FACE_WINK_MS,
    FACE_WINK_PERIOD_MS,
    SIDE_LED_COUNT,
)


def _scale(rgb, level):
    r, g, b = rgb
    return (
        (r * level) // 255,
        (g * level) // 255,
        (b * level) // 255,
    )


def _mode_color(mode):
    if mode == "singing":
        return FACE_SING_COLOR
    if mode == "driving":
        return FACE_DRIVE_COLOR
    if mode == "fault":
        return (255, 40, 40)
    return FACE_EYE_COLOR


def _idle_winking(t_ms):
    """True during the brief wink window once per FACE_WINK_PERIOD_MS."""
    period = int(FACE_WINK_PERIOD_MS)
    wink = int(FACE_WINK_MS)
    if period <= 0 or wink <= 0:
        return False
    if wink >= period:
        wink = period // 4 or 1
    phase = int(t_ms) % period
    # Wink near the end of each period so first seconds after boot stay open.
    return phase >= (period - wink)


def eye_state(t_ms, mode="idle"):
    """Return (left_open, right_open). Time-based only.

    Idle: both open, then a one-eye wink every FACE_WINK_PERIOD_MS.
    Singing/driving: both eyes blink together (prior active path).
    Fault: both open.
    """
    if mode == "fault":
        return (True, True)
    if mode == "idle":
        if not _idle_winking(t_ms):
            return (True, True)
        which = str(FACE_WINK_EYE or "right").lower()
        if which == "left":
            return (False, True)
        return (True, False)
    # active modes: bilateral blink
    phase = int(t_ms) % int(FACE_BLINK_PERIOD_MS)
    close_at = int(FACE_BLINK_PERIOD_MS) - int(FACE_BLINK_MS)
    open_ = phase < close_at
    return (open_, open_)


def eyes_open(t_ms, mode="idle"):
    """Both eyes open (compat). False if either is closed (blink or wink)."""
    left, right = eye_state(t_ms, mode=mode)
    return bool(left and right)


def side_colors(t_ms, mode="idle"):
    """Side strip. Idle is static (no chase); active modes chase on the beat.

    Continuous SK6812 bit-bang can couple into the M5 amp — idle paints a
    fixed dim frame once (main throttles rewrites). Operator product face
    needs the strip visible at idle.
    """
    n = int(SIDE_LED_COUNT)
    base = _mode_color(mode)
    if mode == "fault":
        return [(40, 0, 0)] * n
    dim = _scale(base, int(FACE_IDLE_DIM))
    if mode == "idle":
        if int(FACE_IDLE_SIDE_ON) == 0:
            return [(0, 0, 0)] * n
        # Static soft blue wash — readable on camera, no chase thrash
        return [dim] * n
    bright = _scale(base, int(FACE_CHASE_BRIGHT))
    idx = (int(t_ms) // int(FACE_CHASE_MS)) % n
    colors = [dim] * n
    colors[idx] = bright
    colors[(idx - 1) % n] = _scale(base, int(FACE_CHASE_BRIGHT) // 3)
    if mode in ("singing", "driving"):
        colors[(idx + 5) % n] = _scale(base, int(FACE_CHASE_BRIGHT) // 2)
    return colors


def frame(t_ms, mode="idle", identity="XUSS"):
    left, right = eye_state(t_ms, mode=mode)
    return {
        "mode": mode,
        "identity": identity,
        "eyes_open": bool(left and right),
        "left_open": bool(left),
        "right_open": bool(right),
        "side": side_colors(t_ms, mode=mode),
        "banner_text": banner_text(),
        "banner_x": banner_x(t_ms),
        "t_ms": int(t_ms),
    }
