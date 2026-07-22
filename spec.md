# Xuss Software Specification

**Rev 0.3, July 2026**

Xuss is a pocket companion for the M5Stack **M5GO IoT Starter Kit v2.7**. It boots with a short musical greeting, shows a living face on the screen, plays a full song on demand, and exposes a simple details screen for the sensors built into the M5GO core.

This document is the product contract. The first half is written for the person who owns the device. The second half is written for the implementer who must rebuild that experience (using [silico](https://github.com/tig/silico)) without guessing at product intent.

---

## Working Backwards Artifact: Xuss User's Manual

### Welcome

Thank you for powering on Xuss.

Xuss is a small desk toy that lives on your M5GO. It smiles, winks, changes colors, plays music, and can show a live look at its built-in sensors. It is intentionally simple: three front buttons do almost everything.

Because Xuss runs on a tiny microcontroller, the music is low-fidelity (think classic handheld gadget, not studio speakers). That is normal.

### What's in the box (what you need)

- An **M5Stack M5GO IoT Starter Kit v2.7** (the core unit with screen, speaker, three front buttons, and side LED strips)
- USB power (the cable that came with your M5GO)
- Xuss software already loaded on the device

No extra modules, knobs, or sensors are required for the features in this manual. Xuss uses only what is built into the M5GO core.

### First power-on

1. Plug the M5GO into USB power.
2. Within about two seconds you should hear a short musical riff. That riff is a slice of the song **First** by Tig (a few seconds from the middle of the track).
3. After the riff, Xuss shows its face and waits.

If you hear nothing and see nothing, check the USB cable and power. If the face appears but sound is missing, try another cable or port; the speaker needs a healthy USB supply.

### The face (home screen)

When Xuss is idle, the screen shows:

- A **smiley face** (eyes and a simple smile)
- A **scrolling banner** along the top of the screen (the "hair"), reading:

  > Xuss; built with Silico

- Soft **button hints** along the bottom of the screen, above the physical buttons:
  - Left: **color**
  - Middle: **play** / **pause** symbol
  - Right: **gear** symbol

The side LED strips light in the same color family as the face.

Every **ten seconds**, the right eye gives a short wink.

### Colors (left button)

Press the **left button** (Button A) to cycle the look of the face and the side lights:

| Step | Name | What you see |
|---|---|---|
| 1 | Blue (default) | Bright blue face on a dark blue background; blue side lights |
| 2 | Orange | Warm orange face and sides on a dark orange-tinted background |
| 3 | Red | Red face and sides on a dark red background |
| 4 | Green | Green face and sides on a dark green background |
| 5 | Black | Black face on a **white** background; side lights **off** |

Press again after Black to return to Blue. The banner (hair) follows the color theme.

Hold does not fast-forward: one press, one step.

### Music (middle button)

Xuss can play the full track **First** by Tig through the M5GO speaker.

| Action | What happens |
|---|---|
| Press **middle** (Button B) while idle | Playback starts from the beginning. The screen switches to a **Now Playing** view (music graphic plus the title **First by Tig**). The middle-button hint becomes a pause symbol. |
| Press **middle** while the song is playing | Playback **pauses** and remembers where you left off. The face (or the screen you were on) returns. The middle-button hint becomes a play symbol. |
| Press **middle** while paused | Playback **resumes** from the pause point (it does not restart). |
| Let the song finish | Playback stops at the end. It does **not** loop or auto-restart. Press middle again to play from the start. |

Notes:

- Sound quality is limited by the tiny speaker and the simple digital audio path. The boot riff and the full song use the same kind of audio.
- While the song is playing, Xuss focuses on music and the Now Playing screen. Pause (middle) or open Details (right) when you want the face or the sensor screen back.
- If you open **Details** (right button) while music is playing, Xuss **pauses first**, then shows Details.

There is no volume knob on the front panel in this version. Volume is fixed at a comfortable desk level unless a technician changes it over the serial link (see the technical section).

### Details / sensors (right button)

Press the **right button** (Button C) to open the **Details** screen.

You will see:

- **Firmware name and version** at the top (for support and updates)
- **Built-in motion sensor** (accelerometer, gyroscope, and a temperature reading from that chip)
- **Front button states** (which of A / B / C are currently held)
- Other built-in board readings when available (for example free memory)

Numbers update about **twice per second** so you can tilt the device and watch the motion values change. Labels stay put; only the numbers refresh.

| Control on Details | Effect |
|---|---|
| **Right button** (gear) again | Does nothing (you are already on Details) |
| **Left button** (color) | Leaves Details and returns to the face **without** changing the color theme |
| **Middle button** (play/pause) | Same music rules as on the face |

Details uses only sensors **inside** the M5GO core. Plug-in modules on the Grove ports are not part of this screen.

### Everyday use tips

- **Power**: leave it plugged in on a desk, or unplug when you are done. There is no separate power button on Xuss itself beyond the M5GO hardware.
- **One thing at a time, simply**: play music, change colors, or browse Details. You do not need an app or a phone.
- **If the face freezes while a long song plays**: press middle to pause, or right to open Details (which also pauses). That is expected in this product model while full-song audio is active.
- **Support identity**: the Details screen shows the firmware version. A technician can also read `fw_name` / `fw_version` over the USB serial link.

### Safety and care

- Indoor desk use only.
- Do not cover the speaker or press hard on the screen.
- Keep liquids away from the open ports.
- Use a quality USB cable and a normal computer or USB charger.

### What this version is not

This version of Xuss is a **friendly face and music demo** on the M5GO. It is not a phone, not a full media player with a playlist browser, and not a kit that requires soldering or extra modules.

---

## 1. Product intent (for implementers)

Rebuild the experience in the User's Manual on an M5GO v2.7, driven from this spec.

| In scope | Out of scope (abandoned for this product) |
|---|---|
| Boot musical greeting from *First* | Live ANGLE-knob RPM control |
| Idle face, wink, scrolling hair banner | PIR "greet once" presence chirps |
| Five color themes (including black/white) | Grove modules on the Details screen |
| Full *First* play / pause / resume / no loop | Auto-repeating music |
| Now Playing UI while full-song audio is active | Multi-track library / file browser |
| Details screen: firmware + built-in core sensors | Servo head, mic tricks, fixture/L2 bench drone role |
| Three front buttons with on-screen hints | External DUT tach training as a user feature |
| USB serial identity + escape hatch for development | |

Former "bench instrument" verbs (edge RPM profiles, tach impersonation, knob, greet) are **not** product requirements for Rev 0.3. Do not resurrect them unless a later rev of this document says so.

## 2. Readiness layers (definition of done)

| Layer | Proven when |
|---|---|
| **L0 (host)** | Face timing, theme cycle, song state machine, gear layout, and protocol parsing pass automated tests against a HAL double (no hardware required). |
| **L1 (metal)** | On a real M5GO: boot riff audible, face and banner visible, buttons match the manual, full song play/pause/resume works, Details shows live built-in sensors, escape hatch works, identity on the link. |

Claims name their layer. Host green is never metal done. Self-report is not measurement for audio or display quality: an operator must see and hear the product face.

## 3. Hardware (fixed)

M5Stack **M5GO IoT Starter Kit v2.7**. No soldering. No required external units.

| Piece | Role |
|---|---|
| M5GO core (ESP32, flash, 2.0" 320×240 IPS, speaker, three front buttons, 6-axis IMU) | Face, audio, buttons, Details sensors |
| Ten side RGB LEDs | Theme-matched side light |

Use only **built-in** sensors on the Details screen (IMU on the internal bus, front buttons, and other core-only readings such as heap free). Do not depend on Port A/B/C modules for Rev 0.3 product behavior.

## 4. User-visible behavior (normative)

### 4.1 Boot

1. Emit the identity line on the USB serial link first (`fw_name=XUSS fw_version=…`).
2. Play the boot riff: a short excerpt of *First* (the asset is seconds ~7.5–10 of the track; 11,025 Hz unsigned 8-bit mono PCM). Playback may complete before the idle face loop is fully lively, but identity must not wait on the riff.
3. Enter the idle face with the default **blue** theme.

Boot riff end must not click or hard-cut into silence; ease out cleanly.

### 4.2 Idle face

- Eyes, smile, and theme colors on the IPS panel.
- Hair banner scrolls smoothly right → left with text **`Xuss; built with Silico`** (note the semicolon).
- Right-eye wink on a **time-based** ~10 s period (not "every N control ticks").
- Side LEDs match the active theme; **black** theme forces side LEDs fully off and uses a white background with black face features.
- Bottom of the panel shows persistent hints: **color** / play-or-pause glyph / gear glyph.

Face animation timing is wall-clock based, never "tick count" based.

### 4.3 Themes (Button A)

Cycle order is fixed:

`blue → orange → red → green → black → blue → …`

One edge per press (debounce). Themes retint face, hair bar, banner ink, and side LEDs together.

On the Details screen, Button A **exits to the face** and must **not** advance the theme.

### 4.4 Music (Button B)

Full-track asset: entire *First* at the same PCM format as the boot riff, streamed from on-device storage (not held entirely in RAM).

State machine:

| State | Button B | Result |
|---|---|---|
| idle | press | start from byte 0; show Now Playing |
| playing | press | pause; keep resume offset; leave Now Playing |
| paused | press | resume from offset; show Now Playing |
| natural end | — | idle, offset 0, no auto-repeat |

Now Playing content: a clear "music is on" visual plus the title **First by Tig**.

When not actively playing (paused, finished, or error), restore the previous non-playing UI (face or Details), not only after end-of-track.

Mute (if exposed on the serial parameter table) blocks starting playback and reports a clear status; it does not crash the UI.

### 4.5 Details (Button C)

- From face (idle or paused): open Details immediately.
- From face while song is **playing**: **pause first**, then open Details.
- While Details is already visible: Button C is a **no-op**.
- Details shows firmware identity at the top and live built-in sensor values beneath.
- Sensor values refresh on the order of **500 ms**. Labels and chrome are stable; only value fields update (partial screen update, not a full-panel flash every sample).
- Required readings when hardware is present: IMU acceleration, rotation rate, IMU temperature; front button levels; optional core extras (e.g. free memory) if cheap to obtain.

### 4.6 Button map (summary)

| Button | Face | Playing | Details |
|---|---|---|---|
| A (left) | Next theme | (unreachable while audio owns the loop unless multi-tasking yields; see §5) | Exit to face, no theme change |
| B (middle) | Play / resume | Pause | Play / pause / resume (same rules) |
| C (right) | Open Details | Pause, then Details | No-op |

## 5. Simple multi-tasking model (normative)

Xuss is a single-core, cooperative product. There is no requirement for a preemptive RTOS. There **is** a requirement for a clear, honest task model so implementers do not invent hidden threads or freeze the device forever inside one concern.

### 5.1 Concurrent concerns

The product simultaneously owns these concerns:

1. **UI / face** — theme, wink, banner motion, Now Playing, Details chrome
2. **Input** — debounced front buttons
3. **Audio** — boot riff and full-song PCM to the speaker
4. **Sensors** — Details sampling when that screen is active
5. **Link** — USB serial identity, configuration, and the escape hatch

### 5.2 Rules

1. **One scheduler, many jobs.** A single main loop (or equivalent cooperative scheduler) services the concerns above. Do not require an RTOS.
2. **No silent monopoly.** A long job (especially full-song PCM) must **yield often enough** to:
   - sample Button B (pause) and Button C (pause-then-Details);
   - keep the play/pause affordance honest;
   - accept the escape-hatch commands on the link within a human-reasonable time, or document a short, bounded window if audio temporarily defers serial.
3. **UI honesty during music.** While full-song audio is active, the visible UI may switch to **Now Playing** (that is product UI, not a crash). The idle face is allowed to pause its wink/banner during that presentation. Returning to face or Details when not playing is mandatory (§4.4).
4. **Boot riff is special.** The short boot greeting may run as a one-shot near startup before the steady cooperative loop is fully spinning, provided identity is emitted first and the riff ends cleanly.
5. **Details sampling is low rate.** About 2 Hz is enough. Prefer partial updates for changing values so the panel does not full-refresh every sample.
6. **Face motion is time-based.** Banner position and wink schedule derive from elapsed time, not from "how many loop iterations ran," so multi-tasking load does not change the look of the character more than briefly.

### 5.3 Acceptance sketch for multi-tasking

| Check | Pass when |
|---|---|
| Pause while playing | Middle button pauses within a short, human-noticeable delay mid-track |
| Details while playing | Right button pauses and opens Details without requiring a reset |
| Escape hatch | `repl` / `reboot` remain reachable from the product link without reflashing |
| Idle life | With no song playing, wink and banner continue indefinitely |

## 6. Manners and rails

1. **Identity first.** Boot prints `fw_name` / `fw_version` before other chatter.
2. **Escape hatch from day one.** `repl` parks outputs and returns a usable MicroPython prompt; `reboot` parks and resets. A build without the door fails L1.
3. **Serial is bounded.** Byte-budgeted intake and egress per service turn; malformed input fails closed with a short error; Ctrl-C on the link is data, not a forced interrupt, while the product owns the console.
4. **Self-report is not measurement.** "I think the DAC worked" is not L1. An operator hears the riff and sees the face.
5. **Hardware honesty.** Prefer measure-then-fix on this board (display color packing, speaker path, IMU address) over folklore.

## 7. Protocol and parameters (high level)

ASCII line protocol on USB serial, same family as other silico GCUs: at least `identity`, `get` / `set` / `save` / `defaults`, `repl`, `reboot`.

Keep a small parameter table for commissioning (volume, mute, telemetry rate, and similar). Exact keys may match an existing implementation, but product behavior in §4 does not depend on a large instrument map.

| Expectation | Notes |
|---|---|
| `identity` | Returns firmware name and version |
| `mute` | When set, blocks starting *First*; survives naive "reset everything" if you keep a commissioning-exempt list |
| `repl` / `reboot` | Escape hatch (§6) |

Config persistence, if present, must fall back safely when the on-device image is torn or alien.

## 8. Acceptance (camera / operator)

| Row | Check | Layer |
|---|---|---|
| Boot riff | Greeting within ~2 s of power; identity line first; riff recognizable as *First*; clean ending | L1 |
| Face | Idle face, scrolling banner text correct, ~10 s wink visible | L1 |
| Themes | A cycles blue → orange → red → green → black → blue; sides match; black sides off / white bg | L1 |
| Play / pause / resume | B starts full track; B pauses mid-song; B resumes (not restart); end does not loop | L1 |
| Now Playing | While actively playing, screen shows title **First by Tig** | L1 |
| Details | C opens sensor screen with firmware line; values move when device is tilted; ~0.5 s updates without full-screen flash | L1 |
| Details while playing | C pauses music then shows Details | L1 |
| C on Details | Second C does nothing | L1 |
| A on Details | Returns to face without theme change | L1 |
| Escape hatch | `repl` exits clean; redeploy possible without hardware gymnastics | L1 |

## 9. The build (for the agent that gets pointed here)

Silico is the harness: https://github.com/tig/silico. Read its `AGENTS.md`; the pip distribution is `tig-silico` (never bare `pip install silico`).

Work **spec-first**: this document is the contract. Do not edit the spec to match a convenient implementation; if the spec is wrong, say so in the PR. Carry an **ambiguity log** in the PR for every place this document forced a guess.

Gates that are part of done: `pytest -q`, `silico gate`, and `silico product-path`, plus metal operator checks from §8.

Implementation detail (DAC reuse, LCD endian, font bitmaps, partial blit strategy, file names on the device filesystem) is deliberately **not** prescribed here. Choose durable approaches; measure on the M5GO when the board disagrees with theory.

## 10. Open items

- [ ] Richer multi-tasking: keep the idle face animating *during* full-song audio (Now Playing becomes optional, not mandatory).
- [ ] Front-panel or serial volume control exposed as a first-class user feature.
- [ ] Optional higher-quality audio path if the board allows without harming boot reliability.
- [ ] Playlist / multiple tracks (only if the single-track story stays obvious).
- [ ] Servo pan/tilt head (v2): only if the face is not expressive enough on camera.
)
