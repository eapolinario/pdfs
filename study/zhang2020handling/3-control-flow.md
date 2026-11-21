# Section 3 - Trace the two directions

Covers Section 2 (pp. 3-5) and Section 3 (pp. 6-13).

## The change to look for

> resume takes as input a computation, rather than a value
>
> -- Section 3.1, p. 6

Compare Figures 2 and 4. In Figure 2, the handler supplies the operation's
result. In Figure 4, it supplies work to run at the operation call site; that
work may raise the reverse effects declared by the operation. The caller must
provide handling for those effects (Sections 2-3.1, pp. 4-6).

Keep three pieces separate while reading Figure 4: the operation's argument,
the computation passed to its resumption, and the rest of the suspended
iterator. The computation can transfer control again before the iterator
continues (Section 3.1, pp. 6-7).

## Worksheet: replace a yielded element

This is our renamed, simplified version of Figure 4, not paper code. Leave out
deletion for the first trace:

```text
Offer.offer(n: Int): Unit raises Replace
Replace.replace(n: Int): Unit
```

The producer handles `Replace` around its call to `offer`; the client handles
`Offer` around the producer. Start with the producer's current item equal to 7.

| Step | Work being done | Next destination |
| --- | --- | --- |
| 1 | Producer calls `offer(7)`. | Client's `Offer` handler. |
| 2 | Client resumes with a computation that calls `replace(14)`. | Producer-side `Replace` handler when that computation runs. |
| 3 | `Replace` updates the current item to 14 and resumes. | Remainder of the computation supplied by the client. |
| 4 | That computation finishes with `Unit`. | Producer's suspended work after `offer`. |
| 5 | Producer proceeds to the next item. | Ordinary traversal. |

This follows the two returns in Figure 5: handling replacement returns to the
client's handler computation, and finishing that computation returns to the
iterator (Section 3.1, p. 7). Do not collapse steps 3 and 4.

**Exercise:** Add deletion back in. Mark which code owns each list reference
that must change.

**Self-check:** Replacing a node's value is local to that node. Removing a node
changes the preceding reference, so `Behead` propagates to the preceding node
or to the client holding the first-node reference. That explains both the
extra effect on `iter` and the outer client handler (Section 3.1, pp. 7-8).
Here, modification during traversal is the example; do not read it as a
separate guarantee of thread safety.

## Exercise: move the reverse operation

Draw the same handler nesting twice. First put `replace(14)` inside the
computation passed to `resume`; then put it directly in the `Offer` handler
body, outside that computation.

**Self-check:** Only the first placement sends the operation back through the
resumption. In the second, effects propagate in the handler's own surrounding
context. Bidirectionality does not redirect every effect raised anywhere in a
handler (Section 3.1, "Raising effects within handlers," p. 8).

## Use the Koka discussion to challenge the API

Read the [final Koka reply](https://github.com/koka-lang/koka/issues/548#issuecomment-2163548690)
alongside the paper's ADT and callback workarounds (Section 3.1, p. 8).
The thread contrasts caller-specific recovery with a policy owned uniformly by
the handler, and with returning an explicit error value.

For the worksheet, sketch both an `offer` that returns a command value and one
that returns a callback. Annotate who must interpret or invoke the result.
Then mark where control can return after handling the requested modification.

**Self-check:** The paper objects to the extra protocol and obligations, not
to the existence of alternative encodings. In particular, callers must remember
to force a returned callback; the paper also examines its compilation cost
(Section 3.1, p. 8; Section 7.2, pp. 24-25). The Koka thread is a useful API
design debate, not evidence that every file API should use bidirectional effects.

## Two transfer exercises

**Exceptional async-await:** Trace a failing promise twice in Figure 7:
once when it is already complete at `await`, and once when its result arrives
later. Locate the computation supplied to `resume` in both paths.

**Self-check:** Both paths eventually run the stored result computation at the
await site. It either returns a value or raises the exception there; the
signature of `await` exposes that reverse exception effect to its caller
(Section 3.2, Figures 6-7, pp. 9-11).

**Ping-pong:** Trace three message transfers in Figure 8. Label both the effect
being sent and the reverse effect its operation declares.

**Self-check:** `ping` permits a responding `Pong`, and `pong` permits a responding
`Ping`. Deep resumptions contain their handler, enabling the self-handling
refinement; follow this into the explicit `self` binding in Section 4.3.2
(Sections 3.3-3.3.2, pp. 11-13; Section 4.3.2, p. 17).
The paper explicitly says this protocol discipline does not prevent deadlocks
or provide the full power of session types (Section 8, p. 26).
