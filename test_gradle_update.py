#!/usr/bin/env python3
"""
Tests for the Gradle wrapper update logic in 'versions --update'.

Specification:
- The Gradle policy is a comment '# gradle @<policy>' in libs.versions.toml (the
  '=' form is tolerated). The marker must not match library lines.
- The current Gradle version is read from the distributionUrl in
  gradle-wrapper.properties; only the version inside the URL is rewritten.
- The target version is the highest available stable version that satisfies the
  policy and is newer than the current one; 'pin' never updates.

Usage:
    python test_gradle_update.py
    python -m pytest test_gradle_update.py -v
"""

import importlib.util
import sys
import unittest
from pathlib import Path

_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE))
_SPEC = importlib.util.spec_from_file_location("gradleInit", str(_HERE / "gradleInit.py"))
gradleInit = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(gradleInit)

WRAPPER = (
    "distributionBase=GRADLE_USER_HOME\n"
    "distributionPath=wrapper/dists\n"
    "distributionUrl=https\\://services.gradle.org/distributions/gradle-9.4.1-bin.zip\n"
    "networkTimeout=10000\n"
    "validateDistributionUrl=true\n"
)


class TestParsePolicy(unittest.TestCase):
    def test_canonical_form(self):
        self.assertEqual(gradleInit._parse_gradle_policy("# gradle @*"), "*")
        self.assertEqual(gradleInit._parse_gradle_policy("# gradle @pin"), "pin")
        self.assertEqual(gradleInit._parse_gradle_policy("# gradle @<10.0.0"), "<10.0.0")

    def test_strict_rejects_other_forms(self):
        # Only the canonical "# gradle @<policy>" form is accepted.
        self.assertIsNone(gradleInit._parse_gradle_policy("# gradle = @^"))
        self.assertIsNone(gradleInit._parse_gradle_policy("# gradle@*"))
        self.assertIsNone(gradleInit._parse_gradle_policy("# gradle pin"))

    def test_no_false_match(self):
        self.assertIsNone(gradleInit._parse_gradle_policy(
            "# https://mvnrepository.com/artifact/com.gradleup.shadow/shadow-gradle-plugin @*"))
        self.assertIsNone(gradleInit._parse_gradle_policy(
            "# Gradle wrapper version policy (value in gradle-wrapper.properties)"))
        self.assertIsNone(gradleInit._parse_gradle_policy("kotlin = \"2.4.0\""))


class TestWrapperVersion(unittest.TestCase):
    def test_extract(self):
        self.assertEqual(gradleInit._extract_gradle_version(WRAPPER), "9.4.1")

    def test_rewrite_only_version(self):
        out = gradleInit._rewrite_distribution_url(WRAPPER, "9.5.1")
        self.assertIn("gradle-9.5.1-bin.zip", out)
        self.assertNotIn("9.4.1", out)
        # everything else intact, including the escaped colon
        self.assertIn("https\\://services.gradle.org", out)
        self.assertIn("validateDistributionUrl=true", out)

    def test_rewrite_preserves_all_zip(self):
        text = WRAPPER.replace("-bin.zip", "-all.zip")
        out = gradleInit._rewrite_distribution_url(text, "9.5.1")
        self.assertIn("gradle-9.5.1-all.zip", out)


class TestFilterGradleVersions(unittest.TestCase):
    DATA = [
        {"version": "9.5.1"},
        {"version": "9.4.1"},
        {"version": "9.7.0-20260602012325+0000", "snapshot": True, "nightly": True},
        {"version": "9.6.0-rc-1", "rcFor": "9.6.0", "activeRc": True},
        {"version": "9.0-milestone-1", "milestoneFor": "9.0"},
        {"version": "8.14"},
        {"version": "9.9", "broken": True},
    ]

    def test_default_excludes_nonfinal_and_broken(self):
        self.assertEqual(
            gradleInit._filter_gradle_versions(self.DATA),
            ["9.5.1", "9.4.1", "8.14"],
        )

    def test_include_nightly(self):
        out = gradleInit._filter_gradle_versions(self.DATA, include_nightly=True)
        self.assertIn("9.7.0-20260602012325+0000", out)

    def test_include_rc(self):
        out = gradleInit._filter_gradle_versions(self.DATA, include_rc=True)
        self.assertIn("9.6.0-rc-1", out)


class TestSelectTarget(unittest.TestCase):
    AVAILABLE = ["8.14", "9.3.1", "9.4.1", "9.5.1", "10.0.0"]

    def test_star_picks_highest(self):
        self.assertEqual(
            gradleInit._select_gradle_target("9.4.1", self.AVAILABLE, "*"), "10.0.0")

    def test_upper_bound_stays_below_major(self):
        self.assertEqual(
            gradleInit._select_gradle_target("9.4.1", self.AVAILABLE, "<10.0.0"), "9.5.1")

    def test_caret_minor_only(self):
        self.assertEqual(
            gradleInit._select_gradle_target("9.4.1", self.AVAILABLE, "^9.0.0"), "9.5.1")

    def test_bare_caret_anchors_to_current(self):
        # '@^' has no base version; it must be anchored to the current version.
        self.assertEqual(
            gradleInit._select_gradle_target("9.4.1", self.AVAILABLE, "^"), "9.5.1")

    def test_pin_never_updates(self):
        self.assertIsNone(
            gradleInit._select_gradle_target("9.4.1", self.AVAILABLE, "pin"))

    def test_no_newer_returns_none(self):
        self.assertIsNone(
            gradleInit._select_gradle_target("10.0.0", self.AVAILABLE, "*"))

    def test_ignores_nightly_and_rc(self):
        available = ["9.4.1", "9.5.1", "9.7.0-20260602012325+0000", "9.6.0-rc-1"]
        self.assertEqual(
            gradleInit._select_gradle_target("9.4.1", available, "*"), "9.5.1")


class TestConstraintAnchor(unittest.TestCase):
    """A bare caret/tilde must be anchored to the current version (used by both
    the library and the Gradle update paths; the SSoT uses bare '@^')."""

    def setUp(self):
        self.C = gradleInit.VersionConstraintChecker

    def test_bare_caret_tilde_anchored(self):
        self.assertEqual(self.C.anchor("^", "9.3.1"), "^9.3.1")
        self.assertEqual(self.C.anchor("~", "9.3.1"), "~9.3.1")

    def test_other_constraints_unchanged(self):
        for c in ("*", "pin", "<10.0.0", "^9.0.0", ">=1.0"):
            self.assertEqual(self.C.anchor(c, "9.3.1"), c)

    def test_bare_caret_then_satisfies(self):
        anchored = self.C.anchor("^", "9.3.1")
        self.assertTrue(self.C.satisfies("9.4.2", anchored))   # minor within major
        self.assertFalse(self.C.satisfies("10.0.0", anchored)) # next major excluded


if __name__ == "__main__":
    unittest.main(verbosity=2)
