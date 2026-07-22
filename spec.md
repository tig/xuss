# Xuss Software Specification

**Rev 0.2, July 2026**

Xuss is a bench drone with two jobs. 

* The day job: A fun demo of a M5Stack **M5GO IoT Starter Kit v2.7** that exercises audio output, the display, LEDs, and button input.
* The stage job: proof on camera that a spec plus silico produces a working device in about an hour, using MicroPython.

## Working Backwards Artifact - Xuss User's Manual

Welcome to Xuss. When the little device boots up it will play a 3-ish second riff from an EDM song you may have heard before, [First by Tig](https://kindel.com/tigger/tig) as it's boot sound. Because Xuss is using MicroPython, the sound quality will be low-fidelity.

After booting it will show a smiley face on the screen with a dark blue background. The eyes and mouth will be bright blue. Across the top of the screen a smootly scrolling banner will continuously scroll from right to left, reading "Xuss: Built with Silico". The M5GO LEDs on the side of the device will be a bright blue color. Every 5 seconds, the right eye will blink like Xuss is winking at you.

Button A, when pressed, the LEDs and face on the screen will cycle through different colors: 

1. (The first state) Blue LED. Face is bright blue on a dark background.
2. Red LED. Face is bright red, on a dark red background.
3. Orange LED. Face is yellow on an orange background.
4. Green LED. Face is bright green on a dark green background.
5. No LED. Face is black on a white background.

The banner (which is really the face's hair) matches these colors.

Button B, when pushed will play the entirity of "First". Pressing B while the song is playing will pause it.

## 1. Readiness layers (definition of done)

| Layer | Proven when |
|---|---|
| **L0 (host)** | Song/choreography compiler, edge math, protocol, and config store pass pytest against the HAL double. |
| **L1 (metal, self)** | Edge output frequency verified by external measurement (logic analyzer); pitch within tolerance on the speaker; escape hatch works; identity on the link. |
| **L2 (fixture)** | Xuss, as the bench fixture, runs a sibling GCU's metal gate end to end. Its vehicle is the bench. |

Claims name their layer. Host green is never fixture done.

## 2. Hardware (fixed)

M5Stack **M5GO IoT Starter Kit v2.7**. No soldering anywhere in the build.

| Piece | Role |
|---|---|
| M5GO core (ESP32, 16 MB flash, 2.0" 320x240 IPS, speaker, mic, three buttons, 6-axis IMU) | The drone: face, voice, buttons |
| Ten side RGB LEDs | The light show |

## 3. The edge engine (voice and instrument are one section, deliberately)

One square-wave engine, routable to two sinks.

- Frequency math: `f_hz = rpm × ring_teeth / 60`. At the defaults, 750 rpm is 1,625 Hz and cranking (200 rpm) is 433 Hz.
- `route` selects the sink: `voice` (speaker), `tach` (Port B), or `both`. On `both`, the two outputs shall agree within 0.1%.
- **Profiles are songs.** A profile is a named, timed list of (rpm, ms) pairs. `sing <profile>` plays it on the voice route; `run <profile>` plays it on the tach route. They are the same code path; the acceptance test for one is the acceptance test for the other. Built-ins: `crank_catch_idle` (200 → 433 → overshoot → settle 750), `redline_sweep`, `stall` (750 → dying fall → 0).
- `duty_pct` sets the mark-space ratio, so Xuss can also impersonate a mis-plugged or wrong sensor (a ~5/95 wave instead of ~50/50) when a DUT needs to prove it can tell the difference.
- **The ANGLE unit is a live rpm input** when enabled: pitch tracks the knob within one control tick. Hand someone the knob and they rev the engine.

## 4. Face and presence

- The IPS panel is the face: eyes that track state (idle, singing, driving the DUT, fault). The ten side LEDs carry the beat.
- Face patterns are time-based, never tick-based.
- **PIR greet**: when `greet=1` and the PIR sees a human after quiet, Xuss greets once (short chirp plus face) and then shuts up. It never greets twice for one approach and never interrupts an active instrument run.

## 5. Manners

- Boot: identity line first (`fw_name=XUSS fw_version=…`), then the greeting, then silence until spoken to. **The greeting is seconds 7.5 to 10 of *First*** (`assets/boot-riff.u8.raw`, 11,025 Hz u8 mono, played via the DAC). It is the only sampled sound Xuss makes; it greets in its maker's voice, then sings in its own. Playback never delays readiness: the identity line goes out first and the port answers while it sings.
- `mute` is **commissioning state**: it survives `defaults` and clears only by explicit `set mute 0`.
- Every actuation that touches a DUT announces itself on the link before it moves.

## 6. Rails (normative)

1. **Dead-man on everything that touches the DUT.** Tach output and any forcing channel release to passive when the host goes silent beyond the window. Re-issuing the command is the refresh.
2. **Serial is bounded both directions.** Byte-budgeted intake per tick; poison-to-newline discard with a capped error response; egress capped per tick; Ctrl-C is data.
3. **The escape hatch ships from day one.** `repl` (park outputs, restore the interrupt character, exit clean) and `reboot` (park, hard reset). A build without the door fails L1.
4. **Self-report is not measurement.** L1 pitch and frequency rows are verified by external instruments, not by Xuss's own telemetry.

## 7. Protocol and parameters

ASCII lines, `key=value` telemetry, same contract family as every silico GCU: `identity`, `get/set/save/defaults`, `repl`, `reboot`, plus the instrument verbs (`sing`, `run`, `route`, `rpm`, `stop`).

The parameter table is a completeness contract: every row answers `get` and rejects an out-of-range `set`; no value exists only as a source literal; `defaults` restores every row except `DEFAULTS_EXEMPT`.

| Parameter | Type | Default | Notes |
|---|---|---|---|
| `ring_teeth` | int (10–400) | 130 | Edge math; matches the sibling DUT it feeds |
| `rpm` | int (0–8000) | 0 | Live commanded speed; 0 is silence |
| `duty_pct` | int (5–95) | 50 | Mark-space; ~5 or ~95 impersonates the wrong sensor |
| `route` | enum | voice | `voice` / `tach` / `both` |
| `volume` | int (0–10) | 6 | Stage-appropriate |
| `greet` | int (0/1) | 1 | PIR greeting |
| `knob` | int (0/1) | 0 | ANGLE unit drives `rpm` live |
| `mute` | int (0/1) | 0 | **Commissioning state; survives `defaults`** |
| `telemetry_hz` | int (0–100) | 10 | 0 is off |

Config persists as a single versioned, checksummed image; a torn image falls back to factory in full; an intact image with a different key set migrates, and `mute` survives whenever its row parses.

## 8. Acceptance (written for a camera)

| Row | Check | Layer |
|---|---|---|
| Boot riff | Greeting begins within two seconds of power; identity line first; the riff is recognizably *First* at 7.5 seconds in, by ear on camera; the port answers commands while it plays | L1 |
| On-pitch | `rpm 1600`: measured voice frequency = 1600 × 130 / 60 Hz within 1%, logic-analyzer trace on screen | L1 |
| Same engine | `route both`: speaker and tach pin identical within 0.1% | L1 |
| Knob | `knob 1`: pitch tracks the ANGLE unit within one tick; a human revs the engine by hand | L1 |
| Greet once | Walk up: one chirp, then silence; no second greet for the same approach | L1 |
| Dead-man | Kill the host mid-`run`: tach output releases, face goes idle, on camera | L1 |
| Escape hatch | `repl` exits clean with outputs parked; redeploy with no hands | L1 |
| Wrong-sensor impersonation | `duty_pct 5`: a DUT that measures mark-space can tell | L1 |
| **The closer** | Xuss as fixture runs a sibling GCU's metal gate green. Same unit, same night | **L2** |

## 9. The build (for the agent that gets pointed here)

Silico is the harness: https://github.com/tig/silico. Read its AGENTS.md; the pip distribution is `tig-silico`. Work spec-first: this document is the contract; do not edit it, and carry an ambiguity log in the PR for every place it made you guess. The gates are `pytest -q`, `silico gate`, and `silico product-path`, and all three are part of done.

## 10. Open items

- [ ] Servo pan/tilt head (v2): earns its way in only if the face is not expressive enough on camera.
- [ ] Forcing-channel harness for DUT switch inputs (v2): needs the driver stage; the dead-man rail above already covers it.
- [ ] Current-sense day job (v2): AMeter Grove unit on Port A; report joules per duty cycle to the bench.
- [ ] Mic party trick (v3): Xuss hears the engine it impersonates.
