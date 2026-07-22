"""Hair-bar marquee: scroll math + 5x7 font + off-screen RGB565 compose.

Drawing path for metal: compose the full bar in RAM, then one bulk blit.
That avoids the flicker of clear-bar + many fill_rect glyph updates.
"""

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
    return (0x7F, 0x7F, 0x7F, 0x7F, 0x7F)


def pack_rgb565_panel(r, g, b):
    """RGB → panel 565 word (M5GO MADCTL BGR: swap R/B). SPI uses LE bytes."""
    r = int(r) & 0xFF
    g = int(g) & 0xFF
    b = int(b) & 0xFF
    return ((b & 0xF8) << 8) | ((g & 0xFC) << 3) | (r >> 3)


def _le_bytes(color565):
    """Little-endian byte pair for SPI (M5 setSwapBytes / ILI9342 path)."""
    c = int(color565) & 0xFFFF
    return (c & 0xFF), ((c >> 8) & 0xFF)


def _fill_buf_solid(buf, w, h, color565):
    lo, hi = _le_bytes(color565)
    line = bytearray(w * 2)
    for i in range(w):
        line[i * 2] = lo
        line[i * 2 + 1] = hi
    row_bytes = w * 2
    for y in range(h):
        buf[y * row_bytes : (y + 1) * row_bytes] = line


def _fill_buf_rect(buf, w, h, x, y, rw, rh, color565):
    """Solid rect into bar buffer (clipped)."""
    if rw <= 0 or rh <= 0:
        return
    x0 = x if x > 0 else 0
    y0 = y if y > 0 else 0
    x1 = x + rw if x + rw < w else w
    y1 = y + rh if y + rh < h else h
    if x1 <= x0 or y1 <= y0:
        return
    lo, hi = _le_bytes(color565)
    row_bytes = w * 2
    for yy in range(y0, y1):
        base = yy * row_bytes
        for xx in range(x0, x1):
            i = base + xx * 2
            buf[i] = lo
            buf[i + 1] = hi


def compose_banner_buf(buf, w, h, text, x0, bar_rgb, fg_rgb, pack_fn=None):
    """Compose one hair-bar frame into ``buf`` (len >= w*h*2), row-major RGB565.

    Returns number of foreground pixels set (for host tests). Does not touch LCD.
    """
    if pack_fn is None:
        pack_fn = pack_rgb565_panel
    from defaults import FACE_BANNER_FG, FACE_BAR_COLOR

    if bar_rgb is None:
        bar_rgb = FACE_BAR_COLOR
    if fg_rgb is None:
        fg_rgb = FACE_BANNER_FG
    text = banner_text() if text is None else str(text)
    scale = max(1, int(FACE_BANNER_SCALE))
    w = int(w)
    h = int(h)
    need = w * h * 2
    if buf is None or len(buf) < need:
        raise ValueError("banner buffer too small")

    bg565 = pack_fn(bar_rgb[0], bar_rgb[1], bar_rgb[2])
    fg565 = pack_fn(fg_rgb[0], fg_rgb[1], fg_rgb[2])
    _fill_buf_solid(buf, w, h, bg565)

    glyph_h = 7 * scale
    text_y = max(0, (h - glyph_h) // 2)
    x = int(x0)
    adv = char_advance_px()
    fg_px = 0
    for ch in text:
        if x + adv < 0:
            x += adv
            continue
        if x >= w:
            break
        cols = glyph(ch)
        for col, bits in enumerate(cols):
            for row in range(7):
                if bits & (1 << row):
                    bx = x + col * scale
                    by = text_y + row * scale
                    _fill_buf_rect(buf, w, h, bx, by, scale, scale, fg565)
                    # count clipped area for tests
                    x0c = bx if bx > 0 else 0
                    y0c = by if by > 0 else 0
                    x1c = bx + scale if bx + scale < w else w
                    y1c = by + scale if by + scale < h else h
                    if x1c > x0c and y1c > y0c:
                        fg_px += (x1c - x0c) * (y1c - y0c)
        x += adv
    return fg_px


def make_banner_buf(w=None, h=None):
    """Allocate a reusable hair-bar frame buffer."""
    from defaults import FACE_BANNER_BAR_H

    if w is None:
        w = int(LCD_WIDTH)
    if h is None:
        h = int(FACE_BANNER_BAR_H)
    return bytearray(int(w) * int(h) * 2)


def draw_banner(fill_rect, text, x0, bar_rgb, fg_rgb, screen_w=None, bar_h=None, y0=0):
    """Legacy path: compose off-screen then emit one solid row-strip via fill_rect.

    Prefer ``compose_banner_buf`` + LCD blit on metal. This keeps host tests that
    only mock fill_rect working: we emit a full-bar bg rect then per-pixel fg.
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
    w = int(screen_w)
    h = int(bar_h)
    y0 = int(y0)
    buf = make_banner_buf(w, h)
    compose_banner_buf(buf, w, h, text, x0, bar_rgb, fg_rgb)
    # Emit as single bg pass is wrong for tests that count fg — walk buffer.
    fill_rect(0, y0, w, h, bar_rgb)
    bg565 = pack_rgb565_panel(bar_rgb[0], bar_rgb[1], bar_rgb[2])
    bg_hi = (bg565 >> 8) & 0xFF
    bg_lo = bg565 & 0xFF
    row_bytes = w * 2
    # Group horizontal runs of fg for fewer callbacks (still not the metal path).
    for yy in range(h):
        base = yy * row_bytes
        xx = 0
        while xx < w:
            i = base + xx * 2
            if buf[i] == bg_hi and buf[i + 1] == bg_lo:
                xx += 1
                continue
            run = xx
            while run < w:
                j = base + run * 2
                if buf[j] == bg_hi and buf[j + 1] == bg_lo:
                    break
                run += 1
            fill_rect(xx, y0 + yy, run - xx, 1, fg_rgb)
            xx = run
