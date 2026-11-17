#!/usr/bin/env python3
"""
Tests for the --latest version-policy behavior.

Specification:
- A generated gradle/libs.versions.toml expresses the update policy for each
  dependency in the trailing constraint of its mvnrepository comment line.
- Without --latest the policy is @pin (default, never auto-update).
- With --latest the policy is @* (always update to latest).

These tests render the version catalog of every template through the real
rendering pipeline (hint compilation followed by Jinja2) and assert the
resulting constraints. The assertions inspect only the mvnrepository comment
lines, so the explanatory comment header (which always documents @pin and @*)
does not affect the result.

Usage:
    python test_version_policy.py
    python -m pytest test_version_policy.py -v
"""

import importlib.util
import sys
import unittest
from pathlib import Path
from typing import Dict, List, Optional


# Import gradleInit module (same pattern as test_cli.py)
_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE))
_SPEC = importlib.util.spec_from_file_location("gradleInit", str(_HERE / "gradleInit.py"))
gradleInit = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(gradleInit)


def find_templates_repo() -> Optional[Path]:
    """Locate the gradleInitTemplates repository."""
    locations = [
        Path.home() / ".gradleInit" / "templates" / "official",
        Path(__file__).parent.parent / "gradleInitTemplates",
        Path(__file__).parent / "gradleInitTemplates",
    ]
    for location in locations:
        if location.exists() and location.is_dir():
            return location
    return None


def discover_templates(templates_dir: Path) -> Dict[str, Path]:
    """Discover all templates that provide a TEMPLATE.md."""
    templates = {}
    for item in templates_dir.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            if (item / "TEMPLATE.md").exists():
                templates[item.name] = item
    return templates


def render_version_catalog(template_dir: Path, latest: bool) -> str:
    """Render gradle/libs.versions.toml through the real rendering pipeline.

    The context only needs the variables the catalog references after hint
    compilation: jdk_version, kotlin_version and version_policy.
    """
    toml_file = template_dir / "gradle" / "libs.versions.toml"
    context = {
        "jdk_version": "25",
        "kotlin_version": "2.3.10",
        "version_policy": "@*" if latest else "@pin",
    }
    metadata = gradleInit.TemplateMetadata(template_dir)
    compiled = metadata.compile_template_file(toml_file)
    env = gradleInit.setup_jinja2_environment(template_dir, context)
    return env.from_string(compiled).render(**context)


def extract_constraints(rendered_toml: str) -> List[str]:
    """Return the constraint tokens (without @) from all mvnrepository lines."""
    pattern = gradleInit.VersionManager.URL_PATTERN
    return [
        match.group(2)
        for match in pattern.finditer(rendered_toml)
        if match.group(2) is not None
    ]


class TestVersionPolicyConstraint(unittest.TestCase):
    """Specify that --latest controls the dependency constraints in the catalog."""

    @classmethod
    def setUpClass(cls):
        cls.templates_dir = find_templates_repo()
        if not cls.templates_dir:
            raise unittest.SkipTest("Templates repository not found")
        cls.templates = discover_templates(cls.templates_dir)
        if not cls.templates:
            raise unittest.SkipTest("No templates found")

    def test_default_policy_is_pin(self):
        """Without --latest every mvnrepository constraint must be @pin."""
        for name, template_dir in self.templates.items():
            with self.subTest(template=name):
                rendered = render_version_catalog(template_dir, latest=False)
                constraints = extract_constraints(rendered)
                self.assertTrue(
                    constraints, f"{name}: no mvnrepository constraints found"
                )
                self.assertTrue(
                    all(c == "pin" for c in constraints),
                    f"{name}: expected all constraints @pin, got {constraints}",
                )

    def test_latest_policy_is_star(self):
        """With --latest every mvnrepository constraint must be @*."""
        for name, template_dir in self.templates.items():
            with self.subTest(template=name):
                rendered = render_version_catalog(template_dir, latest=True)
                constraints = extract_constraints(rendered)
                self.assertTrue(
                    constraints, f"{name}: no mvnrepository constraints found"
                )
                self.assertTrue(
                    all(c == "*" for c in constraints),
                    f"{name}: expected all constraints @*, got {constraints}",
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
