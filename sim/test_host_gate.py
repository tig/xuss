"""Host gate: edge/protocol/engine + main path against HAL double."""

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


def test_hal_contract_importable_without_machine():
    hal_mod = _load("hal")
    assert hasattr(hal_mod, "Hal")
    assert hasattr(hal_mod.Hal, "set_edge")
    assert hasattr(hal_mod.Hal, "park_outputs")


def test_edge_math_matches_spec_examples():
    edge = _load("edge")
    defaults = _load("defaults")
    assert edge.rpm_to_hz(750, defaults.RING_TEETH) == 1625.0
    assert abs(edge.rpm_to_hz(200, defaults.RING_TEETH) - 433.333333) < 0.01
    assert abs(edge.rpm_to_hz(1600, defaults.RING_TEETH) - (1600 * 130 / 60)) < 1e-9


def test_profiles_are_songs():
    edge = _load("edge")
    defaults = _load("defaults")
    steps = edge.profile_steps("crank_catch_idle", defaults.PROFILES)
    assert steps[0][0] == 200
    assert edge.profile_rpm_at(steps, 900) == 433
    assert "stall" in defaults.PROFILES


def test_config_completeness_and_mute_survives_defaults():
    config = _load("config")
    cfg = config.factory()
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
    assert a["side"] != b["side"]
    assert face.frame(0, mode="singing")["side"] != face.frame(0, mode="idle")["side"]


def test_protocol_identity_get_set_and_escape():
    main = _load("main")
    link_mod = _load("link")
    fake = _load_sim("hal_double").FakeHal()
    link = link_mod.MemoryLink()
    state = main.init(hal=fake, now_ms=0, link=link)
    assert any("fw_name=XUSS" in x for x in link.out)

    main.feed_line(state, "identity", now_ms=10)
    assert any("fw_version=" in x for x in link.out)

    main.feed_line(state, "set ring_teeth 130", now_ms=20)
    main.feed_line(state, "get ring_teeth", now_ms=30)
    assert "ring_teeth=130" in link.out

    main.feed_line(state, "rpm 1600", now_ms=40)
    main.tick(state, now_ms=50)
    assert fake.last_edge is not None
    assert fake.last_edge[0] > 0
    assert state["mode"] == "singing"

    main.feed_line(state, "stop", now_ms=60)
    main.tick(state, now_ms=70)
    assert state["eng"]["active_rpm"] == 0

    main.feed_line(state, "repl", now_ms=80)
    assert state["exit_repl"] is True


def test_sing_and_run_profiles_and_deadman():
    main = _load("main")
    link_mod = _load("link")
    defaults = _load("defaults")
    fake = _load_sim("hal_double").FakeHal()
    link = link_mod.MemoryLink()
    state = main.init(hal=fake, now_ms=0, link=link)

    main.feed_line(state, "sing stall", now_ms=100)
    assert state["cfg"]["route"] == "voice"
    main.tick(state, now_ms=200)
    assert state["mode"] == "singing"
    assert fake.last_edge[0] > 0

    main.feed_line(state, "run crank_catch_idle", now_ms=300)
    assert state["cfg"]["route"] == "tach"
    main.tick(state, now_ms=400)
    assert state["mode"] == "driving"
    assert fake.last_edge[2] == "tach"  # route

    # Steady tach force (profiles can finish before the dead-man window)
    main.feed_line(state, "route tach", now_ms=500)
    main.feed_line(state, "rpm 1600", now_ms=510)
    main.tick(state, now_ms=520)
    assert state["mode"] == "driving"

    # Dead-man: host silent beyond window while tach forcing
    silent_at = 510 + defaults.DEADMAN_MS + 50
    main.tick(state, now_ms=silent_at)
    assert state["eng"]["parked_reason"] == "deadman"
    assert any("event=deadman" in x for x in link.out)


def test_main_init_tick_drives_face_and_sides():
    main = _load("main")
    fake = _load_sim("hal_double").FakeHal()
    state = main.init(hal=fake, now_ms=0)
    assert fake.backlight is True
    assert fake.last_side is not None
    main.tick(state, now_ms=500)
    assert state["tick_count"] == 1


def test_host_hygiene_gate():
    from silico.host_hygiene import run_hygiene

    report = run_hygiene(ROOT)
    assert report.ok, "\n".join(report.lines)


def test_product_path_uses_shipped_defaults():
    """product_path: drive init/tick/rpm with shipped defaults unmodified."""
    defaults = _load("defaults")
    main = _load("main")
    edge = _load("edge")
    link_mod = _load("link")
    fake = _load_sim("hal_double").FakeHal()
    link = link_mod.MemoryLink()

    state = main.init(hal=fake, now_ms=0, link=link)
    assert state["tick_sleep_ms"] == defaults.TICK_SLEEP_MS
    assert state["cfg"]["ring_teeth"] == defaults.RING_TEETH
    expected_hz = edge.rpm_to_hz(1600, defaults.RING_TEETH)
    main.feed_line(state, "rpm 1600", now_ms=10)
    main.tick(state, now_ms=20)
    assert fake.last_edge is not None
    assert abs(fake.last_edge[0] - expected_hz) < 1.0
    # duty stays mark-space; volume is a separate amplitude channel
    assert fake.last_edge[1] == defaults.DUTY_PCT
    assert fake.last_edge[3] == defaults.VOLUME
    assert state["fw_name"] and state["fw_version"]


def test_product_path_check():
    from silico.product_path import run_product_path_check

    report = run_product_path_check(ROOT)
    assert report.ok, "\n".join(report.lines)
    assert report.sim_refs >= 1
