"""L0: parameter store completeness, mute exempt, image checksum."""

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


def test_every_param_gettable_and_range_reject():
    cfg_mod = _load("config")
    defaults = _load("defaults")
    c = cfg_mod.Config()
    for key, _ in c.all_items():
        assert c.get(key) is not None
    # out of range rejects
    ok, why = c.set("ring_teeth", 5)
    assert not ok and why == "range"
    ok, why = c.set("duty_pct", 1)
    assert not ok and why == "range"
    ok, why = c.set("route", "left")
    assert not ok and why == "range"
    ok, norm = c.set("route", "both")
    assert ok and norm == "both"
    assert c.get("ring_teeth") == defaults.RING_TEETH


def test_mute_survives_defaults():
    cfg_mod = _load("config")
    c = cfg_mod.Config()
    assert c.set("mute", 1)[0]
    assert c.set("rpm", 1000)[0]
    c.defaults()
    assert c.get("mute") == 1
    assert c.get("rpm") == 0


def test_save_load_roundtrip_and_torn():
    cfg_mod = _load("config")
    fake = _load_sim("hal_double").FakeHal()
    c = cfg_mod.Config(hal=fake)
    c.set("volume", 3)
    c.set("mute", 1)
    img = c.save()
    assert fake.config_blob == img

    c2 = cfg_mod.Config(hal=fake)
    reason = c2.load()
    assert reason == "ok"
    assert c2.get("volume") == 3
    assert c2.get("mute") == 1

    fake.config_blob = "v=1;garbage"
    c3 = cfg_mod.Config(hal=fake)
    reason = c3.load()
    assert reason in ("torn", "no_cs", "empty", "cs_mismatch", "bad_int", "range")
    assert c3.get("volume") == 6  # factory
