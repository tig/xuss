# Install / update (Xuss / M5GO)

## Day-2 one-liner (after first flash is done)

```text
python -m pytest -q
silico deploy --port COM7 --yes --verify
```

**Good on metal:** device `FW_VERSION` matches host (`XUSS 0.0.1` for this plate).
Plate LED defaults are still XIAO-shaped (GPIO16); the M5GO face/side LEDs are domain work.

Always pass an explicit port. Confirm board identity every session before `--yes`.

## First-time metal prep (already done on this bench)

1. Board: M5Stack **M5GO IoT Starter Kit v2.7** (ESP32-D0WDQ6-V3, 16MB flash).
2. USB serial: **CH9102** (this bench: **COM7**).
3. Stock was UIFlow-era MicroPython 1.12; first flash is **esptool**, not UF2:

```text
esptool --chip esp32 --port COM7 erase-flash
esptool --chip esp32 --port COM7 write-flash -z 0x1000 ESP32_GENERIC-20260406-v1.28.0.bin
```

4. Then: `silico inspect --port COM7 --apply-mpy-pin` and deploy as above.

Stock root files from before the flash live under `.silico/stock-backup/` (gitignored).
