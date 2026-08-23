# AGENTS.md

Instructions for agents working in this repository.

## What this repo is

A personal collection of publicly accessible PDFs (papers, essays, reports) plus
an index describing them, published as a searchable site at
<https://eapolinario.github.io/pdfs/>.

```
.
├── AGENTS.md      # this file
├── README.md      # human-facing overview
├── metadata.md    # the index of every PDF in the collection
├── files/         # the PDFs themselves
├── study/         # reading notes, one directory per paper (see "Study notes")
├── .agents/       # the add-paper skill
├── .site/         # the GitHub Pages site (see "The site" below)
└── .github/       # the workflow that builds and deploys it
```

Python here is run with [uv](https://docs.astral.sh/uv/guides/scripts/): every
script carries a PEP 723 header, so `uv run <script>` resolves the interpreter
and needs no virtualenv. They are executable too (`./.site/build.py`).

## The task: "here is a link to a PDF"

Whenever the user gives you a link to a PDF, do **all** of the following, in
order, without asking for confirmation. The **`add-paper` skill**
(`.agents/skills/add-paper/`) automates steps 1–5 — use it:

```sh
uv run .agents/skills/add-paper/add_paper.py fetch <url>   # download + inspect
uv run .agents/skills/add-paper/add_paper.py add --file ... --title ...
```

The steps below are what the skill does, and what to fall back on by hand:

1. **Download it into `files/`.**

   ```sh
   curl -sSL -o files/<filename>.pdf <url>
   ```

   Landing pages are not PDFs: a GitHub `/blob/` URL needs
   `raw.githubusercontent.com`, and an arXiv `/abs/` URL needs `/pdf/`.

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

5. **Check the site still builds**, which also verifies that `metadata.md` and
   `files/` agree:

   ```sh
   uv run .site/build.py --check
   ```

6. **Commit** the PDF and the updated `metadata.md` together, e.g.
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
- `formal-methods`
- `paper`
- `programming-languages`
- `software-engineering`

## The add-paper skill

`.agents/skills/add-paper/` holds the skill that adds a paper from a link.

| Path | Role |
| --- | --- |
| `SKILL.md` | When to use it and the judgement calls it cannot make for you |
| `add_paper.py` | `fetch` downloads/verifies/reports; `add` installs the PDF and appends the row |
| `test_add_paper.py` | URL rewriting, filename derivation and cell escaping; run in CI |

The split is deliberate: the script does the mechanical, error-prone half (URL
rewriting, PDF verification, `pdfinfo`, filename derivation, size formatting,
`|` escaping, validation) and refuses to guess the half that needs judgement —
the real title, the year of *original* publication, tags, and notes.

It reuses `.site/build.py` for both `human_size` and the final validation, so
the `Size` column and the correctness rules cannot drift from what CI enforces.
That import is in-process on purpose: the check runs *after* `metadata.md` has
been written, so it must not be able to fail for environmental reasons.

`add_paper.py fetch` suggests a filename only when the author, year and title
word are all known — a partial guess looks authoritative enough to be accepted
by mistake.

## Study notes

`study/` holds reading notes and open questions — working notes meant to make a
second reading cheaper, not summaries. One directory per paper, **named after
the PDF stem**, so `files/shi2026programming.pdf` has `study/shi2026programming/`.

```
study/<pdf-stem>/
├── README.md             # paper header, index of notes, open questions
└── <section>-<topic>.md  # one note per section or theme
```

Note files are named after the section they cover so they sort in reading order
(`2.1-algebraic-effects.md`). See [`study/README.md`](study/README.md) for the
conventions; the ones that matter when writing a note:

- **Quote the paper, with a section and page number**, so a claim can be checked
  without re-reading the PDF.
- **Keep the paper's words in block quotes** and the note's own worked examples
  and analogies outside them. Never blur the two.
- Open questions live in the paper's `README.md` as a checklist.

Notes are not published: `.site/build.py` only reads `metadata.md` and `files/`,
so adding notes cannot break the site, and a paper needs no notes to be indexed.

## The site

<https://eapolinario.github.io/pdfs/> is generated from `metadata.md` — there is
no separate copy of the index to keep in sync, and no build tooling beyond uv
and a browser.

| Path | Role |
| --- | --- |
| `.site/build.py` | Parses `metadata.md` into `manifest.json` and assembles `_site/` |
| `.site/index.html`, `style.css`, `app.js` | The page; `app.js` does the searching, with no third-party JavaScript |
| `.site/test_build.py` | Parser tests, run in CI before every deploy |
| `.github/workflows/pages.yml` | Builds on every push to `main` and deploys to Pages |

```sh
uv run .site/test_build.py             # parser tests
uv run .agents/skills/add-paper/test_add_paper.py
uv run .site/build.py --check          # validate metadata.md against files/
uv run .site/build.py --assemble _site # full site into _site/ (gitignored)
uv run -m http.server -d _site 8000
```

Notes for anyone touching this:

- **`build.py` is a validator too.** It fails on a malformed table, an untagged
  entry, a title that is not a `[Title](files/x.pdf)` link, or any disagreement
  between `metadata.md` and `files/`. A broken row breaks the deploy, so run
  `--check` before committing.
- **Adding a column** to `metadata.md` means updating `COLUMN_KEYS` and
  `REQUIRED_KEYS` in `build.py`; unknown columns are rejected on purpose.
- **The PDFs are served by the site**, copied into the artifact by `build.py`.
  That is fine at this size, but GitHub Pages caps artifacts at 1 GB — if the
  collection ever approaches that, link entries to
  `raw.githubusercontent.com` instead of copying `files/`.
- **Notes lose their emphasis.** `build.py` strips `*...*` from the `Notes`
  column so the client can highlight search matches in plain text.

## Rules

- Only add PDFs the user has provided a link to; the user is responsible for
  confirming they are publicly accessible and redistributable.
- Never commit paywalled or otherwise restricted material.
- One PDF per entry, one entry per PDF — `files/` and `metadata.md` must always
  agree. If you notice drift, fix it. `uv run .site/build.py --check` reports it.
- Do not reformat or rewrite unrelated rows while adding a new one.
