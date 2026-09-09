# 004 — Jacobson/Karels RTT-based timeout estimation

- Date: 2013-11-16 (62944a2)
- Status: as-submitted (frozen)

## Context

The MP requires adaptive retransmission timeouts rather than a fixed timer.
The initial skeleton used a constant 1-second timeout, which both wastes time
on fast links and fires spuriously — the analysis traces show early "timeout
storms" before this was tuned.

## Decision

Implement the textbook Jacobson/Karels estimator inside `Window`:

- Sample RTT only for the **oldest unacked segment**: `start_sample` records
  `(key, time)` when the first segment is sent; `update_estimate` consumes
  the sample when that key's first ACK arrives (`ack_count == 1`).
- `estimated_RTT = 0.875·estimated_RTT + 0.125·sample_RTT`
- `dev_RTT = 0.75·dev_RTT + 0.25·|sample_RTT − estimated_RTT|`
- `timeout_length = estimated_RTT + 4·dev_RTT` (initial 1.0 s, initial
  dev 0.1 s)
- The sender's `select()` blocks for exactly `timeout_length`, so the timer
  is re-armed with a fresh estimate on every loop iteration.

## Consequences

- Retransmissions track real network conditions; after the estimator warms
  up, spurious timeouts essentially vanish (visible in the trace analysis).
- Retransmitted segments are not re-sampled (Karn's algorithm falls out for
  free, because only the first ACK of a key updates the estimate).
- The timeout branch in every state resets cwnd to MSS and ssthresh to
  ⌈cwnd/2⌉ — the classic Reno response.
- Single in-flight sample window (only one key sampled at a time) keeps the
  estimator simple at the cost of slower convergence.
