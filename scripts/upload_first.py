"""Upload assets/first.u8.raw to the device over CDC (chunked base64).

Opens the product `repl` door, enters raw REPL, writes the file, soft-reboots.
"""

from __future__ import annotations

import base64
import os
import sys
import time

try:
    import serial
except ImportError:
    print("need pyserial", file=sys.stderr)
    sys.exit(2)

PORT = os.environ.get("XUSS_PORT", "COM7")
BAUD = 115200
HOST = os.path.join(os.path.dirname(__file__), "..", "assets", "first.u8.raw")
DEST = "first.u8.raw"
CHUNK = 1536  # raw bytes per write (~2k b64)


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


def enter_product_repl(ser: serial.Serial) -> None:
    ser.reset_input_buffer()
    ser.write(b"repl\n")
    ser.flush()
    out = read_for(ser, 1.5)
    if b">>>" not in out and b"MicroPython" not in out:
        # try again
        ser.write(b"\r\nrepl\r\n")
        ser.flush()
        out += read_for(ser, 1.5)
    print("friendly:", out[-120:])


def enter_raw(ser: serial.Serial) -> None:
    ser.write(b"\x01")  # Ctrl-A
    ser.flush()
    out = read_for(ser, 1.0)
    print("raw:", out[:120])
    if b"raw REPL" not in out:
        raise RuntimeError("could not enter raw REPL: %r" % out[:200])


def raw_exec(ser: serial.Serial, code: str, timeout: float = 8.0) -> bytes:
    if not code.endswith("\n"):
        code += "\n"
    ser.write(code.encode("utf-8"))
    ser.write(b"\x04")  # Ctrl-D execute
    ser.flush()
    buf = b""
    t0 = time.time()
    while time.time() - t0 < timeout:
        b = ser.read(256)
        if b:
            buf += b
            # raw response: OK<output>\x04\x04>  or OK\x04E...
            if buf.startswith(b"OK") and buf.count(b"\x04") >= 2:
                break
            if b"\x04>" in buf:
                break
        else:
            time.sleep(0.005)
    return buf


def main() -> int:
    host = os.path.abspath(HOST)
    size = os.path.getsize(host)
    print("upload", host, "->", DEST, "size", size, "port", PORT)

    ser = serial.Serial(PORT, BAUD, timeout=0.05)
    try:
        time.sleep(0.3)
        enter_product_repl(ser)
        enter_raw(ser)

        # create/truncate
        r = raw_exec(ser, "f=open(%r,'wb'); f.close()" % DEST)
        print("create", r[:80])

        written = 0
        with open(host, "rb") as f:
            while True:
                data = f.read(CHUNK)
                if not data:
                    break
                b64 = base64.b64encode(data).decode("ascii")
                code = (
                    "import ubinascii\n"
                    "f=open(%r,'ab')\n"
                    "f.write(ubinascii.a2b_base64(%r))\n"
                    "f.close()\n"
                ) % (DEST, b64)
                r = raw_exec(ser, code, timeout=15.0)
                if not r.startswith(b"OK"):
                    print("chunk fail at", written, r[:200])
                    return 1
                written += len(data)
                if written % (CHUNK * 40) == 0 or written >= size:
                    print("wrote", written, "/", size)

        # verify size
        r = raw_exec(ser, "import os\nprint(os.stat(%r)[6])\n" % DEST)
        print("stat", r)

        # leave raw, soft reboot into app
        ser.write(b"\x02")  # Ctrl-B friendly
        time.sleep(0.2)
        ser.write(b"\x04")  # Ctrl-D soft reboot
        ser.flush()
        time.sleep(1.0)
        print("soft reboot issued")
        return 0
    finally:
        ser.close()


if __name__ == "__main__":
    sys.exit(main())
