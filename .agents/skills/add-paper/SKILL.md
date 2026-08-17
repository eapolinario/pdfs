---
name: add-paper
description: >
  Add a PDF to this collection from a link. Use whenever the user supplies a URL
  to a paper, essay, report, spec or thesis and wants it in the repo — including
  bare links with no instructions, and phrasings like "add this", "collect this",
  "save this paper", "here's a PDF". Handles downloading, verifying, extracting
  metadata, choosing the filename, appending the metadata.md row, and committing.
---

# Adding a paper

`metadata.md` is the source of truth for the collection and for the published
site, so a new entry has to be right. The script does the mechanical half; you do
the judgement half.

**Do all of this without asking for confirmation.** A bare link is a complete
instruction.

## 1. Fetch and inspect

```sh
uv run .agents/skills/add-paper/add_paper.py fetch <url>
```

This normalises the URL (GitHub blob → raw, arXiv `/abs/` → `/pdf/`, OpenReview
forum → PDF), downloads it to `/tmp/add-paper.pdf`, **fails if the bytes are not
a PDF**, and prints the `pdfinfo` fields, a page count, a human-readable size, a
suggested filename, the tags already in use, and the first page of text.

If it prints no filename, it could not derive one with confidence — supply
`--name` yourself in step 3. If it reports a collision, check whether it is the
same document. If it is, say so and stop — do not add a duplicate.

## 2. Decide what the metadata actually says

The script reports; it does not judge. Read its output and fix it:

- **Title and authors.** PDF metadata is often absent or mangled (`Peter
  Naur]hyperref`, a LaTeX template's default, the filename). The first page is
  more reliable than the metadata. Use `et al.` beyond three authors.
- **Year.** The year of *original publication*, not the year the PDF was
  typeset. Naur's essay is 1985 even though that PDF was produced in 2020. The
  script's guess is only a guess — a preprint with no venue is its release year.
- **Tags.** 2–5, lowercase kebab-case, alphabetical. **Reuse an existing tag**
  from the list the script printed before inventing one; near-synonyms are the
  failure mode. See `AGENTS.md` for the full convention.
- **Notes.** One line: what it is, where it was published, why it matters.

## 3. Add it

```sh
uv run .agents/skills/add-paper/add_paper.py add \
  --file /tmp/add-paper.pdf \
  --title "Programming as Theory Building" \
  --authors "Peter Naur" \
  --year 1985 \
  --tags "epistemology, essay, software-engineering" \
  --source "https://pablo.rauzy.name/dev/naur1985programming.pdf" \
  --notes "Essay from *Microprocessing and Microprogramming* 15(5), 253–261. Argues that a program's real value is the theory held by the programmers who built it."
```

This derives the filename (`<lastname><year><word>.pdf`, override with `--name`),
copies the PDF into `files/`, sorts the tags, appends the row with the page count
and size filled in, escapes any `|` in your text, and runs the same validation
`.site/build.py` runs — so a malformed row fails here rather than in CI. `Added`
defaults to today.

`--source` must be the URL actually downloaded from — if step 1 rewrote a
GitHub blob or arXiv abstract URL, pass the rewritten one it printed.

If it reports new tags, add them to the **Tags in use** list in `AGENTS.md`
before committing.

## 4. Commit

Review with `git diff`, then commit the PDF, `metadata.md`, and any `AGENTS.md`
tag additions together:

```sh
git add files/<name>.pdf metadata.md AGENTS.md
git commit -m "Add Naur (1985), Programming as Theory Building"
```

Pushing to `main` rebuilds and redeploys the site automatically.

## When something goes wrong

- **"not a PDF"** — the URL serves an HTML landing page. Find the direct PDF
  link (often a `Download` button) and retry. Report the failure rather than
  adding a broken entry.
- **Paywalled or restricted material** — do not add it.
- **Validation fails** — `metadata.md` and `files/` disagree, or a cell is
  malformed. Fix it before committing; the site build enforces this, so a bad
  row breaks the deploy. `uv run .site/build.py --check` re-runs the check.

The scripts are [uv scripts](https://docs.astral.sh/uv/guides/scripts/) with
PEP 723 headers and no dependencies, so `uv run` needs no setup. They are also
executable directly (`./.agents/skills/add-paper/add_paper.py`).
