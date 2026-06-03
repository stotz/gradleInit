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


if __name__ == "__main__":
    unittest.main(verbosity=2)
