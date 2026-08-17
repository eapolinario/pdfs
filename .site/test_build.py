#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Tests for the metadata.md parser. Run: uv run .site/test_build.py"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import build  # noqa: E402

HEADER = (
    "| Title | Author(s) | Year | Tags | Pages | Size | Source | Added | Notes |\n"
    "| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
)

ROW = (
    "| [Programming as Theory Building](files/naur1985programming.pdf) | Peter Naur | 1985 "
    "| epistemology, essay | 8 | 113 KB | https://example.com/x.pdf | 2026-08-16 "
    "| Essay from *Microprocessing* 15(5). |\n"
)


def doc(*rows):
    return "# Metadata\n\nSome prose.\n\n" + HEADER + "".join(rows)


class ParseTest(unittest.TestCase):
    def test_parses_a_row(self):
        entry = build.parse_metadata(doc(ROW))[0]
        self.assertEqual(entry["title"], "Programming as Theory Building")
        self.assertEqual(entry["path"], "files/naur1985programming.pdf")
        self.assertEqual(entry["authors"], "Peter Naur")
        self.assertEqual(entry["year"], 1985)
        self.assertEqual(entry["tags"], ["epistemology", "essay"])
        self.assertEqual(entry["pages"], 8)
        self.assertEqual(entry["size"], "113 KB")
        self.assertEqual(entry["added"], "2026-08-16")

    def test_strips_markdown_emphasis_from_notes(self):
        entry = build.parse_metadata(doc(ROW))[0]
        self.assertEqual(entry["notes"], "Essay from Microprocessing 15(5).")

    def test_tags_are_sorted_and_deduplicated(self):
        row = ROW.replace("| epistemology, essay |", "| essay, epistemology,  essay |")
        self.assertEqual(build.parse_metadata(doc(row))[0]["tags"], ["epistemology", "essay"])

    def test_escaped_pipes_survive(self):
        row = ROW.replace("Essay from", "Escaped \\| pipe from")
        self.assertIn("Escaped | pipe", build.parse_metadata(doc(row))[0]["notes"])

    def test_ignores_prose_and_later_tables(self):
        text = doc(ROW) + "\nMore prose.\n\n| A |\n| --- |\n| ignored |\n"
        self.assertEqual(len(build.parse_metadata(text)), 1)

    def test_rejects_wrong_cell_count(self):
        with self.assertRaises(build.BuildError):
            build.parse_metadata(doc("| only | three | cells |\n"))

    def test_rejects_unlinked_title(self):
        with self.assertRaises(build.BuildError):
            build.parse_metadata(doc(ROW.replace(
                "[Programming as Theory Building](files/naur1985programming.pdf)",
                "Programming as Theory Building",
            )))

    def test_rejects_non_pdf_link(self):
        with self.assertRaises(build.BuildError):
            build.parse_metadata(doc(ROW.replace("files/naur1985programming.pdf", "http://x/y.pdf")))

    def test_rejects_untagged_entry(self):
        with self.assertRaises(build.BuildError):
            build.parse_metadata(doc(ROW.replace("| epistemology, essay |", "|  |")))

    def test_rejects_unknown_column(self):
        text = doc(ROW).replace("| Notes |", "| Remarks |")
        with self.assertRaises(build.BuildError):
            build.parse_metadata(text)

    def test_rejects_non_numeric_year(self):
        with self.assertRaises(build.BuildError):
            build.parse_metadata(doc(ROW.replace("| 1985 |", "| nineteen |")))


class FilesAgreementTest(unittest.TestCase):
    def setUp(self):
        self.entries = build.parse_metadata(doc(ROW))
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def touch(self, name):
        open(os.path.join(self.tmp.name, name), "wb").close()

    def test_accepts_matching_directory(self):
        self.touch("naur1985programming.pdf")
        build.check_against_files(self.entries, self.tmp.name)

    def test_rejects_missing_file(self):
        with self.assertRaises(build.BuildError):
            build.check_against_files(self.entries, self.tmp.name)

    def test_rejects_unlisted_file(self):
        self.touch("naur1985programming.pdf")
        self.touch("stray.pdf")
        with self.assertRaises(build.BuildError):
            build.check_against_files(self.entries, self.tmp.name)

    def test_rejects_duplicate_entries(self):
        self.touch("naur1985programming.pdf")
        with self.assertRaises(build.BuildError):
            build.check_against_files(self.entries * 2, self.tmp.name)


class ManifestTest(unittest.TestCase):
    def test_counts_tags_and_totals(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        with open(os.path.join(tmp.name, "naur1985programming.pdf"), "wb") as handle:
            handle.write(b"x" * 2048)

        manifest = build.build_manifest(build.parse_metadata(doc(ROW)), tmp.name, commit="abc")
        self.assertEqual(manifest["count"], 1)
        self.assertEqual(manifest["commit"], "abc")
        self.assertEqual(manifest["totalBytes"], 2048)
        self.assertEqual(manifest["totalPages"], 8)
        self.assertEqual(
            [tag["name"] for tag in manifest["tags"]], ["epistemology", "essay"]
        )

    def test_human_size(self):
        self.assertEqual(build.human_size(512), "512 B")
        self.assertEqual(build.human_size(115468), "113 KB")
        self.assertEqual(build.human_size(2140840), "2.0 MB")


class RealRepoTest(unittest.TestCase):
    def test_repository_metadata_is_valid(self):
        with open(os.path.join(build.REPO_ROOT, "metadata.md"), encoding="utf-8") as handle:
            entries = build.parse_metadata(handle.read())
        self.assertTrue(entries)
        build.check_against_files(entries, os.path.join(build.REPO_ROOT, "files"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
