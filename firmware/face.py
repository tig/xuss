"""Face choreography — time-based patterns only (spec §4). No hardware."""

from defaults import (
    FACE_BLINK_MS,
    FACE_BLINK_PERIOD_MS,
    FACE_CHASE_BRIGHT,
    FACE_CHASE_MS,
    FACE_EYE_COLOR,
    FACE_IDLE_DIM,
    SIDE_LED_COUNT,
)


def _scale(rgb, level):
    r, g, b = rgb
    return (
        (r * level) // 255,
        (g * level) // 255,
        (b * level) // 255,
    )


def eyes_open(t_ms):
    """Blink closed for FACE_BLINK_MS at the end of each FACE_BLINK_PERIOD_MS."""
    phase = int(t_ms) % int(FACE_BLINK_PERIOD_MS)
    close_at = int(FACE_BLINK_PERIOD_MS) - int(FACE_BLINK_MS)
    return phase < close_at


def side_colors(t_ms, mode="idle"):
    """Ten RGB tuples for the side strip. Chase carries the idle beat."""
    n = int(SIDE_LED_COUNT)
    dim = _scale(FACE_EYE_COLOR, int(FACE_IDLE_DIM))
    bright = _scale(FACE_EYE_COLOR, int(FACE_CHASE_BRIGHT))
    idx = (int(t_ms) // int(FACE_CHASE_MS)) % n
    if mode == "fault":
        # solid dim red
        return [(40, 0, 0)] * n
    colors = [dim] * n
    colors[idx] = bright
    # trailing glow
    colors[(idx - 1) % n] = _scale(FACE_EYE_COLOR, int(FACE_CHASE_BRIGHT) // 3)
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
