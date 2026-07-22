"""Edge engine math and profile (song) playback — host-importable, no machine.

Frequency: f_hz = rpm * ring_teeth / 60  (spec §3).
"""

from defaults import PROFILES, RING_TEETH


def rpm_to_hz(rpm, ring_teeth=None):
    """Return edge frequency in Hz. rpm 0 is silence (0 Hz)."""
    if ring_teeth is None:
        ring_teeth = RING_TEETH
    rpm = int(rpm)
    if rpm <= 0:
        return 0.0
    return (float(rpm) * float(ring_teeth)) / 60.0


def profile_names():
    return tuple(sorted(PROFILES.keys()))


def get_profile(name):
    """Return tuple of (rpm, ms) or None if unknown."""
    return PROFILES.get(name)


class ProfilePlayer:
    """Time-based profile runner. Advance with ticks_ms from HAL."""

    def __init__(self):
        self.name = None
        self.steps = None
        self.index = 0
        self.step_ends_ms = 0
        self.active = False
        self.done = False

    def start(self, name, now_ms):
        steps = get_profile(name)
        if steps is None:
            return False
        self.name = name
        self.steps = steps
        self.index = 0
        self.active = True
        self.done = False
        dur = int(steps[0][1]) if steps else 0
        self.step_ends_ms = int(now_ms) + dur
        return True

    def stop(self):
        self.active = False
        self.done = True
        self.name = None
        self.steps = None
        self.index = 0

    def current_rpm(self):
        if not self.active or not self.steps:
            return None
        return int(self.steps[self.index][0])

    def tick(self, now_ms):
        """Advance steps by wall time. Returns current rpm or None if inactive/done."""
        if not self.active or not self.steps:
            return None
        now_ms = int(now_ms)
        while self.active and now_ms >= self.step_ends_ms:
            self.index += 1
            if self.index >= len(self.steps):
                self.active = False
                self.done = True
                return None
            dur = int(self.steps[self.index][1])
            self.step_ends_ms = now_ms + dur
        if not self.active:
            return None
        return int(self.steps[self.index][0])
