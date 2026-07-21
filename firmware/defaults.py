"""Shipped product defaults — the configuration the metal build actually runs."""

# --- control loop cadence ---
TICK_SLEEP_MS = 40

# --- edge engine (spec §3) ---
RING_TEETH = 130
RPM_DEFAULT = 0
DUTY_PCT = 50
ROUTE = "voice"  # voice | tach | both
VOLUME = 6
# Greet stays available (set greet 1) but default off so a floating PIR pin
# cannot peep-loop the bench when no unit is attached.
GREET = 0
KNOB = 0
MUTE = 0
# Spec table default is 10; manners prefer quiet until host enables (0).
TELEMETRY_HZ = 0

RING_TEETH_MIN, RING_TEETH_MAX = 10, 400
RPM_MIN, RPM_MAX = 0, 8000
DUTY_PCT_MIN, DUTY_PCT_MAX = 5, 95
VOLUME_MIN, VOLUME_MAX = 0, 10
TELEMETRY_HZ_MIN, TELEMETRY_HZ_MAX = 0, 100

DEFAULTS_EXEMPT = ("mute",)

DEADMAN_MS = 3000

SERIAL_IN_BUDGET = 128
SERIAL_OUT_BUDGET = 256
SERIAL_LINE_MAX = 96
SERIAL_ERR_MAX = 48

EDGE_HZ_MIN = 20
EDGE_HZ_MAX = 20000

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

# --- M5GO pins (docs.m5stack.com M5GO v2.7) ---
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

SPEAKER_PIN = 25
TACH_PIN = 26  # Port B yellow
ANGLE_ADC_PIN = 36  # Port B white (ADC) — ANGLE unit
PIR_PIN = 17  # Port C yellow — PIR unit digital

# Boot riff (spec §5). Re-enabled after idle silence proven (0.3.4).
BOOT_RIFF_ENABLE = 1
BOOT_RIFF_PATH = "boot_riff.u8.raw"
BOOT_RIFF_HZ = 11025
# Host path relative to repo root for tests
BOOT_RIFF_HOST = "assets/boot-riff.u8.raw"

# ANGLE: map ADC raw-ish 0..4095 (ESP32) to rpm
KNOB_RPM_MIN = 0
KNOB_RPM_MAX = 4000
KNOB_ADC_MIN = 0
KNOB_ADC_MAX = 4095

# PIR debounce / re-arm
PIR_QUIET_MS = 3000  # no human before next approach can arm
PIR_GREET_CHIRP_MS = 120
PIR_GREET_HZ = 880
PIR_DEBOUNCE_TICKS = 5  # consecutive high samples before "human"
PIR_BOOT_GRACE_MS = 5000  # ignore PIR after boot (and while riff may run)

# Config image
CONFIG_PATH = "xuss.cfg"
CONFIG_VERSION = 1

# Face timing
FACE_CHASE_MS = 120
FACE_BLINK_PERIOD_MS = 2800
FACE_BLINK_MS = 140
FACE_EYE_COLOR = (0, 220, 255)
FACE_SING_COLOR = (255, 140, 0)
FACE_DRIVE_COLOR = (40, 220, 80)
FACE_BG_COLOR = (0, 0, 16)
FACE_IDLE_DIM = 18
FACE_CHASE_BRIGHT = 120
