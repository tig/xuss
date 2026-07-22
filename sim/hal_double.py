"""Host double for the Xuss HAL."""


class FakeHal:
    def __init__(self):
        self.led = None
        self.backlight = None
        self._ticks = 0
        self.sleeps = []
        self.side_history = []
        self.face_history = []
        self.banner_history = []
        self.last_side = None
        self.last_face = None
        self.last_banner = None
        self.edge_history = []
        self.last_edge = None
        self.park_count = 0
        self.reboot_count = 0
        self.dac_chunks = []
        self.dac_idle_count = 0
        self.angle_raw = 0
        self.pir = 0
        self.button_a = 0
        self.button_b = 0
        self.pcm_plays = []
        self.files = {}
        self.binary_files = {}

    def set_led(self, on: bool) -> None:
        self.led = bool(on)

    def set_side_leds(self, colors) -> None:
        frame = [tuple(c) for c in colors]
        self.last_side = frame
        self.side_history.append(frame)

    def show_face(self, frame) -> None:
        self.last_face = dict(frame)
        self.face_history.append(dict(frame))

    def show_banner(self, frame) -> None:
        self.last_banner = dict(frame)
        self.banner_history.append(dict(frame))

    def set_backlight(self, on: bool) -> None:
        self.backlight = bool(on)

    def set_edge(self, hz, duty_pct, route, volume=10) -> None:
        rec = (float(hz or 0), int(duty_pct), str(route), int(volume))
        self.last_edge = rec
        self.edge_history.append(rec)

    def park_outputs(self) -> None:
        self.park_count += 1
        self.last_edge = (0.0, 0, "park", 0)
        self.edge_history.append(self.last_edge)

    def reboot(self) -> None:
        self.reboot_count += 1

    def write_dac_samples(self, data) -> None:
        self.dac_chunks.append(bytes(data))

    def dac_idle(self) -> None:
        self.dac_idle_count += 1

    def read_angle_raw(self) -> int:
        return int(self.angle_raw)

    def read_pir(self) -> int:
        return 1 if self.pir else 0

    def read_button_a(self) -> int:
        return 1 if self.button_a else 0

    def read_button_b(self) -> int:
        return 1 if self.button_b else 0

    def write_dac_samples(self, data, fade_out=True, sample_hz=None) -> None:
        self.dac_chunks.append(bytes(data) if not isinstance(data, bytes) else data)

    def play_pcm_file(
        self, path, stop_reader=None, sample_hz=None, chunk=None, start_offset=0
    ):
        """Host double: (outcome, offset). pcm_pause_after = bytes to play then pause."""
        self.pcm_plays.append((path, int(start_offset or 0)))
        data = self.binary_files.get(path)
        if data is None:
            return ("missing", 0)
        start = int(start_offset or 0)
        if start < 0:
            start = 0
        if start >= len(data):
            return ("done", 0)
        if stop_reader is not None:
            self.button_b = 0  # release start press
        pause_after = getattr(self, "pcm_pause_after", None)
        if pause_after is not None:
            played = int(pause_after)
            if played < 0:
                played = 0
            end = start + played
            if end >= len(data):
                chunk = data[start:]
                self.write_dac_samples(chunk, fade_out=False, sample_hz=sample_hz)
                self.dac_idle()
                return ("done", 0)
            self.write_dac_samples(data[start:end], fade_out=False, sample_hz=sample_hz)
            self.dac_idle()
            return ("paused", end)
        if stop_reader is not None and stop_reader():
            return ("paused", start)
        self.write_dac_samples(data[start:], fade_out=False, sample_hz=sample_hz)
        self.dac_idle()
        return ("done", 0)

    def show_now_playing(self, title="First by Tig") -> None:
        self.last_now_playing = title
        if not hasattr(self, "now_playing_history"):
            self.now_playing_history = []
        self.now_playing_history.append(title)

    def write_text(self, path: str, text: str) -> None:
        self.files[path] = text

    def read_text(self, path: str):
        return self.files.get(path)

    def ticks_ms(self) -> int:
        return self._ticks

    def sleep_ms(self, ms: int) -> None:
        self.sleeps.append(int(ms))
        self._ticks += int(ms)
