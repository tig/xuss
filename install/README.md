# Install / update (Xuss / M5GO)

## Day-2 one-liner

```text
python -m pytest -q
silico deploy --port COM7 --yes --verify --reset
mpremote connect COM7 cp assets/boot-riff.u8.raw :boot_riff.u8.raw
```

(Or one soft reboot after both writes.) Confirm board identity before `--yes`.

**Good on metal:** `identity` answers `fw_name=XUSS`; side LEDs chase; boot riff once after power; `rpm 750` sings; `repl` opens the door for redeploy.

## Hardware map (v0.3)

| Function | Pin / port |
|----------|------------|
| Speaker | G25 |
| Tach edge (Port B yellow) | G26 |
| ANGLE ADC (Port B white) | G36 |
| PIR (Port C yellow) | G17 |
| Side SK6812 ×10 | G15 |

## First flash (once)

```text
esptool --chip esp32 --port COM7 erase-flash
esptool --chip esp32 --port COM7 write-flash -z 0x1000 ESP32_GENERIC-….bin
```

## L1 acceptance (operator)

External measurement is required for pitch/frequency claims (spec §6). Host green is not L1 done.

| Row | How |
|-----|-----|
| Boot riff | Power cycle; hear *First* after identity line |
| On-pitch | `rpm 1600` + frequency counter on speaker/tach |
| Same engine | `route both` + compare voice vs G26 |
| Knob | `set knob 1`, turn ANGLE on Port B |
| Greet | `set greet 1`, walk up (PIR on Port C) |
| Dead-man | `run stall` then silence host >3s |
| Escape | `repl` then redeploy |
| Wrong-sensor | `set duty_pct 5` on tach |

## L2 fixture

Xuss as fixture for a sibling GCU metal gate: route tach to DUT tach input, `run` / `rpm` profiles, dead-man safe. Document the sibling repo issue/run when executed. Not claimed done until that gate is green on the bench.
