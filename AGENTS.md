# AGENTS.md

Instructions for agents working in this repository.

## What this repo is

A personal collection of publicly accessible PDFs (papers, essays, reports) plus
an index describing them.

```
.
├── AGENTS.md      # this file
├── metadata.md    # the index of every PDF in the collection
└── files/         # the PDFs themselves
```

## The task: "here is a link to a PDF"

Whenever the user gives you a link to a PDF, do **all** of the following, in
order, without asking for confirmation:

1. **Download it into `files/`.**

   ```sh
   curl -sSL -o files/<filename>.pdf <url>
   ```

2. **Verify it is really a PDF** (`file files/<filename>.pdf` should report
   `PDF document`). If the download produced HTML, an error page, or a 0-byte
   file, delete it and report the failure instead of adding an entry.

3. **Extract the metadata** needed for the index:

   ```sh
   pdfinfo files/<filename>.pdf
   ```

   `pdfinfo` gives Title, Author, Pages, and file size. Values are often
   missing or mangled by the PDF producer (e.g. LaTeX artifacts such as
   `Peter Naur]hyperref`) — clean them up, and fall back to reading the first
   page of the document or the source page for the real title, authors, and
   publication year.

4. **Add exactly one row to `metadata.md`**, keeping the table sorted by the
   `Added` date (newest last, i.e. append). Choose tags per [Tags](#tags),
   reusing existing ones wherever they fit.

5. **Commit** the PDF and the updated `metadata.md` together, e.g.
   `Add Naur (1985), Programming as Theory Building`.

## File naming

Use `<firstauthorlastname><year><firstsignificantword>.pdf`, all lowercase,
ASCII only, no spaces or punctuation — for example
`naur1985programming.pdf`. If the source URL already follows this convention,
keep its filename as-is. Never overwrite an existing file: if the name is
taken, check whether it is the same document (skip and say so) before choosing
a suffixed name.

## `metadata.md` columns

| Column | Meaning |
| --- | --- |
| `Title` | Cleaned-up title, linked to the local file: `[Title](files/x.pdf)` |
| `Author(s)` | Comma-separated; use `et al.` beyond three authors |
| `Year` | Year of original publication, **not** the year the PDF was typeset |
| `Tags` | Comma-separated topic/form tags — see [Tags](#tags) below |
| `Pages` | Page count from `pdfinfo` |
| `Size` | Human-readable file size, e.g. `113 KB` |
| `Source` | The exact URL the PDF was downloaded from |
| `Added` | Date the entry was added, `YYYY-MM-DD` |
| `Notes` | One short line: what it is, where it was published, why it matters |

Escape any `|` characters inside cell text as `\|`.

## Tags

Tags are the main way to find things in the collection later, so consistency
matters more than precision.

- **Format:** lowercase ASCII, `kebab-case`, no `#` prefix, no backticks.
- **Count:** 2–5 per entry.
- **Order:** alphabetical within the cell, comma-separated —
  `epistemology, essay, software-engineering`.
- **Kinds:** mostly topic (`distributed-systems`, `epistemology`), optionally
  one form tag (`essay`, `paper`, `report`, `talk`, `thesis`).
- **Reuse before inventing.** Check the list below first and use an existing
  tag if it fits; near-synonyms (`swe` vs `software-engineering`) defeat the
  purpose. If you genuinely need a new tag, add it to the list in the same
  commit.

### Tags in use

- `epistemology`
- `essay`
- `software-engineering`

## Rules

- Only add PDFs the user has provided a link to; the user is responsible for
  confirming they are publicly accessible and redistributable.
- Never commit paywalled or otherwise restricted material.
- One PDF per entry, one entry per PDF — `files/` and `metadata.md` must always
  agree. If you notice drift, fix it.
- Do not reformat or rewrite unrelated rows while adding a new one.
