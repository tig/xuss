"""Product HAL contract — pure shape, no hardware.

Domain logic talks to this surface only. Host sim implements the same methods
with boring values. Device backends live in ``hal_board`` (may import machine).
"""


class Hal:
    """Xuss HAL: time, status LED, edge sinks, serial, config image, power."""

    def set_led(self, on):
        """Drive status LED. on=True means illuminated (backend maps polarity)."""
        raise NotImplementedError

    def ticks_ms(self):
        """Monotonic milliseconds (wrap-safe diffs are the caller's problem)."""
        raise NotImplementedError

    def sleep_ms(self, ms):
        """Block for approximately ms milliseconds."""
        raise NotImplementedError

    def set_edge(self, hz, duty_pct, route):
        """Drive square-wave edge on route: voice | tach | both. hz=0 parks."""
        raise NotImplementedError

    def park_outputs(self):
        """Release DUT-touching and voice outputs to passive."""
        raise NotImplementedError

    def serial_read(self, max_bytes):
        """Non-blocking read up to max_bytes. Return str or bytes (may be empty)."""
        raise NotImplementedError

    def serial_write(self, text):
        """Write a line or chunk to the host link (caller adds newline if needed)."""
        raise NotImplementedError

    def config_read(self):
        """Return config image string or None."""
        return None

    def config_write(self, text):
        """Persist config image string."""
        pass

    def hard_reset(self):
        """Board reset. May not return."""
        raise NotImplementedError

    def enter_repl(self):
        """Restore interrupt char / exit product loop so mpremote can attach."""
        raise NotImplementedError
