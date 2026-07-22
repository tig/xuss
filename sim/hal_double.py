"""Host double for the product HAL — same method names as firmware/hal.py."""


class FakeHal:
    def __init__(self):
        self.led = None
        self._ticks = 0
        self.sleeps = []
        self.edge = None  # (hz, duty_pct, route) or None when parked
        self.park_count = 0
        self.rx = []  # queue of str chunks to feed serial_read
        self.tx = []  # lines/chunks written
        self.config_blob = None
        self.reset_count = 0
        self.repl_count = 0
        self.boot_riff_count = 0

    def set_led(self, on):
        self.led = bool(on)

    def ticks_ms(self):
        return self._ticks

    def sleep_ms(self, ms):
        self.sleeps.append(int(ms))
        self._ticks += int(ms)

    def advance(self, ms):
        self._ticks += int(ms)

    def set_edge(self, hz, duty_pct, route):
        self.edge = (float(hz), int(duty_pct), str(route))

    def park_outputs(self):
        self.park_count += 1
        self.edge = None

    def serial_read(self, max_bytes):
        if not self.rx:
            return ""
        chunk = self.rx.pop(0)
        max_bytes = int(max_bytes)
        if len(chunk) > max_bytes:
            rest = chunk[max_bytes:]
            self.rx.insert(0, rest)
            return chunk[:max_bytes]
        return chunk

    def serial_write(self, text):
        self.tx.append(text)

    def push_line(self, line):
        """Host helper: queue a command line (adds newline if missing)."""
        if not line.endswith("\n"):
            line = line + "\n"
        self.rx.append(line)

    def config_read(self):
        return self.config_blob

    def config_write(self, text):
        self.config_blob = text

    def hard_reset(self):
        self.reset_count += 1

    def enter_repl(self):
        self.repl_count += 1

    def play_boot_riff(self):
        self.boot_riff_count += 1
