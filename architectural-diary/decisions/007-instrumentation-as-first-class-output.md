# 007 — Instrumentation as first-class output

- Date: 2013-11-16 → 2013-11-17 (62944a2, 26aee20, b1989dd, cf4d0ab)
- Status: as-submitted (frozen)

## Context

Half of the assignment grade is the *analysis*: graphs of the trace and
congestion window, plus written interpretation of slow start, fast recovery,
and timeout behavior. That means the transfer program must emit its own
telemetry as a core feature, not an afterthought.

## Decision

Every meaningful event writes a timestamped sample (relative to
`window.start_time`):

- all cwnd mutations go through `Window.update_cwnd`, appending
  `time cwnd` lines → `cwnd_results/cwnd-<file><-lossfile>`;
- every new ACK appends `time acked_seq` lines →
  `trace_results/trace-<file><-lossfile>`;
- every state transition appends
  `time,State,event,ack,dup_ack_count` lines →
  `state_logs/states-<file><-lossfile>`;
- the `--loss-file` CLI option names each run's artifacts so multiple loss
  scenarios coexist (`-0`, `-1`, `-2` suffixes);
- at completion the sender prints throughput = `ack_count · 100 · 8 /
  elapsed` (an integer bits-per-second figure);
- the receiver writes the reassembled stream to `check_file` so
  `diff check_file <input>` verifies end-to-end correctness.

Analysis happens out-of-band in an IPython notebook (`Analysis.ipynb`,
exported to `Analysis.html`) that loads these files and plots them; part-1
diagram in `part-1.png`.

## Consequences

- The graded deliverables (plots, conclusions for parts a–c) are direct
  functions of the logs, and any re-run regenerates everything.
- Committing captured run outputs (trace/cwnd/state files, check_file) was
  deliberate: they are the evidence behind the notebook figures, frozen at
  submission time.
- Heroku deployment of the write-up is enabled by an empty `index.php`
  (buildpack detection) — hosting the analysis was an actual goal.
- Cost: string-concatenated log buffers and file-per-run proliferation in
  the repo root (later organized into per-kind directories).
