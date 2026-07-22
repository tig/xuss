"""Boot entry: identity, protocol loop, edge engine. Host-import safe.

Device starts the loop only when executed as ``__main__`` (MicroPython boot).
Host tests import ``init`` / ``tick`` / ``App`` and inject a fake HAL.
"""

import defaults as D
from config import Config
from edge import ProfilePlayer, rpm_to_hz
from protocol import Protocol, identity_line
from version import FW_NAME, FW_VERSION


class App:
    def __init__(self, hal=None):
        self.hal = hal
        self.config = Config(hal=hal)
        self.config.load()
        self.protocol = Protocol(self)
        self.player = ProfilePlayer()
        self.tick_count = 0
        self.led_on = False
        self.exit_repl = False
        self.exit_reboot = False
        self._last_host_ms = 0
        self._last_telem_ms = 0
        self._route_force = None  # temporary override from sing/run
        self._announced = False
        self.boot_identity_sent = False

    def now(self):
        if self.hal is not None and hasattr(self.hal, "ticks_ms"):
            return int(self.hal.ticks_ms())
        return 0

    def write_line(self, line):
        if self.hal is None or not hasattr(self.hal, "serial_write"):
            return
        if line is None:
            return
        if not line.endswith("\n"):
            line = line + "\n"
        budget = int(D.SERIAL_OUT_BUDGET)
        if len(line) > budget:
            line = line[:budget]
        self.hal.serial_write(line)

    def boot_announce(self):
        """Identity first (spec §5). Port answers while greeting may play."""
        self.write_line(identity_line())
        self.boot_identity_sent = True
        self._last_host_ms = self.now()
        # Boot riff is metal-only; HAL may no-op on host.
        if self.hal is not None and hasattr(self.hal, "play_boot_riff"):
            mute = int(self.config.get("mute") or 0)
            if mute == 0:
                self.hal.play_boot_riff()

    def on_param_set(self, key, value):
        if key == "rpm":
            self._route_force = None
            self._apply_edge()
        elif key in ("duty_pct", "route", "volume", "mute", "ring_teeth"):
            self._apply_edge()

    def on_defaults(self):
        self.player.stop()
        self._route_force = None
        self._apply_edge()

    def request_repl(self):
        self._park()
        self.exit_repl = True

    def request_reboot(self):
        self._park()
        self.exit_reboot = True

    def start_profile(self, name, route_force=None):
        if get_profile_safe(name) is None:
            return "err=unknown_profile name=%s" % name
        # Actuation that can touch DUT must announce first (spec §5).
        route = route_force or self.config.get("route")
        if route in ("tach", "both"):
            self.write_line("actuate kind=profile name=%s route=%s" % (name, route))
        now = self.now()
        if not self.player.start(name, now):
            return "err=unknown_profile name=%s" % name
        self._route_force = route_force
        self._last_host_ms = now
        rpm = self.player.current_rpm()
        if rpm is not None:
            self.config.params["rpm"] = int(rpm)
        self._apply_edge()
        return "ok %s profile=%s route=%s" % (
            "sing" if route_force == "voice" else "run",
            name,
            route_force or self.config.get("route"),
        )

    def stop_profile(self):
        self.player.stop()
        self._route_force = None

    def stop_all(self):
        self.stop_profile()
        self.config.params["rpm"] = 0
        self._park()

    def _park(self):
        if self.hal is not None and hasattr(self.hal, "park_outputs"):
            self.hal.park_outputs()
        self.config.params["rpm"] = 0

    def _active_route(self):
        if self._route_force:
            return self._route_force
        return self.config.get("route")

    def _apply_edge(self):
        if self.hal is None or not hasattr(self.hal, "set_edge"):
            return
        mute = int(self.config.get("mute") or 0)
        rpm = int(self.config.get("rpm") or 0)
        if mute:
            self.hal.park_outputs()
            return
        teeth = int(self.config.get("ring_teeth") or D.RING_TEETH)
        hz = rpm_to_hz(rpm, teeth)
        duty = int(self.config.get("duty_pct") or D.DUTY_PCT)
        route = self._active_route()
        # volume gates voice amplitude on metal; host double records it via set_edge
        if hz <= 0:
            self.hal.park_outputs()
            return
        if route in ("tach", "both"):
            if not self._announced:
                self.write_line(
                    "actuate kind=edge rpm=%d hz=%.3f route=%s" % (rpm, hz, route)
                )
                self._announced = True
        else:
            self._announced = False
        self.hal.set_edge(hz, duty, route)

    def _deadman(self, now):
        """Release DUT-touching outputs when host silent beyond window."""
        window = int(D.DEADMAN_MS)
        if now - self._last_host_ms <= window:
            return
        route = self._active_route()
        rpm = int(self.config.get("rpm") or 0)
        if self.player.active or (rpm > 0 and route in ("tach", "both")):
            # Park tach path; voice-only may continue for stage, but dead-man
            # covers everything that touches the DUT (spec §6.1).
            if self.player.active:
                self.player.stop()
            if route in ("tach", "both"):
                self.config.params["rpm"] = 0
                if self.hal is not None and hasattr(self.hal, "park_outputs"):
                    self.hal.park_outputs()
                self._route_force = None
                self._announced = False

    def _telemetry(self, now):
        hz = int(self.config.get("telemetry_hz") or 0)
        if hz <= 0:
            return
        period = max(1, int(1000 / hz))
        if now - self._last_telem_ms < period:
            return
        self._last_telem_ms = now
        rpm = int(self.config.get("rpm") or 0)
        teeth = int(self.config.get("ring_teeth") or D.RING_TEETH)
        f = rpm_to_hz(rpm, teeth)
        self.write_line(
            "telem rpm=%d hz=%.3f route=%s duty=%s mute=%s"
            % (
                rpm,
                f,
                self._active_route(),
                self.config.get("duty_pct"),
                self.config.get("mute"),
            )
        )

    def tick(self):
        """One cooperative tick: serial → profile → edge → dead-man → telem."""
        self.tick_count += 1
        now = self.now()

        # Serial intake (bounded)
        if self.hal is not None and hasattr(self.hal, "serial_read"):
            chunk = self.hal.serial_read(int(D.SERIAL_IN_BUDGET))
            if chunk:
                self._last_host_ms = now
                for resp in self.protocol.feed(chunk, int(D.SERIAL_OUT_BUDGET)):
                    self.write_line(resp)
                if self.exit_repl or self.exit_reboot:
                    return self._finish_exit()

        # Profile time base
        if self.player.active:
            rpm = self.player.tick(now)
            if rpm is None and self.player.done:
                self.config.params["rpm"] = 0
                self._route_force = None
                self._apply_edge()
            elif rpm is not None:
                self.config.params["rpm"] = int(rpm)
                self._apply_edge()

        self._deadman(now)
        self._telemetry(now)

        # Face placeholder: blink when rpm > 0
        self.led_on = int(self.config.get("rpm") or 0) > 0
        if self.hal is not None and hasattr(self.hal, "set_led"):
            self.hal.set_led(self.led_on)

        return "run"

    def _finish_exit(self):
        self._park()
        if self.exit_reboot:
            if self.hal is not None and hasattr(self.hal, "hard_reset"):
                self.hal.hard_reset()
            return "reboot"
        if self.exit_repl:
            if self.hal is not None and hasattr(self.hal, "enter_repl"):
                self.hal.enter_repl()
            return "repl"
        return "run"


def get_profile_safe(name):
    from edge import get_profile

    return get_profile(name)


def init(hal=None):
    """Plate-compatible init: returns a state dict wrapping App."""
    app = App(hal=hal)
    return {
        "hal": hal,
        "app": app,
        "fw_name": FW_NAME,
        "fw_version": FW_VERSION,
        "tick_count": 0,
        "led_on": False,
        "tick_sleep_ms": int(D.TICK_SLEEP_MS),
    }


def tick(state):
    """Plate-compatible tick."""
    app = state.get("app")
    if app is None:
        return state
    app.tick()
    state["tick_count"] = app.tick_count
    state["led_on"] = app.led_on
    state["fw_name"] = FW_NAME
    state["fw_version"] = FW_VERSION
    state["tick_sleep_ms"] = int(D.TICK_SLEEP_MS)
    return state


def main():
    from hal_board import make_board_hal

    hal = make_board_hal()
    app = App(hal=hal)
    app.boot_announce()
    while True:
        status = app.tick()
        if status in ("repl", "reboot"):
            break
        sleep_ms = int(D.TICK_SLEEP_MS)
        if hasattr(hal, "sleep_ms"):
            hal.sleep_ms(sleep_ms)
        else:
            try:
                import time

                time.sleep(sleep_ms / 1000.0)
            except ImportError:
                pass


if __name__ == "__main__":
    main()
