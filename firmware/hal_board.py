"""Device HAL backend for M5GO — only deploy module allowed to import machine.

Pin map: M5GO IoT Kit v2.7 (ILI9342C, SK6812x10@G15, SPK@G25, Port B@G26).
"""

from defaults import (
    FACE_BG_COLOR,
    FACE_DRIVE_COLOR,
    FACE_EYE_COLOR,
    FACE_SING_COLOR,
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
    SPEAKER_PIN,
    TACH_PIN,
)


def _rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


class _Ili9342:
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
        import time

        self.rst.value(0)
        time.sleep_ms(20)
        self.rst.value(1)
        time.sleep_ms(120)

    def init(self):
        import time

        self.reset()
        self._cmd(0x01)
        time.sleep_ms(150)
        self._cmd(0x11)
        time.sleep_ms(120)
        self._cmd(0x3A)
        self._data_byte(0x55)
        self._cmd(0x36)
        self._data_byte(0x08)
        self._cmd(0x29)
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


def _pwm_duty_u16(duty_pct):
    # 0-100% -> 0-65535
    p = int(duty_pct)
    if p < 0:
        p = 0
    if p > 100:
        p = 100
    return (p * 65535) // 100


def make_board_hal():
    from machine import PWM, Pin, SPI  # type: ignore
    import neopixel  # type: ignore
    import time

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
        lcd_ok = False

    spk_pin = Pin(SPEAKER_PIN, Pin.OUT)
    tach_pin = Pin(TACH_PIN, Pin.OUT)
    spk_pwm = PWM(spk_pin, freq=1000, duty_u16=0)
    tach_pwm = PWM(tach_pin, freq=1000, duty_u16=0)

    _last_face_key = [None]
    _last_edge = [None]  # (hz, duty, route)

    def _apply_pwm(pwm, hz, duty_pct):
        if hz is None or hz <= 0:
            try:
                pwm.duty_u16(0)
            except Exception:
                pwm.duty(0)
            return
        ihz = int(hz)
        if ihz < 1:
            ihz = 1
        try:
            pwm.freq(ihz)
        except ValueError:
            # out of hardware range — park this sink
            try:
                pwm.duty_u16(0)
            except Exception:
                pwm.duty(0)
            return
        try:
            pwm.duty_u16(_pwm_duty_u16(duty_pct))
        except Exception:
            pwm.duty(int(duty_pct * 1023 / 100))

    class BoardHal:
        def set_led(self, on: bool) -> None:
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
            open_eyes = bool(frame.get("eyes_open", True))
            mode = frame.get("mode", "idle")
            key = (open_eyes, mode)
            if key == _last_face_key[0]:
                return
            _last_face_key[0] = key

            bg = FACE_BG_COLOR
            if mode == "singing":
                eye = FACE_SING_COLOR
                bar = FACE_SING_COLOR
            elif mode == "driving":
                eye = FACE_DRIVE_COLOR
                bar = FACE_DRIVE_COLOR
            elif mode == "fault":
                eye = (255, 40, 40)
                bar = eye
            else:
                eye = FACE_EYE_COLOR
                bar = (0, 80, 100)

            lcd.fill(bg)
            lcd.fill_rect(0, 0, LCD_WIDTH, 28, bar)
            if open_eyes:
                lcd.fill_rect(70, 90, 70, 50, eye)
                lcd.fill_rect(90, 105, 24, 24, bg)
                lcd.fill_rect(180, 90, 70, 50, eye)
                lcd.fill_rect(200, 105, 24, 24, bg)
            else:
                lcd.fill_rect(70, 110, 70, 10, eye)
                lcd.fill_rect(180, 110, 70, 10, eye)
            lcd.fill_rect(110, 180, 100, 8, (0, 60, 80))

        def set_backlight(self, on: bool) -> None:
            bl.value(1 if on else 0)

        def set_edge(self, hz, duty_pct, route) -> None:
            key = (float(hz or 0), int(duty_pct), str(route))
            if key == _last_edge[0]:
                return
            _last_edge[0] = key
            hz = float(hz or 0)
            duty = int(duty_pct)
            r = str(route)
            voice_on = r in ("voice", "both") and hz > 0
            tach_on = r in ("tach", "both") and hz > 0
            _apply_pwm(spk_pwm, hz if voice_on else 0, duty)
            _apply_pwm(tach_pwm, hz if tach_on else 0, duty)

        def park_outputs(self) -> None:
            _last_edge[0] = (0.0, 0, "park")
            _apply_pwm(spk_pwm, 0, 0)
            _apply_pwm(tach_pwm, 0, 0)

        def reboot(self) -> None:
            self.park_outputs()
            import machine  # type: ignore

            machine.reset()

        def ticks_ms(self) -> int:
            return int(time.ticks_ms())

        def sleep_ms(self, ms: int) -> None:
            time.sleep_ms(int(ms))

    return BoardHal()
