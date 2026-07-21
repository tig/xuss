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
