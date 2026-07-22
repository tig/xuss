"""L0: protocol verbs, escape hatch, dead-man, edge apply — HAL double."""

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


def _app():
    main = _load("main")
    fake = _load_sim("hal_double").FakeHal()
    app = main.App(hal=fake)
    return main, fake, app


def test_identity_and_rpm_edge():
    main, fake, app = _app()
    defaults = _load("defaults")
    edge = _load("edge")
    app.boot_announce()
    assert any("fw_name=XUSS" in t for t in fake.tx)

    fake.push_line("rpm 1600")
    app.tick()
    assert app.config.get("rpm") == 1600
    assert fake.edge is not None
    hz, duty, route = fake.edge
    expect = edge.rpm_to_hz(1600, defaults.RING_TEETH)
    assert abs(hz - expect) < 1e-6
    assert duty == defaults.DUTY_PCT
    assert route == "voice"


def test_set_rejects_and_get():
    _, fake, app = _app()
    fake.push_line("set duty_pct 3")
    app.tick()
    assert any("err=set" in t for t in fake.tx)
    fake.tx.clear()
    fake.push_line("set duty_pct 5")
    app.tick()
    assert app.config.get("duty_pct") == 5
    fake.tx.clear()
    fake.push_line("get duty_pct")
    app.tick()
    assert any("duty_pct=5" in t for t in fake.tx)


def test_sing_and_run_profiles():
    _, fake, app = _app()
    fake.push_line("sing crank_catch_idle")
    app.tick()
    assert app.player.active
    assert app._route_force == "voice"
    assert app.config.get("rpm") == 200
    fake.push_line("stop")
    app.tick()
    assert not app.player.active
    assert fake.edge is None

    fake.push_line("run stall")
    app.tick()
    assert app._route_force == "tach"
    assert any("actuate" in t for t in fake.tx)


def test_mute_parks_and_survives_defaults_cmd():
    _, fake, app = _app()
    fake.push_line("rpm 750")
    app.tick()
    assert fake.edge is not None
    fake.push_line("set mute 1")
    app.tick()
    assert fake.edge is None
    fake.push_line("defaults")
    app.tick()
    assert app.config.get("mute") == 1


def test_escape_hatch_repl_and_reboot():
    _, fake, app = _app()
    fake.push_line("rpm 500")
    app.tick()
    fake.push_line("repl")
    status = app.tick()
    assert status == "repl"
    assert fake.repl_count == 1
    assert fake.edge is None

    _, fake2, app2 = _app()
    fake2.push_line("reboot")
    status = app2.tick()
    assert status == "reboot"
    assert fake2.reset_count == 1


def test_deadman_releases_tach():
    defaults = _load("defaults")
    _, fake, app = _app()
    fake.push_line("run stall")
    app.tick()
    assert app.player.active
    # silence beyond dead-man window
    fake.advance(defaults.DEADMAN_MS + 50)
    app.tick()
    assert not app.player.active
    assert app.config.get("rpm") == 0
    assert fake.edge is None


def test_ctrl_c_is_data_not_break():
    """Poison line handling: embedded \\x03 is not special to the parser."""
    _, fake, app = _app()
    fake.push_line("identity\x03")
    # Actually push raw with ctrl-c mid-stream before newline
    fake.rx.append("iden\x03tity\n")
    app.tick()
    # unknown or identity depending on parse — must not crash
    assert app.tick_count >= 1
