#!/usr/bin/env python3
"""
Tests that the Gradle wrapper JAR is committed (not git-ignored) in templates.

Specification:
- A generated project must track gradle/wrapper/gradle-wrapper.jar, per Gradle's
  recommendation, so the project builds without a pre-installed Gradle.
- A .gitignore with a broad "*.jar" rule must therefore un-ignore the wrapper jar
  with a negation placed AFTER "*.jar" (last matching pattern wins in git).

This test uses git's own ignore evaluation (git check-ignore) against each
template .gitignore, which is the ground truth.

Usage:
    python test_wrapper_gitignore.py
    python -m pytest test_wrapper_gitignore.py -v
"""

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import List, Optional

WRAPPER_JAR = "gradle/wrapper/gradle-wrapper.jar"


def find_templates_repo() -> Optional[Path]:
    locations = [
        Path.home() / ".gradleInit" / "templates" / "official",
        Path(__file__).parent.parent / "gradleInitTemplates",
        Path(__file__).parent / "gradleInitTemplates",
    ]
    for location in locations:
        if location.exists() and location.is_dir():
            return location
    return None


def templates_with_gitignore(templates_dir: Path) -> List[Path]:
    result = []
    for item in sorted(templates_dir.iterdir()):
        if item.is_dir() and (item / ".gitignore").exists():
            result.append(item)
    return result


def is_ignored(gitignore_text: str, path: str) -> bool:
    """Return True if git would ignore `path` given this .gitignore content."""
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        (repo / ".gitignore").write_text(gitignore_text, encoding="utf-8")
        result = subprocess.run(
            ["git", "check-ignore", "-q", path],
            cwd=repo,
        )
        # exit 0 -> path is ignored; exit 1 -> not ignored.
        return result.returncode == 0


class TestWrapperJarTracked(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if shutil.which("git") is None:
            raise unittest.SkipTest("git not available")
        cls.templates_dir = find_templates_repo()
        if not cls.templates_dir:
            raise unittest.SkipTest("Templates repository not found")
        cls.templates = templates_with_gitignore(cls.templates_dir)
        if not cls.templates:
            raise unittest.SkipTest("No templates with .gitignore found")

    def test_wrapper_jar_not_ignored(self):
        for template in self.templates:
            with self.subTest(template=template.name):
                text = (template / ".gitignore").read_text(encoding="utf-8")
                self.assertFalse(
                    is_ignored(text, WRAPPER_JAR),
                    f"{template.name}: {WRAPPER_JAR} is git-ignored; the "
                    f"negation must come after the *.jar rule",
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
