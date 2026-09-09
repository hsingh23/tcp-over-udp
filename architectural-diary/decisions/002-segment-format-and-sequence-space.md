# 002 — Text segment format and mod-9000 sequence space

- Date: 2013-11-15 (introduced in 71ef976; header parsing formalized in fba8ca9)
- Status: as-submitted (frozen)

## Context

We need a wire format for datagrams carrying file data plus per-segment
metadata (sequence number, end-of-transfer flag), and a sequence space small
enough to be assigned by the MP but large enough to avoid wraparound
ambiguity.

## Decision

Encode segments as plain text:

```
SEQ:<sequence_number>,LAST:<0|1>##<data>
```

- MSS is 100 bytes of payload per segment (`chunkify_file` reads the file in
  100-byte chunks; the last chunk is flagged `LAST:1`).
- Sequence numbers cycle **modulo 9000** on both ends (`SequenceCounter`,
  `Reassemble.max_sequence_num`).
- The receiver parses the header by string `partition("##")` and
  `split(",")` into a `Header` namedtuple; the ACK is just the ASCII number.

## Consequences

- Segments are human-readable in tcpdump/Wireshark and trivially debuggable
  with prints — valuable while hand-debugging loss behavior.
- Text framing is inefficient (header overhead per 100-byte payload) and
  would corrupt if file data contained the `##` or `,` patterns; acceptable
  because correctness of the congestion-control algorithms, not wire
  efficiency, was graded. The receiver never re-parses data, only the header
  prefix, so binary payloads mostly survive.
- With max_cwnd capped at 25 segments, the un-ACKed window (≤ 25) can never
  approach the 9000 sequence space, so wraparound is unambiguous by
  construction.
