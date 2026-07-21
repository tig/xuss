"""Host double for the Xuss HAL — same method names as firmware/hal.py."""


class FakeHal:
    def __init__(self):
        self.led = None
        self.backlight = None
        self._ticks = 0
        self.sleeps: list[int] = []
        self.side_history: list[list] = []
        self.face_history: list[dict] = []
        self.last_side = None
        self.last_face = None

    def set_led(self, on: bool) -> None:
        self.led = bool(on)

    def set_side_leds(self, colors) -> None:
        frame = [tuple(c) for c in colors]
        self.last_side = frame
        self.side_history.append(frame)

    def show_face(self, frame) -> None:
        self.last_face = dict(frame)
        self.face_history.append(dict(frame))

    def set_backlight(self, on: bool) -> None:
        self.backlight = bool(on)

    def ticks_ms(self) -> int:
        return self._ticks

    def sleep_ms(self, ms: int) -> None:
        self.sleeps.append(int(ms))
        self._ticks += int(ms)
