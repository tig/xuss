"""Boot riff playback state — time-based sample streaming. Host-importable."""

from defaults import BOOT_RIFF_HZ, BOOT_RIFF_PATH, TICK_SLEEP_MS


def load_riff_bytes(loader=None):
    """loader(path) -> bytes | None. Default tries host path then device name."""
    if loader is not None:
        return loader()
    # Host: prefer assets path
    try:
        from defaults import BOOT_RIFF_HOST
        from pathlib import Path

        p = Path(__file__).resolve().parents[1] / BOOT_RIFF_HOST
        if p.is_file():
            return p.read_bytes()
    except Exception:
        pass
    return None


def make_riff(data, now_ms=0):
    if not data:
        return {"active": False, "data": b"", "i": 0, "hz": BOOT_RIFF_HZ, "t0": now_ms}
    return {
        "active": True,
        "data": data,
        "i": 0,
        "hz": BOOT_RIFF_HZ,
        "t0": int(now_ms),
        "len": len(data),
    }


def riff_done(riff):
    return not riff or not riff.get("active")


def riff_samples_for_tick(riff, tick_ms=None):
    """How many samples to emit this tick (approximate real-time)."""
    if tick_ms is None:
        tick_ms = TICK_SLEEP_MS
    if not riff or not riff.get("active"):
        return 0
    hz = int(riff.get("hz") or BOOT_RIFF_HZ)
    return max(1, int(hz * int(tick_ms) / 1000))


def riff_advance(riff, n, hal=None):
    """Push up to n samples to HAL.write_dac; return True if still active."""
    if not riff or not riff.get("active"):
        return False
    data = riff.get("data") or b""
    i = int(riff.get("i") or 0)
    end = min(len(data), i + int(n))
    if hal is not None and hasattr(hal, "write_dac_samples"):
        hal.write_dac_samples(data[i:end])
    elif hal is not None and hasattr(hal, "write_dac"):
        for b in data[i:end]:
            hal.write_dac(b)
    riff["i"] = end
    if end >= len(data):
        riff["active"] = False
        if hal is not None and hasattr(hal, "dac_idle"):
            hal.dac_idle()
        return False
    return True
