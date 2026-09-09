# 003 — Cumulative ACKs and duplicate-ACK detection in Window

- Date: 2013-11-16 → 2013-11-17 (evolved through ba3a1c0, 189345b, 56dff25)
- Status: as-submitted (frozen)

## Context

Fast retransmit needs the receiver to keep acknowledging while segments are
missing, and the sender to distinguish "new progress" from "repeated ACK".
The earliest implementation used a linked-list `SentList`/`SegmentCount` pair
and echo-style ACKs, which was buggy (the integration commit alone fixed five
defects) and made duplicate-ACK counting error-prone.

## Decision

- The receiver ACKs the sequence number of the **last in-order segment it
  holds** (`Reassemble.expecting()` — effectively cumulative). Out-of-order
  arrivals therefore repeat the last ACK, which is exactly the signal fast
  retransmit needs.
- The sender keeps in-flight segments in an `OrderedDict {seq: segment}` and
  classifies ACKs in exactly one place, `Window.add_ack`:
  - same key as last ACK → `dup_ack_count += 1`; the **2nd copy** emits
    `dup_ack`, the **3rd copy** emits `triple_ack` (classic "three
    duplicate ACKs" counting the original);
  - new key → reset the counter, emit `new_ack`, and drop every in-flight
    segment with `seq <= ack` (cumulative release).
- Fast retransmit sends only the single segment following the ACK number
  (`retansmit_missing_segment`), and all `dup_ack_count` mutation lives in
  `add_ack`, not in the state handlers.

## Consequences

- Clean Reno behavior: triple-dup-ACK → fast retransmit + fast recovery;
  new ACK in fast recovery deflates cwnd to ssthresh and exits.
- The intermediate state (189345b) was committed known-broken and fixed in
  the very next commit (56dff25) — the history honestly checkpoints a
  half-done refactor.
- One known wrinkle kept for simplicity: `add_ack` treats the ACK number as
  "everything ≤ N delivered", which requires loss to be confined to the
  receiver (the sender's own link is assumed lossless) — true for the MP's
  simulated-loss model.
