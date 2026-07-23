# Xuss

Xuss is a pocket companion for the M5Stack **M5GO IoT Starter Kit v2.7**. It boots with a short musical greeting, shows a living face on the screen, plays a full song on demand, and can show a details screen for the sensors built into the M5GO core.

The name is the short half of Turminder Xuss, the drone in Iain M. Banks' *Matter*: precise dirty work while the human keeps judgment.

## Status

**Spec only — clean start.** [spec.md](spec.md) is the product contract (Rev 0.3). There is no plate, firmware, or host gate in this tree yet.

First ship is driven by an agent with [silico](https://github.com/tig/silico): host tools → scaffold the plate → host gate green → board talk over USB → operator-visible product face.

## Hardware

- **M5Stack M5GO IoT Starter Kit v2.7** (core with screen, speaker, three front buttons, side LED strips)
- USB power / data cable

No extra modules are required for the features in the spec.
