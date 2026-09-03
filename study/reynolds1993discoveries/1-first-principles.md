# From evaluation contexts to continuations

Covers the paper's central concept across §§1–7 (pp. 233–242). The derivation
and examples are this note's own; quotations are Reynolds's.

## 1. Start with a hole

Suppose evaluation has reached the marked subexpression:

```text
10 + ([ ] * 2)
```

If the hole produces `x`, the rest of the computation is:

```text
x |-> 10 + (x * 2)
```

That function is the continuation of the hole. More generally, an evaluation
context `E[ ]` induces:

```text
k_E = x |-> E[x]
```

This is the paper's repeated definition:

> representing "the meaning of the rest of the program" as a function or
> procedure
>
> — introduction, p. 233

The phrase "rest of the program" is dynamic. The source text after an
expression is insufficient: the continuation closes over values and
environments already established.

## 2. Derive the CPS type

A direct-style computation producing `A` has type:

```text
e : A
```

Give it an explicit consumer:

```text
k : A -> R
```

The transformed computation does not return an `A`; it gives an `A` to `k`,
which determines the final answer `R`:

```text
e_cps : (A -> R) -> R
```

This type is forced by the data flow. It is not a notation to memorize.

The answer type `R` is usually fixed for a whole CPS computation. Polymorphism
in `R` recovers more of direct style; control operators complicate that simple
story because captured continuations can expose or change answer types.

## 3. Derive the transform compositionally

For values:

```text
C[n] k = k n
```

For addition, first compute the left operand, then the right, then pass their
sum onward:

```text
C[e1 + e2] k =
  C[e1] (lambda v1.
    C[e2] (lambda v2.
      k (v1 + v2)))
```

Notice what became syntax:

1. evaluation order;
2. intermediate result names;
3. the destination of every result;
4. the fact that each call is in tail position.

This explains why Wadsworth found that continuations describe both jumps and
constructs that constrain evaluation order:

> Wadsworth had discovered the use of continuations to describe the behavior
> of labels and goto's, and had soon realized that the method also sufficed to
> describe call by value and other constructs that constrain the order of
> evaluation.
>
> — §5, p. 239

## 4. See calls and jumps become the same operation

In direct style:

```text
f(x) = g(x + 1) + 2
```

The call to `g` must save a return point: "when `g` returns `y`, add two." In
CPS:

```text
f_cps(x, k) =
  g_cps(x + 1, lambda y. k(y + 2))
```

`g_cps` receives that return point as an ordinary argument. It does not return
to `f_cps`; it transfers to the supplied continuation. This is Dijkstra's
"link" treated as a parameter (§1, p. 234).

Van Wijngaarden saw the implementation consequence:

> no procedure ever returns because it always calls for another one before it
> ends
>
> — §2, p. 236

That statement assumes proper tail calls. Without them, CPS source code can
consume a host-language stack even though the abstract control process needs
none. The executable laboratory uses a trampoline to make the required
implementation strategy explicit.

## 5. Generalize from one future to alternatives

For a partial computation, make both possible futures explicit:

```text
parse : Input
     -> (Value -> Input -> R)  -- success
     -> (() -> R)              -- failure
     -> R
```

The success continuation receives a value and remaining input. The failure
continuation says what search to resume. Failure is therefore not merely data
like `None`: it is a suspended policy for what happens next.

F. L. Morris recalled that this form was easier to recognize:

> every function needed two continuation arguments, one in case of success
> and one in case of failure. I think the choice of two continuations was
> easier to recognize than just one.
>
> — §4, p. 239

Once both branches are explicit, backtracking is ordinary function
composition: a choice's failure continuation tries the next choice.

## 6. Reify a continuation as a value

Ordinary CPS passes the current continuation downward. `call/cc` additionally
hands that continuation to the program as an escape function:

```text
call_cc(f) k = f (lambda x. lambda ignored_k. k x) k
```

Read it inside out:

1. `k` is the current continuation.
2. `lambda x. ...` packages it as an escape function.
3. Invoking the escape with `x` creates a CPS computation.
4. That computation ignores the continuation at the invocation site.
5. It resumes the captured `k` with `x`.

Landin's `J` was an ancestor of this move:

> the J operator provided a means of embedding continuations in values
>
> — §1, p. 234

Ignoring `ignored_k` is the essence of non-local exit: the dynamic future at
the invocation site is discarded in favor of the captured future.

## 7. Connect the three settings

The same object appears at three levels:

| Setting | Continuation is | Main payoff |
| --- | --- | --- |
| CPS transformation | an extra function parameter | explicit control and evaluation order |
| Definitional interpreter | an argument to the evaluator | host-independent object-language control |
| Denotational semantics | a mathematical function in the semantic domain | compositional meaning for jumps |

This is why the paper uses the plural **discoveries**. The abstraction was not
merely forgotten and rediscovered unchanged; different problems exposed
different faces of it.

## Exercises

1. Transform `1 + (2 * 3)` by hand. Name every continuation and beta-reduce the
   result with the identity continuation.
2. Transform `let x = e1 in e2`. Which continuation corresponds to the
   environment extension?
3. Add `Div(e1, e2)` to the laboratory. First return an error as data; then add
   a separate failure continuation. Compare the types and call sites.
4. Modify the CPS evaluator to evaluate the right operand first. Confirm that
   arithmetic results agree while trace output changes.
5. Remove the trampoline and run a million state-machine steps. Explain the
   failure without claiming that Reynolds or van Wijngaarden was wrong.
6. Implement `throw`/`catch` from `call_cc`. Identify which continuation is
   discarded at `throw`.
7. Extend `choose` so that its success continuation can request the next
   answer. This derives a lazy stream of search results from success and failure
   continuations.
