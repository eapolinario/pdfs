# Handling Bidirectional Control Flow - Flashcards

[Study guide](README.md) | [Paper](../../files/zhang2020handling.pdf)

24 cards, grouped in the guide's reading order. Recall an answer before opening
it; explain it in your own words rather than memorizing the wording.
Answers are paraphrases, not quotations. Discussion cards describe their dated
sources, not guaranteed behavior of current language implementations.
Unresolved questions remain in the [study guide](README.md#open-questions).

The paper's starting point:

> resume takes as input a computation, rather than a value
>
> -- Section 3.1, p. 6

## Pass 1 - Control flow

### 1. What does a bidirectional resumption receive?

<details>
<summary>Answer</summary>

A computation, not just a result value. The computation runs at the operation
call site and may raise the operation's declared reverse effects.

Source: Section 3.1, [pp. 6-7](../../files/zhang2020handling.pdf#page=6).

</details>

### 2. What handling must the caller of a bidirectional operation arrange?

<details>
<summary>Answer</summary>

Handling for the initiating effect and for the reverse effects declared by the
operation. The operation's signature exposes those obligations to its caller.

Source: Section 3.1, [p. 6](../../files/zhang2020handling.pdf#page=6).

</details>

### 3. Does an effect raised directly in a handler body automatically travel back to the operation call site?

<details>
<summary>Answer</summary>

No. Effects raised outside the computation passed to the resumption propagate
in the handler's own surrounding context.

Source: Section 3.1, "Raising effects within handlers,"
[p. 8](../../files/zhang2020handling.pdf#page=8).

</details>

### 4. After a reverse-effect handler resumes, which computation continues first?

<details>
<summary>Answer</summary>

The computation supplied by the original handler. Only after that finishes does
the originally suspended caller continue after its operation.

Source: Section 3.1, Figure 5,
[p. 7](../../files/zhang2020handling.pdf#page=7).

</details>

### 5. Why is deleting a yielded list node handled differently from replacing its value?

<details>
<summary>Answer</summary>

Replacement updates the node itself. Deletion changes the reference held by
the preceding node or by the client holding the list's first-node reference,
so `Behead` must reach that owner.

Source: Section 3.1, [pp. 7-8](../../files/zhang2020handling.pdf#page=7).

</details>

### 6. Where does an asynchronous failure emerge in the paper's promise encoding?

<details>
<summary>Answer</summary>

At the `await` site. The stored result computation raises the exception when
run through the await resumption, and `await` declares the exception effect.

Source: Section 3.2, Figures 6-7,
[pp. 9-11](../../files/zhang2020handling.pdf#page=9).

</details>

### 7. What makes a handler deep rather than shallow?

<details>
<summary>Answer</summary>

A deep handler's resumption contains that handler at its outermost layer, so
subsequent effects in the resumed computation can be handled by it again.

Source: Section 3.3.1, [p. 12](../../files/zhang2020handling.pdf#page=12).

</details>

### 8. Does the ping-pong encoding guarantee deadlock freedom?

<details>
<summary>Answer</summary>

No. Its signatures constrain the exchange of effects, but the paper explicitly
does not claim deadlock freedom or the full power of session types.

Source: Section 8, [p. 26](../../files/zhang2020handling.pdf#page=26).

</details>

## Pass 2 - Abstraction, lifetimes, and proofs

### 9. What is accidental handling?

<details>
<summary>Answer</summary>

A handler intercepts an effect it was not intended to handle merely because
its signature matches. The effect reaches the wrong handler, not necessarily
no handler.

Source: Section 4.1, [pp. 13-14](../../files/zhang2020handling.pdf#page=13).

</details>

### 10. How does tunneling select handlers?

<details>
<summary>Answer</summary>

Through lexically resolved handler bindings, made explicit as handler arguments.
An intervening dynamically enclosing handler cannot intercept an effect just
because it has the same signature.

Source: Section 4.3, Figure 10,
[pp. 15-16](../../files/zhang2020handling.pdf#page=15).

</details>

### 11. What does effect parametricity require of a function polymorphic over an abstract effect?

<details>
<summary>Answer</summary>

Uniform behavior over that abstract effect. The function must not inspect its
runtime signature to decide whether a private handler should intercept it.

Source: Section 4.2, [p. 15](../../files/zhang2020handling.pdf#page=15).

</details>

### 12. Why is lexical scoping alone insufficient for handler safety?

<details>
<summary>Answer</summary>

A closure can capture a lexically available handler and outlive its scope.
Correctly selecting a handler does not ensure that handler is still alive.

Source: Section 4.3.1, [p. 16](../../files/zhang2020handling.pdf#page=16).

</details>

### 13. What does treating handler lifetimes as effects accomplish?

<details>
<summary>Answer</summary>

Using a handler gives a computation that handler's lifetime effect. The type
system can then prevent the computation from outliving the handler it uses.

Source: Section 4.3.1, [p. 16](../../files/zhang2020handling.pdf#page=16).

</details>

### 14. What escape does Olaf's `t-down` rule forbid?

<details>
<summary>Answer</summary>

The locally bound lifetime must not occur in the result type or residual
effects outside its delimiter, although it may be used inside.

Source: Section 5.3, Figure 13,
[pp. 20-21](../../files/zhang2020handling.pdf#page=20).

</details>

### 15. Which extra lifetime may a resumption input use under `t-klam`?

<details>
<summary>Answer</summary>

Its current handler's own lifetime, allowing use of `self`. This is not
permission to capture arbitrary handlers installed later.

Source: Section 5.3, Figure 13,
[pp. 20-21](../../files/zhang2020handling.pdf#page=20).

</details>

### 16. Does giving two handler implementations the same type make them interchangeable?

<details>
<summary>Answer</summary>

No. The soundness theorem says logically related terms are contextually
equivalent; sharing a type alone does not establish logical relatedness.

Source: Section 6.2, Theorem 3,
[p. 24](../../files/zhang2020handling.pdf#page=24).

</details>

### 17. What does type safety guarantee for closed, well-typed Olaf computations with no residual effects?

<details>
<summary>Answer</summary>

They do not get stuck: after reduction they are values or can take another
step. This allows divergence; it does not guarantee termination.

Source: Section 6.2, Theorem 2,
[p. 23](../../files/zhang2020handling.pdf#page=23).

</details>

### 18. What must be shown before an Effekt failure can refute Olaf's safety theorem?

<details>
<summary>Answer</summary>

That the failing behavior has a translation which is closed and well-typed
under Olaf's actual rules, yet gets stuck. A failure in a richer source
implementation is not that derivation.

Sources: Section 5, [p. 17](../../files/zhang2020handling.pdf#page=17);
Section 6.2, [p. 23](../../files/zhang2020handling.pdf#page=23);
[Effekt formalization discussion, November 2025](https://github.com/effekt-lang/effekt/issues/1176#issuecomment-3498963086).

</details>

## Pass 3 - Discussion traps and implementation evidence

### 19. What differs between an Effekt effect annotation and a boxed function's capture annotation?

<details>
<summary>Answer</summary>

In the cited discussion, effects name capability types, while captures name
term-level capability instances. Those instances must be in scope.

Source: [effekt-lang/effekt#395 explanation, February 2024](https://github.com/effekt-lang/effekt/issues/395#issuecomment-1960978500).

</details>

### 20. Why is returning a boxed, effectful function not automatically equivalent to an operation with an impure parameter?

<details>
<summary>Answer</summary>

The particular encoding's capture restrictions can exclude programs that the
operation permits. The thread demonstrates this with a definition-site
exception; similar signatures do not prove equal expressiveness.

Source: [effekt-lang/effekt#395 encoding counterexample, February 2024](https://github.com/effekt-lang/effekt/issues/395#issuecomment-1961690461).

</details>

### 21. What escapes incorrectly in the Effekt bidirectional-resumption counterexample?

<details>
<summary>Answer</summary>

A saved computation still depends on a fresh inner `escape` handler, but the
saved continuation does not include its prompt. Later execution tries to use
that handler after the prompt has gone.

Source: [effekt-lang/effekt#1176 stack trace, November 2025](https://github.com/effekt-lang/effekt/issues/1176#issuecomment-3493957114).

</details>

### 22. What API choice distinguishes per-call recovery from uniform handler-owned recovery?

<details>
<summary>Answer</summary>

Per-call recovery exposes failure to the caller, through an explicit result
or a caller-handled effect. Uniform recovery can live in the handler or its
configuration instead.

Source: [koka-lang/koka#548 recovery-policy discussion, June 2024](https://github.com/koka-lang/koka/issues/548#issuecomment-2163548690).

</details>

### 23. Does the paper prove that ordinary handlers cannot encode bidirectionality?

<details>
<summary>Answer</summary>

No. It sketches callback encodings and leaves general type-preserving
feasibility dependent on the target language. Its inexpressibility claim about
particular prior calculi is a conjecture, not a universal impossibility proof.

Sources: Section 7.2, [p. 24](../../files/zhang2020handling.pdf#page=24);
Section 8, [p. 26](../../files/zhang2020handling.pdf#page=26).
This qualifies the [Lobsters Koka question, June 2025](https://lobste.rs/s/tyacrw/handling_bidirectional_control_flow).

</details>

### 24. What does the reported 2.1x callback slowdown actually support?

<details>
<summary>Answer</summary>

Avoiding callback overhead in the measured hand-translated ping-pong workload
on modified muC++. It is neither a modern Koka-versus-Effekt benchmark nor a
universal lower bound on callback implementations.

Source: Section 7.2, [p. 25](../../files/zhang2020handling.pdf#page=25).

</details>
