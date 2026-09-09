# AGENTS.md — working guide for coding agents

Archived 2013 Python 2 class project implementing TCP Reno-style reliable
transfer over UDP. Treat the code as a museum piece: prefer documentation and
analysis over "fixing" it. Do not modernize Python 2 syntax unless that is the
explicit task.

## Commands

There is no build system, test suite, or dependency file (standard library
only). Everything is run by hand with **Python 2**:

```sh
# receiver first (binds port, loads loss file)
python reciever.py -p 9200 -f 1

# then sender
python sender.py -d localhost -p 9200 -f 10000_bytes -l 1
```

Useful read-only inspection commands:

```sh
git log --oneline                           # 25 commits, 2013-11-15 → 2013-11-17
git show <sha>                              # inspect any historical change
head -5 trace_results/trace-10000_bytes-0   # experiment telemetry format
head -5 cwnd_results/cwnd-10000_bytes-0     # "time cwnd" pairs
head -5 state_logs/states-10000_bytes-0     # "time,State,event,ack,dup_ack_count"
```

Verification of a transfer (after running both ends): `diff check_file 10000_bytes`.

Guardfile targets exist for the Ruby `guard` gem (dev-time auto-restart of the
sender when util.py changes). Do not run `guard`; it launches long-lived
processes. Never execute other repo scripts either (see Gotchas).

## Architecture map

```
sender.py
  TCPStateMachine(file, udp, destination)
    chunks file into 100-byte segments (last one flagged LAST:1)
    Window (util.py) holds all protocol state:
      cwnd, ssthresh, in-flight OrderedDict {seq: segment},
      RTT estimates, dup-ack counter, trace/cwnd/state logs
    main loop: select([udp], timeout=timeout_length)
      -> timeout event  -> TCPStates transition
      -> ack data       -> Window.add_ack -> event -> TCPStates transition
    on completion: write trace_results/, cwnd_results/, state_logs/,
                   print throughput (ack_count*100*8/elapsed)

TCPStates.py  (pure state logic, @staticmethod handlers)
  SlowStart        new_ack: cwnd+=MSS, -> CongestionAvoidance at ssthresh
  CongestionAvoidance  new_ack: cwnd += MSS*round(MSS/cwnd, -1)
  FastRecovery     entered on triple_ack: ssthresh=ceil(cwnd/2),
                                     cwnd=ssthresh+3*MSS, retransmit, stay
  any state + timeout: ssthresh=ceil(cwnd/2), cwnd=MSS, retransmit,
                       -> SlowStart

reciever.py
  Decider(lossfile)      deterministic loss: mode 0 none / 1 every Nth /
                         2 explicit receive-ordinal list
  Reassemble             bounded 25-entry out-of-order buffer, seq mod 9000,
                         sorted drain, cumulative "expecting()" ack
  main loop: recvfrom -> parse "SEQ:n,LAST:x##data" -> Decider gate ->
             Reassemble.add -> sendto(ack) -> stop on LAST:1
             writes check_file

util.py  setup_socket_{sender,reciever}, parse_input_{sender,reciever},
         SequenceCounter (mod-9000), Window (transmit_as_allowed,
         add_ack, RTT sampling, update_cwnd, retansmit_missing_segment)
```

Key constants (Window instantiation in sender.py): MSS=100 bytes,
ssthresh=1000, max_sequence_number=9000, max_cwnd=25 segments,
timeout_length=1.0 s initial.

Data artifacts (trace_results/, cwnd_results/, state_logs/, *_bytes, 0/1/2/5/
10/20, check_file) are captured experiment outputs — inputs to the Analysis
notebook, not source code. Analysis.ipynb/Analysis.html/part-1.png are the
assignment write-up.

## Conventions (as practiced in this repo)

- Python 2.7, standard library only. Print statements, `iteritems()`,
  `xrange()`, old-style `super(...)` calls.
- No package structure, no tests, no linting, no requirements file.
- Commit messages follow conventional-commit style after the 2026-09-08
  messages-only history rewrite (`feat:`, `fix:`, `docs:`, `chore:`,
  `test:`, `refactor(scope):`). Three merge commits kept standard git
  messages. Pre-rewrite history: local branch `backup/pre-docs-20260908`.
- Misspelled identifiers are load-bearing public API surface:
  `reciever.py` and `retansmit_missing_segment` are referenced by name in
  docs, notebooks, and history — do not "fix" the spelling in isolation.

## Gotchas

- **Python 2 only.** Running under Python 3 fails immediately (`print`
  statements). Nothing here is pip-installable.
- **Typo'd names**: receiver script is `reciever.py`; retransmit method is
  `retansmit_missing_segment`.
- **Working directory matters**: the sender writes into `trace_results/`,
  `cwnd_results/`, `state_logs/` and the receiver writes `check_file`
  relative to cwd; those directories must exist.
- **Mod-9000 sequence space** with max_cwnd 25 keeps the window far below the
  wraparound horizon; don't raise max_cwnd without reconsidering ambiguity on
  wraparound.
- **ACK semantics are "last in-order received"** (not next-expected):
  `Reassemble.expecting()` returns `8999` when `current_sequence == 0`.
- `chunkify_file` marks the last chunk by mutating `chunks[-1][0] = 1`; an
  empty input file would crash (`chunks[-1]` on empty list).
- `Analysis.ipynb` contains embedded 2013-era outputs; re-executing requires
  a Python 2 matplotlib environment.
- `index.php` is intentionally empty (Heroku buildpack marker).

## Verifying changes

If you must modify protocol code, verify by behavior, not tests:

1. Run a no-loss transfer (`-f 0` receiver loss file) and
   `diff check_file <input>` — must be identical.
2. Run with loss (`-f 1`) — transfer must still complete and diff clean.
3. Inspect `state_logs/` for sane state ordering (SlowStart →
   CongestionAvoidance; FastRecovery episodes on triple acks) and
   `cwnd_results/` for the sawtooth pattern.
4. Confirm no stray breakpoints: `grep -rn set_trace *.py` should show only
   commented-out lines.

## Pointers

- README.md — protocol design, run instructions, structure
- CHANGELOG.md — commit-by-commit history (post-rewrite hashes)
- architectural-diary/ — decision records (ADR-style) and narrative
- prompt.md — full spec to recreate the project from nothing
- MP2.pdf — original assignment specification
