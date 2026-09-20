# The Discoveries of Continuations

John C. Reynolds, 1993 · 15 pp.

- PDF: [`files/reynolds1993discoveries.pdf`](../../files/reynolds1993discoveries.pdf)
- Source: <https://homepages.inf.ed.ac.uk/wadler/papers/papers-we-love/reynolds-discoveries.pdf>

Reynolds's paper is a history of an idea, not a continuation tutorial. Its
organizing claim is that continuations were independently discovered because
the same abstraction solves problems in program transformation, definitional
interpreters, and denotational semantics.

## Questions the paper answers

Read these as prompts. Try to answer each before following its link back into
the paper.

1. **What is a continuation?** A representation of "the meaning of the rest of
   the program" as a function or procedure (§§1, 5, pp. 233, 240).
2. **What existed before the abstraction had a name?** Algol implementors'
   program points (code plus environment), Dijkstra's return link, Landin's
   SECD dump, and Landin's `J` operator (§1, pp. 233–234).
3. **How does CPS eliminate `goto`?** Give every procedure an extra label
   parameter denoting what follows the call, make every path end in a jump, and
   then turn labels into procedures and jumps into calls (§2, pp. 235–236).
4. **Why do CPS procedures not consume a conventional call stack?** They never
   return: their last action transfers control to another procedure. A proper
   implementation can therefore reuse the current activation (§2, p. 236).
5. **Why is CPS more than a `goto`-elimination trick?** It also makes evaluation
   order explicit, can remove procedures returning complex values, supports
   program proofs, and gives semantics to non-local control (§§2, 5–7,
   pp. 236–242).
6. **How can an interpreter enforce call-by-value independently of its host
   language?** It evaluates subexpressions by passing explicit continuations,
   rather than relying on the host's argument-evaluation strategy (§4,
   pp. 238–239).
7. **Why are two continuations sometimes easier to discover than one?** Success
   and failure make the two possible futures operationally visible, as in
   SNOBOL-style failure and search (§4, p. 239).
8. **What did Wadsworth contribute?** He named the concept and used it as the
   denotation of the rest of a program, making full jumps and evaluation order
   mathematically tractable (§5, pp. 239–240).
9. **What was Fischer's technical contribution?** The first proof that a CPS
   transformation preserves meaning in an appropriate closure-based setting
   (§7, p. 242).
10. **Why was the idea repeatedly rediscovered?** It appeared in distinct
    intellectual settings, and early presentations exposed a transformation
    without isolating or motivating the general abstraction (§§2, 9,
    pp. 236–237, 243).
11. **What broader lesson does Reynolds draw?** Ideas are rarely born in full
    generality, and possessing an idea is different from naming, motivating,
    and communicating it (§9, p. 243).

## A first-principles reading route

The paper is easiest to understand in two passes.

### Pass 1 — discover the invariant

Read the abstract and §1 (pp. 233–234), then stop. For each representation
below, ask: **what information is required to determine the next computation?**

| Historical object | Code | Environment | What makes it continuation-like? |
| --- | --- | --- | --- |
| Algol program point | label | stack reference | jumping needs both |
| Dijkstra's link | return address | caller state | it says how the caller resumes |
| SECD dump | saved control | saved stack/environment | it encodes work after current control |
| Landin's `J` value | captured dump | captured machine state | the future becomes a value |

The invariant is not "a callback" or "a return address." It is **the complete
consumer of the current computation's result**. In a higher-order language that
consumer can be represented by a function `A -> R`.

Now work through [the derivation](1-first-principles.md) and run the laboratory:

```sh
uv run study/reynolds1993discoveries/continuations.py
```

### Pass 2 — distinguish the discoveries

Read §§2–8 (pp. 235–243), classifying each episode along two axes:

| Person | Setting | What was reified? |
| --- | --- | --- |
| van Wijngaarden | source transformation | successor labels as procedure parameters |
| Mazurkiewicz | algorithm semantics | labels mapped to tail functions |
| F. L. Morris | definitional interpreters | expression and command continuations |
| Wadsworth | denotational semantics | the meaning of the program remainder |
| J. H. Morris | lambda calculus / Algol transformation | continuations eliminating non-local transfers and complex returns |
| Fischer | program transformation and proof | a semantics-preserving CPS transform |
| Abdali | translation of Algol into pure lambda calculus | immediate and remote program remainders |

Then read §9. The chronology matters less than the fact that these are
different routes to the same invariant.

## Questions to answer while deriving

- [ ] For an expression of type `A`, why does its CPS form have the shape
      `(A -> R) -> R`?
- [ ] In the CPS evaluator, where is left-to-right evaluation order stated?
- [ ] Why is `k(x)` a transfer of control rather than an ordinary return?
- [ ] Under what runtime condition is van Wijngaarden's "no procedure ever
      returns" claim true? What happens in a language without tail-call
      elimination?
- [ ] How does a failure continuation differ from returning `Option[A]`?
- [ ] Derive the type of `call/cc` from its implementation before looking it
      up.
- [ ] Which examples use an escape continuation once, and which could safely
      invoke one more than once?
- [ ] What part of a continuation is code, and what part is captured
      environment?
- [ ] Is a continuation a semantic object, an implementation technique, or a
      source-level value? Give one example of each from the paper.

## Open questions

- [ ] Reynolds says the transformed program need not grow a stack if calls are
      implemented appropriately (§2, p. 236), while J. H. Morris notes that a
      conventional stack implementation exhausts it (§6, p. 241). State the
      exact implementation assumption reconciling these claims.
- [ ] The paper says F. L. Morris's continuation interpreter enforces
      call-by-value in either a call-by-value or call-by-name host (§4,
      pp. 238–239). Write the corresponding call-by-name counterexample in a
      lazy language.
- [ ] Fischer proved semantic preservation in a closure model (§7, p. 242).
      What simulation relation would you use to prove the tiny evaluator's
      direct and CPS versions equivalent?
- [ ] Where should delimited continuations fit in this history? They postdate
      the discoveries Reynolds recounts, but separate "the rest of the program"
      from "the rest up to which boundary?"
