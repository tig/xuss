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
| `silico inspect --port COM7` → `XUSS 0.0.1` | Host and device identity match |
| Host gates green | `pytest -q`, `silico gate`, `silico product-path` |

**Honest metal note:** the plate hello-metal toggles `LED_PIN` from `firmware/defaults.py` (currently 16, XIAO-era). On M5GO that pin is **not** a documented front-face LED; visible face/side-LED/boot-riff behavior is domain work from `spec.md`, not claimed done by this plate blink.

## Dry plan (no write)

```text
silico deploy --port COMx
```
