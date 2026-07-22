"""Device HAL backend for M5GO — only deploy module allowed to import machine.

Pin map: M5GO IoT Kit v2.7 (ILI9342C, SK6812x10@G15, SPK@G25, Port B@G26).

Voice and tach are both hardware PWM (pitch-honest). Loudness is NOT encoded
by thinning duty — that turns a square into a nasty pulse train. Volume 0 mutes
voice; 1-10 play a clean mark-space square (default 50%).
"""

from defaults import (
    ANGLE_ADC_PIN,
    BOOT_RIFF_FADE_MS,
    BOOT_RIFF_HOLD_MID_MS,
    BOOT_RIFF_HZ,
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
    PIR_PIN,
    SIDE_LED_COUNT,
    SIDE_LED_PIN,
    SPEAKER_PIN,
    TACH_PIN,
)


def _rgb565(r, g, b):
    """Pack operator RGB into panel wire order.

    M5GO ILI9342C is brought up with MADCTL BGR (0x36 = 0x08). Feeding
    RGB565 as-is swaps red and blue on the glass — blues look orange.
    Swap R/B here so defaults FACE_*_COLOR stay natural RGB for humans.
    """
    r = int(r) & 0xFF
    g = int(g) & 0xFF
    b = int(b) & 0xFF
    return ((b & 0xF8) << 8) | ((g & 0xFC) << 3) | (r >> 3)


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
    p = int(duty_pct)
    if p < 0:
        p = 0
    if p > 100:
        p = 100
    return (p * 65535) // 100


def emergency_silence():
    """Last-ditch: G25/G26 low. Safe without a HAL instance."""
    from machine import PWM, Pin  # type: ignore

    for n in (SPEAKER_PIN, TACH_PIN):
        try:
            PWM(Pin(n)).deinit()
        except Exception:
            pass
        try:
            Pin(n, Pin.OUT).value(0)
        except Exception:
            pass


def make_board_hal():
    from machine import PWM, Pin, SPI  # type: ignore
    import neopixel  # type: ignore
    import time

    # Absolute silence before any peripheral brings the amp up
    emergency_silence()

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

    from machine import ADC, DAC  # type: ignore

    # Do NOT leave LEDC running at boot — duty=0 PWM still hums the M5 amp.
    # Idle = digital OUT low, no PWM/DAC object.
    spk_pin = Pin(SPEAKER_PIN, Pin.OUT)
    spk_pin.value(0)
    tach_pin = Pin(TACH_PIN, Pin.OUT)
    tach_pin.value(0)
    spk_pwm = [None]
    tach_pwm = [None]
    spk_dac = [None]
    voice_mode = ["off"]  # off | pwm | dac
    _last_spk = [None]
    _last_tach = [None]

    try:
        angle_adc = ADC(Pin(ANGLE_ADC_PIN))
        try:
            angle_adc.atten(ADC.ATTN_11DB)
        except Exception:
            pass
    except Exception:
        angle_adc = None

    try:
        # Pull-down: floating Port C must not look like a human forever
        try:
            pir_pin = Pin(PIR_PIN, Pin.IN, Pin.PULL_DOWN)
        except Exception:
            pir_pin = Pin(PIR_PIN, Pin.IN)
    except Exception:
        pir_pin = None

    def _spk_off():
        """True silence: tear down DAC/PWM and hold pin hard low.

        Dropping the DAC ref alone is not enough on ESP32 — the peripheral can
        keep driving the amp. Rebind as GPIO OUT=0 after writing digital 0.
        """
        if spk_pwm[0] is not None:
            try:
                spk_pwm[0].duty_u16(0)
            except Exception:
                pass
            try:
                spk_pwm[0].deinit()
            except Exception:
                pass
            spk_pwm[0] = None
        if spk_dac[0] is not None:
            try:
                spk_dac[0].write(0)
            except Exception:
                pass
            spk_dac[0] = None
        try:
            # Re-mux pin away from DAC/LEDC onto digital GPIO
            p = Pin(SPEAKER_PIN, Pin.OUT)
            p.value(0)
            time.sleep_ms(5)
            p.value(0)
        except Exception:
            pass
        voice_mode[0] = "off"
        _last_spk[0] = (0.0, 0)
        _last_edge[0] = (0.0, 0, "off", 0)

    def _tach_off():
        if tach_pwm[0] is not None:
            try:
                tach_pwm[0].duty_u16(0)
            except Exception:
                pass
            try:
                tach_pwm[0].deinit()
            except Exception:
                pass
            tach_pwm[0] = None
        try:
            p = Pin(TACH_PIN, Pin.OUT)
            p.value(0)
        except Exception:
            pass
        _last_tach[0] = (0.0, 0)

    def _spk_to_dac():
        _spk_off()
        try:
            spk_dac[0] = DAC(Pin(SPEAKER_PIN))
            spk_dac[0].write(128)
        except Exception:
            spk_dac[0] = None
        voice_mode[0] = "dac"
        _last_spk[0] = None

    def _spk_set(hz, duty_pct):
        key = (float(hz or 0), int(duty_pct))
        if hz is None or hz <= 0:
            if _last_spk[0] != (0.0, 0) or voice_mode[0] != "off":
                _spk_off()
            return
        if key == _last_spk[0] and voice_mode[0] == "pwm" and spk_pwm[0] is not None:
            return
        # stop any DAC/prior PWM cleanly
        if spk_dac[0] is not None or voice_mode[0] == "dac":
            _spk_off()
        ihz = int(round(float(hz)))
        if ihz < 1:
            ihz = 1
        try:
            if spk_pwm[0] is not None:
                try:
                    spk_pwm[0].deinit()
                except Exception:
                    pass
            spk_pwm[0] = PWM(Pin(SPEAKER_PIN), freq=ihz, duty_u16=0)
            time.sleep_ms(1)
            spk_pwm[0].duty_u16(_pwm_duty_u16(duty_pct))
            voice_mode[0] = "pwm"
            _last_spk[0] = key
        except Exception:
            _spk_off()

    def _tach_set(hz, duty_pct):
        key = (float(hz or 0), int(duty_pct))
        if hz is None or hz <= 0:
            if _last_tach[0] != (0.0, 0):
                _tach_off()
            return
        if key == _last_tach[0] and tach_pwm[0] is not None:
            return
        ihz = int(round(float(hz)))
        if ihz < 1:
            ihz = 1
        try:
            if tach_pwm[0] is not None:
                try:
                    tach_pwm[0].deinit()
                except Exception:
                    pass
            tach_pwm[0] = PWM(Pin(TACH_PIN), freq=ihz, duty_u16=0)
            time.sleep_ms(1)
            tach_pwm[0].duty_u16(_pwm_duty_u16(duty_pct))
            _last_tach[0] = key
        except Exception:
            _tach_off()

    _last_face_key = [None]
    _last_edge = [None]

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
            # Idle: draw once per mode only (never full-screen thrash / brownout loop)
            key = (mode, open_eyes if mode != "idle" else True)
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
                try:
                    from defaults import FACE_BAR_COLOR

                    bar = FACE_BAR_COLOR
                except Exception:
                    bar = (0, 50, 120)

            # Avoid full-frame fill when possible — only clear once per mode change
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
            # Smile: simple upward arc from filled bars (readable on camera)
            if mode == "idle":
                # Softer blue mouth than full eye fill
                mouth = (int(eye[0] * 2 // 3), int(eye[1] * 2 // 3), int(eye[2] * 2 // 3))
            else:
                mouth = eye
            # corners up, center lower = smile
            lcd.fill_rect(100, 175, 18, 10, mouth)
            lcd.fill_rect(202, 175, 18, 10, mouth)
            lcd.fill_rect(115, 185, 90, 10, mouth)
            lcd.fill_rect(125, 195, 70, 8, mouth)

        def set_backlight(self, on: bool) -> None:
            bl.value(1 if on else 0)

        def set_edge(self, hz, duty_pct, route, volume=10) -> None:
            key = (float(hz or 0), int(duty_pct), str(route), int(volume))
            if key == _last_edge[0]:
                return
            _last_edge[0] = key
            hz = float(hz or 0)
            duty = int(duty_pct)
            r = str(route)
            vol = int(volume)
            # Voice: clean square at duty_pct (default 50). Volume is mute gate only
            # on this beeper-class speaker (amplitude via duty sounds worse).
            voice_on = r in ("voice", "both") and hz > 0 and vol > 0
            tach_on = r in ("tach", "both") and hz > 0
            if voice_on:
                _spk_set(hz, duty)
            else:
                _spk_off()
            if tach_on:
                _tach_set(hz, duty)
            else:
                _tach_off()

        def park_outputs(self) -> None:
            _last_edge[0] = (0.0, 0, "park", 0)
            _spk_off()
            _tach_off()

        def reboot(self) -> None:
            self.park_outputs()
            import machine  # type: ignore

            machine.reset()

        def write_dac_samples(self, data) -> None:
            """Play u8 mono PCM. Busy-wait on ticks_us (sleep_us is too jittery)."""
            if not data:
                return
            _spk_to_dac()
            dac = spk_dac[0]
            if dac is None:
                return
            # 11,025 Hz => ~90.7 us/sample. Prefer slightly long over short (less harsh).
            hz = int(BOOT_RIFF_HZ)
            period = max(1, (1000000 + hz // 2) // hz)
            n = len(data)
            # Long ease-out to mid (u8 silence = 128). Linear then squared so the
            # last half of the fade is much quieter (less cliff into mute).
            fade_ms = int(BOOT_RIFF_FADE_MS) if BOOT_RIFF_FADE_MS else 400
            fade_n = min(n, max(1, (hz * fade_ms) // 1000))
            hold_ms = int(BOOT_RIFF_HOLD_MID_MS) if BOOT_RIFF_HOLD_MID_MS else 50
            try:
                for _ in range(16):
                    dac.write(128)
                t_next = time.ticks_us()
                for i in range(n):
                    b = data[i]
                    if isinstance(b, str):
                        v = ord(b)
                    else:
                        v = int(b) & 0xFF
                    if i >= n - fade_n:
                        # progress 0 at fade start → fade_n at end
                        step = i - (n - fade_n) + 1  # 1..fade_n
                        # remain_frac = 1 - (step/fade_n); ease with remain^2
                        remain = fade_n - step + 1  # fade_n..1
                        # scale = (remain/fade_n)^2
                        scale = (remain * remain) // fade_n  # fade_n..~0
                        v = 128 + ((v - 128) * scale) // fade_n
                    if v < 0:
                        v = 0
                    if v > 255:
                        v = 255
                    dac.write(v)
                    t_next = time.ticks_add(t_next, period)
                    while True:
                        d = time.ticks_diff(t_next, time.ticks_us())
                        if d <= 0:
                            if d < -period * 4:
                                t_next = time.ticks_us()
                            break
                # Park at mid on the DAC before unmux — avoids a rail slap
                for _ in range(max(1, (hz * hold_ms) // 1000)):
                    dac.write(128)
                    t_next = time.ticks_add(t_next, period)
                    while time.ticks_diff(t_next, time.ticks_us()) > 0:
                        pass
                time.sleep_ms(hold_ms)
            except Exception:
                pass
            _spk_off()

        def dac_idle(self) -> None:
            _spk_off()

        def read_angle_raw(self) -> int:
            if angle_adc is None:
                return 0
            try:
                # ESP32 ADC.read_u16 or read
                if hasattr(angle_adc, "read_u16"):
                    return int(angle_adc.read_u16() >> 4)  # ~12-bit-ish
                return int(angle_adc.read())
            except Exception:
                return 0

        def read_pir(self) -> int:
            if pir_pin is None:
                return 0
            try:
                return 1 if pir_pin.value() else 0
            except Exception:
                return 0

        def write_text(self, path: str, text: str) -> None:
            with open(path, "w") as f:
                f.write(text)

        def read_text(self, path: str):
            try:
                with open(path, "r") as f:
                    return f.read()
            except Exception:
                return None

        def ticks_ms(self) -> int:
            return int(time.ticks_ms())

        def sleep_ms(self, ms: int) -> None:
            time.sleep_ms(int(ms))

    return BoardHal()
