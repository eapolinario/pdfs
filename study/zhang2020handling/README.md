# Handling Bidirectional Control Flow

Yizhou Zhang, Guido Salvaneschi, Andrew C. Myers, 2020. OOPSLA, Article 139,
30 pp.

- PDF: [`files/zhang2020handling.pdf`](../../files/zhang2020handling.pdf)
- DOI: <https://doi.org/10.1145/3428207>
- Author's copy: <https://www.cs.cornell.edu/andru/papers/ufo/>

Page references use PDF page numbers: p. 6 is the printed page 139:6.

## Collected discussions

Collected on 2026-11-12. These are annotated links, not archived copies of the
threads.

| Discussion | Date | What to read it for |
| --- | --- | --- |
| [koka-lang/koka#548: Explicit effects in operation result types](https://github.com/koka-lang/koka/issues/548) | June 2024 | The most approachable entry point: should a file-reading failure be handled at each call site, uniformly by the handler, or returned as an error value? The thread explicitly links this paper. |
| [effekt-lang/effekt#395: Impure arity types](https://github.com/effekt-lang/effekt/issues/395) | February 2024 | Effects versus captures, capability-passing, and the difference between bidirectional operations and encodings that return effectful functions. |
| [effekt-lang/effekt#1176: Bidirectional resume leaking a local handler](https://github.com/effekt-lang/effekt/issues/1176) | November 2025 | A detailed safety counterexample and discussion of capture tracking, handler lifetimes, and the boundary between a formal calculus and source Effekt. |
| [Lobsters: Handling bidirectional control flow](https://lobste.rs/s/tyacrw/handling_bidirectional_control_flow) | June 2025 | A direct but very short paper thread. The submission highlights Lisp-style conditions; its single comment asks what this adds over Koka-style effects with explicit tunneling/masking. It does not answer that question. |

Two citation traps matter when following these links. The
[first Koka reply](https://github.com/koka-lang/koka/issues/548#issuecomment-2152767117)
attributes its linked paper to Biernacki et al., but the DOI is this paper's.
The [Effekt explanation](https://github.com/effekt-lang/effekt/issues/395#issuecomment-1960978500)
also discusses its authors' different OOPSLA 2020 paper, DOI
[10.1145/3428194](https://doi.org/10.1145/3428194). Do not merge those two
papers, or identify this paper's core language Olaf with source Effekt.

## Open questions

- [ ] Reconstruct a typed callback encoding of Figure 4 in a specific target
      language. Which guarantees require explicit conventions or extra types?
- [ ] Can the escape from effekt-lang/effekt#1176 be expressed in Olaf, or does
      it rely on constructs or typing rules outside the modeled language?
- [ ] Work out the Lisp-condition-system connection suggested by the Lobsters
      submission: distinguish signaling, selecting a restart, and resuming.
