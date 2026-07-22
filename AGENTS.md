# AGENTS.md

Guidance for AI coding agents working in **xuss**.

## What this repo is

A GCU (one shippable edge device) built on the [silico](https://github.com/tig/silico) spine. Read silico's AGENTS.md for the harness, the Day 1 playbook, and the plate.

## How to work here

1. **Read `spec.md` first and take it literally.** It is the contract. Do not edit it; if you believe it is wrong, say so in your PR instead.
2. Work on a branch, PR to `main`, do not merge. The PR body carries an **ambiguity log**: every place the spec was silent or ambiguous, and the choice you made.
3. The gates are `pytest -q`, `silico gate`, and `silico product-path`. All three are part of done.
4. Ground in part truth before writing hardware-facing code: `silico parts --fetch` pulls local copies of the pointers in `parts.toml`. Never commit fetched documents.
5. Hardware honesty: claim readiness per spec §1. Self-report is not measurement (§6 rail 4).
6. First flash on this board is esptool (ESP32); afterward, mpremote like every GCU. The escape hatch (`repl`/`reboot`) is required from day one; a build without the door fails L1.

## Improve silico as you go
 
Part of your job in this repo is to **make silico better for the next agent**, not only to ship Grady.
 
Whenever you spend tokens (or wall-clock) recovering from something that a better silico default, doc, error message, plate, CLI flag, or knowledge note would have prevented:
 
1. **Notice the friction** — wrong port heuristics, missing first-flash recipe, demoted CH340 on a product that *is* CH340, opaque deploy/inspect failures, Windows-only footguns, stale pin guidance, etc.
2. **Search for duplicates first** on [tig/silico issues](https://github.com/tig/silico/issues) (open and recently closed).
3. If none fits, **file a new issue** against `tig/silico` with: what you were doing, what went wrong, recovery path, and a concrete proposed change (doc, code, plate, or knowledge note). Prefer an upstream fix PR when you have access and the change is small and reusable.
4. Do **not** soft-fork silico manners into a kinder local essay, invent a parallel host spine in grady, or leave recovery only in chat.
 
Leaving tribal recovery in chat only violates **Make it better than you found it** (silico tenets / AGENTS).
