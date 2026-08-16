#!/usr/bin/env python3
"""Turn metadata.md into manifest.json and assemble the GitHub Pages site.

metadata.md is the single source of truth. This script parses its table,
validates that it agrees with files/, and emits a JSON manifest that the
static page loads and searches client-side.

    python3 .site/build.py --assemble _site
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_DIR = os.path.join(REPO_ROOT, ".site")
STATIC_FILES = ("index.html", "style.css", "app.js")

COLUMN_KEYS = {
    "title": "title",
    "author(s)": "authors",
    "authors": "authors",
    "year": "year",
    "tags": "tags",
    "pages": "pages",
    "size": "size",
    "source": "source",
    "added": "added",
    "notes": "notes",
}

REQUIRED_KEYS = ("title", "authors", "year", "tags", "pages", "size", "source", "added", "notes")

LINK_RE = re.compile(r"^\[(?P<title>.+)\]\((?P<path>[^)]+)\)$")
SEPARATOR_RE = re.compile(r"^[\s:|-]+$")
EMPHASIS_RE = re.compile(r"(?<!\w)\*(?P<text>[^*]+)\*(?!\w)")


class BuildError(Exception):
    """Raised when metadata.md is malformed or disagrees with files/."""


def split_row(line):
    """Split a markdown table row on unescaped pipes."""
    cells = re.split(r"(?<!\\)\|", line.strip())
    if cells and not cells[0].strip():
        cells = cells[1:]
    if cells and not cells[-1].strip():
        cells = cells[:-1]
    return [cell.strip().replace("\\|", "|") for cell in cells]


def find_table(text):
    """Return the rows of the first markdown table in the document."""
    rows = []
    for line in text.splitlines():
        if line.lstrip().startswith("|"):
            rows.append(line)
        elif rows:
            break
    if len(rows) < 2:
        raise BuildError("no markdown table found in metadata.md")
    return rows


def strip_emphasis(text):
    """Drop markdown emphasis markers so the client can highlight raw text."""
    return EMPHASIS_RE.sub(lambda m: m.group("text"), text)


def parse_int(value, field, title):
    try:
        return int(value)
    except ValueError:
        raise BuildError(f"{title!r}: {field} is not a number: {value!r}")


def parse_metadata(text):
    rows = find_table(text)
    header = [COLUMN_KEYS.get(cell.lower()) for cell in split_row(rows[0])]
    if None in header:
        unknown = [c for c in split_row(rows[0]) if c.lower() not in COLUMN_KEYS]
        raise BuildError(f"unknown column(s) in metadata.md: {', '.join(unknown)}")
    missing = [key for key in REQUIRED_KEYS if key not in header]
    if missing:
        raise BuildError(f"metadata.md is missing column(s): {', '.join(missing)}")
    if not SEPARATOR_RE.match(rows[1]):
        raise BuildError("metadata.md table is missing its header separator row")

    entries = []
    for number, row in enumerate(rows[2:], start=1):
        cells = split_row(row)
        if len(cells) != len(header):
            raise BuildError(
                f"row {number} has {len(cells)} cells, expected {len(header)}: {row.strip()}"
            )
        record = dict(zip(header, cells))

        link = LINK_RE.match(record["title"])
        if not link:
            raise BuildError(
                f"row {number}: Title must be a link like [Title](files/x.pdf), got {record['title']!r}"
            )
        title = link.group("title")
        path = link.group("path")
        if not path.startswith("files/") or not path.lower().endswith(".pdf"):
            raise BuildError(f"{title!r}: link must point at a PDF in files/, got {path!r}")

        tags = sorted({tag.strip() for tag in record["tags"].split(",") if tag.strip()})
        if not tags:
            raise BuildError(f"{title!r}: has no tags")

        entries.append(
            {
                "title": title,
                "path": path,
                "authors": record["authors"],
                "year": parse_int(record["year"], "Year", title),
                "tags": tags,
                "pages": parse_int(record["pages"], "Pages", title),
                "size": record["size"],
                "source": record["source"],
                "added": record["added"],
                "notes": strip_emphasis(record["notes"]),
            }
        )
    return entries


def check_against_files(entries, files_dir):
    """metadata.md and files/ must describe exactly the same set of PDFs."""
    listed = [entry["path"][len("files/") :] for entry in entries]
    duplicates = sorted({name for name in listed if listed.count(name) > 1})
    if duplicates:
        raise BuildError(f"listed more than once in metadata.md: {', '.join(duplicates)}")

    if not os.path.isdir(files_dir):
        raise BuildError(f"missing directory: {files_dir}")
    actual = {name for name in os.listdir(files_dir) if name.lower().endswith(".pdf")}

    orphans = sorted(set(listed) - actual)
    if orphans:
        raise BuildError(f"listed in metadata.md but not in files/: {', '.join(orphans)}")
    unlisted = sorted(actual - set(listed))
    if unlisted:
        raise BuildError(f"in files/ but not listed in metadata.md: {', '.join(unlisted)}")


def human_size(num_bytes):
    if num_bytes < 1024:
        return f"{num_bytes} B"
    for unit in ("KB", "MB", "GB"):
        num_bytes /= 1024
        if num_bytes < 1024:
            return f"{num_bytes:.0f} {unit}" if num_bytes >= 10 else f"{num_bytes:.1f} {unit}"
    return f"{num_bytes:.1f} TB"


def build_manifest(entries, files_dir, commit=None):
    total_bytes = 0
    for entry in entries:
        path = os.path.join(files_dir, entry["path"][len("files/") :])
        entry["bytes"] = os.path.getsize(path) if os.path.exists(path) else 0
        total_bytes += entry["bytes"]

    counts = {}
    for entry in entries:
        for tag in entry["tags"]:
            counts[tag] = counts.get(tag, 0) + 1
    tags = [
        {"name": name, "count": count}
        for name, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    ]

    return {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "commit": commit,
        "count": len(entries),
        "totalBytes": total_bytes,
        "totalSize": human_size(total_bytes),
        "totalPages": sum(entry["pages"] for entry in entries),
        "tags": tags,
        "entries": entries,
    }


def assemble(manifest, out_dir, files_dir):
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)

    for name in STATIC_FILES:
        shutil.copy2(os.path.join(SITE_DIR, name), os.path.join(out_dir, name))
    shutil.copytree(files_dir, os.path.join(out_dir, "files"))

    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=1, ensure_ascii=False)
        handle.write("\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", default=os.path.join(REPO_ROOT, "metadata.md"))
    parser.add_argument("--files", default=os.path.join(REPO_ROOT, "files"))
    parser.add_argument("--assemble", metavar="DIR", help="write the full site to DIR")
    parser.add_argument("--commit", help="commit SHA to record in the manifest")
    parser.add_argument("--check", action="store_true", help="validate only, write nothing")
    args = parser.parse_args(argv)

    try:
        with open(args.metadata, encoding="utf-8") as handle:
            entries = parse_metadata(handle.read())
        check_against_files(entries, args.files)
        manifest = build_manifest(entries, args.files, args.commit)
    except BuildError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    if args.check:
        print(f"ok: {manifest['count']} entries, {manifest['totalSize']}")
        return 0

    if args.assemble:
        assemble(manifest, args.assemble, args.files)
        print(
            f"built {args.assemble}: {manifest['count']} entries, "
            f"{len(manifest['tags'])} tags, {manifest['totalSize']}"
        )
    else:
        json.dump(manifest, sys.stdout, indent=1, ensure_ascii=False)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
