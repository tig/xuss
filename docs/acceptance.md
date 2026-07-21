# Acceptance tracker (Xuss)

Spec §8. Update when proven. Self-report is not measurement for pitch/frequency.

| Row | Layer | Status | Evidence |
|-----|-------|--------|----------|
| Boot riff | L1 | Implemented | Asset + DAC stream; operator ear check |
| On-pitch | L1 | Code ready | Needs frequency counter / LA |
| Same engine | L1 | Code ready | Needs dual measurement |
| Knob | L1 | Implemented | ANGLE G36; host test maps ADC |
| Greet once | L1 | Implemented | PIR G17; host test one-shot |
| Dead-man | L1 | Implemented | Host test + metal code |
| Escape hatch | L1 | Implemented | `repl` smoke on COM7 |
| Wrong-sensor | L1 | Implemented | `duty_pct` on tach PWM |
| The closer | L2 | Open | Run sibling GCU metal gate with Xuss as tach source |
