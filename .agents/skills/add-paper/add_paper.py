#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Mechanical half of adding a paper to the collection.

    uv run .agents/skills/add-paper/add_paper.py fetch <url>
    uv run .agents/skills/add-paper/add_paper.py add --file ... --title ...

`fetch` does the error-prone bookkeeping — normalising the URL, checking the
bytes really are a PDF, reading pdfinfo, suggesting a filename — and leaves the
judgement calls (real title, year of *original* publication, tags, notes) to
whoever runs it. `add` then installs the file and appends the metadata.md row.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from urllib.parse import urlparse

REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
FILES_DIR = os.path.join(REPO_ROOT, "files")
METADATA = os.path.join(REPO_ROOT, "metadata.md")
AGENTS = os.path.join(REPO_ROOT, "AGENTS.md")

# Reuse the site builder so the Size column and the validation rules can never
# drift from what CI enforces. Imported in-process on purpose: the check runs
# after metadata.md has already been written, so it must not depend on finding
# an interpreter or on uv being reachable from a subprocess.
sys.path.insert(0, os.path.join(REPO_ROOT, ".site"))
import build  # noqa: E402

human_size = build.human_size

STOPWORDS = {
    "a", "an", "the", "on", "of", "in", "for", "to", "and", "or", "is", "are",
    "at", "by", "with", "from", "as", "into", "towards", "toward", "about",
}

# LaTeX/hyperref and Word producers leave junk in the metadata; strip it early.
AUTHOR_JUNK = re.compile(r"\]hyperref.*$|\\\w+|[{}]")


class Failure(Exception):
    """Anything that should stop the run with a readable message."""


def run(cmd, **kwargs):
    return subprocess.run(cmd, capture_output=True, text=True, **kwargs)


def normalise_url(url):
    """Rewrite common landing-page URLs to the actual PDF."""
    parsed = urlparse(url)
    host, path = parsed.netloc.lower(), parsed.path

    if host in ("github.com", "www.github.com") and "/blob/" in path:
        owner_repo, rest = path.split("/blob/", 1)
        return f"https://raw.githubusercontent.com{owner_repo}/{rest}", "GitHub blob page"

    if host.endswith("arxiv.org"):
        match = re.match(r"^/(abs|pdf)/(?P<id>.+?)(?:v\d+)?(?:\.pdf)?$", path)
        if match and path.startswith("/abs/"):
            return f"https://arxiv.org/pdf/{match.group('id')}", "arXiv abstract page"

    if host.endswith("openreview.net") and path.startswith("/forum"):
        return url.replace("/forum?", "/pdf?"), "OpenReview forum page"

    return url, None


def download(url, dest):
    result = run(["curl", "-sSL", "--fail", "--max-time", "180", "-o", dest, url])
    if result.returncode != 0:
        raise Failure(f"download failed: {result.stderr.strip() or f'curl exit {result.returncode}'}")
    if not os.path.exists(dest) or os.path.getsize(dest) == 0:
        raise Failure("download produced an empty file")

    with open(dest, "rb") as handle:
        head = handle.read(5)
    if head != b"%PDF-":
        preview = head.decode("latin-1", "replace")
        raise Failure(
            f"not a PDF (starts with {preview!r}) — the URL probably serves HTML; "
            "find the direct PDF link"
        )


def pdfinfo(path):
    result = run(["pdfinfo", path])
    if result.returncode != 0:
        raise Failure(f"pdfinfo failed: {result.stderr.strip()}")
    info = {}
    for line in result.stdout.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            info[key.strip()] = value.strip()
    return info


def first_page_text(path, lines=25):
    result = run(["pdftotext", "-f", "1", "-l", "1", path, "-"])
    if result.returncode != 0:
        return ""
    return "\n".join(line for line in result.stdout.splitlines() if line.strip())[:2000]


def clean_author(raw):
    return AUTHOR_JUNK.sub("", raw or "").strip(" ,;")


def last_name(authors):
    first = re.split(r",| and |;|&", authors or "")[0].strip()
    parts = [p for p in re.split(r"\s+", first) if p]
    return re.sub(r"[^a-z]", "", parts[-1].lower()) if parts else ""


def significant_word(title):
    for word in re.split(r"[^A-Za-z0-9]+", title or ""):
        if word and word.lower() not in STOPWORDS:
            return re.sub(r"[^a-z0-9]", "", word.lower())
    return ""


def suggest_name(title, authors, year):
    """Only suggest a name when every part is actually known.

    A partial guess (no author, a stray word from a licence header) is worse
    than no guess, because it looks authoritative enough to be accepted.
    """
    surname, word = last_name(authors), significant_word(title)
    if not (surname and year and word):
        return ""
    return f"{surname}{year}{word}.pdf"


def guess_year(info, text):
    """Prefer a year printed on the first page; fall back to the typeset date."""
    for candidate in re.findall(r"\b(1[89]\d{2}|20\d{2})\b", text or ""):
        return candidate
    match = re.search(r"\b(20\d{2}|1\d{3})\b", info.get("CreationDate", ""))
    return match.group(1) if match else ""


def known_tags():
    if not os.path.exists(AGENTS):
        return set()
    with open(AGENTS, encoding="utf-8") as handle:
        section = handle.read().split("### Tags in use", 1)
    if len(section) < 2:
        return set()
    body = section[1].split("\n## ", 1)[0]
    return set(re.findall(r"^- `([^`]+)`", body, re.MULTILINE))


def cmd_fetch(args):
    url, rewrote = normalise_url(args.url)
    if rewrote:
        print(f"note: {rewrote} — downloading {url}", file=sys.stderr)

    staging = args.out or os.path.join(tempfile.gettempdir(), "add-paper.pdf")
    download(url, staging)

    info = pdfinfo(staging)
    text = first_page_text(staging)
    title = (info.get("Title") or "").strip()
    authors = clean_author(info.get("Author"))
    year = guess_year(info, text)
    size_bytes = os.path.getsize(staging)

    suggested = suggest_name(title, authors, year)
    collision = ""
    if suggested and os.path.exists(os.path.join(FILES_DIR, suggested)):
        collision = f"{suggested} already exists in files/ — check whether it is the same document"

    report = {
        "url": url,
        "staged": staging,
        "suggestedName": suggested,
        "collision": collision,
        "pdfinfo": {
            "title": title,
            "authors": authors,
            "pages": int(info.get("Pages", 0) or 0),
            "creator": info.get("Creator", ""),
            "created": info.get("CreationDate", ""),
        },
        "bytes": size_bytes,
        "size": human_size(size_bytes),
        "yearGuess": year,
        "knownTags": sorted(known_tags()),
    }

    if args.json:
        json.dump(report, sys.stdout, indent=1, ensure_ascii=False)
        print()
    else:
        print(f"staged      {staging}")
        print(f"source      {url}")
        print(f"title       {title or '(none in metadata — read the first page)'}")
        print(f"authors     {authors or '(none in metadata — read the first page)'}")
        print(f"pages       {report['pdfinfo']['pages']}")
        print(f"size        {report['size']}")
        print(f"year guess  {year or '(unknown)'}   [from first page, else typeset date]")
        print(f"producer    {info.get('Creator', '')}")
        print(f"filename    {suggested or '(derive it yourself)'}")
        if collision:
            print(f"WARNING     {collision}")
        print(f"tags in use {', '.join(report['knownTags'])}")
        print("\n--- first page ---")
        print(text[:1200])
    return 0


def escape_cell(text):
    return str(text).replace("|", "\\|").strip()


def cmd_add(args):
    if not os.path.exists(args.file):
        raise Failure(f"no such file: {args.file}")

    name = args.name or suggest_name(args.title, args.authors, args.year)
    if not name:
        raise Failure(
            "could not derive a filename from the title and authors — pass --name "
            "explicitly (<lastname><year><word>.pdf)"
        )
    if not name.endswith(".pdf"):
        name += ".pdf"
    target = os.path.join(FILES_DIR, name)
    if os.path.exists(target):
        raise Failure(
            f"files/{name} already exists — if it is the same document, skip it; "
            "otherwise pass an explicit --name"
        )

    tags = sorted({tag.strip() for tag in args.tags.split(",") if tag.strip()})
    if not tags:
        raise Failure("--tags is required (2-5 tags, see AGENTS.md)")
    unknown = [tag for tag in tags if tag not in known_tags()]

    os.makedirs(FILES_DIR, exist_ok=True)
    shutil.copy2(args.file, target)

    info = pdfinfo(target)
    pages = args.pages or int(info.get("Pages", 0) or 0)
    row = "| {} | {} | {} | {} | {} | {} | {} | {} | {} |\n".format(
        f"[{escape_cell(args.title)}](files/{name})",
        escape_cell(args.authors),
        args.year,
        ", ".join(tags),
        pages,
        human_size(os.path.getsize(target)),
        escape_cell(args.source),
        args.added or date.today().isoformat(),
        escape_cell(args.notes),
    )

    with open(METADATA, encoding="utf-8") as handle:
        lines = handle.readlines()
    last_row = max(i for i, line in enumerate(lines) if line.lstrip().startswith("|"))
    lines.insert(last_row + 1, row)
    with open(METADATA, "w", encoding="utf-8") as handle:
        handle.writelines(lines)

    print(f"added files/{name}")
    print(row.rstrip())

    try:
        with open(METADATA, encoding="utf-8") as handle:
            entries = build.parse_metadata(handle.read())
        build.check_against_files(entries, FILES_DIR)
    except build.BuildError as error:
        raise Failure(f"{error} — fix metadata.md before committing")
    print(f"ok: {len(entries)} entries, metadata.md and files/ agree")

    if unknown:
        print(
            "\nnote: new tag(s) " + ", ".join(f"`{tag}`" for tag in unknown) +
            " — add them to the 'Tags in use' list in AGENTS.md in this same commit"
        )
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    fetch = sub.add_parser("fetch", help="download a PDF and report its metadata")
    fetch.add_argument("url")
    fetch.add_argument("--out", help="where to stage the download (default: a temp file)")
    fetch.add_argument("--json", action="store_true", help="machine-readable output")
    fetch.set_defaults(func=cmd_fetch)

    add = sub.add_parser("add", help="install a staged PDF and append its metadata.md row")
    add.add_argument("--file", required=True, help="the staged PDF from `fetch`")
    add.add_argument("--title", required=True)
    add.add_argument("--authors", required=True, help="comma-separated; 'et al.' beyond three")
    add.add_argument("--year", required=True, help="year of ORIGINAL publication")
    add.add_argument("--tags", required=True, help="comma-separated, lowercase kebab-case")
    add.add_argument("--source", required=True, help="the exact URL downloaded from")
    add.add_argument("--notes", required=True, help="one line: what it is, where published, why it matters")
    add.add_argument("--name", help="override the derived filename")
    add.add_argument("--pages", type=int, help="override the page count")
    add.add_argument("--added", help="override the Added date (default: today)")
    add.set_defaults(func=cmd_add)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Failure as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
