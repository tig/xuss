"""Shipped product defaults — the configuration the metal build actually runs.

Host tests that inject different gains/setpoints prove a *different* product.
At least one sim scenario must import this module and drive the control path
with these values unmodified (see silico product-path / AGENTS).
"""

# --- control loop cadence ---
TICK_SLEEP_MS = 40

# --- edge engine (spec §3) ---
RING_TEETH = 130
RPM_DEFAULT = 0
DUTY_PCT = 50
ROUTE = "voice"  # voice | tach | both
VOLUME = 6
GREET = 1
KNOB = 0
MUTE = 0
# 0 = silence until host asks (spec §5 manners: quiet after identity)
TELEMETRY_HZ = 0

# Parameter ranges (completeness contract)
RING_TEETH_MIN, RING_TEETH_MAX = 10, 400
RPM_MIN, RPM_MAX = 0, 8000
DUTY_PCT_MIN, DUTY_PCT_MAX = 5, 95
VOLUME_MIN, VOLUME_MAX = 0, 10
TELEMETRY_HZ_MIN, TELEMETRY_HZ_MAX = 0, 100

# mute survives defaults (spec §5 / §7)
DEFAULTS_EXEMPT = ("mute",)

# Dead-man: host silence releases DUT-touching outputs (spec §6)
DEADMAN_MS = 3000

# Serial rails (spec §6) — per-tick budgets
SERIAL_IN_BUDGET = 128
SERIAL_OUT_BUDGET = 256
SERIAL_LINE_MAX = 96
SERIAL_ERR_MAX = 48

# PWM floor/ceiling (Hz) for ESP32 hardware PWM comfort band
EDGE_HZ_MIN = 20
EDGE_HZ_MAX = 20000

# Built-in profiles: list of (rpm, duration_ms)
PROFILE_CRANK_CATCH_IDLE = (
    (200, 800),
    (433, 600),
    (900, 400),
    (750, 1200),
)
PROFILE_REDLINE_SWEEP = tuple((rpm, 80) for rpm in range(200, 4001, 100))
PROFILE_STALL = (
    (750, 500),
    (500, 400),
    (250, 400),
    (100, 500),
    (0, 300),
)
PROFILES = {
    "crank_catch_idle": PROFILE_CRANK_CATCH_IDLE,
    "redline_sweep": PROFILE_REDLINE_SWEEP,
    "stall": PROFILE_STALL,
}

# --- M5GO face / metal pins (docs.m5stack.com M5GO v2.7) ---
SIDE_LED_PIN = 15
SIDE_LED_COUNT = 10

LCD_SPI_ID = 2
LCD_SCK_PIN = 18
LCD_MOSI_PIN = 23
LCD_CS_PIN = 14
LCD_DC_PIN = 27
LCD_RST_PIN = 33
LCD_BL_PIN = 32
LCD_WIDTH = 320
LCD_HEIGHT = 240
LCD_BAUD = 40_000_000

# Speaker DAC/PWM pin (shared SPK path on Core)
SPEAKER_PIN = 25
# Grove Port B signal (yellow) — tach edge to DUT
TACH_PIN = 26

# Face timing (time-based, never tick-count based — spec §4)
FACE_CHASE_MS = 120
FACE_BLINK_PERIOD_MS = 2800
FACE_BLINK_MS = 140
FACE_EYE_COLOR = (0, 220, 255)
FACE_SING_COLOR = (255, 140, 0)
FACE_DRIVE_COLOR = (40, 220, 80)
FACE_BG_COLOR = (0, 0, 16)
FACE_IDLE_DIM = 18
FACE_CHASE_BRIGHT = 120
