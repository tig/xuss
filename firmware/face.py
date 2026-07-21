"""Face choreography — time-based patterns only (spec §4). No hardware."""

from defaults import (
    FACE_BLINK_MS,
    FACE_BLINK_PERIOD_MS,
    FACE_CHASE_BRIGHT,
    FACE_CHASE_MS,
    FACE_DRIVE_COLOR,
    FACE_EYE_COLOR,
    FACE_IDLE_DIM,
    FACE_SING_COLOR,
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


def eyes_open(t_ms):
    """Blink closed for FACE_BLINK_MS at the end of each FACE_BLINK_PERIOD_MS."""
    phase = int(t_ms) % int(FACE_BLINK_PERIOD_MS)
    close_at = int(FACE_BLINK_PERIOD_MS) - int(FACE_BLINK_MS)
    return phase < close_at


def side_colors(t_ms, mode="idle"):
    """Ten RGB tuples for the side strip. Chase carries the beat."""
    n = int(SIDE_LED_COUNT)
    base = _mode_color(mode)
    if mode == "fault":
        return [(40, 0, 0)] * n
    dim = _scale(base, int(FACE_IDLE_DIM))
    bright = _scale(base, int(FACE_CHASE_BRIGHT))
    idx = (int(t_ms) // int(FACE_CHASE_MS)) % n
    # singing: faster feel via dual highlights
    colors = [dim] * n
    colors[idx] = bright
    colors[(idx - 1) % n] = _scale(base, int(FACE_CHASE_BRIGHT) // 3)
    if mode in ("singing", "driving"):
        colors[(idx + 5) % n] = _scale(base, int(FACE_CHASE_BRIGHT) // 2)
    return colors


def frame(t_ms, mode="idle", identity="XUSS"):
    """Full face frame for HAL show_face / set_side_leds."""
    return {
        "mode": mode,
        "identity": identity,
        "eyes_open": eyes_open(t_ms) if mode != "fault" else True,
        "side": side_colors(t_ms, mode=mode),
        "t_ms": int(t_ms),
    }
