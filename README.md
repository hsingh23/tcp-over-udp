# tcp-over-udp

A TCP-like reliable-transfer protocol implemented on top of UDP, built as a
university computer-networking course machine problem (the assignment spec is
in [`MP2.pdf`](MP2.pdf)). Created by Harsh Singh (hsingh23) and Ziqi Peng
(peng20) in November 2013.

> **Archived / legacy project.** This is a finished class assignment written
> in **Python 2** (print statements, `iteritems`, `xrange`). It will not run
> unmodified on Python 3. It is preserved as submitted; see
> [AGENTS.md](AGENTS.md) if you plan to touch anything.

## What and why

UDP gives you datagrams with no reliability: packets can be lost, duplicated,
or arrive out of order. This project implements the mechanisms TCP uses to
recover that reliability — sequence numbers, cumulative acknowledgements,
retransmission on timeout and on triple duplicate ACK, and the **TCP Reno
congestion-control state machine** (slow start, congestion avoidance, fast
recovery) with Jacobson/Karels RTT-based timeout estimation — entirely in
user space over a UDP socket.

The sender transfers a file in 100-byte segments and logs enough telemetry
(trace of acked sequence numbers, congestion-window size over time, and the
state-machine transitions) to graph its own congestion behavior. The receiver
optionally simulates packet loss according to a loss-pattern file, so the
protocol's recovery mechanisms can be exercised deterministically. The
resulting plots and write-ups live in `Analysis.ipynb` / `Analysis.html` and
`part-1.png`.

## Protocol design

- **Segment format** — human-readable text:
  `SEQ:<sequence_number>,LAST:<0|1>##<data>`, where `LAST:1` marks the final
  segment of the transfer. Data payload per segment (MSS) is **100 bytes**.
- **Sequence space** — sequence numbers are taken **modulo 9000** by both
  sender and receiver (`SequenceCounter`, `Reassemble`).
- **ACKs** — the receiver ACKs the highest in-order sequence number it has
  (`Reassemble.expecting()`); ACKs are cumulative. The sender drops all
  in-flight segments with sequence ≤ ACK and counts repeats: the 2nd copy of
  an ACK is a `dup_ack`, the 3rd is a `triple_ack`.
- **Congestion control (TCP Reno)** — implemented as a state machine in
  `TCPStates.py` with three states:
  - **Slow start**: cwnd += MSS per new ACK; transition to congestion
    avoidance when cwnd ≥ ssthresh (initial ssthresh 1000 bytes; cwnd capped
    at 25·MSS).
  - **Congestion avoidance**: cwnd grows by roughly MSS per RTT
    (`cwnd += MSS·round(MSS/cwnd, -1)`).
  - **Fast recovery**: entered on triple duplicate ACK — ssthresh = ⌈cwnd/2⌉,
    cwnd = ssthresh + 3·MSS, retransmit the missing segment; exit to
    congestion avoidance with cwnd = ssthresh on the next new ACK.
  - **Timeout** in any state: ssthresh = ⌈cwnd/2⌉, cwnd = MSS, retransmit,
    back to slow start.
- **Timeout estimation** — Jacobson/Karels: `estimated_RTT = 0.875·est +
  0.125·sample`, `dev_RTT = 0.75·dev + 0.25·|sample − est|`,
  `timeout_length = estimated_RTT + 4·dev_RTT` (initial timeout 1.0 s). The
  sender's `select()` uses this timeout to detect loss.
- **Receiver-side loss simulation** — the `Decider` in `reciever.py` reads a
  loss file with three modes:
  - `0` — no loss;
  - `1 N` — drop every Nth received segment;
  - `2 k1 k2 …` — drop the listed received-sequence ordinals.
- **Reassembly** — the receiver buffers out-of-order segments in a bounded
  (25-entry) buffer, appends in-order data to the result, and drains the
  buffer in sorted order as gaps fill. The reassembled file is written to
  `check_file`.

## Features

- Reliable file transfer over UDP with duplicate-ACK and timeout retransmission
- Full Reno congestion control with per-event state logging
- RTT estimation with adaptive retransmission timeout
- Deterministic receiver-side loss injection for experiments
- Trace / cwnd / state-log instrumentation and an IPython notebook analysis of
  the runs (including graphs for parts a–c of the assignment)
- End-of-run throughput report (bits per second)

## Stack

- **Python 2.7** (standard library only: `socket`, `select`, `getopt`,
  `collections`, `math`, `time`)
- IPython notebook + matplotlib for the analysis (`Analysis.ipynb`)
- `Guardfile` for guard-gem auto-restart during development
- Empty `index.php` for Heroku PHP-buildpack detection (hosting the write-up)

## Running

Start the receiver first (it binds the UDP port and loads the loss file),
then the sender. Example (as documented in 2013):

```sh
# receiver: port 9200, loss file "1" (drop every 1st segment? see modes above)
python reciever.py -p 9200 -f 1

# sender: send file 10000_bytes to localhost:9200, tag outputs with loss file
python sender.py -d localhost -p 9200 -f 10000_bytes -l 1
```

Both scripts accept long options (`--domain`, `--port`, `--file`,
`--loss-file`). Note the historical misspelling: the receiver script is
`reciever.py`.

Outputs created by a sender run:

| Path | Contents |
| --- | --- |
| `trace_results/trace-<file><-lossfile>` | `time acked_sequence` samples |
| `cwnd_results/cwnd-<file><-lossfile>` | `time cwnd` samples |
| `state_logs/states-<file><-lossfile>` | `time,State,event,ack,dup_ack_count` transitions |
| `check_file` | the receiver's reassembled output |

Verify correctness with `diff check_file <sent-file>` (e.g.
`diff check_file 10000_bytes`). The sender prints throughput in bits/sec at
the end. **Requires Python 2.**

## Repository structure

```
sender.py       sender: TCPStateMachine + Window driving the protocol
reciever.py     receiver: Decider (loss) + Reassemble (reordering)  [sic]
TCPStates.py    SlowStart / CongestionAvoidance / FastRecovery states
util.py         sockets, CLI parsing, SequenceCounter, Window
MP2.pdf         assignment specification
Analysis.ipynb  notebook analysis of the runs (also exported to Analysis.html)
part-1.png      Part 1 diagram
0 1 2 5 10 20   small loss-pattern files (mode 0/1/2 formats)
*_bytes         transfer payloads and loss patterns for 1KB/10KB/100KB/1MB runs
trace_results/  cwnd_results/  state_logs/   captured experiment outputs
Guardfile       guard-gem auto-restart rules (dev-time)
index.php       empty; Heroku buildpack marker
```

## Environment variables

None. The programs read no environment variables; all configuration is via
CLI flags.

## Further reading

- [CHANGELOG.md](CHANGELOG.md) — every commit, newest first
- [AGENTS.md](AGENTS.md) — how to work on this repo (agent guide)
- [architectural-diary/](architectural-diary/) — protocol and design decisions
- [prompt.md](prompt.md) — one-shot prompt that recreates this project from scratch
