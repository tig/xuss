"""Device HAL backend — the only plate module allowed to import ``machine``.

Listed in silico.toml ``[hal].allow_machine``. Host tests never import this
module; they inject ``sim.hal_double.FakeHal`` (or a plant) into ``main.init``.
"""

# No ``from __future__ import annotations`` — MicroPython has no __future__
# (tig/silico#46). Keep deploy-set modules MP-safe.

from defaults import LED_PIN, TACH_PIN, VOICE_PIN


def make_board_hal():
    """Construct the on-metal HAL. Imports machine only when called on device."""
    from machine import Pin, PWM  # type: ignore
    import time
    import sys

    try:
        import uselect as select
    except ImportError:
        try:
            import select
        except ImportError:
            select = None

    led = Pin(LED_PIN, Pin.OUT)
    led.value(1)  # active-low off default (may be unused on M5GO)

    tach = Pin(TACH_PIN, Pin.OUT)
    tach.value(0)

    # Square wave on voice pin via PWM when possible; park sets duty 0.
    try:
        voice_pwm = PWM(Pin(VOICE_PIN), freq=1000, duty=0)
    except Exception:
        voice_pwm = None
        voice_pin = Pin(VOICE_PIN, Pin.OUT)
        voice_pin.value(0)
    else:
        voice_pin = None

    try:
        tach_pwm = PWM(tach, freq=1000, duty=0)
    except Exception:
        tach_pwm = None

    config_path = "xuss.cfg"

    class BoardHal:
        def __init__(self):
            self._poll = None
            if select is not None:
                try:
                    self._poll = select.poll()
                    self._poll.register(sys.stdin, select.POLLIN)
                except Exception:
                    self._poll = None

        def set_led(self, on):
            # Active-low style; harmless if pin is not a real LED on M5GO.
            led.value(0 if on else 1)

        def ticks_ms(self):
            return int(time.ticks_ms())

        def sleep_ms(self, ms):
            time.sleep_ms(int(ms))

        def set_edge(self, hz, duty_pct, route):
            hz = float(hz)
            duty_pct = int(duty_pct)
            route = str(route)
            if hz <= 0:
                self.park_outputs()
                return
            # MP PWM duty is 0-1023 on ESP32 classic in many builds.
            duty = int(max(0, min(1023, (duty_pct * 1023) // 100)))
            freq = max(1, int(hz))
            if route in ("voice", "both") and voice_pwm is not None:
                try:
                    voice_pwm.freq(freq)
                    voice_pwm.duty(duty)
                except Exception:
                    pass
            if route in ("tach", "both"):
                if tach_pwm is not None:
                    try:
                        tach_pwm.freq(freq)
                        tach_pwm.duty(duty)
                    except Exception:
                        tach.value(1 if duty_pct >= 50 else 0)
                else:
                    tach.value(1 if duty_pct >= 50 else 0)

        def park_outputs(self):
            if voice_pwm is not None:
                try:
                    voice_pwm.duty(0)
                except Exception:
                    pass
            if voice_pin is not None:
                voice_pin.value(0)
            if tach_pwm is not None:
                try:
                    tach_pwm.duty(0)
                except Exception:
                    pass
            tach.value(0)

        def serial_read(self, max_bytes):
            max_bytes = int(max_bytes)
            if max_bytes <= 0:
                return ""
            if self._poll is None:
                return ""
            try:
                ev = self._poll.poll(0)
            except Exception:
                return ""
            if not ev:
                return ""
            try:
                data = sys.stdin.read(max_bytes)
            except Exception:
                return ""
            if data is None:
                return ""
            return data

        def serial_write(self, text):
            try:
                sys.stdout.write(text)
                try:
                    sys.stdout.flush()
                except Exception:
                    pass
            except Exception:
                pass

        def config_read(self):
            try:
                with open(config_path, "r") as f:
                    return f.read()
            except Exception:
                return None

        def config_write(self, text):
            try:
                with open(config_path, "w") as f:
                    f.write(text)
            except Exception:
                pass

        def hard_reset(self):
            try:
                import machine

                machine.reset()
            except Exception:
                pass

        def enter_repl(self):
            # Soft exit: park already done by App. Raising SystemExit ends main.
            raise SystemExit

        def play_boot_riff(self):
            # Sampled riff is a later metal slice (DAC + assets/). No-op for L0.
            return

    return BoardHal()
