"""Product HAL contract — pure shape, no hardware.

Domain logic talks to this surface only. Host sim implements the same methods
with boring values. Device backends live in ``hal_board`` (may import machine).
"""


class Hal:
    """Xuss HAL: time helpers, side LEDs, IPS face."""

    def set_led(self, on: bool) -> None:
        """Legacy status LED. On M5GO this maps to a center side-pair highlight."""
        raise NotImplementedError

    def set_side_leds(self, colors) -> None:
        """Drive ten side SK6812s. ``colors`` is a sequence of (r, g, b) 0-255."""
        raise NotImplementedError

    def show_face(self, frame) -> None:
        """Render a face frame dict (eyes, identity, mode) on the IPS panel."""
        raise NotImplementedError

    def set_backlight(self, on: bool) -> None:
        """LCD backlight."""
        raise NotImplementedError

    def ticks_ms(self) -> int:
        """Monotonic milliseconds (wrap-safe diffs are the caller's problem)."""
        raise NotImplementedError

    def sleep_ms(self, ms: int) -> None:
        """Block for approximately ``ms`` milliseconds."""
        raise NotImplementedError
