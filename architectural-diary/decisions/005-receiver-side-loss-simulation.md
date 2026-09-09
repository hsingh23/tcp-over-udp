# 005 — Deterministic receiver-side loss simulation

- Date: 2013-11-15 (71ef976), hardened in e91fc3b (int coercion)
- Status: as-submitted (frozen)

## Context

To exercise retransmission and congestion control repeatably, loss must be
controllable from an input file, not left to a real flaky network. The MP
specifies loss-model files, and the repo carries several (`0`, `1`, `2`, `5`,
`10`, `20`, and `*_bytes` variants used as transfer payloads/labels).

## Decision

A `Decider` class at the receiver gates every arriving segment through an
`is_valid()` predicate chosen by the first token of the loss file:

| Loss file | Mode | Behavior |
| --- | --- | --- |
| `0` | none | every segment accepted |
| `1 N` | periodic | drop every Nth **received** segment (`rsn % N == 0`) |
| `2 k1 k2 …` | explicit | drop the listed receive ordinals |

`rsn` counts segments as they arrive (before validity), so periodic loss
stays periodic even while the sender retransmits. Dropped segments are
silently discarded — no ACK is generated — which naturally produces the
duplicate-ACK stream fast retransmit consumes.

## Consequences

- Experiments are exactly reproducible; the notebook can compare loss levels
  0/1/2 with identical inputs.
- Loss semantics are "in the last hop before the receiver": ACKs are never
  lost and the sender's link is clean, matching the MP's model.
- Strategy pattern (binding `is_valid` to `yes`/`repeated`/`selected`) keeps
  the main receive loop free of loss logic — three lines decide a segment's
  fate.
