"""Face choreography — time-based patterns only (spec §4). No hardware."""

from banner import banner_text, banner_x
from defaults import (
    FACE_BLINK_MS,
    FACE_BLINK_PERIOD_MS,
    FACE_CHASE_BRIGHT,
    FACE_CHASE_MS,
    FACE_IDLE_DIM,
    FACE_IDLE_SIDE_ON,
    FACE_THEME_DEFAULT,
    FACE_THEMES,
    FACE_WINK_EYE,
    FACE_WINK_MS,
    FACE_WINK_PERIOD_MS,
    SIDE_LED_COUNT,
)


def theme_count():
    return len(FACE_THEMES)


def theme_at(idx):
    """Return theme dict for index (wraps)."""
    n = theme_count()
    if n <= 0:
        return {
            "name": "blue",
            "eye": (40, 140, 255),
            "bar": (0, 50, 120),
            "bg": (0, 0, 20),
            "banner_fg": (200, 230, 255),
            "side": (40, 140, 255),
        }
    i = int(idx) % n
    if i < 0:
        i += n
    return FACE_THEMES[i]


def next_theme_index(idx):
    n = theme_count()
    if n <= 0:
        return 0
    return (int(idx) + 1) % n


def _scale(rgb, level):
    r, g, b = rgb
    return (
        (r * level) // 255,
        (g * level) // 255,
        (b * level) // 255,
    )


def _base_color(mode, theme):
    """Primary face/side color for mode under the active theme."""
    eye = theme.get("eye") or (40, 140, 255)
    if mode == "fault":
        return (255, 40, 40)
    # Active modes use the same theme hue (slightly brighter wash via chase).
    return eye


def _idle_winking(t_ms):
    """True during the brief wink window once per FACE_WINK_PERIOD_MS."""
    period = int(FACE_WINK_PERIOD_MS)
    wink = int(FACE_WINK_MS)
    if period <= 0 or wink <= 0:
        return False
    if wink >= period:
        wink = period // 4 or 1
    phase = int(t_ms) % period
    return phase >= (period - wink)


def eye_state(t_ms, mode="idle"):
    """Return (left_open, right_open). Time-based only."""
    if mode == "fault":
        return (True, True)
    if mode == "idle":
        if not _idle_winking(t_ms):
            return (True, True)
        which = str(FACE_WINK_EYE or "right").lower()
        if which == "left":
            return (False, True)
        return (True, False)
    phase = int(t_ms) % int(FACE_BLINK_PERIOD_MS)
    close_at = int(FACE_BLINK_PERIOD_MS) - int(FACE_BLINK_MS)
    open_ = phase < close_at
    return (open_, open_)


def eyes_open(t_ms, mode="idle"):
    left, right = eye_state(t_ms, mode=mode)
    return bool(left and right)


def side_colors(t_ms, mode="idle", theme=None):
    """Side strip. Theme side (0,0,0) ⇒ fully off (black theme)."""
    if theme is None:
        theme = theme_at(FACE_THEME_DEFAULT)
    n = int(SIDE_LED_COUNT)
    side = theme.get("side")
    if side is None:
        side = theme.get("eye") or (0, 0, 0)
    # Black / off theme
    if side[0] == 0 and side[1] == 0 and side[2] == 0:
        return [(0, 0, 0)] * n
    if mode == "fault":
        return [(40, 0, 0)] * n
    base = side
    dim = _scale(base, int(FACE_IDLE_DIM))
    if mode == "idle":
        if int(FACE_IDLE_SIDE_ON) == 0:
            return [(0, 0, 0)] * n
        return [dim] * n
    bright = _scale(base, int(FACE_CHASE_BRIGHT))
    idx = (int(t_ms) // int(FACE_CHASE_MS)) % n
    colors = [dim] * n
    colors[idx] = bright
    colors[(idx - 1) % n] = _scale(base, int(FACE_CHASE_BRIGHT) // 3)
    if mode in ("singing", "driving"):
        colors[(idx + 5) % n] = _scale(base, int(FACE_CHASE_BRIGHT) // 2)
    return colors


def frame(t_ms, mode="idle", identity="XUSS", theme_idx=None):
    if theme_idx is None:
        theme_idx = FACE_THEME_DEFAULT
    theme = theme_at(theme_idx)
    left, right = eye_state(t_ms, mode=mode)
    eye = _base_color(mode, theme)
    return {
        "mode": mode,
        "identity": identity,
        "eyes_open": bool(left and right),
        "left_open": bool(left),
        "right_open": bool(right),
        "side": side_colors(t_ms, mode=mode, theme=theme),
        "banner_text": banner_text(),
        "banner_x": banner_x(t_ms),
        "theme_idx": int(theme_idx) % theme_count() if theme_count() else 0,
        "theme_name": theme.get("name"),
        "eye_color": eye,
        "bar_color": theme.get("bar") or (0, 50, 120),
        "bg_color": theme.get("bg") or (0, 0, 20),
        "banner_fg": theme.get("banner_fg") or (200, 230, 255),
        "t_ms": int(t_ms),
    }
