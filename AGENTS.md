# AGENTS.md

Guidance for AI coding agents working in **xuss**.

## What this repo is

A **GCU** (General Contact Unit — Silico’s term for one shippable edge product) built on the [silico](https://github.com/tig/silico) spine. Read silico’s `AGENTS.md` for first ship, plate, host gate, metal path, and operator manners. Package name is `tig-silico`; never bare `pip install silico`.

## How to work here

1. **Read `spec.md` first.** It is the product contract. Prefer clarifying with the operator (silico **spec interview mode** when thin or contradictory) over inventing domain moat.
2. **Stay in this checkout** when workspace mode is `gcu`. Do not scaffold a product into a silico package tree or invent a second repo.
3. **Manners tools are required**, not optional: `silico welcome`, `bedside ask` / `bedside step` (or same-contract host pickers), `silico doctor` / `wait-device` / `inspect` / `deploy`. Decline / exit 10 = halt writes.
4. After go, first ship means plate + host gate **and** hello metal (board talk + confirmed product face) — do not stop at host-only.
5. **Make it better than you found it:** when the path is rough, fix or file on `tig/silico` / `tig/bedside`. Do not soft-fork manners into a kinder local essay or leave recovery only in chat.
