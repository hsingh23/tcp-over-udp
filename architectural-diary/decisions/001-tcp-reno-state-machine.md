# 001 — TCP Reno state machine as static classes

- Date: 2013-11-15 (introduced in 71ef976; handlers made @staticmethod in b1989dd)
- Status: as-submitted (frozen)

## Context

The assignment (MP2.pdf) requires TCP-like congestion control over UDP:
slow start, congestion avoidance, and fast retransmit/recovery responding to
new ACKs, duplicate ACKs, and timeouts.

## Decision

Implement congestion control as an explicit state machine: three state
classes (`SlowStart`, `CongestionAvoidance`, `FastRecovery`) in TCPStates.py,
each with a single `next(event, window)` handler registered on a `State`
namespace. The sender produces `Event` namedtuples (`new_ack`, `dup_ack`,
`triple_ack`, `timeout`); the current state's handler mutates the shared
`Window` (cwnd, ssthresh, retransmissions, transmission) and returns the next
state. Handlers are `@staticmethod`s — states are stateless; all mutable
state lives in `Window`.

## Consequences

- Transition logic is readable and maps 1:1 to the textbook Reno diagram;
  every transition is logged to `state_logs/` for the analysis write-up.
- Window changes made through `update_cwnd()` are timestamped, which is what
  makes the cwnd-over-time plots possible.
- Handlers both decide *and* perform side effects (transmit, retransmit),
  so the states are hard to unit-test in isolation — acceptable for a
  two-week class project with no test suite.
- Every state repeats an identical timeout branch (copy-paste); noted as a
  known simplification.
