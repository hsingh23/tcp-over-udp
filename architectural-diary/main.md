# Architectural diary — tcp-over-udp

Narrative record of how this project came to be, reconstructed in 2026-09-08
from the commit history (post-rewrite hashes), the code as submitted, and the
assignment spec (MP2.pdf). Written after the fact; the original developers
did not leave design notes.

## The project

A two-week university networking machine problem (November 2013): implement a
TCP-like reliable transfer protocol over raw UDP, with working congestion
control, measurable behavior, and a written analysis of the traces. Team:
Harsh Singh (hsingh23) and Ziqi Peng (peng20), with a README contribution
from Thomas Deegan (tadeegan) via PR #1.

## Narrative

1. **Skeleton first (71ef976, 2013-11-15).** The initial commit landed the
   whole shape at once: a sender built around a TCP state machine, a receiver
   with a loss-simulating `Decider`, the three Reno states as classes, and a
   util module for sockets/CLI/window bookkeeping. At this point it used a
   connected-socket style API and a coroutine-driven run loop — ideas that
   did not survive contact with UDP.
2. **Making UDP actually work (d447abc → e097b2d → 329b6fc).** The first
   refactor switched to `sendto`/`recvfrom` with explicit addresses and moved
   transmission into the `Window` class. Two rounds of bug-fixing followed:
   a `sendto` missing its address argument (TypeError), single-chunk file
   reads, and — the classic — sequence number 0 evaluating as falsy and
   stalling the window. The receiver's exit condition also had to be fixed
   (`break` only exits the inner `for`).
3. **Measurement (62944a2).** Jacobson/Karels RTT estimation replaced the
   fixed 1-second timeout, and every cwnd change and acked sequence number
   started being logged — the telemetry the analysis demanded.
4. **Collaboration and reassembly (b4d2831 → 8838945/0ef04a7 → ba3a1c0).**
   Ziqi added the receiver's `Reassemble` class (bounded out-of-order buffer,
   modular sequence numbers) on a parallel line; merges brought it together
   with Harsh's sender work. Integration fixed cumulative-ACK semantics
   (ACK the next expected sequence), fast-retransmit plumbing, and a bug
   appending `seq` instead of `data`.
5. **Observability and polish (b1989dd → cf4d0ab → 428f80e).** ACK counting,
   then throughput reporting, then a `--loss-file` option so experiments
   across loss scenarios write distinguishable artifacts into per-kind
   directories.
6. **The big correctness turn (189345b → 56dff25).** A deliberately
   checkpointed "broken" rewrite replaced linked-list bookkeeping with an
   `OrderedDict` of in-flight segments and cumulative ACK handling
   (`dup_ack` on the 2nd copy, `triple_ack` on the 3rd). The follow-up fixed
   duplicate-ACK counting so fast retransmit actually fired, and centralized
   all `dup_ack_count` mutation in `Window.add_ack`.
7. **Analysis and submission (5d25b6d, c1ef79b, 49d5610, 250770f).** An
   IPython notebook plotted trace/cwnd/state data across loss levels 0–2
   (after fixing swapped plot axes), with written conclusions for parts b
   and c. Final commits expanded the README, disabled ipdb breakpoints, and
   credited the authors.

## Decisions

Numbered decision records live in [decisions/](decisions/):

- [001 — TCP Reno state machine as static classes](decisions/001-tcp-reno-state-machine.md)
- [002 — Text segment format and mod-9000 sequence space](decisions/002-segment-format-and-sequence-space.md)
- [003 — Cumulative ACKs and duplicate-ACK detection in Window](decisions/003-cumulative-acks-and-dup-ack-detection.md)
- [004 — Jacobson/Karels RTT-based timeout estimation](decisions/004-jacobson-karels-rtt-timeouts.md)
- [005 — Deterministic receiver-side loss simulation](decisions/005-receiver-side-loss-simulation.md)
- [006 — Bounded out-of-order reassembly buffer](decisions/006-bounded-out-of-order-reassembly.md)
- [007 — Instrumentation-first: logs as first-class outputs](decisions/007-instrumentation-as-first-class-output.md)

## Trivia that survives in the tree

The receiver file is `reciever.py` (misspelled) and the retransmit helper is
`retansmit_missing_segment` (also misspelled) — both shipped to the grader
that way. `index.php` is empty on purpose (Heroku buildpack marker), and the
`Guardfile` documents a guard-gem dev loop that restarted the sender on every
`util.py` save.
