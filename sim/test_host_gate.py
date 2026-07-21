"""Host gate: edge/config/face + main path against HAL double; product path honest."""

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
    assert isinstance(version.FW_NAME, str) and version.FW_NAME
    assert isinstance(version.FW_VERSION, str) and version.FW_VERSION.count(".") >= 2


def test_hal_contract_importable_without_machine():
    hal_mod = _load("hal")
    assert hasattr(hal_mod, "Hal")


def test_edge_math_matches_spec_examples():
    edge = _load("edge")
    defaults = _load("defaults")
    # 750 rpm @ 130 teeth => 1625 Hz; 200 rpm => ~433.33 Hz
    assert edge.rpm_to_hz(750, defaults.RING_TEETH) == 1625.0
    assert abs(edge.rpm_to_hz(200, defaults.RING_TEETH) - 433.333333) < 0.01
    assert abs(edge.rpm_to_hz(1600, defaults.RING_TEETH) - (1600 * 130 / 60)) < 1e-9


def test_profiles_are_songs():
    edge = _load("edge")
    defaults = _load("defaults")
    steps = edge.profile_steps("crank_catch_idle", defaults.PROFILES)
    assert steps[0][0] == 200
    assert edge.profile_rpm_at(steps, 0) == 200
    assert edge.profile_rpm_at(steps, 900) == 433
    assert edge.profile_total_ms(steps) > 0
    assert "stall" in defaults.PROFILES
    assert "redline_sweep" in defaults.PROFILES


def test_config_completeness_and_mute_survives_defaults():
    config = _load("config")
    cfg = config.factory()
    assert config.get_param(cfg, "ring_teeth") == 130
    ok, _ = config.set_param(cfg, "rpm", 1600)
    assert ok
    ok, err = config.set_param(cfg, "rpm", 9000)
    assert not ok and err == "range"
    ok, _ = config.set_param(cfg, "mute", 1)
    assert ok
    config.apply_defaults(cfg)
    assert cfg["mute"] == 1
    assert cfg["rpm"] == 0


def test_face_is_time_based_not_tick_based():
    face = _load("face")
    defaults = _load("defaults")
    a = face.frame(0, mode="idle")
    b = face.frame(defaults.FACE_CHASE_MS, mode="idle")
    # chase advances with wall time
    assert a["side"] != b["side"]
    # blink closed near period end
    closed = face.frame(defaults.FACE_BLINK_PERIOD_MS - 1, mode="idle")
    open_ = face.frame(0, mode="idle")
    assert open_["eyes_open"] is True
    assert closed["eyes_open"] is False


def test_main_init_tick_drives_face_and_sides():
    main = _load("main")
    fake = _load_sim("hal_double").FakeHal()
    state = main.init(hal=fake, now_ms=0)
    assert fake.backlight is True
    assert fake.last_side is not None
    assert fake.last_face is not None
    assert state["fw_name"]
    assert state["fw_version"]
    main.tick(state, now_ms=500)
    assert len(fake.side_history) >= 2
    assert state["tick_count"] == 1


def test_host_hygiene_gate():
    from silico.host_hygiene import run_hygiene

    report = run_hygiene(ROOT)
    assert report.ok, "\n".join(report.lines)


def test_product_path_uses_shipped_defaults():
    """product_path: drive init/tick with shipped defaults unmodified."""
    defaults = _load("defaults")
    main = _load("main")
    edge = _load("edge")
    fake = _load_sim("hal_double").FakeHal()

    state = main.init(hal=fake, now_ms=0)
    assert state["tick_sleep_ms"] == defaults.TICK_SLEEP_MS
    assert state["cfg"]["ring_teeth"] == defaults.RING_TEETH
    # edge path on shipped ring_teeth (instrument math is L0 host proof)
    assert edge.rpm_to_hz(750, defaults.RING_TEETH) == 1625.0
    main.tick(state, now_ms=defaults.FACE_CHASE_MS * 3)
    assert fake.last_side is not None
    assert len(fake.last_side) == defaults.SIDE_LED_COUNT
    assert state["fw_name"] and state["fw_version"]


def test_product_path_check():
    from silico.product_path import run_product_path_check

    report = run_product_path_check(ROOT)
    assert report.ok, "\n".join(report.lines)
    assert report.sim_refs >= 1
