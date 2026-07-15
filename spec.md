# Xuss Software Specification (draft)

**Rev 0.1, July 2026**

Xuss is a bench drone with two jobs. The day job: a test instrument that generates engine-speed edge trains, forces inputs, and measures current for sibling GCUs on the bench. The stage job: proof on camera that a spec plus silico produces a working device in about an hour. The trick that keeps the demo honest is that the voice *is* the instrument output: an engine-speed edge train is an audible square wave, and when Xuss sings it is demonstrably on-pitch per this spec's own edge-generator section.

This is a **requirements** document. It states outcomes, interfaces, and acceptance rows. It does not prescribe module layout or internal APIs.

## 1. Readiness layers (definition of done)

| Layer | Proven when |
|---|---|
| **L0 (host)** | Song/choreography compiler, edge math, protocol, and config store pass pytest against the HAL double. |
| **L1 (metal, self)** | Edge output frequency verified by external measurement (logic analyzer); pitch within tolerance on the speaker; escape hatch works; identity on the link. |
| **L2 (fixture)** | Xuss, as the bench fixture, runs a sibling GCU's metal gate end to end. Its vehicle is the bench. |

Claims name their layer. Host green is never fixture done.

**Nothing in this spec is TBD-by-measurement.** Xuss is the instrument, not the mystery; every default below is a choice, not a placeholder. (Its sibling GCUs are the other way around, which is the point of building it.)

## 2. Hardware (fixed)

M5Stack **M5GO IoT Starter Kit v2.7**. No soldering anywhere in the build.

| Piece | Role |
|---|---|
| M5GO core (ESP32, 16 MB flash, 2.0" 320x240 IPS, speaker, mic, three buttons, 6-axis IMU) | The drone: face, voice, buttons |
| Ten side RGB LEDs | The light show |
| Grove Port A (I2C) | Day-job sensors: current-sense unit (INA226 class) |
| Grove Port B (GPIO) | **Tach edge output to the DUT** (Grove pigtail) |
| Grove Port C (UART) | Reserved |
| ANGLE unit | **The throttle**: a human revs the simulated engine by hand |
| PIR unit | Presence: greet once when a human approaches |
| RGB / IR / ENV III / HUB units | Light show extension, spares, ambient garnish |

First firmware flash is esptool (ESP32, not UF2); afterward deploys are mpremote over USB CDC like every silico GCU.

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

- Boot: identity line first (`fw_name=XUSS fw_version=…`), then one greeting chirp, then silence until spoken to.
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
| Boot riff | Two seconds or less from power to greeting; identity line first | L1 |
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
