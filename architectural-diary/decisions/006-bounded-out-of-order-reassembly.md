# 006 — Bounded out-of-order reassembly buffer

- Date: 2013-11-16 (b4d2831 by ziqi; integrated and debugged in ba3a1c0)
- Status: as-submitted (frozen)

## Context

UDP delivers datagrams out of order. Once the sender's window exceeds one
segment, the receiver must buffer arrivals that are ahead of the gap it is
waiting for, deliver data in order, and know what to ACK. The buffer also has
to be bounded, since the sequence space wraps (mod 9000) and memory is not.

## Decision

The `Reassemble` class in reciever.py:

- keeps `current_sequence` (next expected, mod 9000) and a `result` string;
- on `add(seq, data)`: if `seq == current_sequence`, append data and advance;
  else if `seq > current_sequence` and the buffer holds ≤ 25 entries, stash
  it keyed by sequence number;
- after every add, drains the buffer in **sorted key order** while the head
  equals `current_sequence`, appending and advancing;
- returns `expecting()` — the sequence number to ACK — which is
  `current_sequence − 1` mod 9000 (with 8999 when current is 0).

## Consequences

- Cumulative ACK semantics fall out naturally: repeats of the last ACK mean
  "still missing the segment after me".
- Buffer cap 25 mirrors the sender's max_cwnd, so the receiver can always
  absorb a full window of out-of-order data; beyond that, ahead-of-gap
  segments are dropped and must be retransmitted.
- One bug from the original contribution (appending `seq` instead of `data`
  in the in-order branch) survived until integration (fixed in ba3a1c0) — a
  good example of why the `diff check_file <original>` verification step
  exists.
- In-order delivery via a growing Python string is O(n²) in the worst case;
  irrelevant at 1 MB / 100-byte chunks in 2013.
