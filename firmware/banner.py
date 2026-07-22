"""Hair-bar marquee: scroll math + 5x7 font (host-importable, no machine)."""

from defaults import (
    FACE_BANNER_GAP_PX,
    FACE_BANNER_SCALE,
    FACE_BANNER_SPEED_PX_S,
    FACE_BANNER_TEXT,
    LCD_WIDTH,
)

# 5-column × 7-row glyphs; each tuple is 5 column bytes, bit0 = top row.
_FONT = {
    " ": (0x00, 0x00, 0x00, 0x00, 0x00),
    ";": (0x00, 0x36, 0x36, 0x00, 0x00),
    ".": (0x00, 0x60, 0x60, 0x00, 0x00),
    ",": (0x00, 0x80, 0x60, 0x00, 0x00),
    ":": (0x00, 0x6C, 0x6C, 0x00, 0x00),
    "-": (0x08, 0x08, 0x08, 0x08, 0x08),
    "X": (0x63, 0x14, 0x08, 0x14, 0x63),
    "S": (0x26, 0x49, 0x49, 0x49, 0x32),
    "i": (0x00, 0x44, 0x7D, 0x40, 0x00),
    "l": (0x00, 0x41, 0x7F, 0x40, 0x00),
    "c": (0x38, 0x44, 0x44, 0x44, 0x28),
    "o": (0x38, 0x44, 0x44, 0x44, 0x38),
    "u": (0x3C, 0x40, 0x40, 0x3C, 0x40),
    "s": (0x48, 0x54, 0x54, 0x54, 0x24),
    "b": (0x7F, 0x48, 0x44, 0x44, 0x38),
    "t": (0x04, 0x3F, 0x44, 0x40, 0x20),
    "w": (0x3C, 0x40, 0x30, 0x40, 0x3C),
    "h": (0x7F, 0x08, 0x04, 0x04, 0x78),
    "e": (0x38, 0x54, 0x54, 0x54, 0x18),
    "a": (0x20, 0x54, 0x54, 0x54, 0x78),
    "d": (0x38, 0x44, 0x44, 0x48, 0x7F),
    "n": (0x7C, 0x08, 0x04, 0x04, 0x78),
    "g": (0x0C, 0x52, 0x52, 0x52, 0x3E),
    "r": (0x7C, 0x08, 0x04, 0x04, 0x08),
    "k": (0x7F, 0x10, 0x28, 0x44, 0x00),
    "m": (0x7C, 0x04, 0x18, 0x04, 0x78),
    "p": (0x7E, 0x14, 0x14, 0x14, 0x08),
    "y": (0x0C, 0x50, 0x50, 0x50, 0x3C),
    "f": (0x08, 0x7E, 0x09, 0x01, 0x02),
    "v": (0x1C, 0x20, 0x40, 0x20, 0x1C),
    "A": (0x7E, 0x11, 0x11, 0x11, 0x7E),
    "B": (0x7F, 0x49, 0x49, 0x49, 0x36),
    "C": (0x3E, 0x41, 0x41, 0x41, 0x22),
    "D": (0x7F, 0x41, 0x41, 0x22, 0x1C),
    "E": (0x7F, 0x49, 0x49, 0x49, 0x41),
    "F": (0x7F, 0x09, 0x09, 0x09, 0x01),
    "G": (0x3E, 0x41, 0x49, 0x49, 0x7A),
    "H": (0x7F, 0x08, 0x08, 0x08, 0x7F),
    "I": (0x00, 0x41, 0x7F, 0x41, 0x00),
    "J": (0x20, 0x40, 0x41, 0x3F, 0x01),
    "K": (0x7F, 0x08, 0x14, 0x22, 0x41),
    "L": (0x7F, 0x40, 0x40, 0x40, 0x40),
    "M": (0x7F, 0x02, 0x0C, 0x02, 0x7F),
    "N": (0x7F, 0x04, 0x08, 0x10, 0x7F),
    "O": (0x3E, 0x41, 0x41, 0x41, 0x3E),
    "P": (0x7F, 0x09, 0x09, 0x09, 0x06),
    "Q": (0x3E, 0x41, 0x51, 0x21, 0x5E),
    "R": (0x7F, 0x09, 0x19, 0x29, 0x46),
    "T": (0x01, 0x01, 0x7F, 0x01, 0x01),
    "U": (0x3F, 0x40, 0x40, 0x40, 0x3F),
    "V": (0x1F, 0x20, 0x40, 0x20, 0x1F),
    "W": (0x3F, 0x40, 0x38, 0x40, 0x3F),
    "Y": (0x07, 0x08, 0x70, 0x08, 0x07),
    "Z": (0x61, 0x51, 0x49, 0x45, 0x43),
}


def banner_text():
    return str(FACE_BANNER_TEXT)


def char_advance_px():
    """Pixel width of one glyph column advance (glyph + 1px gap), scaled."""
    scale = max(1, int(FACE_BANNER_SCALE))
    return (5 + 1) * scale


def text_width_px(text=None):
    text = banner_text() if text is None else str(text)
    return len(text) * char_advance_px()


def loop_width_px(text=None, screen_w=None):
    """Full scroll loop: text clears left, then re-enters from right."""
    if screen_w is None:
        screen_w = int(LCD_WIDTH)
    tw = text_width_px(text)
    gap = max(0, int(FACE_BANNER_GAP_PX))
    return tw + int(screen_w) + gap


def banner_x(t_ms, text=None, screen_w=None):
    """Left edge of the text string. Decreases over time (right → left).

    At t=0 the string's left edge is at screen_w (just off the right edge).
    """
    if screen_w is None:
        screen_w = int(LCD_WIDTH)
    speed = max(1, int(FACE_BANNER_SPEED_PX_S))
    loop = loop_width_px(text, screen_w=screen_w)
    if loop <= 0:
        return int(screen_w)
    dist = (int(t_ms) * speed) // 1000
    # x starts at screen_w and walks left; modulo keeps it looping.
    return int(screen_w) - (dist % loop)


def glyph(ch):
    if ch in _FONT:
        return _FONT[ch]
    # fallback: solid block for unknown
    return (0x7F, 0x7F, 0x7F, 0x7F, 0x7F)


def iter_glyph_blocks(ch, origin_x, origin_y, scale=None):
    """Yield (x, y, w, h) solid blocks for set bits (scale×scale each)."""
    if scale is None:
        scale = max(1, int(FACE_BANNER_SCALE))
    cols = glyph(ch)
    for col, bits in enumerate(cols):
        for row in range(7):
            if bits & (1 << row):
                yield (
                    origin_x + col * scale,
                    origin_y + row * scale,
                    scale,
                    scale,
                )


def draw_banner(fill_rect, text, x0, bar_rgb, fg_rgb, screen_w=None, bar_h=None, y0=0):
    """Draw marquee into the hair bar via fill_rect(x, y, w, h, rgb).

    fill_rect is the LCD (or a recorder). Clips to the bar rectangle.
    """
    from defaults import FACE_BANNER_BAR_H, FACE_BANNER_FG, FACE_BAR_COLOR

    if screen_w is None:
        screen_w = int(LCD_WIDTH)
    if bar_h is None:
        bar_h = int(FACE_BANNER_BAR_H)
    if bar_rgb is None:
        bar_rgb = FACE_BAR_COLOR
    if fg_rgb is None:
        fg_rgb = FACE_BANNER_FG
    text = banner_text() if text is None else str(text)
    scale = max(1, int(FACE_BANNER_SCALE))
    y0 = int(y0)
    bar_h = int(bar_h)
    screen_w = int(screen_w)
    fill_rect(0, y0, screen_w, bar_h, bar_rgb)
    glyph_h = 7 * scale
    text_y = y0 + max(0, (bar_h - glyph_h) // 2)
    x = int(x0)
    adv = char_advance_px()
    y1 = y0 + bar_h
    for ch in text:
        # skip fully off-left / stop when fully off-right
        if x + adv < 0:
            x += adv
            continue
        if x >= screen_w:
            break
        for bx, by, bw, bh in iter_glyph_blocks(ch, x, text_y, scale=scale):
            # Clip block to bar/screen
            x_left = bx if bx > 0 else 0
            y_top = by if by > y0 else y0
            x_right = bx + bw if bx + bw < screen_w else screen_w
            y_bot = by + bh if by + bh < y1 else y1
            if x_right > x_left and y_bot > y_top:
                fill_rect(x_left, y_top, x_right - x_left, y_bot - y_top, fg_rgb)
        x += adv
