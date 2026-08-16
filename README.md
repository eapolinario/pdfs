# pdfs

A small collection of publicly accessible papers, essays and reports —
**browse and search it at [eapolinario.github.io/pdfs](https://eapolinario.github.io/pdfs/)**.

- [`metadata.md`](metadata.md) — the index, and the source of truth
- [`files/`](files/) — the PDFs
- [`AGENTS.md`](AGENTS.md) — how entries get added

## The site

[`.site/build.py`](.site/build.py) parses the `metadata.md` table into
`manifest.json` and assembles the page; [`.site/app.js`](.site/app.js) searches
that manifest in the browser. There is no build tooling and no third-party
JavaScript.

Search accepts plain words, `"quoted phrases"`, and the field filters
`tag:`, `author:`, `year:`, `title:` and `note:`. Terms combine with AND, and
the query is reflected in the URL, so any search is a shareable link:
[`?q=tag:essay`](https://eapolinario.github.io/pdfs/?q=tag:essay).

Build it locally:

```sh
python3 .site/test_build.py            # parser tests
python3 .site/build.py --check         # validate metadata.md against files/
python3 .site/build.py --assemble _site
python3 -m http.server -d _site 8000
```

The build fails if `metadata.md` and `files/` disagree, so CI enforces the
one-PDF-per-entry rule on every push.
