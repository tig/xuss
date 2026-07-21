# Xuss

A bench drone that sings the engine it simulates.

Xuss is the fourth GCU built on [silico](https://github.com/tig/silico), and a different shape of proof from the other three: its customer is the dev loop itself. The day job is a test instrument (engine-speed edge trains, input forcing, current measurement) for sibling GCUs on the bench. The stage job is a video: start with a spec, point silico at it, and about an hour later it is singing and dancing per the spec.

The name is the short half of Turminder Xuss, the drone in Iain M. Banks' *Matter*: precise dirty work while the human keeps judgment.

## Status

**L0 host complete; L1 metal implemented on M5GO; L2 fixture not yet run.**

| Layer | Status |
|-------|--------|
| L0 host | `pytest`, `silico gate`, `silico product-path` |
| L1 metal | Protocol, edge engine, face, boot riff, ANGLE/PIR, dead-man, escape hatch on hardware |
| L1 camera rows | Require external instruments / operator (see [install/README.md](install/README.md)) |
| L2 fixture | Sibling GCU metal gate not executed yet |

Contract: [spec.md](spec.md). C twin: [tig/xuss-c](https://github.com/tig/xuss-c). Background: [tig/silico#50](https://github.com/tig/silico/issues/50).

## Hardware

M5Stack **M5GO IoT Starter Kit v2.7**, zero solder. See install notes for pin map.
