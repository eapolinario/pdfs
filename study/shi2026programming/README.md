# A Programming Paradigm for Spatiotemporal Composability

Yifan Shi, Wei Zhang, Tianyi Cui (Peking University, DeepSeek-AI), 2026 · 88 pp.

- PDF: [`files/shi2026programming.pdf`](../../files/shi2026programming.pdf)
- Source: <https://raw.githubusercontent.com/cordiverse/paper/main/paper.pdf>

The paper lifts effects and coeffects from static type disciplines into runtime
mechanisms — **revertible effects** and **reactive coeffects** — to get a
calculus of dynamic component composition, implemented in the Cordis
meta-framework.

## Notes

| Note | Covers |
| --- | --- |
| [2.1 Algebraic effects](2.1-algebraic-effects.md) | Effect signatures, handlers, the continuation `κ`, and why §2.1 is setup for a contrast |
| [2.2 Coeffects](2.2-coeffects.md) | Comonadic and graded coeffects, sensitivity analysis, and the pivot in §2.3 |
| [5.3 Cordis in practice](5.3-cordis-in-practice.md) | Footnote 4's v3/v4 split, the v4 release timeline, and how `deepseek-ai/deepseek-harness` vendors Cordis |

## The shape of the argument

Worth holding onto while reading, because §2 makes more sense read backwards
from §2.3:

1. §1.2.1 — plugin systems cannot unload a plugin's effects without a restart.
2. §2.1, §2.2 — effects describe a program's impact on the world; coeffects
   describe the world's constraints on the program. Both are well developed.
3. §2.3 — but both are *static instruments*, and no fixed lexical scope can
   delimit a plugin loaded after deployment.
4. §3 — so reify them as runtime mechanisms: pair every effect with an inverse,
   re-resolve every dependency as providers come and go.

## Open questions

- [ ] §3.1.3 "Independence of Effects" — what exactly is being ruled out? Does
      independence mean commuting effects, or something weaker?
- [ ] Does the formalism cover an effect registered *during* teardown? The
      harness had to reject effect creation while a fiber is `UNLOADING` to stop
      such effects escaping the unload snapshot — see
      [5.3 Cordis in practice](5.3-cordis-in-practice.md).
- [ ] The one-sided inverse (§3.1, and p. 74) is supplied by the caller rather
      than derived. What stops a caller from supplying a *wrong* inverse, and
      does the runtime detect it?
- [ ] §6.7 asks what a language with a second-class context would offer. Is that
      a concession that the runtime approach is a workaround for a missing
      language feature?
- [ ] Effekt's `box` recovers first-class capabilities by tracking them in types
      (p. 74). How much of Cordis's runtime tracking could that have bought
      statically?
- [ ] The empirical claim about Koishi's ecosystem (§1.2.1, p. 74 note) — how
      large is the sample, and is the comparison to other plugin ecosystems
      like-for-like?
