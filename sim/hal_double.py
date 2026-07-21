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
        self.edge_history: list[tuple] = []
        self.last_edge = None
        self.park_count = 0
        self.reboot_count = 0

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

    def set_edge(self, hz, duty_pct, route, volume=10) -> None:
        rec = (float(hz or 0), int(duty_pct), str(route), int(volume))
        self.last_edge = rec
        self.edge_history.append(rec)

    def park_outputs(self) -> None:
        self.park_count += 1
        self.last_edge = (0.0, 0, "park")
        self.edge_history.append(self.last_edge)

    def reboot(self) -> None:
        self.reboot_count += 1

    def ticks_ms(self) -> int:
        return self._ticks

    def sleep_ms(self, ms: int) -> None:
        self.sleeps.append(int(ms))
        self._ticks += int(ms)
