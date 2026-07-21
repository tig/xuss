"""Device HAL backend for M5GO — only deploy module allowed to import machine.

Pin map: M5GO IoT Kit v2.7 docs (ILI9342C + SK6812x10 on G15).
"""

from defaults import (
    FACE_BG_COLOR,
    FACE_EYE_COLOR,
    LCD_BAUD,
    LCD_BL_PIN,
    LCD_CS_PIN,
    LCD_DC_PIN,
    LCD_HEIGHT,
    LCD_MOSI_PIN,
    LCD_RST_PIN,
    LCD_SCK_PIN,
    LCD_SPI_ID,
    LCD_WIDTH,
    SIDE_LED_COUNT,
    SIDE_LED_PIN,
)


def _rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


class _Ili9342:
    """Minimal ILI9342C driver: init, fill, rects. Enough for the idle face."""

    def __init__(self, spi, cs, dc, rst, bl):
        self.spi = spi
        self.cs = cs
        self.dc = dc
        self.rst = rst
        self.bl = bl
        self.width = LCD_WIDTH
        self.height = LCD_HEIGHT

    def _cmd(self, c):
        self.dc.value(0)
        self.cs.value(0)
        self.spi.write(bytearray([c]))
        self.cs.value(1)

    def _data(self, buf):
        self.dc.value(1)
        self.cs.value(0)
        self.spi.write(buf)
        self.cs.value(1)

    def _data_byte(self, b):
        self._data(bytearray([b]))

    def reset(self):
        self.rst.value(0)
        import time

        time.sleep_ms(20)
        self.rst.value(1)
        time.sleep_ms(120)

    def init(self):
        import time

        self.reset()
        self._cmd(0x01)  # SWRESET
        time.sleep_ms(150)
        self._cmd(0x11)  # SLPOUT
        time.sleep_ms(120)
        self._cmd(0x3A)  # COLMOD
        self._data_byte(0x55)  # 16-bit
        # MADCTL: M5 Core landscape, BGR often needed on ILI9342
        self._cmd(0x36)
        self._data_byte(0x08)
        self._cmd(0x29)  # DISPON
        time.sleep_ms(20)
        self.bl.value(1)

    def _window(self, x0, y0, x1, y1):
        self._cmd(0x2A)
        self._data(bytearray([x0 >> 8, x0 & 0xFF, x1 >> 8, x1 & 0xFF]))
        self._cmd(0x2B)
        self._data(bytearray([y0 >> 8, y0 & 0xFF, y1 >> 8, y1 & 0xFF]))
        self._cmd(0x2C)

    def fill_rect(self, x, y, w, h, color_rgb):
        if w <= 0 or h <= 0:
            return
        x0 = max(0, int(x))
        y0 = max(0, int(y))
        x1 = min(self.width - 1, x0 + int(w) - 1)
        y1 = min(self.height - 1, y0 + int(h) - 1)
        if x1 < x0 or y1 < y0:
            return
        c = _rgb565(*color_rgb)
        hi = c >> 8
        lo = c & 0xFF
        row_w = x1 - x0 + 1
        # chunk rows to keep allocations small on ESP32
        row = bytearray(row_w * 2)
        for i in range(row_w):
            row[i * 2] = hi
            row[i * 2 + 1] = lo
        self._window(x0, y0, x1, y1)
        self.dc.value(1)
        self.cs.value(0)
        for _ in range(y1 - y0 + 1):
            self.spi.write(row)
        self.cs.value(1)

    def fill(self, color_rgb):
        self.fill_rect(0, 0, self.width, self.height, color_rgb)


def make_board_hal():
    """Construct the on-metal HAL. Imports machine only when called on device."""
    from machine import Pin, SPI  # type: ignore
    import neopixel  # type: ignore
    import time

    # Side LEDs: SK6812 x10 on G15 (M5 recommends open-drain)
    try:
        led_pin = Pin(SIDE_LED_PIN, Pin.OPEN_DRAIN)
    except (AttributeError, TypeError, ValueError):
        led_pin = Pin(SIDE_LED_PIN, Pin.OUT)
    np = neopixel.NeoPixel(led_pin, int(SIDE_LED_COUNT))

    bl = Pin(LCD_BL_PIN, Pin.OUT)
    cs = Pin(LCD_CS_PIN, Pin.OUT)
    dc = Pin(LCD_DC_PIN, Pin.OUT)
    rst = Pin(LCD_RST_PIN, Pin.OUT)
    cs.value(1)
    bl.value(0)

    spi = SPI(
        LCD_SPI_ID,
        baudrate=LCD_BAUD,
        polarity=0,
        phase=0,
        sck=Pin(LCD_SCK_PIN),
        mosi=Pin(LCD_MOSI_PIN),
    )
    lcd = _Ili9342(spi, cs, dc, rst, bl)
    lcd_ok = False
    try:
        lcd.init()
        lcd.fill(FACE_BG_COLOR)
        lcd_ok = True
    except Exception:
        # Still drive side LEDs if panel init fails
        lcd_ok = False

    _last_face_key = [None]

    class BoardHal:
        def set_led(self, on: bool) -> None:
            # Map legacy status to center pair of side LEDs when idle chase is off
            mid = int(SIDE_LED_COUNT) // 2
            if on:
                np[mid] = FACE_EYE_COLOR
                np[mid - 1] = FACE_EYE_COLOR
            else:
                np[mid] = (0, 0, 0)
                np[mid - 1] = (0, 0, 0)
            np.write()

        def set_side_leds(self, colors) -> None:
            n = int(SIDE_LED_COUNT)
            for i in range(n):
                if i < len(colors):
                    r, g, b = colors[i]
                    np[i] = (int(r), int(g), int(b))
                else:
                    np[i] = (0, 0, 0)
            np.write()

        def show_face(self, frame) -> None:
            if not lcd_ok:
                return
            # Avoid full redraw every tick: key on eyes + mode + coarse time bucket
            open_eyes = bool(frame.get("eyes_open", True))
            mode = frame.get("mode", "idle")
            key = (open_eyes, mode)
            if key == _last_face_key[0]:
                return
            _last_face_key[0] = key

            bg = FACE_BG_COLOR
            eye = FACE_EYE_COLOR if mode != "fault" else (255, 40, 40)
            lcd.fill(bg)
            # title bar
            bar = (0, 80, 100) if mode == "idle" else eye
            lcd.fill_rect(0, 0, LCD_WIDTH, 28, bar)
            # identity stripe (no font: solid block left + right "eyes" region)
            if open_eyes:
                # left eye
                lcd.fill_rect(70, 90, 70, 50, eye)
                lcd.fill_rect(90, 105, 24, 24, bg)
                # right eye
                lcd.fill_rect(180, 90, 70, 50, eye)
                lcd.fill_rect(200, 105, 24, 24, bg)
            else:
                # closed lids
                lcd.fill_rect(70, 110, 70, 10, eye)
                lcd.fill_rect(180, 110, 70, 10, eye)
            # mouth idle line
            lcd.fill_rect(110, 180, 100, 8, (0, 60, 80))

        def set_backlight(self, on: bool) -> None:
            bl.value(1 if on else 0)

        def ticks_ms(self) -> int:
            return int(time.ticks_ms())

        def sleep_ms(self, ms: int) -> None:
            time.sleep_ms(int(ms))

    return BoardHal()
