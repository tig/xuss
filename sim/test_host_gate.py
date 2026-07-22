"""Host gate: firmware loads without a board; HAL seam honest; product path shipped."""

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
    assert version.FW_NAME == "XUSS"


def test_hal_contract_importable_without_machine():
    # Contract module must not touch hardware.
    hal_mod = _load("hal")
    assert hasattr(hal_mod, "Hal")


def test_main_init_tick_with_fake_hal():
    main = _load("main")
    fake = _load_sim("hal_double").FakeHal()
    state = main.init(hal=fake)
    main.tick(state)
    assert state["fw_name"]
    assert state["fw_version"]
    assert state["tick_count"] >= 1


def test_host_hygiene_gate():
    """Silico hygiene: deploy set host-importable; only allowlisted stems use machine."""
    from silico.host_hygiene import run_hygiene

    report = run_hygiene(ROOT)
    assert report.ok, "\n".join(report.lines)


def test_product_path_uses_shipped_defaults():
    """Drive init/tick with *shipped* defaults — not test-local substitutes.

    product_path: honest host proof that cadence and edge math come from
    firmware/defaults.py rather than literals in the test.
    """
    defaults = _load("defaults")
    edge = _load("edge")
    main = _load("main")
    fake = _load_sim("hal_double").FakeHal()

    state = main.init(hal=fake)
    app = state["app"]
    assert state["tick_sleep_ms"] == defaults.TICK_SLEEP_MS

    # Command rpm via protocol; frequency must match shipped ring_teeth math.
    fake.push_line("rpm 750")
    main.tick(state)
    assert app.config.get("ring_teeth") == defaults.RING_TEETH
    assert app.config.get("rpm") == 750
    assert fake.edge is not None
    hz, duty, route = fake.edge
    assert abs(hz - edge.rpm_to_hz(750, defaults.RING_TEETH)) < 1e-9
    assert duty == defaults.DUTY_PCT
    assert route == defaults.ROUTE
    assert state["fw_name"] and state["fw_version"]


def test_product_path_check():
    from silico.product_path import run_product_path_check

    report = run_product_path_check(ROOT)
    assert report.ok, "\n".join(report.lines)
    assert report.sim_refs >= 1
