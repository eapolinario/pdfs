# pdfs

A small collection of publicly accessible papers, essays and reports —
**browse and search it at [eapolinario.github.io/pdfs](https://eapolinario.github.io/pdfs/)**.

- [`metadata.md`](metadata.md) — the index, and the source of truth
- [`files/`](files/) — the PDFs
- [`study/`](study/) — reading notes and open questions, one directory per paper
- [`AGENTS.md`](AGENTS.md) — how entries get added

## Adding a paper

[`.agents/skills/add-paper/`](.agents/skills/add-paper/) is a skill that takes a
link and does the rest. `fetch` normalises the URL (GitHub `/blob/` → raw, arXiv
`/abs/` → `/pdf/`), verifies the bytes really are a PDF, and reports what
`pdfinfo` and the first page say:

```sh
uv run .agents/skills/add-paper/add_paper.py fetch <url>
```

`add` then installs the PDF under the repo's naming convention, appends the
`metadata.md` row with the page count and size filled in, and validates the
result:

```sh
uv run .agents/skills/add-paper/add_paper.py add --file /tmp/add-paper.pdf \
  --title "..." --authors "..." --year 1985 --tags "essay, ..." \
  --source "<url>" --notes "..."
```

It deliberately will not guess the title, the year of *original* publication,
the tags or the notes — those need reading the paper.

## The site

[`.site/build.py`](.site/build.py) parses the `metadata.md` table into
`manifest.json` and assembles the page; [`.site/app.js`](.site/app.js) searches
that manifest in the browser. There is no build tooling and no third-party
JavaScript.

Search accepts plain words, `"quoted phrases"`, and the field filters
`tag:`, `author:`, `year:`, `title:` and `note:`. Terms combine with AND, and
the query is reflected in the URL, so any search is a shareable link:
[`?q=tag:essay`](https://eapolinario.github.io/pdfs/?q=tag:essay).

Build it locally — the Python here is
[uv scripts](https://docs.astral.sh/uv/guides/scripts/), so there is nothing to
install and no virtualenv to activate:

```sh
uv run .site/test_build.py            # parser tests
uv run .agents/skills/add-paper/test_add_paper.py
uv run .site/build.py --check         # validate metadata.md against files/
uv run .site/build.py --assemble _site
uv run -m http.server -d _site 8000
```

The build fails if `metadata.md` and `files/` disagree, so CI enforces the
one-PDF-per-entry rule on every push.
