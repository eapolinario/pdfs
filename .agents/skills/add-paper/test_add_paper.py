#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Tests for the add-paper helper. Run: uv run .agents/skills/add-paper/test_add_paper.py"""

import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import add_paper  # noqa: E402


class NormaliseUrlTest(unittest.TestCase):
    def rewrite(self, url):
        return add_paper.normalise_url(url)[0]

    def test_github_blob_becomes_raw(self):
        self.assertEqual(
            self.rewrite("https://github.com/cordiverse/paper/blob/main/paper.pdf"),
            "https://raw.githubusercontent.com/cordiverse/paper/main/paper.pdf",
        )

    def test_arxiv_abs_becomes_pdf(self):
        self.assertEqual(
            self.rewrite("https://arxiv.org/abs/1706.03762"), "https://arxiv.org/pdf/1706.03762"
        )

    def test_arxiv_version_suffix_is_dropped(self):
        self.assertEqual(
            self.rewrite("https://arxiv.org/abs/1706.03762v5"), "https://arxiv.org/pdf/1706.03762"
        )

    def test_openreview_forum_becomes_pdf(self):
        self.assertEqual(
            self.rewrite("https://openreview.net/forum?id=abc"), "https://openreview.net/pdf?id=abc"
        )

    def test_plain_pdf_url_is_untouched(self):
        url = "https://pablo.rauzy.name/dev/naur1985programming.pdf"
        self.assertEqual(self.rewrite(url), url)
        self.assertIsNone(add_paper.normalise_url(url)[1])

    def test_raw_github_url_is_untouched(self):
        url = "https://raw.githubusercontent.com/o/r/main/paper.pdf"
        self.assertEqual(self.rewrite(url), url)


class ResolveSourceTest(unittest.TestCase):
    def test_http_url_is_a_url(self):
        self.assertEqual(
            add_paper.resolve_source("https://example.org/paper.pdf"),
            ("url", "https://example.org/paper.pdf"),
        )

    def test_file_url_becomes_a_path(self):
        self.assertEqual(
            add_paper.resolve_source("file:///tmp/a%20paper.pdf"), ("path", "/tmp/a paper.pdf")
        )

    def test_file_url_with_localhost_host_becomes_a_path(self):
        self.assertEqual(
            add_paper.resolve_source("file://localhost/tmp/paper.pdf"), ("path", "/tmp/paper.pdf")
        )

    def test_file_url_with_a_remote_host_is_rejected(self):
        with self.assertRaises(add_paper.Failure):
            add_paper.resolve_source("file://elsewhere/tmp/paper.pdf")

    def test_absolute_path_is_a_path(self):
        self.assertEqual(add_paper.resolve_source("/tmp/paper.pdf"), ("path", "/tmp/paper.pdf"))

    def test_tilde_is_expanded(self):
        self.assertEqual(
            add_paper.resolve_source("~/Downloads/paper.pdf"),
            ("path", os.path.expanduser("~/Downloads/paper.pdf")),
        )

    def test_relative_path_that_exists_is_a_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = os.path.join(tmp, "paper.pdf")
            open(target, "wb").close()
            cwd = os.getcwd()
            os.chdir(tmp)
            try:
                self.assertEqual(add_paper.resolve_source("paper.pdf"), ("path", target))
            finally:
                os.chdir(cwd)

    # A bare hostname is a typo'd URL far more often than a missing file.
    def test_scheme_less_url_stays_a_url(self):
        self.assertEqual(
            add_paper.resolve_source("arxiv.org/abs/1706.03762"),
            ("url", "arxiv.org/abs/1706.03762"),
        )

    def test_empty_argument_is_rejected(self):
        with self.assertRaises(add_paper.Failure):
            add_paper.resolve_source("   ")


class LocalStagingTest(unittest.TestCase):
    def stage(self, contents, name="paper.pdf"):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp)
        source = os.path.join(tmp, name)
        with open(source, "wb") as handle:
            handle.write(contents)
        return source, os.path.join(tmp, "staged.pdf")

    def test_copies_a_real_pdf(self):
        source, dest = self.stage(b"%PDF-1.4\nbody\n")
        add_paper.copy_local(source, dest)
        with open(dest, "rb") as handle:
            self.assertEqual(handle.read(), b"%PDF-1.4\nbody\n")

    def test_rejects_html_saved_as_pdf(self):
        source, dest = self.stage(b"<!DOCTYPE html>")
        with self.assertRaises(add_paper.Failure):
            add_paper.copy_local(source, dest)
        self.assertFalse(os.path.exists(dest))

    def test_rejects_an_empty_file(self):
        source, dest = self.stage(b"")
        with self.assertRaises(add_paper.Failure):
            add_paper.copy_local(source, dest)

    def test_rejects_a_missing_file(self):
        with self.assertRaises(add_paper.Failure):
            add_paper.copy_local("/nonexistent/paper.pdf", "/tmp/staged.pdf")

    def test_rejects_a_directory(self):
        source, dest = self.stage(b"%PDF-1.4\n")
        with self.assertRaises(add_paper.Failure):
            add_paper.copy_local(os.path.dirname(source), dest)


class NamingTest(unittest.TestCase):
    def test_matches_the_repo_convention(self):
        self.assertEqual(
            add_paper.suggest_name("Programming as Theory Building", "Peter Naur", "1985"),
            "naur1985programming.pdf",
        )

    def test_skips_stopwords(self):
        self.assertEqual(
            add_paper.suggest_name("A Note on the Confinement Problem", "Butler Lampson", "1973"),
            "lampson1973note.pdf",
        )

    def test_uses_first_author_surname(self):
        self.assertEqual(
            add_paper.suggest_name("Attention Is All You Need", "Ashish Vaswani, Noam Shazeer", "2017"),
            "vaswani2017attention.pdf",
        )

    def test_strips_punctuation_and_case(self):
        self.assertEqual(
            add_paper.suggest_name("Time, Clocks!", "Leslie Lamport", "1978"),
            "lamport1978time.pdf",
        )

    # A half-guess looks authoritative enough to get accepted by mistake.
    def test_refuses_to_guess_without_an_author(self):
        self.assertEqual(add_paper.suggest_name("Attention Is All You Need", "", "2017"), "")

    def test_refuses_to_guess_without_a_year(self):
        self.assertEqual(add_paper.suggest_name("Some Title", "Peter Naur", ""), "")

    def test_refuses_to_guess_without_a_title(self):
        self.assertEqual(add_paper.suggest_name("", "Peter Naur", "1985"), "")


class CleanAuthorTest(unittest.TestCase):
    def test_strips_hyperref_artifact(self):
        self.assertEqual(add_paper.clean_author("Peter Naur]hyperref"), "Peter Naur")

    def test_strips_latex_commands_and_braces(self):
        self.assertEqual(add_paper.clean_author(r"{\bf Leslie Lamport}"), "Leslie Lamport")

    def test_handles_missing_author(self):
        self.assertEqual(add_paper.clean_author(None), "")


class EscapeCellTest(unittest.TestCase):
    def test_escapes_pipes(self):
        self.assertEqual(add_paper.escape_cell("a | b"), "a \\| b")

    def test_trims_whitespace(self):
        self.assertEqual(add_paper.escape_cell("  padded  "), "padded")


class YearGuessTest(unittest.TestCase):
    def test_prefers_a_year_on_the_first_page(self):
        self.assertEqual(add_paper.guess_year({"CreationDate": "Tue Jun 2 2020"}, "Naur 1985"), "1985")

    def test_falls_back_to_the_typeset_date(self):
        self.assertEqual(add_paper.guess_year({"CreationDate": "Tue Jun 2 05:59:16 2020"}, ""), "2020")

    def test_returns_empty_when_nothing_is_known(self):
        self.assertEqual(add_paper.guess_year({}, ""), "")


class TagsTest(unittest.TestCase):
    def test_reads_the_tag_list_from_agents_md(self):
        tags = add_paper.known_tags()
        self.assertIn("essay", tags)
        self.assertIn("software-engineering", tags)
        # The list must stop at the next heading, not swallow the whole file.
        self.assertTrue(all(" " not in tag for tag in tags), tags)


class SharedWithSiteBuildTest(unittest.TestCase):
    def test_size_formatting_matches_the_site(self):
        self.assertIs(add_paper.human_size, add_paper.build.human_size)
        self.assertEqual(add_paper.human_size(115468), "113 KB")


if __name__ == "__main__":
    unittest.main(verbosity=2)
