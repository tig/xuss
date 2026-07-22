# Install / update (Xuss)

## Day-2 one-liner (after first-flash is done once)

```text
python -m pytest -q
silico deploy --port COM7 --yes --verify --reset
# soft-reset once more if the app is not running after verify:
mpremote connect COM7 reset
```

Always pass an explicit port. Re-confirm board identity if more than one serial device is present.

## First flash (once, ESP32 / M5GO)

If `silico inspect --port COMx` cannot enter a modern MicroPython REPL:

```text
python -m pip install esptool
esptool --chip esp32 --port COMx erase-flash
esptool --chip esp32 --port COMx write-flash -z 0x1000 ESP32_GENERIC-<date>-vX.Y.Z.bin
silico inspect --port COMx --apply-mpy-pin
```

Firmware: https://micropython.org/download/ESP32_GENERIC/  
After first-flash, app updates are mpremote/`silico deploy` only — no re-teach of esptool.

## What “good” looks like today

| Signal | Meaning |
|--------|---------|
| `silico inspect --port COM7` → `XUSS 0.1.0` (or current `FW_VERSION`) | Host and device identity match |
| Host gates green | `pytest -q`, `silico gate`, `silico product-path` |
| Link answers `identity` | `fw_name=XUSS fw_version=…` on the serial line |

**Honest metal note:** L0 proves protocol, edge math, config, and escape hatch on the host double. On M5GO, PWM edge on `VOICE_PIN`/`TACH_PIN` is best-effort; L1 pitch/frequency rows still need an external instrument (spec §6.4). Face/side LEDs and boot riff DAC remain open (issue #5 / later slices).

## Dry plan (no write)

```text
silico deploy --port COMx
```
