"""Versioned checksummed config image (spec §7). Host-importable."""

from defaults import CONFIG_VERSION, DEFAULTS_EXEMPT
from config import factory, set_param

# Simple portable checksum (not crypto): sum of bytes mod 65536
def _checksum(payload: str) -> int:
    total = 0
    for ch in payload:
        total = (total + ord(ch)) & 0xFFFF
    return total


def encode(cfg: dict) -> str:
    """Encode config to a single-line image: v|k=v,...|cs"""
    keys = sorted(k for k in cfg.keys())
    body = ",".join("%s=%s" % (k, cfg[k]) for k in keys)
    payload = "v=%s|%s" % (CONFIG_VERSION, body)
    return "%s|cs=%s" % (payload, _checksum(payload))


def decode(text: str):
    """Return (ok, cfg_or_None). Torn/bad checksum -> (False, None)."""
    if not text:
        return False, None
    text = text.strip()
    if "|cs=" not in text:
        return False, None
    payload, _, cs_part = text.rpartition("|cs=")
    try:
        cs = int(cs_part)
    except Exception:
        return False, None
    if _checksum(payload) != cs:
        return False, None
    if not payload.startswith("v="):
        return False, None
    try:
        ver_s, _, body = payload.partition("|")
        ver = int(ver_s.split("=", 1)[1])
    except Exception:
        return False, None
    cfg = factory()
    if body:
        for pair in body.split(","):
            if "=" not in pair:
                continue
            k, v = pair.split("=", 1)
            if k == "route":
                ok, _ = set_param(cfg, k, v)
            else:
                ok, _ = set_param(cfg, k, v)
            # unknown keys skipped for migration; mute applied if present
            if not ok and k in DEFAULTS_EXEMPT:
                try:
                    cfg[k] = int(v)
                except Exception:
                    pass
    # version may differ; still accept if checksum ok (migration)
    _ = ver
    return True, cfg


def save_to_hal(hal, cfg: dict) -> bool:
    """Write image via HAL if supported; else False."""
    if hal is None or not hasattr(hal, "write_text"):
        return False
    try:
        from defaults import CONFIG_PATH

        hal.write_text(CONFIG_PATH, encode(cfg))
        return True
    except Exception:
        return False


def load_from_hal(hal):
    """Return cfg dict or None."""
    if hal is None or not hasattr(hal, "read_text"):
        return None
    try:
        from defaults import CONFIG_PATH

        text = hal.read_text(CONFIG_PATH)
        ok, cfg = decode(text or "")
        if ok:
            return cfg
    except Exception:
        pass
    return None
