"""Edge engine math and song profiles — host-importable, no hardware."""


def rpm_to_hz(rpm, ring_teeth):
    """f_hz = rpm * ring_teeth / 60 (spec §3)."""
    return (float(rpm) * float(ring_teeth)) / 60.0


def profile_steps(name, profiles):
    """Return the timed (rpm, ms) list for a built-in profile name."""
    if name not in profiles:
        raise KeyError(name)
    return profiles[name]


def profile_total_ms(steps):
    total = 0
    for _rpm, ms in steps:
        total += int(ms)
    return total


def profile_rpm_at(steps, t_ms):
    """Sample profile rpm at time t_ms from start; past end returns last rpm."""
    if not steps:
        return 0
    if t_ms < 0:
        return int(steps[0][0])
    elapsed = 0
    last = int(steps[0][0])
    for rpm, ms in steps:
        last = int(rpm)
        if t_ms < elapsed + int(ms):
            return last
        elapsed += int(ms)
    return last
