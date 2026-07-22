"""Product HAL contract — pure shape, no hardware."""


class Hal:
    def set_led(self, on: bool) -> None:
        raise NotImplementedError

    def set_side_leds(self, colors) -> None:
        raise NotImplementedError

    def show_face(self, frame) -> None:
        raise NotImplementedError

    def show_banner(self, frame) -> None:
        """Optional: hair-bar marquee only (default: fall back via show_face)."""
        self.show_face(frame)

    def set_backlight(self, on: bool) -> None:
        raise NotImplementedError

    def set_edge(self, hz, duty_pct, route, volume=10) -> None:
        raise NotImplementedError

    def park_outputs(self) -> None:
        raise NotImplementedError

    def reboot(self) -> None:
        raise NotImplementedError

    def ticks_ms(self) -> int:
        raise NotImplementedError

    def sleep_ms(self, ms: int) -> None:
        raise NotImplementedError

    def write_dac_samples(self, data: bytes) -> None:
        """Play u8 PCM samples on speaker DAC (blocking chunk)."""
        raise NotImplementedError

    def dac_idle(self) -> None:
        """Return DAC to mid/idle after sample playback."""
        raise NotImplementedError

    def read_angle_raw(self) -> int:
        """ADC raw for ANGLE unit (0..4095 class)."""
        raise NotImplementedError

    def read_pir(self) -> int:
        """1 if human present, else 0."""
        raise NotImplementedError

    def read_button_a(self) -> int:
        """1 if left front button (Button A) is pressed, else 0."""
        return 0

    def read_button_b(self) -> int:
        """1 if middle front button (Button B) is pressed, else 0."""
        return 0

    def play_pcm_file(self, path, stop_reader=None, sample_hz=None, chunk=None) -> str:
        """Stream u8 mono PCM from path. Return done|stopped|missing|error."""
        return "missing"

    def write_text(self, path: str, text: str) -> None:
        raise NotImplementedError

    def read_text(self, path: str):
        """Return str or None."""
        raise NotImplementedError
