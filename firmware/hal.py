"""Product HAL contract — pure shape, no hardware.

Domain logic talks to this surface only. Host sim implements the same methods
with boring values. Device backends live in ``hal_board`` (may import machine).
"""


class Hal:
    """Xuss HAL: time, face, edge sinks, escape hatch."""

    def set_led(self, on: bool) -> None:
        raise NotImplementedError

    def set_side_leds(self, colors) -> None:
        """Drive ten side SK6812s. ``colors`` is a sequence of (r, g, b) 0-255."""
        raise NotImplementedError

    def show_face(self, frame) -> None:
        """Render a face frame dict on the IPS panel."""
        raise NotImplementedError

    def set_backlight(self, on: bool) -> None:
        raise NotImplementedError

    def set_edge(self, hz, duty_pct, route) -> None:
        """Square-wave engine to voice / tach / both. hz<=0 parks that sink."""
        raise NotImplementedError

    def park_outputs(self) -> None:
        """Release all actuation to passive (dead-man / stop / repl)."""
        raise NotImplementedError

    def reboot(self) -> None:
        """Hard reset after parking."""
        raise NotImplementedError

    def ticks_ms(self) -> int:
        raise NotImplementedError

    def sleep_ms(self, ms: int) -> None:
        raise NotImplementedError
