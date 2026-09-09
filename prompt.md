# One-shot recreation prompt — tcp-over-udp

Give this prompt to a coding agent with an empty directory to recreate this
project from scratch (Python 2.7, standard library only). It captures the
goal, full protocol specification, every design decision, a phased build
order, and acceptance criteria. Derived from the code as submitted
(November 2013) and the architectural diary.

---

## Goal

Implement a TCP-like reliable file-transfer protocol over UDP in user space,
including TCP Reno congestion control (slow start, congestion avoidance,
fast recovery), adaptive RTT-based retransmission timeouts, receiver-side
deterministic loss simulation, and out-of-order reassembly — plus the
instrumentation needed to graph the protocol's behavior. Two programs:
`sender.py` and `reciever.py` (note the intentional misspelling), with shared
helpers in `util.py` and state logic in `TCPStates.py`.

## Protocol specification

### Segment format (wire)
```
SEQ:<sequence_number>,LAST:<0|1>##<data>
```
- Payload per segment (MSS) = 100 bytes of file data.
- `LAST:1` on the final segment terminates the transfer.
- Sequence numbers are assigned mod **9000** on both ends.
- ACK messages are the ASCII decimal of the acknowledged sequence number.

### ACK semantics
- Receiver ACKs the last in-order sequence number it holds (cumulative);
  `expecting()` returns `current_sequence − 1` mod 9000 (8999 when 0).
- Sender classification (all in `Window.add_ack`):
  - ACK equals previous ACK → 2nd copy emits `dup_ack`, 3rd copy emits
    `triple_ack`;
  - new ACK → reset counter, emit `new_ack`, drop every in-flight segment
    with `seq <= ack`.
- The sender's link is assumed lossless; loss occurs only at the receiver.

### Congestion control (Reno state machine, TCPStates.py)
Constants: MSS=100.0 bytes, initial ssthresh=1000.0, max_cwnd=25 segments,
initial timeout 1.0 s.
- **SlowStart**: new_ack → cwnd += MSS; if cwnd ≥ ssthresh →
  CongestionAvoidance.
- **CongestionAvoidance**: new_ack → cwnd += MSS·round(MSS/cwnd, −1)
  (~MSS per RTT).
- **FastRecovery** (on triple_ack from any state): ssthresh = ⌈cwnd/2⌉,
  cwnd = ssthresh + 3·MSS, retransmit the missing segment; dup/triple ack →
  cwnd += MSS, stay; new_ack → cwnd = ssthresh, → CongestionAvoidance
  (and transmit as allowed).
- **Timeout** (any state): ssthresh = ⌈cwnd/2⌉, cwnd = MSS, dup_ack_count = 0,
  retransmit the segment after the last ACK, → SlowStart.
- Transmission rule: send new segments while `unused_capacity() =
  (cwnd − len(in_flight)·MSS)/MSS ≥ 1` (`transmit_as_allowed`).
- Retransmission target: the single segment at `(ack + 1) mod 9000` if still
  in flight (`retansmit_missing_segment` — misspelled on purpose).

### Timeout estimation (Jacobson/Karels, in Window)
- Sample the oldest unacked segment only; consume on that key's first ACK.
- `estimated_RTT = 0.875·est + 0.125·sample`
- `dev_RTT = 0.75·dev + 0.25·|sample − est|` (initial dev 0.1)
- `timeout_length = estimated_RTT + 4·dev_RTT`
- Sender main loop: `select([sock], [], [], timeout_length)`; empty read set
  → timeout event, else read ACK with `recvfrom` and dispatch.

### Receiver
- Bind UDP socket; read loss file; parse segments; gate each with `Decider`:
  - `0` → accept all;
  - `1 N` → drop every Nth received segment (count pre-validity arrivals);
  - `2 k1 k2 …` → drop the listed receive ordinals.
- Accepted segments go to `Reassemble`: if seq == current_sequence append and
  advance (mod 9000); else if seq > current and buffer ≤ 25 entries, stash;
  then drain buffer in sorted order while head == current_sequence.
- Reply with `expecting()` via `sendto` to the sender's address; stop after a
  valid `LAST:1` segment; write reassembled bytes to `check_file`.

### Instrumentation (all timestamps relative to run start)
- `cwnd_results/cwnd-<file><-lossfile>`: `time cwnd` on every change.
- `trace_results/trace-<file><-lossfile>`: `time acked_seq` on every new ACK.
- `state_logs/states-<file><-lossfile>`:
  `time,State,event,ack,dup_ack_count` on every transition.
- On completion print throughput = `ack_count·100·8 / elapsed` (bits/sec).

### CLI (getopt)
- sender: `-d/--domain`, `-p/--port`, `-f/--file`, `-l/--loss-file`
  (optional, defaults ""); loss file suffixes output names.
- receiver: `-p/--port`, `-f/--file` (the loss file).
- Missing required args → print usage and exit(2).

## Design decisions (all of them)

1. Python 2.7 standard library only; no packaging, no tests.
2. Stateless `@staticmethod` state handlers; all mutable state in `Window`.
3. Events are namedtuples: `new_ack`, `dup_ack`, `triple_ack`, `timeout`.
4. In-flight bookkeeping is an `OrderedDict {seq: segment}` (replaced an
   earlier buggy linked-list SentList).
5. Human-readable text segment format for debuggability; binary-unsafe
   framing accepted as a known limitation.
6. mod-9000 sequence space with window ≤ 25 makes wraparound unambiguous.
7. ACK = last in-order received (not next-expected); duplicates are the fast
   retransmit signal; ACK counting (2nd/3rd copy) lives only in `add_ack`.
8. Fast retransmit resends exactly one segment (ack+1 mod 9000).
9. Loss simulated at the receiver via a three-mode `Decider` strategy object;
   drops are silent (no ACK).
10. Reassembly buffer bounded at 25 entries, drained in sorted order.
11. Jacobson/Karels EWMA timeouts; only first-ACK samples counted
    (Karn's algorithm emerges naturally).
12. `select()` timeout doubles as the retransmission timer.
13. Logs are string buffers flushed to per-run files; `--loss-file` names
    experiments; throughput printed at exit.
14. `check_file` + `diff` is the correctness check.
15. IPython notebook (matplotlib) performs all analysis out-of-band; captured
    run artifacts are committed as evidence; empty `index.php` for Heroku.

## Phased build order

1. **Skeleton**: util.py (sockets, getopt parsing, SequenceCounter mod 9000),
   reciever.py (recvfrom loop, Decider), sender.py (chunkify file into
   100-byte chunks, flag last), TCPStates.py with the three states.
2. **Plumbing**: sender/receiver exchange datagrams; receiver parses
   `SEQ/LAST` headers and echoes ACKs; sender reads ACKs with recvfrom.
   Watch for: sendto needs an explicit address; sequence 0 is falsy — compare
   against None, never truthiness; receiver exit must be a loop flag, not a
   `break` inside `for`.
3. **State machine integration**: Window owns cwnd/ssthresh/in-flight dict;
   transmit_as_allowed on window opening; state transitions on events.
4. **ACK correctness**: cumulative release (`seq <= ack`), dup/triple
   classification, fast retransmit of the single missing segment, exit from
   FastRecovery on new_ack.
5. **RTT estimation + timeouts**: sampling, EWMAs, adaptive select timeout.
6. **Instrumentation**: trace/cwnd/state logs, per-run filenames via
   `--loss-file`, throughput print, check_file output.
7. **Analysis**: notebook loading the logs; plots of trace and cwnd for loss
   levels 0–2; written conclusions for slow start / fast recovery / timeout
   behavior; Part 1 diagram.

## Acceptance criteria

1. `python reciever.py -p <port> -f <lossfile>` then
   `python sender.py -d localhost -p <port> -f <file>` completes for loss
   modes 0, 1, and 2, and `diff check_file <file>` is empty in all cases.
2. With no loss, cwnd shows exponential-then-linear growth crossing the
   initial ssthresh (1000 bytes).
3. With loss, state_logs show triple-ack-triggered FastRecovery episodes and
   timeouts collapsing cwnd to MSS with ssthresh halved; cwnd plot shows the
   classic sawtooth.
4. After the RTT estimator warms up, spurious timeouts cease (timeout_length
   converges to est + 4·dev).
5. Trace/cwnd/state files exist per run and are named with the loss-file
   suffix; sender prints a positive integer throughput.
6. Transfer of a 1 MB file at ~100-byte segments completes in a few seconds
   on localhost with no loss (reference run: ~1.92 s).
7. No `set_trace`/debugger calls active in the shipped code.

---

*Recreation fidelity note: the original is Python 2 (print statements,
`iteritems`, `xrange`). Recreating under Python 3 is acceptable if the
protocol constants and observable behavior above are preserved.*
