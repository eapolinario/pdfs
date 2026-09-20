---
name: add-paper
description: >
  Add a PDF to this collection from a link or a local file. Use whenever the
  user supplies a URL to a paper, essay, report, spec or thesis — or a path to
  one already downloaded (e.g. ~/Downloads/paper.pdf) — and wants it in the
  repo, including bare links or paths with no instructions, and phrasings like
  "add this", "collect this", "save this paper", "here's a PDF". Handles
  downloading, verifying, extracting metadata, choosing the filename, appending
  the metadata.md row, and committing.
---

# Adding a paper

`metadata.md` is the source of truth for the collection and for the published
site, so a new entry has to be right. The script does the mechanical half; you do
the judgement half.

**Do all of this without asking for confirmation.** A bare link — or a bare path
to a PDF on disk — is a complete instruction.

## 1. Fetch and inspect

```sh
uv run .agents/skills/add-paper/add_paper.py fetch <url-or-path>
```

The argument is either a URL or a PDF already on disk
(`~/Downloads/paper.pdf`, a relative path, or a `file://` URL). Publishers
behind Cloudflare — Wiley, Elsevier, IEEE — refuse curl, so a browser download
is often the only way to get the bytes; hand the script that file.

For a URL it normalises it (GitHub blob → raw, arXiv `/abs/` → `/pdf/`,
OpenReview forum → PDF) and downloads it. For a path it copies the file. Either
way it stages the result at `/tmp/add-paper.pdf`, **fails if the bytes are not a
PDF**, and prints the `pdfinfo` fields, a page count, a human-readable size, a
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

`--source` is the URL a reader can get the paper from — the collection is of
publicly accessible PDFs, so every row has to say where it came from. If step 1
rewrote a GitHub blob or arXiv abstract URL, pass the rewritten one it printed.
**A local file has no such URL**, so find the canonical one yourself: the DOI
landing page, the publisher's PDF link, the author's copy. Never record a
`file://` path or a `~/Downloads` path.

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

- **"not a PDF"** — for a URL, it serves an HTML landing page: find the direct
  PDF link (often a `Download` button) and retry. For a local file, the download
  saved the landing page instead of the document. Report the failure rather than
  adding a broken entry.
- **"download failed" behind a paywall-ish CDN** — Wiley, Elsevier, IEEE and
  friends block curl even for open-access articles. Ask the user to download it
  in a browser and pass the path, and record the article URL as `--source`.
- **"no such file"** — the path is wrong, or the shell ate a space. Quote it.
- **Paywalled or restricted material** — do not add it.
- **Validation fails** — `metadata.md` and `files/` disagree, or a cell is
  malformed. Fix it before committing; the site build enforces this, so a bad
  row breaks the deploy. `uv run .site/build.py --check` re-runs the check.

The scripts are [uv scripts](https://docs.astral.sh/uv/guides/scripts/) with
PEP 723 headers and no dependencies, so `uv run` needs no setup. They are also
executable directly (`./.agents/skills/add-paper/add_paper.py`).
