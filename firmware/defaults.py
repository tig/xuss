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
# Front buttons (active-low, external pull-ups). Left = Button A.
BUTTON_A_PIN = 39
BUTTON_B_PIN = 38
BUTTON_C_PIN = 37
BTN_DEBOUNCE_MS = 250

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
# Software ease-out on top of the asset's own fade (ms of tail → mid 128)
BOOT_RIFF_FADE_MS = 400
BOOT_RIFF_HOLD_MID_MS = 50
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

# Face timing / palette (blue family — operator product face, not orange/green)
FACE_CHASE_MS = 120
FACE_BLINK_PERIOD_MS = 2800
FACE_BLINK_MS = 140
# Idle wink: one eye closes briefly every 10s (time-based, not tick-based).
FACE_WINK_PERIOD_MS = 10000
FACE_WINK_MS = 220
FACE_WINK_EYE = "right"  # which eye closes during idle wink
FACE_EYE_COLOR = (40, 140, 255)  # idle eyes / smile
FACE_SING_COLOR = (90, 190, 255)  # singing — bright blue (was orange)
FACE_DRIVE_COLOR = (20, 90, 230)  # driving DUT — deep blue (was green)
FACE_BG_COLOR = (0, 0, 20)
FACE_BAR_COLOR = (0, 50, 120)  # top status bar / hair when idle
# Idle side strip: static dim (paint once). Higher dim keeps pure primaries true.
# Chase is reserved for singing/driving to limit SK6812 bit-bang amp coupling.
FACE_IDLE_DIM = 90
FACE_CHASE_BRIGHT = 200
FACE_IDLE_SIDE_ON = 1  # 0 = all-off idle strip (legacy silence-first)
# Hair-bar marquee (time-based scroll, right → left).
FACE_BANNER_TEXT = "Xuss; built with Silico"
FACE_BANNER_SPEED_PX_S = 48  # smooth ~1–2 px per control tick
FACE_BANNER_GAP_PX = 64  # quiet gap before the text re-enters
FACE_BANNER_SCALE = 2  # 5x7 font → 10x14 in the 28px bar
FACE_BANNER_BAR_H = 28
FACE_BANNER_FG = (200, 230, 255)  # light blue on dark hair
# Left-button color cycle (Button A). Side LEDs match; black = side off.
# Use pure primaries for eye/side — muddy mixes (e.g. red 255,48,48) read as
# pink on SK6812 and yellow/teal washes on the IPS.
# side (0,0,0) ⇒ fully off. Black theme: dark face, no banner, sides off.
FACE_THEMES = (
    {
        "name": "blue",
        "eye": (0, 120, 255),
        "bar": (0, 40, 140),
        "bg": (0, 0, 24),
        "banner_fg": (180, 220, 255),
        "side": (0, 100, 255),
    },
    {
        "name": "orange",
        "eye": (255, 100, 0),
        "bar": (160, 50, 0),
        "bg": (24, 8, 0),
        "banner_fg": (255, 200, 120),
        "side": (255, 90, 0),
    },
    {
        "name": "red",
        "eye": (255, 0, 0),
        "bar": (140, 0, 0),
        "bg": (24, 0, 0),
        "banner_fg": (255, 120, 120),
        "side": (255, 0, 0),
    },
    {
        "name": "green",
        "eye": (0, 255, 0),
        "bar": (0, 120, 0),
        "bg": (0, 20, 0),
        "banner_fg": (120, 255, 120),
        "side": (0, 255, 0),
    },
    {
        "name": "black",
        # Pure black face (no charcoal wash); sides off; banner invisible.
        "eye": (0, 0, 0),
        "bar": (0, 0, 0),
        "bg": (0, 0, 0),
        "banner_fg": (0, 0, 0),
        "side": (0, 0, 0),  # off
    },
)
FACE_THEME_DEFAULT = 0  # blue
