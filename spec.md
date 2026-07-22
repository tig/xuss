# Xuss Software Specification

**Rev 0.3, July 2026**

Xuss is a pocket companion for the M5Stack **M5GO IoT Starter Kit v2.7**. It boots with a short musical greeting, shows a living face on the screen, plays a full song on demand, and exposes a simple details screen for the sensors built into the M5GO core.

This document is the product contract. The first half is written for the person who owns the device. The second half is written for the implementer who must rebuild that experience (using [silico](https://github.com/tig/silico)) without guessing at product intent.

Host/board techniques (ESP32 DAC lifecycle, IPS color packing, large-asset deploy, M5GO power) live in silico knowledge — not as product moat here.

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

Press the **left button** (Button A) to cycle the look of the face and the side lights **when you are on the face (not playing music)**:

| Step | Name | What you see |
|---|---|---|
| 1 | Blue (default) | Bright blue face on a dark blue background; blue side lights |
| 2 | Orange | Warm orange face and sides on a dark orange-tinted background |
| 3 | Red | Red face and sides on a dark red background |
| 4 | Green | Green face and sides on a dark green background |
| 5 | Black | Black face on a **white** background; side lights **off** |

Press again after Black to return to Blue. The banner (hair) follows the color theme.

Hold does not fast-forward: one press, one step.

**While a song is playing**, the left button does **not** change colors. It **pauses** the music and brings you back to the face with the same theme as before.

### Music (middle button)

Xuss can play the full track **First** by Tig through the M5GO speaker.

| Action | What happens |
|---|---|
| Press **middle** (Button B) while idle | Playback starts from the beginning. The screen switches to a **Now Playing** view (music graphic plus the title **First by Tig**). The middle-button hint becomes a pause symbol. |
| Press **middle** while the song is playing | Playback **pauses** and remembers where you left off. The face (or Details, if that is where you came from) returns. The middle-button hint becomes a play symbol. |
| Press **middle** while paused | Playback **resumes** from the pause point (it does not restart). |
| Let the song finish | Playback stops at the end. It does **not** loop or auto-restart. Press middle again to play from the start. |

Notes:

- Sound quality is limited by the tiny speaker and the simple digital audio path. The boot riff and the full song use the same kind of sample audio (not a square-wave beeper tone for music).
- While the song is playing, the screen shows **Now Playing** (the idle face may stop winking and scrolling until you pause). That is normal.
- If you open **Details** (right button) while music is playing, Xuss **pauses first**, then shows Details.
- If you press **left** while music is playing, Xuss **pauses**, returns to the **face**, and does **not** change the color theme.

There is no volume knob on the front panel in this version. Volume is fixed at a comfortable desk level unless a technician changes it over the serial link (see the technical section).

### Details / sensors (right button)

Press the **right button** (Button C) to open the **Details** screen.

You will see:

- **Firmware name and version** at the top (for support and updates) — digits must be readable, not solid blocks
- **Built-in motion sensor** (accelerometer, gyroscope, and a temperature reading from that chip)
- **Front button states** (which of A / B / C are currently held)
- Other built-in board readings when available (for example free memory)

Numbers update about **ten times per second** so you can tilt the device and watch the motion values change. Labels stay put; only the numbers refresh.

| Control on Details | Effect |
|---|---|
| **Right button** (gear) again | Does nothing (you are already on Details) |
| **Left button** (color) | Leaves Details and returns to the face **without** changing the color theme |
| **Middle button** (play/pause) | Same music rules as on the face |

Details uses only sensors **inside** the M5GO core. Plug-in modules on the Grove ports are not part of this screen.

### Power on and off (battery)

Xuss uses the M5GO’s own power control. There is no separate Xuss power key.

While running **on battery** (USB unplugged):

- **Single-click** the red power button on the side to **turn the device on**.
- **Quick double-click** the red power button to **turn the device off**.

Long-press is not how this hardware powers down. If the unit is still warm after a double-click, try again with two short taps.

While **USB is plugged in**, the M5GO stays powered from the cable (and typically charges the battery). Unplug USB first if you want a true battery-style off.

Some M5GO / Core v2.7 units also have a small **hardware battery switch** on the bottom or back that fully isolates the pack (`0` = battery disconnected). Use that as a hard kill if you need the battery cut completely.

### Everyday use tips

- **Desk use**: leave it plugged into USB for all-day play, or run from battery and double-click the red button when you are done.
- **One thing at a time, simply**: play music, change colors, or browse Details. You do not need an app or a phone.
- **While music plays**: expect the Now Playing screen (not the winking face). Pause with middle, left (back to face, same color), or right (Details after pause).
- **Support identity**: the Details screen shows the firmware version. A technician can also read `fw_name` / `fw_version` over the USB serial link even while music is playing.

### Safety and care

- Indoor desk use only.
- Do not cover the speaker or press hard on the screen.
- Keep liquids away from the open ports.
- Use a quality USB cable and a normal computer or USB charger.

### What this version is not

This version of Xuss is a **friendly face and music demo** on the M5GO. It is not a phone, not a full media player with a playlist browser, and not a kit that requires soldering or extra modules. It is not an engine-speed or bench-instrument product.

---

## 1. Product intent (for implementers)

Rebuild the experience in the User's Manual on an M5GO v2.7, driven from this spec:

- Boot musical greeting from *First* (sample PCM)
- Idle face, time-based wink, scrolling hair banner
- Five color themes (including black/white)
- Full *First* play / pause / resume / no loop
- Now Playing UI while full-song audio is active (idle face may freeze)
- Details screen: firmware + built-in core sensors only
- Three front buttons with on-screen hints
- USB serial: identity + escape hatch + small commissioning params
- **Speaker path: sample PCM only** for this rev (no LEDC PWM on the speaker pin)

**Not product requirements for Rev 0.3** (do not reintroduce as the product):

- ANGLE-knob live RPM, PIR greet, edge/tach profiles (`sing` / `run`), Grove modules on Details, multi-track library

## 2. Readiness layers (definition of done)

| Layer | Proven when |
|---|---|
| **L0 (host)** | Face timing, theme cycle, song state machine, Details layout, and protocol parsing pass automated tests against a HAL double (no hardware required). |
| **L1 (metal)** | On a real M5GO: boot riff audible, face and banner visible, buttons match the manual, full song play/pause/resume works, Details shows live built-in sensors, escape hatch works **including while a song is playing**, identity on the link. |

Claims name their layer. Host green is never metal done. Self-report is not measurement for audio or display quality: an operator must see and hear the product face.

## 3. Hardware (fixed)

M5Stack **M5GO IoT Starter Kit v2.7**. No soldering. No required external units.

| Piece | Role |
|---|---|
| M5GO core (ESP32, flash, 2.0" 320×240 IPS, speaker, three front buttons, 6-axis IMU) | Face, audio, buttons, Details sensors |
| Ten side RGB LEDs | Theme-matched side light |
| Side red power button (+ battery base) | On/off on battery: single-click on, quick double-click off (M5GO / Core v2.7). USB power keeps the unit on. |

Use only **built-in** sensors on the Details screen (IMU on the internal bus, front buttons, and other core-only readings such as heap free). Do not depend on Port A/B/C modules for Rev 0.3 product behavior.

Power is **hardware-owned** by the M5GO power path (not an Xuss software feature). Product firmware must not fight the power button or require a long-press convention that this board does not implement.

**Speaker:** product audio is **unsigned 8-bit mono PCM** on the board speaker path. Do **not** drive LEDC PWM on the speaker pin in this revision (avoids destroying DAC sample quality for the rest of the boot; see silico `knowledge/esp32-audio.md`).

## 4. User-visible behavior (normative)

### 4.1 Boot

1. Emit the identity line on the USB serial link first (`fw_name=XUSS fw_version=…`).
2. Play the boot riff: a short excerpt of *First* (the asset is seconds ~7.5–10 of the track; 11,025 Hz unsigned 8-bit mono PCM). Playback may complete before the idle face loop is fully lively, but identity must not wait on the riff.
3. Enter the idle face with the default **blue** theme.

Boot riff end must not click or hard-cut into silence; ease out cleanly.

### 4.2 Idle face

- Eyes, smile, and theme colors on the IPS panel.
- Hair banner scrolls smoothly right → left with text **`Xuss; built with Silico`** (note the semicolon). Banner motion updates only the hair-bar region (not a full-panel redraw every step).
- Right-eye wink on a **time-based** ~10 s period (not "every N control ticks"). A wink **repaints only the affected eye** (open ↔ closed). It must not clear or redraw the whole screen, the other eye, the smile, the banner, or the button hints.
- Side LEDs match the active theme; **black** theme forces side LEDs fully off and uses a white background with black face features.
- Bottom of the panel shows persistent hints: **color** / play-or-pause glyph / gear glyph.

Face animation timing is wall-clock based, never "tick count" based. Prefer regional updates (eye, banner strip, value fields) over full-frame fills whenever only part of the picture changed.

**Glyph set:** every on-screen string the product shows (banner, labels, firmware version, sensor values) must render with a font that includes at least space, `0–9`, `+`, `-`, `.`, and the letters used in product copy. Missing glyphs that draw as solid blocks are a product defect.

### 4.3 Themes (Button A)

Cycle order is fixed:

`blue → orange → red → green → black → blue → …`

One edge per press (debounce). Themes retint face, hair bar, banner ink, and side LEDs together.

| Context | Button A |
|---|---|
| Face (not playing) | Next theme |
| Full-song **playing** (Now Playing) | **Pause**, restore **face**, **do not** advance theme |
| Details | Exit to face, **do not** advance theme |

### 4.4 Music (Button B)

Full-track asset: entire *First* at the same PCM format as the boot riff, **streamed from on-device storage** (not held entirely in RAM). Deploy must place the file on the device filesystem and **verify non-zero size**. If the file is missing or empty, refuse playback with a clear link status (and do not hang the UI).

State machine:

| State | Button B | Result |
|---|---|---|
| idle | press | start from byte 0; show Now Playing |
| playing | press | pause; keep resume offset; leave Now Playing |
| paused | press | resume from offset; show Now Playing |
| natural end | — | idle, offset 0, no auto-repeat |

Now Playing content: a clear "music is on" visual plus the title **First by Tig**. Idle face wink/banner may stop while Now Playing is up.

When not actively playing (paused, finished, or error), restore the previous non-playing UI (face or Details), not only after end-of-track.

`mute=1` (if set) blocks starting playback and reports a clear status; it does not crash the UI.

### 4.5 Details (Button C)

- From face (idle or paused): open Details immediately.
- From face while song is **playing**: **pause first**, then open Details.
- While Details is already visible: Button C is a **no-op**.
- Details shows firmware identity at the top and live built-in sensor values beneath.
- Sensor values refresh every **100 ms** (~10 Hz) as a **visual** rate. Labels and chrome are stable; only value fields update (partial screen update, not a full-panel flash every sample).
- Required readings when hardware is present: IMU acceleration, rotation rate, IMU temperature; front button levels; optional core extras (e.g. free memory) if cheap to obtain.

### 4.6 Button map (summary)

| Button | Face (idle/paused) | Playing (Now Playing) | Details |
|---|---|---|---|
| A (left) | Next theme | Pause → face, **no** theme change | Exit to face, no theme change |
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
5. **Link** — USB serial identity, commissioning params, and the escape hatch

### 5.2 Rules

1. **One scheduler, many jobs.** A single main loop (or equivalent cooperative scheduler) services the concerns above. Do not require an RTOS.
2. **No silent monopoly on long audio.** Full-song PCM must **yield often enough** to:
   - sample Button A (pause → face, no theme change), Button B (pause), and Button C (pause-then-Details);
   - **service the USB serial link** so `identity`, `repl`, and `reboot` work **while the song is playing** (not only after pause or end). Bounded intake/egress per yield is fine; multi-minute deafness to the link is not.
3. **UI honesty during music.** While full-song audio is active, the visible UI **may** switch to **Now Playing** and freeze idle wink/banner. That is product UI, not a crash. Returning to face or Details when not playing is mandatory (§4.4).
4. **Boot riff is special.** The short boot greeting may run as a one-shot near startup before the steady cooperative loop is fully spinning, provided identity is emitted first and the riff ends cleanly. Full-song rules (link service, A/B/C) apply to the long track, not necessarily to the few-second boot riff.
5. **Details sampling.** Refresh sensor values every **100 ms** (visual). Only value fields update; chrome stays put.
6. **Face motion is time-based.** Banner position and wink schedule derive from elapsed time, not from "how many loop iterations ran."
7. **Regional paints.** Wink → eye only. Banner scroll → hair bar only. Details numbers → value strips only. Full-screen clears are for mode changes (theme, enter/leave Details, Now Playing), not for routine animation.

### 5.3 Acceptance sketch for multi-tasking

| Check | Pass when |
|---|---|
| Pause while playing | Middle button pauses within a short, human-noticeable delay mid-track |
| A while playing | Left button pauses, shows face, theme index unchanged |
| Details while playing | Right button pauses and opens Details without requiring a reset |
| Link while playing | `identity` and `repl` succeed mid-track without requiring a prior pause |
| Idle life | With no song playing, wink and banner continue indefinitely |

## 6. Manners and rails

1. **Identity first.** Boot prints `fw_name` / `fw_version` before other chatter.
2. **Escape hatch from day one.** `repl` parks outputs and returns a usable MicroPython prompt; `reboot` parks and resets. A build without the door fails L1. Must work mid-song (§5.2).
3. **Serial is bounded.** Byte-budgeted intake and egress per service turn; malformed input fails closed with a short error; Ctrl-C on the link is data, not a forced interrupt, while the product owns the console.
4. **Self-report is not measurement.** "I think the DAC worked" is not L1. An operator hears the riff and sees the face.
5. **Hardware honesty.** Prefer measure-then-fix on this board (display color packing, speaker path, IMU address) over folklore. Promote reusable truths to silico knowledge.

## 7. Protocol and parameters (canonical allow-list)

ASCII line protocol on USB serial. **This is the complete product command surface for Rev 0.3.** Do not reintroduce instrument verbs as product requirements.

### 7.1 Required commands

| Command | Behavior |
|---|---|
| `identity` | Returns `fw_name=… fw_version=…` |
| `repl` | Escape hatch: park outputs, restore interrupt character, exit clean to MicroPython prompt |
| `reboot` | Park outputs, hard reset |

### 7.2 Optional commissioning

| Command / param | Behavior |
|---|---|
| `get` / `set` / `save` / `defaults` | Only if you persist commissioning state |
| `mute` | `0`/`1`; when `1`, blocks starting *First*; may survive `defaults` if you keep an exempt list |
| `volume` | Integer desk level if exposed; default is a comfortable fixed level |
| `telemetry_hz` | Optional; `0` = off |

### 7.3 Not product requirements

Do **not** require for Rev 0.3: `rpm`, `route`, `sing`, `run`, `stop` (as instrument), `knob`, `greet`, `ring_teeth`, named engine profiles, or ANGLE/PIR units.

Config persistence, if present, must fall back safely when the on-device image is torn or alien.

## 8. Acceptance (camera / operator)

| Row | Check | Layer |
|---|---|---|
| Boot riff | Greeting within ~2 s of power; identity line first; riff recognizable as *First*; clean ending | L1 |
| Face | Idle face, scrolling banner text correct, ~10 s wink visible | L1 |
| Themes | A cycles blue → orange → red → green → black → blue; sides match; black sides off / white bg | L1 |
| Play / pause / resume | B starts full track; B pauses mid-song; B resumes (not restart); end does not loop | L1 |
| Now Playing | While actively playing, screen shows title **First by Tig** | L1 |
| A while playing | A pauses and returns to face; theme index unchanged | L1 |
| Details | C opens sensor screen with firmware line (readable digits); values move when tilted; ~100 ms updates without full-screen flash | L1 |
| Wink paint | Idle wink changes only the right eye; rest of the face does not flash | L1 |
| Details while playing | C pauses music then shows Details | L1 |
| C on Details | Second C does nothing | L1 |
| A on Details | Returns to face without theme change | L1 |
| Link mid-song | `identity` works while track is playing; `repl` exits clean mid-song | L1 |
| Missing song file | Clear failure if full-track asset absent; UI remains usable | L1 |
| Escape hatch | After `repl`, redeploy possible without hardware gymnastics | L1 |
| PCM speaker path | Music is sample audio; product does not use PWM square wave on the speaker for *First* | L1 |
)
