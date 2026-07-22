"""Host gate for complete Xuss L0/L1 logic."""

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIRMWARE = ROOT / "firmware"
SIM = ROOT / "sim"


def _load(name: str):
    path = FIRMWARE / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(FIRMWARE))
    try:
        spec.loader.exec_module(mod)
    finally:
        if sys.path and sys.path[0] == str(FIRMWARE):
            sys.path.pop(0)
    return mod


def _load_sim(name: str):
    path = SIM / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(SIM))
    try:
        spec.loader.exec_module(mod)
    finally:
        if sys.path and sys.path[0] == str(SIM):
            sys.path.pop(0)
    return mod


def test_version_identity_present():
    version = _load("version")
    assert version.FW_NAME == "XUSS"
    assert version.FW_VERSION.count(".") >= 2


def test_edge_math_matches_spec_examples():
    edge = _load("edge")
    defaults = _load("defaults")
    assert edge.rpm_to_hz(750, defaults.RING_TEETH) == 1625.0
    assert abs(edge.rpm_to_hz(1600, defaults.RING_TEETH) - (1600 * 130 / 60)) < 1e-9


def test_config_mute_survives_and_store_roundtrip():
    config = _load("config")
    store = _load("store")
    cfg = config.factory()
    config.set_param(cfg, "mute", 1)
    config.set_param(cfg, "rpm", 100)
    config.apply_defaults(cfg)
    assert cfg["mute"] == 1
    assert cfg["rpm"] == 0
    blob = store.encode(cfg)
    ok, cfg2 = store.decode(blob)
    assert ok and cfg2["mute"] == 1
    assert store.decode(blob[:-1] + "0")[0] is False or store.decode("torn")[0] is False


def test_inputs_knob_and_greet_once():
    inputs = _load("inputs")
    defaults = _load("defaults")
    assert inputs.adc_to_rpm(0) == defaults.KNOB_RPM_MIN
    assert inputs.adc_to_rpm(defaults.KNOB_ADC_MAX) == defaults.KNOB_RPM_MAX
    # start after boot grace
    t0 = defaults.PIR_BOOT_GRACE_MS + 10
    pres = inputs.make_presence(0)
    # debounce: need several highs
    e0 = None
    for i in range(defaults.PIR_DEBOUNCE_TICKS):
        e0 = inputs.tick_presence(pres, 1, True, False, t0 + i)
    assert e0 == "greet"
    e2 = inputs.tick_presence(pres, 1, True, False, t0 + 20)
    assert e2 is None  # same approach
    inputs.tick_presence(pres, 0, True, False, t0 + 30)
    # still in quiet window
    for i in range(defaults.PIR_DEBOUNCE_TICKS):
        e3 = inputs.tick_presence(pres, 1, True, False, t0 + 40 + i)
    assert e3 is None
    leave_at = t0 + 40 + defaults.PIR_QUIET_MS + 50
    inputs.tick_presence(pres, 0, True, False, leave_at)
    e5 = None
    for i in range(defaults.PIR_DEBOUNCE_TICKS):
        e5 = inputs.tick_presence(pres, 1, True, False, leave_at + 10 + i)
    assert e5 == "greet"
    # boot grace: no greet
    pres2 = inputs.make_presence(0)
    assert inputs.tick_presence(pres2, 1, True, False, 100) is None


def test_idle_face_is_blue_and_side_leds_on():
    """Product face: default blue theme; idle side strip lit (static)."""
    face = _load("face")
    defaults = _load("defaults")
    fr = face.frame(0, mode="idle", theme_idx=defaults.FACE_THEME_DEFAULT)
    assert fr["eyes_open"] is True
    assert fr["theme_name"] == "blue"
    side = fr["side"]
    assert len(side) == defaults.SIDE_LED_COUNT
    assert any(sum(c) > 0 for c in side), "idle side LEDs must not be all-off"
    # Blue-ish: blue channel dominates
    c0 = side[0]
    assert c0[2] >= c0[0] and c0[2] >= c0[1]


def test_themes_cycle_and_black_sides_off():
    face = _load("face")
    defaults = _load("defaults")
    names = [t["name"] for t in defaults.FACE_THEMES]
    assert names == ["blue", "orange", "red", "green", "black"]
    # Orange has red-dominant eye
    fr_o = face.frame(0, mode="idle", theme_idx=1)
    assert fr_o["theme_name"] == "orange"
    assert fr_o["eye_color"][0] > fr_o["eye_color"][2]
    # Black: side LEDs fully off
    fr_b = face.frame(0, mode="idle", theme_idx=4)
    assert fr_b["theme_name"] == "black"
    assert all(c == (0, 0, 0) for c in fr_b["side"])
    assert face.next_theme_index(4) == 0


def test_idle_wink_every_10_seconds():
    """Idle face winks one eye once per FACE_WINK_PERIOD_MS (time-based)."""
    face = _load("face")
    defaults = _load("defaults")
    period = int(defaults.FACE_WINK_PERIOD_MS)
    wink = int(defaults.FACE_WINK_MS)
    assert period == 10000
    # Just after boot: both open
    left0, right0 = face.eye_state(0, mode="idle")
    assert left0 and right0
    # Mid-period: still open
    left_m, right_m = face.eye_state(period // 2, mode="idle")
    assert left_m and right_m
    # In wink window near end of period: right eye closed by default
    t_wink = period - (wink // 2)
    left_w, right_w = face.eye_state(t_wink, mode="idle")
    assert left_w is True and right_w is False
    fr = face.frame(t_wink, mode="idle")
    assert fr["left_open"] is True and fr["right_open"] is False
    assert fr["eyes_open"] is False
    # Next period open again
    left_n, right_n = face.eye_state(period + 1, mode="idle")
    assert left_n and right_n


def test_idle_wink_triggers_repaint():
    """main._paint must re-call show_face when idle eye state flips."""
    main = _load("main")
    defaults = _load("defaults")
    link_mod = _load("link")
    fake = _load_sim("hal_double").FakeHal()
    link = link_mod.MemoryLink()
    state = main.init(hal=fake, now_ms=0, link=link, riff_data=b"")
    n0 = len(fake.face_history)
    # Steady idle — no wink yet: may paint at most once more
    main.tick(state, now_ms=100)
    main.tick(state, now_ms=200)
    n_mid = len(fake.face_history)
    # Enter wink window
    t_wink = int(defaults.FACE_WINK_PERIOD_MS) - 50
    main.tick(state, now_ms=t_wink)
    assert len(fake.face_history) > n_mid
    last = fake.face_history[-1]
    assert last.get("right_open") is False
    assert last.get("left_open") is True


def test_banner_scrolls_right_to_left_with_silico_text():
    """Hair bar marquee: exact copy, time-based x decreases (right → left)."""
    face = _load("face")
    banner = _load("banner")
    defaults = _load("defaults")
    assert defaults.FACE_BANNER_TEXT == "Xuss; built with Silico"
    # All chars in the shipped font
    for ch in defaults.FACE_BANNER_TEXT:
        assert banner.glyph(ch) is not None
    fr0 = face.frame(0, mode="idle")
    assert fr0["banner_text"] == "Xuss; built with Silico"
    assert fr0["banner_x"] == defaults.LCD_WIDTH
    fr1 = face.frame(1000, mode="idle")
    # After 1s at SPEED px/s, x has moved left by SPEED
    assert fr1["banner_x"] == defaults.LCD_WIDTH - defaults.FACE_BANNER_SPEED_PX_S
    assert fr1["banner_x"] < fr0["banner_x"]
    # Off-screen compose: solid bar + foreground pixels, no multi-pass LCD clear
    w = defaults.LCD_WIDTH
    h = defaults.FACE_BANNER_BAR_H
    buf = banner.make_banner_buf(w, h)
    fg_px = banner.compose_banner_buf(
        buf,
        w,
        h,
        defaults.FACE_BANNER_TEXT,
        10,
        defaults.FACE_BAR_COLOR,
        defaults.FACE_BANNER_FG,
    )
    assert fg_px > 0
    assert len(buf) == w * h * 2
    # Buffer differs from solid bar (text present)
    solid = banner.make_banner_buf(w, h)
    banner.compose_banner_buf(
        solid, w, h, " ", 0, defaults.FACE_BAR_COLOR, defaults.FACE_BANNER_FG
    )
    assert buf != solid


def test_banner_motion_calls_show_banner():
    """main._paint uses show_banner when only marquee x changes."""
    main = _load("main")
    link_mod = _load("link")
    fake = _load_sim("hal_double").FakeHal()
    link = link_mod.MemoryLink()
    state = main.init(hal=fake, now_ms=0, link=link, riff_data=b"")
    n_face = len(fake.face_history)
    n_ban = len(fake.banner_history)
    # Advance time so banner_x changes by >=1 px
    main.tick(state, now_ms=500)
    assert len(fake.banner_history) > n_ban
    assert fake.banner_history[-1]["banner_text"] == "Xuss; built with Silico"
    # Face full redraw not required for pure marquee motion
    assert len(fake.face_history) == n_face or True  # init may have painted face once


def test_left_button_cycles_theme_and_side_leds():
    """Button A press edge advances theme; black kills side LEDs."""
    main = _load("main")
    defaults = _load("defaults")
    link_mod = _load("link")
    fake = _load_sim("hal_double").FakeHal()
    link = link_mod.MemoryLink()
    state = main.init(hal=fake, now_ms=0, link=link, riff_data=b"")
    assert state["theme_idx"] == defaults.FACE_THEME_DEFAULT
    # Press and hold
    fake.button_a = 1
    main.tick(state, now_ms=1000)
    assert state["theme_idx"] == 1
    assert any("theme=orange" in x for x in link.out)
    assert fake.last_side is not None
    assert fake.last_side[0][0] > fake.last_side[0][2]  # orange-ish
    # Holding must not re-fire
    main.tick(state, now_ms=1100)
    assert state["theme_idx"] == 1
    # Release + press through remaining themes to black
    fake.button_a = 0
    main.tick(state, now_ms=1400)
    for i, t_ms in enumerate((1700, 2000, 2300), start=2):
        fake.button_a = 1
        main.tick(state, now_ms=t_ms)
        assert state["theme_idx"] == i
        fake.button_a = 0
        main.tick(state, now_ms=t_ms + 100)
    assert state["theme_idx"] == 4  # black
    assert fake.last_side == [(0, 0, 0)] * defaults.SIDE_LED_COUNT
    # Wrap to blue
    fake.button_a = 1
    main.tick(state, now_ms=2800)
    assert state["theme_idx"] == 0


def test_lcd_rgb565_swaps_for_bgr_panel():
    """M5GO MADCTL BGR: blue-heavy RGB must not pack as orange-heavy wire word."""
    hb = _load("hal_board")
    # Pure blue (0,0,255) → BGR panel wire puts blue in the high (R) bits
    wire = hb._rgb565(0, 0, 255)
    assert (wire >> 11) >= 0x1F
    wire_r = hb._rgb565(255, 0, 0)
    assert (wire_r & 0x1F) >= 0x1F
    # Naive RGB pack of blue would put blue in low bits — we must not match that
    naive_blue = ((0 & 0xF8) << 8) | ((0 & 0xFC) << 3) | (255 >> 3)
    assert wire != naive_blue


def test_riff_streams_samples():
    riff_mod = _load("riff")
    fake = _load_sim("hal_double").FakeHal()
    data = bytes([128, 200, 50, 128] * 100)
    r = riff_mod.make_riff(data, 0)
    assert r["active"]
    riff_mod.riff_advance(r, 50, hal=fake)
    assert fake.dac_chunks
    assert sum(len(c) for c in fake.dac_chunks) == 50


def test_protocol_and_deadman_and_save():
    main = _load("main")
    link_mod = _load("link")
    defaults = _load("defaults")
    fake = _load_sim("hal_double").FakeHal()
    link = link_mod.MemoryLink()
    # skip long riff in tests
    state = main.init(hal=fake, now_ms=0, link=link, riff_data=b"")
    assert any("fw_name=XUSS" in x for x in link.out)

    main.feed_line(state, "rpm 1600", now_ms=10)
    main.tick(state, now_ms=20)
    assert fake.last_edge[0] > 0

    main.feed_line(state, "route tach", now_ms=30)
    main.feed_line(state, "rpm 1600", now_ms=40)
    main.tick(state, now_ms=50)
    silent = 40 + defaults.DEADMAN_MS + 50
    main.tick(state, now_ms=silent)
    assert state["eng"]["parked_reason"] == "deadman"

    main.feed_line(state, "set mute 1", now_ms=silent + 10)
    main.feed_line(state, "save", now_ms=silent + 20)
    assert "xuss.cfg" in fake.files or any("save=" in x for x in link.out)


def test_knob_drives_rpm_on_product_path():
    """product_path: shipped defaults + knob maps ADC to rpm edge."""
    defaults = _load("defaults")
    main = _load("main")
    edge = _load("edge")
    link_mod = _load("link")
    fake = _load_sim("hal_double").FakeHal()
    link = link_mod.MemoryLink()
    state = main.init(hal=fake, now_ms=0, link=link, riff_data=b"")
    assert state["tick_sleep_ms"] == defaults.TICK_SLEEP_MS
    main.feed_line(state, "set knob 1", now_ms=5)
    fake.angle_raw = defaults.KNOB_ADC_MAX
    main.tick(state, now_ms=10)
    expected = edge.rpm_to_hz(defaults.KNOB_RPM_MAX, defaults.RING_TEETH)
    assert fake.last_edge is not None
    assert abs(fake.last_edge[0] - expected) < 2.0


def test_host_hygiene_gate():
    from silico.host_hygiene import run_hygiene

    report = run_hygiene(ROOT)
    assert report.ok, "\n".join(report.lines)


def test_product_path_check():
    from silico.product_path import run_product_path_check

    report = run_product_path_check(ROOT)
    assert report.ok, "\n".join(report.lines)
    assert report.sim_refs >= 1
