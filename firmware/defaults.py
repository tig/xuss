"""Shipped product defaults — the configuration the metal build actually runs.

Host tests that inject different gains/setpoints prove a *different* product.
At least one sim scenario must import this module and drive the control path
with these values unmodified (see silico product-path / AGENTS).

Parameter table is the completeness contract from spec §7.
"""

# --- control cadence ---
# Host/metal tick sleep when idle (ms). Active edge output may use a shorter path.
TICK_SLEEP_MS = 20

# Dead-man: release DUT-touching outputs if host silent this long (ms).
DEADMAN_MS = 1500

# Serial rails (spec §6.2) — budgets per tick.
SERIAL_IN_BUDGET = 128
SERIAL_OUT_BUDGET = 256
SERIAL_ERR_MAX = 48

# --- parameter table (spec §7) ---
RING_TEETH = 130
RPM = 0
DUTY_PCT = 50
ROUTE = "voice"  # voice | tach | both
VOLUME = 6
GREET = 1
KNOB = 0
MUTE = 0
TELEMETRY_HZ = 10

# Ranges for set validation (inclusive).
RING_TEETH_MIN = 10
RING_TEETH_MAX = 400
RPM_MIN = 0
RPM_MAX = 8000
DUTY_PCT_MIN = 5
DUTY_PCT_MAX = 95
VOLUME_MIN = 0
VOLUME_MAX = 10
TELEMETRY_HZ_MIN = 0
TELEMETRY_HZ_MAX = 100

ROUTES = ("voice", "tach", "both")

# Survives `defaults` (commissioning state). Cleared only by explicit set mute 0.
DEFAULTS_EXEMPT = ("mute",)

# Config image
CONFIG_VERSION = 1

# --- profiles are songs (rpm, duration_ms) ---
# crank_catch_idle: crank → catch flare → overshoot → settle idle (all RPM).
# Spec prose "200 → 433" collides with cranking *frequency* at defaults; we treat
# the profile as RPM steps (ambiguity log).
PROFILE_CRANK_CATCH_IDLE = (
    (200, 1000),
    (1100, 250),
    (900, 350),
    (750, 2000),
)

PROFILE_REDLINE_SWEEP = (
    (750, 200),
    (1500, 200),
    (2500, 200),
    (3500, 200),
    (4500, 200),
    (5500, 200),
    (6500, 300),
    (0, 200),
)

PROFILE_STALL = (
    (750, 400),
    (400, 500),
    (150, 700),
    (50, 500),
    (0, 200),
)

PROFILES = {
    "crank_catch_idle": PROFILE_CRANK_CATCH_IDLE,
    "redline_sweep": PROFILE_REDLINE_SWEEP,
    "stall": PROFILE_STALL,
}

# Face / status (domain placeholder pin until issue #5 lands M5GO map).
LED_PIN = 16

# Tach edge out (M5Stack Port B yellow/GPIO26 class — metal map may refine).
TACH_PIN = 26

# Speaker / DAC path markers for board HAL (not sampled audio; square edge).
VOICE_PIN = 25
