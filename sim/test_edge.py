"""L0: edge math and profile player against shipped defaults."""

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIRMWARE = ROOT / "firmware"


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


def test_rpm_to_hz_defaults():
    edge = _load("edge")
    defaults = _load("defaults")
    # Spec: 750 rpm → 1625 Hz; 200 rpm → 433 Hz (at ring_teeth=130)
    assert defaults.RING_TEETH == 130
    assert abs(edge.rpm_to_hz(750, defaults.RING_TEETH) - 1625.0) < 1e-9
    assert abs(edge.rpm_to_hz(200, defaults.RING_TEETH) - (200 * 130 / 60)) < 1e-9
    assert edge.rpm_to_hz(0, defaults.RING_TEETH) == 0.0


def test_builtin_profiles_exist():
    edge = _load("edge")
    names = set(edge.profile_names())
    assert "crank_catch_idle" in names
    assert "redline_sweep" in names
    assert "stall" in names


def test_profile_player_time_based():
    edge = _load("edge")
    p = edge.ProfilePlayer()
    assert p.start("stall", now_ms=0)
    assert p.current_rpm() == 750
    # still in first step
    assert p.tick(100) == 750
    # advance past first step (400 ms)
    rpm = p.tick(400)
    assert rpm == 400
    # run to end
    while p.active:
        p.tick(p.step_ends_ms)
    assert p.done
    assert p.tick(99999) is None
