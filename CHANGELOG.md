# Changelog

All notable changes to this repository, newest first.

> **History-rewrite note (2026-09-08):** commit messages in this repository were
> rewritten (messages only — every tree and file is byte-for-byte unchanged) to
> replace informal checkpoint messages ("time to test", "broken", "all is well")
> with conventional-commit messages that describe what each change actually
> does. All commit hashes changed as a result; the log below lists the
> **post-rewrite** hashes. Three merge commits kept their standard git merge
> messages. A pre-rewrite snapshot of `master` exists locally on branch
> `backup/pre-docs-20260908`.

## 2013-11-17

### 71089a3 — docs: add authors and Part 1 diagram (Harsh Singh)
- Credit Harsh Singh (hsingh23) and Ziqi Peng (peng20) in README.md.
- Add `part-1.png` (the Part 1 diagram) and reference it from the README.
- No code changes; final submission touch-up.

### 25638c7 — chore: expand README and disable ipdb breakpoints (Harsh Singh)
- Rewrite README.md with sender/receiver usage and output-file documentation.
- Comment out or remove `ipdb.set_trace` imports/breakpoints in sender.py, util.py, reciever.py.
- Delete stale root-level cwnd result files; refresh 10000-byte run 1/2 logs.

### 250770f — docs(analysis): finalize write-ups for parts b and c (Harsh Singh)
- Add cwnd plot cells and written conclusions for assignment parts b and c.
- Annotate slow-start termination, fast-recovery timing, and the early timeout storm in the third trace run.
- Clean up the notebook; regenerate Analysis.html and the checkpoint copy.

### 41286f7 — docs(analysis): re-run notebook against new state logs (Harsh Singh)
- Re-execute Analysis.ipynb against `state_logs/states-10000_bytes-*` runs.
- Refresh embedded figures and narration, including the new dup_ack_count column.
- First commit to include the state_logs output files.

### 56dff25 — fix(window): correct duplicate-ACK counting for fast retransmit (Harsh Singh)
- Emit `dup_ack` on the first repeat of the last ACK and `triple_ack` on the next; Window.add_ack owns all dup_ack_count mutation.
- Call transmit_as_allowed when exiting FastRecovery on new_ack; remove a leftover set_trace breakpoint.
- Log dup_ack_count in state log lines; regenerate 10000-byte results and notebook.

### 189345b — refactor(window): rework ACK bookkeeping around cumulative acks (Harsh Singh)
- WIP snapshot (tree known broken at this commit): replace SentList/SegmentCount with an OrderedDict of in-flight segments.
- Treat ACKs cumulatively: repeats increment dup_ack_count (2nd → dup_ack, 3rd+ → triple_ack); a new ACK removes all segments with sequence ≤ ACK.
- Rename retansmit_missing_segments → retansmit_missing_segment (retransmit only the segment after the ACK number); add state-machine logging to ./state_logs/; int-coerce loss-file tokens in reciever.py.

## 2013-11-16

### c1ef79b — fix(analysis): swap x/y axes in notebook plots (Harsh Singh)
- Plot data as (x[0], x[1]) instead of (x[1], x[0]) so charts show the intended orientation.
- Re-run the notebook to refresh embedded figures; regenerate Analysis.html.

### 9ec04dc — chore: add empty index.php for Heroku buildpack detection (Harsh Singh)
- Add an empty index.php at the repo root (0 bytes) so the Heroku PHP buildpack detects the app.
- No runtime code affected.

### 5d25b6d — docs: add IPython notebook analysis of trace/cwnd results (Harsh Singh)
- Populate Analysis.ipynb with load/plot helpers and executed plots for 10000_bytes runs at loss levels 0–2.
- Include the Analysis.html export and the notebook checkpoint copy.
- Add cwnd/trace result files for loss levels 1 and 2.

### d7c593c — feat: print sender throughput at end of transfer (Harsh Singh)
- Report throughput as ACK count × 100-byte chunk × 8 bits / elapsed seconds, replacing the raw count-and-duration print.
- Refresh result artifacts for the 10000_bytes-0 run.

### 428f80e — feat: add --loss-file option and report sender running time (Harsh Singh)
- Parse `-l/--loss-file` in parse_input_sender; suffix trace/cwnd output filenames with it.
- Write results into trace_results/ and cwnd_results/ instead of the repo root.
- Print ACK count plus elapsed time at completion; add 10000_bytes test data, Analysis.ipynb, and result artifacts.

### b1989dd — feat: count and print ACKs processed by sender (Harsh Singh)
- Add ack_count to TCPStateMachine, incremented on new-ACK events, printed when the transfer completes.
- Make the SlowStart/CongestionAvoidance/FastRecovery `.next` handlers @staticmethod.
- Drop per-ACK debug prints; refresh check_file and cwnd/trace artifacts.

### ba3a1c0 — fix: integrate Reassemble into receiver and fix window bugs (Harsh Singh)
- Wire the Reassemble buffer into the receiver loop; ACKs carry the next expected sequence number and the reassembled stream is written to check_file.
- Fix int casting of sequence numbers, append data (not seq) to the result, and call send_segment correctly in fast retransmit.
- Use timeout_length for the sender's select timeout; return None instead of an unbound event from get_ack; regenerate cwnd/trace data.

### 0ef04a7 — Merge branch 'master' of https://github.com/hsingh23/tcp-over-udp (ziqi)
- Sync collaborator work from GitHub master into the local branch containing the new Reassemble class.
- Combined diff reconciles parse_segment's tuple → Header namedtuple change.

### b4d2831 — feat: add Reassemble class to buffer and reorder segments (ziqi)
- Add Reassemble to reciever.py: bounded 25-entry buffer, modular sequence numbers (mod 9000).
- Accumulate in-order data to the result and drain the buffer in sorted order when gaps fill.
- (Introduced a bug — appending seq instead of data in the in-order branch — fixed in ba3a1c0.)

### 8838945 — Merge branch 'master' of github.com:hsingh23/tcp-over-udp (Harsh Singh)
- Sync local master (new test data files) with the remote, which contained PR #1's README addition.
- Non-conflicting merge; only README.md changed relative to the first parent.

### be5b40b — test: add 1KB/100KB/1MB loss files and 1MB transfer trace data (Harsh Singh)
- Add loss-pattern input files (1000_bytes, 100000_bytes, 1000000_bytes) for the receiver's Decider.
- Capture the first experiment output from the new logging: trace-1000000_bytes and cwnd-1000000_bytes (10001 samples each).
- Shows the congestion window ramping 200 → 1000 bytes over a ~1.92 s 1 MB transfer.

### cf302d5 — chore: add .gitignore for compiled Python files (Harsh Singh)
- Ignore `*.py[oc]` so compiled .pyc/.pyo bytecode is no longer tracked.
- Follows the removal of accidentally committed TCPStates.pyc and util.pyc.

### 62944a2 — feat: add RTT-based timeout estimation and trace/cwnd logging (Harsh Singh)
- Implement Jacobson/Karels RTT estimation in Window: estimated_RTT and dev_RTT as EWMAs; timeout_length = estimated_RTT + 4·dev_RTT.
- Route all congestion-window changes through update_cwnd so every change is timestamped; log acked sequence numbers to match.
- Sender writes trace-\<file\> and cwnd-\<file\> after transfer; parse receiver headers into a namedtuple; drop committed .pyc files; float MSS/ssthresh with 1.0 s initial timeout.

### 09faa5f — Merge pull request #1 from tadeegan/master (Harsh Singh)
- Merge Thomas Deegan's branch adding the placeholder README.md (title + tagline).

### 329b6fc — fix: handle sequence number 0, counter wraparound, and receiver exit (Harsh Singh)
- Window.shift_window compared peek() for truthiness, so sequence number 0 (falsy) stalled the window; compare against None instead.
- SequenceCounter.next wraps with modulo; add a peek_next helper.
- Replace the receiver's break (which only exited the inner for-loop) with a not_done flag so the process stops after the last segment.

### e097b2d — fix: make sender and receiver exchange UDP packets correctly (Harsh Singh)
- Receiver reads segments with recvfrom and replies via sendto to the sender's address (the old call was missing the address argument and raised TypeError).
- Sender reads ACKs with recvfrom and re-invokes the state transition in run(), dropped in the prior refactor.
- Fix chunkify_file to read the entire file in MSS-sized chunks rather than just the first chunk.

### 410d41e — docs: add README with project title and tagline (Thomas Deegan)
- Create a placeholder README.md with the project title and a one-line tagline via the GitHub web interface.

### d447abc — refactor: rework UDP sockets and move transmission into Window (Harsh Singh)
- Replace connected-socket setup with sender/receiver-specific helpers using sendto to a resolved destination address.
- Move segment transmission into Window (transmit_as_allowed, retansmit_missing_segments) invoked by the TCP state machine on ack/timeout events.
- Drop the coroutine run loop in sender.py for a plain event handler; pre-chunk the file in TCPStateMachine; update the Guardfile; (inadvertently) commit .pyc binaries.

## 2013-11-15

### 71ef976 — feat: add TCP-over-UDP sender, receiver, and congestion control (Harsh Singh)
- Initial MP2 implementation: sender.py with a TCP Reno-style state machine (slow start, congestion avoidance, fast recovery) from TCPStates.py.
- reciever.py drops segments per a loss file via a Decider class; util.py provides socket setup, CLI parsing, and window/ACK bookkeeping.
- Also add the MP2 spec PDF, a Guardfile for auto-restart, and sample loss files (0, 1, 2, 5, 10, 20).
