# Study notes

Reading notes and open questions for PDFs in [`files/`](../files/). These are
working notes, not summaries: they exist to make a second reading cheaper than
the first.

## Layout

One directory per paper, named after the PDF it belongs to — the notes for
`files/shi2026programming.pdf` live in `study/shi2026programming/`.

```
study/
├── README.md                 # this file
└── <pdf-stem>/
    ├── README.md             # paper header, index of notes, open questions
    └── <section>-<topic>.md  # one note per section or theme
```

Note files are named after the section they cover, so they sort in reading
order: `2.1-algebraic-effects.md`, `2.2-coeffects.md`.

## Conventions

- **Quote the paper, with a location.** Every claim about what the paper says
  carries a section and page number, so a note can be checked against the PDF
  without re-reading it.
- **Separate what the paper says from what the note adds.** Worked examples and
  analogies are the note's own; block quotes are the paper's.
- **Keep questions where they are asked.** Open questions live in the paper's
  `README.md` and are struck through or moved into a note once answered.
- Notes are not part of the published site. `.site/build.py` only reads
  `metadata.md` and `files/`.
