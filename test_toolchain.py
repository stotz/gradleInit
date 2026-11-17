#!/usr/bin/env python3
"""
Tests for the JVM toolchain configuration in template build files.

Specification:
- A template must set its Gradle JVM toolchain to the SELECTED JDK, so the build
  runs on the JDK the user chose and has installed.
- A template must NOT cap the toolchain below the selected JDK (the historical
  minOf(jdk, 24) pattern). Capping the toolchain forces Gradle to look for a JDK
  that may not be installed (the JDK-25 build failure). Kotlin 2.3.0+ emits Java
  25 bytecode, so the cap is obsolete for the pinned Kotlin.

Usage:
    python test_toolchain.py
    python -m pytest test_toolchain.py -v
"""

import unittest
from pathlib import Path
from typing import List, Optional


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


def gradle_build_files(templates_dir: Path) -> List[Path]:
    """All Gradle Kotlin DSL build files, including subproject/raw variants."""
    files: List[Path] = []
    for path in templates_dir.rglob("*"):
        if not path.is_file():
            continue
        name = path.name
        if name.endswith(".gradle.kts") or ".gradle.kts." in name or name.endswith(".kts"):
            files.append(path)
    return files


class TestToolchainNotCapped(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.templates_dir = find_templates_repo()
        if not cls.templates_dir:
            raise unittest.SkipTest("Templates repository not found")
        cls.build_files = gradle_build_files(cls.templates_dir)

    def test_no_capped_toolchain(self):
        """No build file may cap the toolchain via jvmToolchain(minOf(...))."""
        offenders = []
        for path in self.build_files:
            text = path.read_text(encoding="utf-8")
            if "jvmToolchain(minOf(" in text:
                offenders.append(str(path.relative_to(self.templates_dir)))
        self.assertEqual(
            offenders, [],
            "toolchain must use the selected JDK, not a capped value; offenders: "
            + ", ".join(offenders),
        )

    def test_toolchain_uses_jdk(self):
        """Every jvmToolchain call must reference the selected JDK version."""
        bad = []
        for path in self.build_files:
            for line in path.read_text(encoding="utf-8").splitlines():
                if "jvmToolchain(" in line:
                    if "jdk" not in line and "jdkVersion" not in line:
                        bad.append(f"{path.name}: {line.strip()}")
        self.assertEqual(bad, [], "jvmToolchain calls without a JDK reference: " + ", ".join(bad))


if __name__ == "__main__":
    unittest.main(verbosity=2)
