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
