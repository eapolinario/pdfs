# Sections 5-7 - Know exactly what is proved

Covers Section 5 (pp. 17-21), Section 6 (pp. 21-24), Section 7 (pp. 24-25),
and the limitations discussed in Section 8 (p. 26).

> well-typed Olaf programs do not get stuck
>
> -- Section 6.2, p. 23

## Read the contract before the logical relation

Olaf is the core language, not an implementation of all source Effekt.
It omits imperative state, makes handler arguments explicit, and restricts an
interface to one operation. It does contain functions encoded as objects,
continuations, recursive interfaces, and fixpoint handlers
(Sections 5-5.1, pp. 17-19).

Use the results as three distinct contracts:

| Result | What to take away | Do not infer |
| --- | --- | --- |
| Theorem 1: parametricity | Well-typed terms satisfy the logical relation; effect-polymorphic code behaves uniformly over its abstract effects. Section 6.2, p. 23. | An abstraction may inspect a hidden effect's signature whenever it finds a matching local handler. |
| Theorem 2: type safety | A closed, well-typed computation with no residual effects cannot get stuck: it is a value or can step. Section 6.2, p. 23. | Termination, deadlock freedom, or correctness of every later language implementation. |
| Theorem 3: soundness | Logically related terms are contextually equivalent. Section 6.2, p. 24. | Any two implementations with the same type are interchangeable. |

The results are mechanized in Coq; Section 6.3 links the
[Olaf proof artifact](https://github.com/yizhouzhang/olaf-coq) (p. 24).

For a second pass through Section 6.1, connect each device to its job:
step indexing handles recursive definitions, worlds track fresh lifetimes,
and relations on evaluation contexts account for continuations
(Section 6.1, p. 23). Reconstruct that dependency map before attempting the
whole of Figure 14.

## Two rules worth annotating

In Figure 13, mark these premises rather than treating lifetime tracking as
background notation:

- **`t-down`:** A local lifetime can be used inside its delimiter, but must not
  escape in the result type or remaining effects.
- **`t-klam`:** A resumption accepts the declared result computation with the
  additional lifetime of its current handler, enabling self-handling. This is
  not blanket permission to capture every subsequently installed handler.

Both observations follow the rule explanations in Section 5.3 (pp. 20-21).
They connect the lifetime discipline and fixpoint handlers of Section 4.3 to
the formal language (pp. 16-17).

## Read the Effekt bug as a boundary exercise

The [stack-trace counterexample](https://github.com/effekt-lang/effekt/issues/1176#issuecomment-3493957114)
is a useful stress test for one's understanding. Our condensed trace of that
example is:

1. An outer prompt serves the `bi` and `yield` handlers.
2. The `bi` handler installs a fresh inner `escape` handler, then resumes with
   work that calls `yield()` followed by `escape()`.
3. The `yield` handler saves its resumption in a boxed function. The saved
   computation still refers to `escape`, but the inner prompt is not part of
   the continuation it saves.
4. Calling the function later reaches `escape()` after its prompt has gone.

**Exercise:** Draw the stack at steps 2-4 and mark the missing lifetime or
capture dependency. Distinguish this from the wrong-scheduler example in the
[previous note](4-abstraction-safety.md).

**Self-check:** A handler reference is not sufficient if its prompt is no
longer available. The [maintainer's analysis](https://github.com/effekt-lang/effekt/issues/1176#issuecomment-3496084792)
identifies that the resumption's captures omit the newly supplied
computation's dependency on `escape`.

The November 2025 thread compares restricting what a resumed computation may
capture with restricting where resumptions may escape. These lose different
programs; read them as design proposals, not settled guarantees of the current
compiler. The
[formalization discussion](https://github.com/effekt-lang/effekt/issues/1176#issuecomment-3498963086)
explicitly distinguishes those source-language interactions from existing
proofs and links this paper.

Before calling the example a counterexample to Olaf, translate it and establish
that it is closed and well-typed under Olaf's actual rules. A failure accepted
by a richer source implementation is not that derivation. The translation is
an [open question](README.md#open-questions), not a result established here.

## Answer the expressiveness question carefully

Section 7.2 sketches returning callbacks from ordinary effect operations and
forcing them at operation call sites. It explicitly leaves general
type-preserving feasibility to examination of each target language (p. 24).
Section 8 conjectures inexpressibility in particular prior calculi; it does
not prove a universal impossibility result (p. 26).

**Exercise:** Draft a reply to the
[Lobsters question](https://lobste.rs/s/tyacrw/handling_bidirectional_control_flow)
under four headings: programming interface, static guarantees, typed encoding,
and compilation cost.

**Self-check:** Separate the effectful-computation resumption interface from
the abstraction/lifetime guarantees, then qualify any encoding claim by the
target's features. Do not replace these with "ordinary effects cannot do it."
See Section 3.1 (pp. 6-8), Sections 4-6 (pp. 13-24), and Section 7.2 (p. 24).

Finally, constrain the performance claim. The paper measures two hand
translations of ping-pong into a modified muC++ implementation: the callback
version takes 42.6 ms versus 19.8 ms, a reported 2.1x slowdown
(Section 7.2, p. 25). It leaves a full-featured compiler to future work
(Section 7, p. 24). This supports investigating direct compilation and
tail-resumption optimization; it is not a benchmark of modern Koka versus
Effekt, or a universal lower bound on callback implementations.
