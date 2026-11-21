# Section 4 - Separate routing from lifetime safety

Covers Sections 4.1-4.3 (pp. 13-17).

> A loss of parametricity is a loss of modular reasoning.
>
> -- Section 4.2, p. 15

## Worksheet: two handlers with the same signature

Figure 9 is worth tracing before reading the proof. `pinger` installs an
`Async` handler for its own operations, while `ponger` expects its asynchronous
operations to reach an outer scheduler. Signature-based dynamic lookup lets
`pinger` intercept operations it was not intended to handle
(Section 4.1, pp. 13-14).

Our reduced worksheet names the outer scheduler `A` and `pinger`'s local
scheduler `B`. These names denote different handlers, not different effect
signatures.

| Operation site | Closest matching handler dynamically | Intended handler under lexical resolution |
| --- | --- | --- |
| `pinger`'s own asynchronous read | `B` | `B` |
| `ponger`'s asynchronous fetch during the exchange | `B` | `A` |

The second row is the problem, not an unhandled operation. Both handlers can
implement the same interface while giving observably different behavior.
Figure 10 makes the intended choices explicit with handler arguments
(Sections 4.1-4.3, pp. 14-16).

**Exercise:** Annotate every `async` and `await` in Figures 9-10 with the handler
identity it uses. Then explain the role of the abstract effect variable `alpha`.

**Self-check:** `pinger` must remain oblivious to effects represented by its
abstract parameter. Its private scheduler is not permission to intercept those
effects. The caller that instantiates the parameter supplies the relevant
handler; lexical resolution makes that routing explicit
(Sections 4.2-4.3, pp. 15-16).

## Routing is not lifetime checking

Lexical resolution answers *which handler*. It does not by itself ensure a
closure cannot capture that handler and use it after its scope has ended.
The paper therefore tracks handler lifetimes as computational effects
(Section 4.3.1, p. 16).

Keep these failure modes distinct:

| Failure | Obligation to examine |
| --- | --- |
| A private handler intercepts someone else's effect. | Abstraction-safe routing and effect parametricity; Sections 4.1-4.3, pp. 13-16. |
| A computation refers to a handler whose lifetime has ended. | Lifetime tracking and escape restrictions; Section 4.3.1, p. 16. |

The [Lobsters question](https://lobste.rs/s/tyacrw/handling_bidirectional_control_flow)
asks what the design adds over Koka-style tunneling/masking. Do not answer by
claiming bypass directives do not exist: the paper discusses `inject`, `lift`,
and adaptors as alternative approaches to avoiding accidental handling
(Section 8, p. 26).

A better comparison keeps three axes separate: allowing effectful computations
as resumption inputs, selecting handler identities, and tracking their
lifetimes. Sections 3.1 and 4.3 supply those mechanisms; typed encodability is a
further, target-dependent issue (pp. 6-8, 15-17; Section 7.2, p. 24).

## Bridge to the Effekt discussion

Read the [effects-versus-captures explanation](https://github.com/effekt-lang/effekt/issues/395#issuecomment-1960978500).
In that discussion, an effect annotation mentions capability types, while a
boxed function's capture annotation mentions term-level capability instances.
Confusing these is why several proposed signatures fail.

The same reply explains a bidirectional operation by explicitly passing an
exception capability from the operation's call site. In a handler
implementation, use of that capability belongs under the bidirectional
resumption, rather than being silently moved to the handler's definition site.
This is an explanatory connection to the paper's call-site mechanism, not a
claim that Effekt and Olaf have identical syntax or typing rules
(Section 3.1, p. 8; Section 4.3, pp. 15-16).

**Exercise:** Sketch `getUser` as an operation receiving an explicit exception
capability. Label where that capability becomes available. Compare it with an
operation that instead returns a boxed, effectful function.

**Self-check:** Track the *instances* available to each computation, not just
the effect names in its interface. The
[follow-up encoding counterexample](https://github.com/effekt-lang/effekt/issues/395#issuecomment-1961690461)
shows that the proposed returned-function encoding's capture restrictions rule
out a use of definition-site exceptions. Similar-looking operation signatures
are not enough to establish equal expressiveness.
