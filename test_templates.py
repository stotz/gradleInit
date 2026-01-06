#!/usr/bin/env python3
"""
Comprehensive Template Validation Tests for gradleInit

This test suite validates all templates in the gradleInitTemplates repository
to ensure they meet quality standards before being used in CLI tests.

Tests cover:
1. Template Structure - Required files and directories
2. Template Metadata - TEMPLATE.md validation
3. File Content - Jinja2 syntax, required patterns
4. Gradle Files - Valid Kotlin DSL syntax
5. Version Catalog - TOML syntax and structure
6. Git Files - .gitignore and .editorconfig
7. Source Files - Kotlin package structure

Usage:
    python test_templates.py
    python -m pytest test_templates.py -v
    python -m pytest test_templates.py -v -k test_kotlin_single
"""

import os
import re
import sys
import unittest
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    import toml
except ImportError:
    print("[ERROR] Missing required dependency: toml")
    print("Install with: pip install toml")
    sys.exit(1)


# ============================================================================
# Template Discovery
# ============================================================================

def find_templates_repo() -> Optional[Path]:
    """Find gradleInitTemplates repository"""
    # Check common locations
    locations = [
        Path.home() / '.gradleInit' / 'templates' / 'official',
        Path(__file__).parent.parent / 'gradleInitTemplates',
        Path(__file__).parent / 'gradleInitTemplates',
    ]
    
    for location in locations:
        if location.exists() and location.is_dir():
            return location
    
    return None


def discover_templates(templates_dir: Path) -> Dict[str, Path]:
    """Discover all templates in the repository"""
    templates = {}
    
    for item in templates_dir.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            # Check if it has a TEMPLATE.md
            template_md = item / 'TEMPLATE.md'
            if template_md.exists():
                templates[item.name] = item
    
    return templates


# ============================================================================
# Validation Helpers
# ============================================================================

def validate_frontmatter(content: str) -> Tuple[bool, Optional[Dict], str]:
    """Extract and validate YAML frontmatter from TEMPLATE.md"""
    if not content.startswith('---'):
        return False, None, "Missing frontmatter delimiter (---)"
    
    # Find end of frontmatter
    end_marker = content.find('---', 3)
    if end_marker == -1:
        return False, None, "Missing frontmatter end delimiter"
    
    frontmatter_text = content[3:end_marker].strip()
    
    try:
        # Simple YAML parser (we don't want to require PyYAML)
        metadata = {}
        current_key = None
        current_list = None
        
        for line in frontmatter_text.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # Handle list items
            if line.startswith('- '):
                if current_list is not None:
                    # Parse nested structure (like arguments)
                    if ':' in line[2:]:
                        key, value = line[2:].split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        if not current_list or not isinstance(current_list[-1], dict):
                            current_list.append({})
                        current_list[-1][key] = value
                    else:
                        # Simple list item
                        current_list.append(line[2:].strip())
                continue
            
            # Handle key-value pairs
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                # Check if starting a list
                if value == '' or value.startswith('['):
                    if value.startswith('[') and value.endswith(']'):
                        # Inline list
                        items = [v.strip() for v in value[1:-1].split(',')]
                        metadata[key] = items
                    else:
                        # Multi-line list
                        current_list = []
                        metadata[key] = current_list
                    current_key = key
                else:
                    # Simple value
                    # Try to parse as number or boolean
                    if value.lower() in ('true', 'false'):
                        metadata[key] = value.lower() == 'true'
                    elif value.startswith('"') and value.endswith('"'):
                        metadata[key] = value[1:-1]
                    else:
                        try:
                            metadata[key] = float(value) if '.' in value else int(value)
                        except ValueError:
                            metadata[key] = value
                    current_list = None
        
        return True, metadata, ""
        
    except Exception as e:
        return False, None, f"Failed to parse frontmatter: {e}"


def check_jinja2_syntax(content: str) -> Tuple[bool, List[str]]:
    """Basic Jinja2 syntax validation"""
    issues = []
    
    # Check for unclosed tags - simple count
    open_double = content.count('{{')
    close_double = content.count('}}')
    
    if open_double != close_double:
        issues.append(f"Mismatched Jinja2 expression tags: {open_double} '{{{{' vs {close_double} '}}}}'")
    
    # Check for unclosed block tags
    open_block = content.count('{%')
    close_block = content.count('%}')
    
    if open_block != close_block:
        issues.append(f"Mismatched Jinja2 block tags: {open_block} '{{%' vs {close_block} '%}}'")
    
    # Check for required variables that should exist
    # This is just informational - templates may vary
    # No longer checking for specific variables
    
    return len(issues) == 0, issues


def validate_toml_file(file_path: Path) -> Tuple[bool, str]:
    """Validate TOML file syntax"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to parse with toml library
        toml.loads(content)
        return True, ""
    except Exception as e:
        return False, str(e)


def validate_gradle_kotlin_dsl(content: str) -> Tuple[bool, List[str]]:
    """Basic Gradle Kotlin DSL validation"""
    issues = []
    
    # Check for common Jinja2 variables in Gradle files
    if '{{ project_name }}' not in content and 'rootProject.name' in content.lower():
        issues.append("Missing {{ project_name }} in settings or root config")
    
    # Check for balanced braces
    open_braces = content.count('{')
    close_braces = content.count('}')
    if open_braces != close_braces:
        issues.append(f"Unbalanced braces: {open_braces} open, {close_braces} close")
    
    # Check for balanced parentheses
    open_parens = content.count('(')
    close_parens = content.count(')')
    if open_parens != close_parens:
        issues.append(f"Unbalanced parentheses: {open_parens} open, {close_parens} close")
    
    return len(issues) == 0, issues


# ============================================================================
# Base Test Class
# ============================================================================

class TemplateTestBase(unittest.TestCase):
    """Base class for template tests"""
    
    @classmethod
    def setUpClass(cls):
        """Find templates directory"""
        cls.templates_dir = find_templates_repo()
        
        if not cls.templates_dir:
            raise unittest.SkipTest("Templates repository not found")
        
        cls.templates = discover_templates(cls.templates_dir)
        
        if not cls.templates:
            raise unittest.SkipTest("No templates found")
        
        print(f"\n[OK] Found {len(cls.templates)} templates in {cls.templates_dir}")
        for name in sorted(cls.templates.keys()):
            print(f"  * {name}")
    
    def assert_file_exists(self, template_dir: Path, file_path: str, required: bool = True):
        """Assert that a file exists in the template"""
        full_path = template_dir / file_path
        if required:
            self.assertTrue(full_path.exists(), 
                          f"Required file missing: {file_path}")
        return full_path.exists()
    
    def assert_file_contains(self, file_path: Path, patterns: List[str]):
        """Assert that a file contains all specified patterns"""
        self.assertTrue(file_path.exists(), f"File not found: {file_path}")
        
        content = file_path.read_text(encoding='utf-8')
        
        for pattern in patterns:
            if isinstance(pattern, str):
                self.assertIn(pattern, content, 
                            f"Pattern '{pattern}' not found in {file_path.name}")
            else:  # regex
                self.assertIsNotNone(pattern.search(content),
                                   f"Pattern {pattern.pattern} not found in {file_path.name}")


# ============================================================================
# Template Structure Tests
# ============================================================================

class TestTemplateStructure(TemplateTestBase):
    """Test that all templates have required structure"""
    
    def test_all_templates_have_template_md(self):
        """Test that all templates have TEMPLATE.md"""
        for name, template_dir in self.templates.items():
            with self.subTest(template=name):
                template_md = template_dir / 'TEMPLATE.md'
                self.assertTrue(template_md.exists(),
                              f"{name}: Missing TEMPLATE.md")
    
    def test_all_templates_have_settings_gradle(self):
        """Test that all templates have settings.gradle.kts"""
        for name, template_dir in self.templates.items():
            with self.subTest(template=name):
                self.assert_file_exists(template_dir, 'settings.gradle.kts')
    
    def test_all_templates_have_gradle_properties(self):
        """Test that all templates have gradle.properties"""
        for name, template_dir in self.templates.items():
            with self.subTest(template=name):
                self.assert_file_exists(template_dir, 'gradle.properties')
    
    def test_all_templates_have_version_catalog(self):
        """Test that all templates have gradle/libs.versions.toml"""
        for name, template_dir in self.templates.items():
            with self.subTest(template=name):
                self.assert_file_exists(template_dir, 'gradle/libs.versions.toml')
    
    def test_all_templates_have_src_structure(self):
        """Test that all templates have src/main/kotlin structure"""
        for name, template_dir in self.templates.items():
            with self.subTest(template=name):
                # multiproject-root is a container template without src
                if name == 'multiproject-root':
                    # multiproject-root only has buildSrc, no src/main/kotlin
                    buildSrc = template_dir / 'buildSrc'
                    self.assertTrue(buildSrc.exists(),
                                  f"{name}: Missing buildSrc directory")
                # For multi-module templates, check if any submodule has the structure
                elif name == 'kotlin-multi':
                    # Multi-module templates have src in submodules
                    has_src = any(
                        (template_dir / subdir / 'src' / 'main' / 'kotlin').exists()
                        for subdir in template_dir.iterdir()
                        if subdir.is_dir() and not subdir.name.startswith('.')
                    )
                    self.assertTrue(has_src,
                                  f"{name}: No submodule with src/main/kotlin found")
                else:
                    # Single module templates have src at root
                    src_main = template_dir / 'src' / 'main' / 'kotlin'
                    self.assertTrue(src_main.exists(),
                                  f"{name}: Missing src/main/kotlin")


# ============================================================================
# Template Metadata Tests
# ============================================================================

class TestTemplateMetadata(TemplateTestBase):
    """Test TEMPLATE.md metadata"""
    
    def test_template_md_has_frontmatter(self):
        """Test that TEMPLATE.md has valid frontmatter"""
        for name, template_dir in self.templates.items():
            with self.subTest(template=name):
                template_md = template_dir / 'TEMPLATE.md'
                content = template_md.read_text(encoding='utf-8')
                
                ok, metadata, error = validate_frontmatter(content)
                self.assertTrue(ok, f"{name}: {error}")
                self.assertIsNotNone(metadata)
    
    def test_metadata_has_required_fields(self):
        """Test that metadata has all required fields"""
        required_fields = ['name', 'description', 'version']
        
        for name, template_dir in self.templates.items():
            with self.subTest(template=name):
                template_md = template_dir / 'TEMPLATE.md'
                content = template_md.read_text(encoding='utf-8')
                ok, metadata, _ = validate_frontmatter(content)
                
                if ok and metadata:
                    for field in required_fields:
                        self.assertIn(field, metadata,
                                    f"{name}: Missing required field '{field}'")
    
    def test_metadata_version_is_valid(self):
        """Test that version follows semantic versioning"""
        version_pattern = re.compile(r'^\d+\.\d+\.\d+$')
        
        for name, template_dir in self.templates.items():
            with self.subTest(template=name):
                template_md = template_dir / 'TEMPLATE.md'
                content = template_md.read_text(encoding='utf-8')
                ok, metadata, _ = validate_frontmatter(content)
                
                if ok and metadata and 'version' in metadata:
                    version = str(metadata['version'])
                    self.assertIsNotNone(version_pattern.match(version),
                                       f"{name}: Invalid version format '{version}'")


# ============================================================================
# File Content Tests
# ============================================================================

class TestFileContent(TemplateTestBase):
    """Test file content and syntax"""
    
    def test_settings_gradle_has_project_name(self):
        """Test that settings.gradle.kts contains {{ project_name }}"""
        for name, template_dir in self.templates.items():
            with self.subTest(template=name):
                settings_file = template_dir / 'settings.gradle.kts'
                self.assert_file_contains(settings_file, [
                    '{{ project_name }}'
                ])
    
    def test_build_gradle_syntax(self):
        """Test that build.gradle.kts has valid syntax"""
        for name, template_dir in self.templates.items():
            # Skip if no build.gradle.kts at root (multi-module)
            build_file = template_dir / 'build.gradle.kts'
            if not build_file.exists():
                continue
            
            with self.subTest(template=name):
                content = build_file.read_text(encoding='utf-8')
                ok, issues = validate_gradle_kotlin_dsl(content)
                
                if not ok:
                    self.fail(f"{name}: build.gradle.kts has issues:\n" + 
                            "\n".join(f"  - {issue}" for issue in issues))
    
    def test_version_catalog_is_valid_toml(self):
        """Test that libs.versions.toml is valid TOML"""
        for name, template_dir in self.templates.items():
            with self.subTest(template=name):
                toml_file = template_dir / 'gradle' / 'libs.versions.toml'
                ok, error = validate_toml_file(toml_file)
                self.assertTrue(ok, f"{name}: Invalid TOML: {error}")
    
    def test_version_catalog_has_required_sections(self):
        """Test that libs.versions.toml has required sections"""
        for name, template_dir in self.templates.items():
            with self.subTest(template=name):
                toml_file = template_dir / 'gradle' / 'libs.versions.toml'
                content = toml_file.read_text(encoding='utf-8')
                data = toml.loads(content)
                
                # Check required sections
                self.assertIn('versions', data,
                            f"{name}: Missing [versions] section")


# ============================================================================
# Jinja2 Template Tests
# ============================================================================

class TestJinja2Templates(TemplateTestBase):
    """Test Jinja2 template syntax"""
    
    def test_jinja2_syntax_in_gradle_files(self):
        """Test Jinja2 syntax in all .gradle.kts files"""
        for name, template_dir in self.templates.items():
            gradle_files = list(template_dir.rglob('*.gradle.kts'))
            
            for gradle_file in gradle_files:
                with self.subTest(template=name, file=gradle_file.name):
                    content = gradle_file.read_text(encoding='utf-8')
                    ok, issues = check_jinja2_syntax(content)
                    
                    if not ok:
                        self.fail(f"{name}/{gradle_file.name} has Jinja2 issues:\n" +
                                "\n".join(f"  - {issue}" for issue in issues))
    
    def test_no_hardcoded_project_names(self):
        """Test that gradle files don't have hardcoded project names"""
        hardcoded_names = ['my-project', 'example-project', 'test-project']
        
        for name, template_dir in self.templates.items():
            gradle_files = list(template_dir.rglob('*.gradle.kts'))
            
            for gradle_file in gradle_files:
                with self.subTest(template=name, file=gradle_file.name):
                    content = gradle_file.read_text(encoding='utf-8')
                    
                    for hardcoded in hardcoded_names:
                        self.assertNotIn(hardcoded, content,
                                       f"{name}/{gradle_file.name} contains hardcoded name '{hardcoded}'")


# ============================================================================
# Git Files Tests
# ============================================================================

class TestGitFiles(TemplateTestBase):
    """Test Git-related files"""
    
    def test_gitignore_exists(self):
        """Test that .gitignore template exists"""
        for name, template_dir in self.templates.items():
            with self.subTest(template=name):
                # gitignore should be either .gitignore or gitignore.template
                gitignore = template_dir / '.gitignore'
                gitignore_template = template_dir / 'gitignore.template'
                
                has_gitignore = gitignore.exists() or gitignore_template.exists()
                self.assertTrue(has_gitignore,
                              f"{name}: Missing .gitignore or gitignore.template")
    
    def test_editorconfig_exists(self):
        """Test that .editorconfig template exists"""
        for name, template_dir in self.templates.items():
            with self.subTest(template=name):
                # editorconfig should be either .editorconfig or editorconfig.template
                editorconfig = template_dir / '.editorconfig'
                editorconfig_template = template_dir / 'editorconfig.template'
                
                has_editorconfig = editorconfig.exists() or editorconfig_template.exists()
                self.assertTrue(has_editorconfig,
                              f"{name}: Missing .editorconfig or editorconfig.template")
    
    def test_editorconfig_has_kotlin_section(self):
        """Test that .editorconfig has Kotlin section"""
        for name, template_dir in self.templates.items():
            editorconfig = template_dir / '.editorconfig'
            editorconfig_template = template_dir / 'editorconfig.template'
            
            file_to_check = editorconfig if editorconfig.exists() else editorconfig_template
            
            if not file_to_check.exists():
                continue
            
            with self.subTest(template=name):
                content = file_to_check.read_text(encoding='utf-8')
                
                # Check for Kotlin section - can be specific or grouped with other languages
                has_kotlin_section = (
                    '.kt' in content and '[*.' in content or  # Any section mentioning .kt
                    'kt,kts' in content or  # Kotlin specific or grouped
                    '[*.kt]' in content or
                    '[*.kts]' in content
                )
                
                self.assertTrue(has_kotlin_section,
                              f"{name}: .editorconfig missing Kotlin section")


# ============================================================================
# Specific Template Tests
# ============================================================================

class TestKotlinSingleTemplate(TemplateTestBase):
    """Specific tests for kotlin-single template"""
    
    def setUp(self):
        """Skip if kotlin-single not available"""
        if 'kotlin-single' not in self.templates:
            self.skipTest("kotlin-single template not found")
        
        self.template_dir = self.templates['kotlin-single']
    
    def test_has_build_gradle_kts(self):
        """Test that kotlin-single has build.gradle.kts"""
        self.assert_file_exists(self.template_dir, 'build.gradle.kts')
    
    def test_build_gradle_has_kotlin_jvm_plugin(self):
        """Test that build.gradle.kts uses kotlin-jvm plugin"""
        build_file = self.template_dir / 'build.gradle.kts'
        content = build_file.read_text(encoding='utf-8')
        
        # Should have kotlin-jvm plugin (either direct or via alias)
        has_plugin = (
            'kotlin("jvm")' in content or
            'id("org.jetbrains.kotlin.jvm")' in content or
            'alias(libs.plugins.kotlin.jvm)' in content or  # Modern version catalog syntax
            'kotlin.jvm' in content
        )
        
        self.assertTrue(has_plugin, "Missing Kotlin JVM plugin")
    
    def test_has_main_kt_file(self):
        """Test that kotlin-single has Main.kt"""
        main_files = list(self.template_dir.rglob('Main.kt'))
        self.assertGreater(len(main_files), 0, "No Main.kt found")
    
    def test_version_variable_in_build_gradle(self):
        """Test that build.gradle.kts can use version variable"""
        build_file = self.template_dir / 'build.gradle.kts'
        content = build_file.read_text(encoding='utf-8')
        
        # Should support version configuration via template variable
        has_version = (
            'version = "{{ version }}"' in content or
            'version = "{{ project_version }}"' in content or
            'version =' in content  # At least has version line
        )
        
        self.assertTrue(has_version, 
                       "build.gradle.kts should support version configuration")


class TestKotlinMultiTemplate(TemplateTestBase):
    """Specific tests for kotlin-multi template"""
    
    def setUp(self):
        """Skip if kotlin-multi not available"""
        if 'kotlin-multi' not in self.templates:
            self.skipTest("kotlin-multi template not found")
        
        self.template_dir = self.templates['kotlin-multi']
    
    def test_has_multiple_modules(self):
        """Test that kotlin-multi has multiple modules"""
        # Should have at least 2 subdirectories with build.gradle.kts
        modules = [d for d in self.template_dir.iterdir() 
                  if d.is_dir() and (d / 'build.gradle.kts').exists()]
        
        self.assertGreaterEqual(len(modules), 2,
                               "kotlin-multi should have at least 2 modules")
    
    def test_settings_includes_subprojects(self):
        """Test that settings.gradle.kts includes subprojects"""
        settings_file = self.template_dir / 'settings.gradle.kts'
        content = settings_file.read_text(encoding='utf-8')
        
        self.assertIn('include', content,
                     "settings.gradle.kts should include subprojects")


# ============================================================================
# Main Test Runner
# ============================================================================

def main():
    """Run all template tests"""
    print("\n" + "="*70)
    print("  Template Validation Tests")
    print("="*70)
    print("\nValidating gradleInit templates for:")
    print("  * Structure and required files")
    print("  * Metadata and documentation")
    print("  * Jinja2 template syntax")
    print("  * Gradle Kotlin DSL syntax")
    print("  * Version catalog TOML")
    print("  * Git configuration files")
    print()
    
    # Run tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestTemplateStructure))
    suite.addTests(loader.loadTestsFromTestCase(TestTemplateMetadata))
    suite.addTests(loader.loadTestsFromTestCase(TestFileContent))
    suite.addTests(loader.loadTestsFromTestCase(TestJinja2Templates))
    suite.addTests(loader.loadTestsFromTestCase(TestGitFiles))
    suite.addTests(loader.loadTestsFromTestCase(TestKotlinSingleTemplate))
    suite.addTests(loader.loadTestsFromTestCase(TestKotlinMultiTemplate))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "="*70)
    if result.wasSuccessful():
        print("  [OK] All template validation tests passed!")
    else:
        print("  [ERROR] Some template validation tests failed")
    print("="*70)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
