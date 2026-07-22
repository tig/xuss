"""Parameter store: get/set/save/defaults with validation (spec §7).

Persists as a versioned, checksummed image via HAL when available.
mute is DEFAULTS_EXEMPT (commissioning state).
"""

import defaults as D


# Ordered param keys — completeness contract.
PARAM_KEYS = (
    "ring_teeth",
    "rpm",
    "duty_pct",
    "route",
    "volume",
    "greet",
    "knob",
    "mute",
    "telemetry_hz",
)


def factory_params():
    return {
        "ring_teeth": int(D.RING_TEETH),
        "rpm": int(D.RPM),
        "duty_pct": int(D.DUTY_PCT),
        "route": str(D.ROUTE),
        "volume": int(D.VOLUME),
        "greet": int(D.GREET),
        "knob": int(D.KNOB),
        "mute": int(D.MUTE),
        "telemetry_hz": int(D.TELEMETRY_HZ),
    }


def _checksum(pairs):
    """Simple portable checksum over sorted key=value lines."""
    acc = 0
    for k in sorted(pairs.keys()):
        s = "%s=%s" % (k, pairs[k])
        for ch in s:
            acc = (acc + ord(ch) * 17) & 0xFFFFFFFF
            acc = (acc ^ (acc << 3)) & 0xFFFFFFFF
    return acc & 0xFFFF


def encode_image(params):
    """Return a single-line image string (no newlines)."""
    parts = ["v=%d" % int(D.CONFIG_VERSION)]
    for k in PARAM_KEYS:
        parts.append("%s=%s" % (k, params[k]))
    body = ";".join(parts)
    # checksum over params only (stable if version tag moves)
    cs = _checksum(params)
    return body + ";cs=%04x" % cs


def decode_image(text):
    """Parse image; return (params_dict or None, reason).

    Torn / bad checksum → full factory (caller applies).
    Intact with subset of keys → migrate; mute kept if present.
    """
    if not text or not isinstance(text, str):
        return None, "empty"
    text = text.strip()
    if not text:
        return None, "empty"
    fields = {}
    for part in text.split(";"):
        if not part or "=" not in part:
            continue
        k, v = part.split("=", 1)
        fields[k.strip()] = v.strip()
    if "cs" not in fields:
        return None, "no_cs"
    try:
        cs_got = int(fields["cs"], 16)
    except ValueError:
        return None, "bad_cs"
    # Build candidate params from known keys only.
    candidate = factory_params()
    for k in PARAM_KEYS:
        if k in fields:
            if k == "route":
                candidate[k] = fields[k]
            else:
                try:
                    candidate[k] = int(fields[k])
                except ValueError:
                    return None, "bad_int"
    cs_calc = _checksum(candidate)
    if cs_calc != cs_got:
        # Try checksum over only keys present in image (migration path).
        present = {}
        for k in PARAM_KEYS:
            if k in fields:
                present[k] = candidate[k]
        if _checksum(present) != cs_got:
            return None, "cs_mismatch"
    # Validate ranges; invalid → factory full.
    for k in PARAM_KEYS:
        ok, _ = validate(k, candidate[k])
        if not ok:
            return None, "range"
    return candidate, "ok"


def validate(key, value):
    """Return (ok: bool, normalized_or_error_str)."""
    if key not in PARAM_KEYS:
        return False, "unknown"
    if key == "route":
        s = str(value).strip().lower()
        if s not in D.ROUTES:
            return False, "range"
        return True, s
    try:
        n = int(value)
    except (TypeError, ValueError):
        return False, "type"
    if key == "ring_teeth":
        if n < D.RING_TEETH_MIN or n > D.RING_TEETH_MAX:
            return False, "range"
    elif key == "rpm":
        if n < D.RPM_MIN or n > D.RPM_MAX:
            return False, "range"
    elif key == "duty_pct":
        if n < D.DUTY_PCT_MIN or n > D.DUTY_PCT_MAX:
            return False, "range"
    elif key == "volume":
        if n < D.VOLUME_MIN or n > D.VOLUME_MAX:
            return False, "range"
    elif key in ("greet", "knob", "mute"):
        if n not in (0, 1):
            return False, "range"
    elif key == "telemetry_hz":
        if n < D.TELEMETRY_HZ_MIN or n > D.TELEMETRY_HZ_MAX:
            return False, "range"
    return True, n


class Config:
    def __init__(self, hal=None):
        self.hal = hal
        self.params = factory_params()
        self._dirty = False

    def load(self):
        """Load from HAL if present; torn image → factory (mute not preserved)."""
        if self.hal is None or not hasattr(self.hal, "config_read"):
            return "factory"
        raw = self.hal.config_read()
        if raw is None:
            self.params = factory_params()
            return "factory"
        parsed, reason = decode_image(raw)
        if parsed is None:
            self.params = factory_params()
            return "torn"
        self.params = parsed
        return reason

    def get(self, key):
        if key not in PARAM_KEYS:
            return None
        return self.params[key]

    def set(self, key, value):
        ok, norm = validate(key, value)
        if not ok:
            return False, norm
        self.params[key] = norm
        self._dirty = True
        return True, norm

    def defaults(self):
        """Restore factory for every row except DEFAULTS_EXEMPT."""
        kept = {}
        for k in D.DEFAULTS_EXEMPT:
            if k in self.params:
                kept[k] = self.params[k]
        self.params = factory_params()
        for k, v in kept.items():
            self.params[k] = v
        self._dirty = True
        return dict(self.params)

    def save(self):
        img = encode_image(self.params)
        if self.hal is not None and hasattr(self.hal, "config_write"):
            self.hal.config_write(img)
        self._dirty = False
        return img

    def all_items(self):
        return [(k, self.params[k]) for k in PARAM_KEYS]
