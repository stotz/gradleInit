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

    def test_pin_never_updates(self):
        self.assertIsNone(
            gradleInit._select_gradle_target("9.4.1", self.AVAILABLE, "pin"))

    def test_no_newer_returns_none(self):
        self.assertIsNone(
            gradleInit._select_gradle_target("10.0.0", self.AVAILABLE, "*"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
