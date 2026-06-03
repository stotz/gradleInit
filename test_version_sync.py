#!/usr/bin/env python3
"""
Tests for tools/version_sync.py (--check mode).

Specification:
- parse_ssot reads the version SSoT into a flat alias->version dict and exposes
  the Gradle version under the alias 'gradle'.
- run_check reports zero issues when every derived location (template catalogs,
  tool defaults, annotated READMEs) matches the SSoT.
- The individual checks detect: a drifted catalog value, a drifted or unknown
  README span, a drifted generated block, drifted tool defaults, and an
  unmarked version number inside a managed prose region (strict mode).

Usage:
    python test_version_sync.py
    python -m pytest test_version_sync.py -v
"""

import importlib.util
import sys
import unittest
from pathlib import Path


_HERE = Path(__file__).parent
_TOOL = _HERE / "tools" / "version_sync.py"
_SPEC = importlib.util.spec_from_file_location("version_sync", str(_TOOL))
version_sync = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(version_sync)

# Directory that contains both gradleInit and gradleInitTemplates.
ROOT = _HERE.parent
VERSIONS_DIR = _HERE / "versions"


class TestParseSsot(unittest.TestCase):
    """parse_ssot exposes all versions including the synthetic 'gradle'."""

    def test_parses_known_values(self):
        ssot, overrides = version_sync.parse_ssot(VERSIONS_DIR)
        self.assertEqual(ssot["kotlin"], "2.3.10")
        self.assertEqual(ssot["gradle"], "9.3.1")
        self.assertEqual(ssot["junit"], "5.13.4")
        self.assertEqual(ssot["shadow"], "9.3.1")
        self.assertEqual(overrides, [])


class TestRunCheckConsistent(unittest.TestCase):
    """The bootstrapped repositories must be fully consistent."""

    def test_no_issues_on_bootstrap(self):
        errors = version_sync.run_check(ROOT)
        self.assertEqual(errors, [], "expected a clean tree, got:\n" + "\n".join(errors))


class TestSpanChecks(unittest.TestCase):
    def test_unknown_key_is_error(self):
        errors = version_sync.check_readme_spans(
            "x <!--v:bogus-->1.0<!--/v--> y", {"kotlin": "2.3.10"}, "f"
        )
        self.assertEqual(len(errors), 1)
        self.assertIn("unknown version key", errors[0])

    def test_value_mismatch_is_error(self):
        errors = version_sync.check_readme_spans(
            "<!--v:kotlin-->9.9.9<!--/v-->", {"kotlin": "2.3.10"}, "f"
        )
        self.assertEqual(len(errors), 1)
        self.assertIn("SSoT says 2.3.10", errors[0])

    def test_matching_span_is_clean(self):
        errors = version_sync.check_readme_spans(
            "<!--v:kotlin-->2.3.10<!--/v-->", {"kotlin": "2.3.10"}, "f"
        )
        self.assertEqual(errors, [])


class TestVregionStrict(unittest.TestCase):
    def test_unmarked_version_is_error(self):
        text = "<!-- vregion:begin -->Foo 1.2.3 bar<!-- vregion:end -->"
        errors = version_sync.check_vregion_strict(text, "f")
        self.assertEqual(len(errors), 1)
        self.assertIn("unmarked version", errors[0])

    def test_marked_version_is_clean(self):
        text = "<!-- vregion:begin -->Foo <!--v:foo-->1.2.3<!--/v--> bar<!-- vregion:end -->"
        errors = version_sync.check_vregion_strict(text, "f")
        self.assertEqual(errors, [])


class TestBlockCheck(unittest.TestCase):
    def test_block_mismatch_is_error(self):
        text = (
            "<!-- versions:begin -->\n"
            "JUnit:       9.9.9\n"
            "<!-- versions:end -->"
        )
        errors = version_sync.check_readme_block(text, {"junit": "5.13.4"}, "f")
        self.assertEqual(len(errors), 1)
        self.assertIn("SSoT says 5.13.4", errors[0])


class TestToolDefaults(unittest.TestCase):
    def test_gradle_default_mismatch_is_error(self):
        text = "DEFAULT_GRADLE_VERSION = \"1.0\"\n        'kotlin_version': '2.3.10',\n"
        errors = version_sync.check_tool_defaults(
            text, {"gradle": "9.3.1", "kotlin": "2.3.10"}
        )
        self.assertEqual(len(errors), 1)
        self.assertIn("DEFAULT_GRADLE_VERSION", errors[0])


class TestApplyFunctions(unittest.TestCase):
    def test_apply_span_updates_known_only(self):
        text = "<!--v:shadow-->9.0.0<!--/v--> <!--v:bogus-->1.0<!--/v-->"
        new_text, changes = version_sync.apply_readme_spans(text, {"shadow": "9.3.1"})
        self.assertIn("<!--v:shadow-->9.3.1<!--/v-->", new_text)
        self.assertIn("<!--v:bogus-->1.0<!--/v-->", new_text)
        self.assertEqual(len(changes), 1)

    def test_apply_toml_skips_jinja_and_respects_section(self):
        text = (
            "[versions]\n"
            'kotlin = "{{ kotlin_version }}"\n'
            'shadow = "9.0.0"\n'
            "\n[libraries]\n"
            'shadow-lib = { module = "x", version.ref = "shadow" }\n'
        )
        new_text, changes = version_sync.apply_toml_versions(
            text, {"shadow": "9.3.1", "kotlin": "2.3.10"}, [], "demo"
        )
        self.assertIn('shadow = "9.3.1"', new_text)
        self.assertIn('kotlin = "{{ kotlin_version }}"', new_text)  # untouched
        self.assertIn('version.ref = "shadow"', new_text)  # library line untouched
        self.assertEqual(len(changes), 1)

    def test_apply_tool_defaults_updates_both(self):
        text = "DEFAULT_GRADLE_VERSION = \"1.0\"\n    'kotlin_version': '0.0.1',\n"
        new_text, changes = version_sync.apply_tool_defaults(
            text, {"gradle": "9.3.1", "kotlin": "2.3.10"}
        )
        self.assertIn('DEFAULT_GRADLE_VERSION = "9.3.1"', new_text)
        self.assertIn("'kotlin_version': '2.3.10'", new_text)
        self.assertEqual(len(changes), 2)

    def test_apply_block_preserves_label_and_note(self):
        text = (
            "<!-- versions:begin -->\n"
            "Kotlin:      0.0.1 (via kotlin_version variable)\n"
            "<!-- versions:end -->"
        )
        new_text, changes = version_sync.apply_readme_block(text, {"kotlin": "2.3.10"})
        self.assertIn("Kotlin:      2.3.10 (via kotlin_version variable)", new_text)
        self.assertEqual(len(changes), 1)


class TestApplyRoundtrip(unittest.TestCase):
    """A bumped SSoT propagated by --apply must leave --check clean."""

    def test_bump_apply_then_check_clean(self):
        import shutil
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            shutil.copytree(_HERE, tmp_root / "gradleInit")
            shutil.copytree(ROOT / "gradleInitTemplates", tmp_root / "gradleInitTemplates")

            # No-op apply on the consistent copy changes nothing.
            self.assertEqual(version_sync.run_apply(tmp_root), [])

            # Bump JUnit in the SSoT only.
            ssot_toml = tmp_root / "gradleInit" / "versions" / "gradle" / "libs.versions.toml"
            ssot_toml.write_text(
                ssot_toml.read_text(encoding="utf-8").replace(
                    'junit = "5.13.4"', 'junit = "5.99.0"'
                ),
                encoding="utf-8",
            )

            # Now there is drift; apply must resolve it everywhere.
            self.assertNotEqual(version_sync.run_check(tmp_root), [])
            changes = version_sync.run_apply(tmp_root)
            self.assertTrue(changes)
            self.assertEqual(
                version_sync.run_check(tmp_root), [],
                "check must be clean after apply",
            )

            # The propagated value is present in a template catalog.
            cat = (tmp_root / "gradleInitTemplates" / "kotlin-single"
                   / "gradle" / "libs.versions.toml").read_text(encoding="utf-8")
            self.assertIn('junit = "5.99.0"', cat)


class TestUpdateMode(unittest.TestCase):
    """version_sync --update raises only the SSoT (Gradle path is deterministic)."""

    @classmethod
    def setUpClass(cls):
        gi_path = _HERE / "gradleInit.py"
        spec = importlib.util.spec_from_file_location("gradleInit", str(gi_path))
        cls.gi = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.gi)

    def test_gradle_ssot_plan_picks_within_policy(self):
        toml_text = "[versions]\n# gradle @^\nkotlin = \"2.3.10\"\n"
        wrapper = ("distributionUrl=https\\://services.gradle.org/distributions/"
                   "gradle-9.4.1-bin.zip\n")
        available = ["9.4.1", "9.5.1", "10.0.0", "9.7.0-20260602012325+0000"]
        current, target, policy = version_sync.gradle_ssot_plan(
            self.gi, toml_text, wrapper, available)
        self.assertEqual((current, policy), ("9.4.1", "^"))
        self.assertEqual(target, "9.5.1")  # caret stays below the next major, no nightly

    def test_gradle_ssot_plan_pin(self):
        toml_text = "[versions]\n# gradle @pin\n"
        wrapper = "distributionUrl=...gradle-9.4.1-bin.zip\n"
        _, target, _ = version_sync.gradle_ssot_plan(self.gi, toml_text, wrapper, ["9.5.1"])
        self.assertIsNone(target)

    def test_gradle_ssot_plan_no_policy(self):
        self.assertEqual(
            version_sync.gradle_ssot_plan(self.gi, "[versions]\n", "x", ["9.5.1"]),
            (None, None, None))

    def test_run_update_writes_only_ssot_wrapper(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vdir = root / "gradleInit" / "versions" / "gradle"
            (vdir / "wrapper").mkdir(parents=True)
            (vdir / "libs.versions.toml").write_text(
                "[versions]\n# gradle @*\nkotlin = \"2.3.10\"\n", encoding="utf-8")
            wrapper = vdir / "wrapper" / "gradle-wrapper.properties"
            wrapper.write_text(
                "distributionUrl=https\\://services.gradle.org/distributions/"
                "gradle-9.4.1-bin.zip\n", encoding="utf-8")

            original_fetch = self.gi.fetch_gradle_versions
            self.gi.fetch_gradle_versions = lambda **kw: ["9.4.1", "9.5.1",
                                                          "9.7.0-20260602012325+0000"]
            try:
                rc = version_sync.run_update(root, assume_yes=True, gi=self.gi,
                                             maven_central=None)
            finally:
                self.gi.fetch_gradle_versions = original_fetch

            self.assertEqual(rc, 0)
            self.assertIn("gradle-9.5.1-bin.zip", wrapper.read_text(encoding="utf-8"))
            self.assertNotIn(b"\r", wrapper.read_bytes())  # LF only, never CRLF

    def test_run_update_ssot_toml_is_lf(self):
        import tempfile

        class FakeMaven:
            def get_versions(self, g, a, limit=1, include_prerelease=False):
                return ["1.1.0"]
            def get_matching_version(self, g, a, ctype, cvalue, current):
                return "1.1.0"
            def get_version_info(self, g, a):
                return {"version": "1.1.0", "age_hours": 1000}
            def get_latest_version(self, g, a):
                return "1.1.0"

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vdir = root / "gradleInit" / "versions" / "gradle"
            (vdir / "wrapper").mkdir(parents=True)
            toml = vdir / "libs.versions.toml"
            toml.write_text(
                "[versions]\n# gradle @*\n"
                "# https://mvnrepository.com/artifact/io.mockk/mockk @^\n"
                'mockk = "1.0.0"\n\n'
                "[libraries]\n"
                'mockk = { module = "io.mockk:mockk", version.ref = "mockk" }\n',
                encoding="utf-8")
            wrapper = vdir / "wrapper" / "gradle-wrapper.properties"
            wrapper.write_text("distributionUrl=...gradle-9.4.1-bin.zip\n", encoding="utf-8")

            original_fetch = self.gi.fetch_gradle_versions
            self.gi.fetch_gradle_versions = lambda **kw: ["9.4.1"]
            try:
                rc = version_sync.run_update(root, assume_yes=True, gi=self.gi,
                                             maven_central=FakeMaven())
            finally:
                self.gi.fetch_gradle_versions = original_fetch

            self.assertEqual(rc, 0)
            self.assertIn('mockk = "1.1.0"', toml.read_text(encoding="utf-8"))
            self.assertNotIn(b"\r", toml.read_bytes())  # SSoT catalog stays LF


class TestWriteLf(unittest.TestCase):
    """version_sync must write LF on every platform (signature hashes raw bytes)."""

    def test_normalizes_crlf_to_lf(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "f.txt"
            version_sync._write_lf(p, "a\r\nb\r\nc\n")
            self.assertEqual(p.read_bytes(), b"a\nb\nc\n")


if __name__ == "__main__":
    unittest.main(verbosity=2)
