"""Measure ESP32 DAC vs PWM on GPIO25 under sequenced conditions.

Host-driven: opens product `repl` door (or uses friendly REPL), soft-resets
into a clean MicroPython, runs on-device experiments, prints a results table.

This is measurement, not product code. Results justify HAL choices.

Usage:
  py -3 scripts/measure_dac.py
  py -3 scripts/measure_dac.py --port COM7
"""

from __future__ import annotations

import argparse
import sys
import time

try:
    import serial
except ImportError:
    print("need pyserial", file=sys.stderr)
    sys.exit(2)

# On-device measurement program (MicroPython). Printed lines are RESULTS.
ON_DEVICE = r"""
import sys
import time
from machine import Pin, PWM, DAC

PIN = 25
results = []

def rec(name, ok, detail=""):
    line = "RESULT|%s|%s|%s" % (name, "OK" if ok else "FAIL", detail)
    results.append(line)
    print(line)

def try_dac(label, factory):
    try:
        d = factory()
        d.write(160)
        time.sleep_ms(20)
        d.write(128)
        rec(label, True, type(d).__name__)
        return d
    except Exception as e:
        rec(label, False, repr(e))
        return None

def safe_deinit(obj, label):
    if obj is None:
        rec(label, True, "none")
        return
    try:
        if hasattr(obj, "deinit"):
            obj.deinit()
            rec(label, True, "deinit()")
        else:
            rec(label, True, "no-deinit-attr")
    except Exception as e:
        rec(label, False, repr(e))

print("MEASURE_DAC_BEGIN")
print("sys", sys.version)
print("implementation", sys.implementation)

# --- A: cold DAC after this script starts (post soft-reset, no product HAL) ---
d = try_dac("A_cold_DAC_25", lambda: DAC(25))
safe_deinit(d, "A_deinit")

# --- B: DAC(Pin(25)) form ---
d = try_dac("B_DAC_Pin25", lambda: DAC(Pin(25)))
safe_deinit(d, "B_deinit")

# --- C: GPIO OUT low then DAC (Xuss _spk_off remux pattern) ---
try:
    p = Pin(25, Pin.OUT)
    p.value(0)
    time.sleep_ms(5)
    rec("C_gpio_out_low", True, "ok")
except Exception as e:
    rec("C_gpio_out_low", False, repr(e))
d = try_dac("C_DAC_after_gpio_out", lambda: DAC(25))
safe_deinit(d, "C_deinit")

# --- D: open DAC, write PCM-ish, deinit, reopen (boot-riff then song pattern) ---
d = try_dac("D1_DAC_open", lambda: DAC(25))
if d is not None:
    try:
        t0 = time.ticks_us()
        for i in range(256):
            d.write(128 + ((i % 32) - 16))
            # ~11kHz-ish
            while time.ticks_diff(time.ticks_us(), t0) < 90:
                pass
            t0 = time.ticks_add(t0, 90)
        rec("D2_write_256", True, "ok")
    except Exception as e:
        rec("D2_write_256", False, repr(e))
    safe_deinit(d, "D3_deinit")
    d2 = try_dac("D4_DAC_reopen_after_deinit", lambda: DAC(25))
    safe_deinit(d2, "D5_deinit")
else:
    rec("D2_write_256", False, "skipped")
    rec("D4_DAC_reopen_after_deinit", False, "skipped")

# --- E: open DAC, drop ref WITHOUT deinit, remux GPIO, reopen (old Xuss bug) ---
d = try_dac("E1_DAC_open", lambda: DAC(25))
if d is not None:
    try:
        d.write(128)
    except Exception:
        pass
    d = None  # drop ref, no deinit
    rec("E2_drop_ref_no_deinit", True, "dropped")
    try:
        p = Pin(25, Pin.OUT)
        p.value(0)
        rec("E3_gpio_remux", True, "ok")
    except Exception as e:
        rec("E3_gpio_remux", False, repr(e))
    d2 = try_dac("E4_DAC_reopen_WITHOUT_prior_deinit", lambda: DAC(25))
    safe_deinit(d2, "E5_deinit")
else:
    rec("E4_DAC_reopen_WITHOUT_prior_deinit", False, "skipped")

# --- F: PWM then deinit then DAC ---
try:
    pwm = PWM(Pin(25), freq=40000, duty_u16=32768)
    time.sleep_ms(30)
    pwm.deinit()
    rec("F1_PWM_then_deinit", True, "ok")
except Exception as e:
    rec("F1_PWM_then_deinit", False, repr(e))
    pwm = None
d = try_dac("F2_DAC_after_PWM_deinit", lambda: DAC(25))
safe_deinit(d, "F3_deinit")

# --- G: PWM without deinit, then DAC ---
try:
    pwm = PWM(Pin(25), freq=40000, duty_u16=20000)
    time.sleep_ms(20)
    # drop without deinit
    pwm = None
    rec("G1_PWM_drop_no_deinit", True, "dropped")
except Exception as e:
    rec("G1_PWM_drop_no_deinit", False, repr(e))
d = try_dac("G2_DAC_after_PWM_no_deinit", lambda: DAC(25))
safe_deinit(d, "G3_deinit")

# --- H: final cleanup + DAC once more ---
try:
    p = Pin(25, Pin.OUT)
    p.value(0)
except Exception:
    pass
d = try_dac("H_final_DAC", lambda: DAC(25))
safe_deinit(d, "H_deinit")

print("MEASURE_DAC_END")
print("RESULT_COUNT|%d" % len(results))
"""


def read_for(ser: serial.Serial, seconds: float) -> bytes:
    buf = b""
    t0 = time.time()
    while time.time() - t0 < seconds:
        b = ser.read(512)
        if b:
            buf += b
        else:
            time.sleep(0.01)
    return buf


def enter_raw(ser: serial.Serial) -> None:
    ser.write(b"\x01")
    ser.flush()
    out = read_for(ser, 1.0)
    if b"raw REPL" not in out:
        raise RuntimeError("raw REPL failed: %r" % (out[:200],))


def raw_exec(ser: serial.Serial, code: str, timeout: float = 30.0) -> bytes:
    if not code.endswith("\n"):
        code += "\n"
    ser.write(code.encode("utf-8"))
    ser.write(b"\x04")
    ser.flush()
    buf = b""
    t0 = time.time()
    while time.time() - t0 < timeout:
        b = ser.read(256)
        if b:
            buf += b
            if buf.startswith(b"OK") and buf.count(b"\x04") >= 2:
                break
            if b"MEASURE_DAC_END" in buf and buf.count(b"\x04") >= 2:
                break
        else:
            time.sleep(0.005)
    return buf


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default="COM7")
    ap.add_argument("--out", default="scripts/measure_dac_results.txt")
    args = ap.parse_args()

    ser = serial.Serial(args.port, 115200, timeout=0.05)
    try:
        time.sleep(0.3)
        ser.reset_input_buffer()
        ser.write(b"repl\n")
        ser.flush()
        friendly = read_for(ser, 1.2)
        print("friendly:", friendly[-100:])

        enter_raw(ser)

        # Park product main so soft-reset lands in REPL (no kbd_intr / no HAL).
        park = raw_exec(
            ser,
            "import os\n"
            "try:\n"
            " os.rename('main.py','main.py._meas')\n"
            " print('parked main')\n"
            "except Exception as e:\n"
            " print('park',e)\n",
            timeout=5.0,
        )
        print("park:", park)

        ser.write(b"\x02")
        time.sleep(0.15)
        ser.write(b"\x04")
        ser.flush()
        boot = read_for(ser, 3.0)
        print("soft reboot:", boot[-150:])

        enter_raw(ser)
        resp = raw_exec(ser, ON_DEVICE, timeout=45.0)
        text = resp.decode("utf-8", errors="replace")
        print(text)

        lines = [ln for ln in text.splitlines() if ln.startswith("RESULT|")]
        print("\n=== TABLE ===")
        print("%-40s %-6s %s" % ("test", "ok", "detail"))
        print("-" * 80)
        for ln in lines:
            parts = ln.split("|", 3)
            if len(parts) >= 4:
                print("%-40s %-6s %s" % (parts[1], parts[2], parts[3]))

        with open(args.out, "w", encoding="utf-8") as f:
            f.write("# measure_dac.py results (device measurement)\n")
            f.write(text)
            f.write("\n")
        print("\nwrote", args.out)

        restore = raw_exec(
            ser,
            "import os\n"
            "try:\n"
            " os.rename('main.py._meas','main.py')\n"
            " print('restored main')\n"
            "except Exception as e:\n"
            " print('restore',e)\n",
            timeout=5.0,
        )
        print("restore:", restore)

        ser.write(b"\x02")
        time.sleep(0.15)
        ser.write(b"\x04")
        ser.flush()
        return 0 if lines else 1
    finally:
        ser.close()


if __name__ == "__main__":
    sys.exit(main())
