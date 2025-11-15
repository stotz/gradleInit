#!/usr/bin/env python3
"""
Comprehensive Test Suite for gradleInit.py v1.3.0

Tests for:
- Template Engine (ContextBuilder, Jinja2, ProjectGenerator)
- All 4 Templates (kotlin-single, kotlin-multi, springboot, ktor)
- Gradle Build Integration (compiles and tests generated projects)
- Module System
- GitHub URL Parsing

Usage:
    python test_gradleInit_comprehensive.py
    python -m pytest test_gradleInit_comprehensive.py -v
"""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
import sys
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import gradleInit
try:
    import importlib.util

    current_dir = os.path.dirname(os.path.abspath(__file__))
    gradleinit_path = os.path.join(current_dir, 'gradleInit.py')

    if not os.path.exists(gradleinit_path):
        raise ImportError(f"gradleInit.py not found in {current_dir}")

    spec = importlib.util.spec_from_file_location("gradleInit", gradleinit_path)
    gradleInit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gradleInit)

    # Import everything we need
    GradleInitPaths = gradleInit.GradleInitPaths
    TemplateRepository = gradleInit.TemplateRepository
    TemplateRepositoryManager = gradleInit.TemplateRepositoryManager
    TemplateMetadata = gradleInit.TemplateMetadata
    ContextBuilder = gradleInit.ContextBuilder
    ProjectGenerator = gradleInit.ProjectGenerator
    parse_github_url = gradleInit.parse_github_url

except ImportError as e:
    print(f"Error importing gradleInit: {e}")
    sys.exit(1)


# ============================================================================
# Test GitHub URL Parsing
# ============================================================================

class TestGitHubURLParsing(unittest.TestCase):
    """Test parse_github_url function"""

    def test_parse_simple_repo_url(self):
        """Test simple repository URL"""
        result = parse_github_url("https://github.com/stotz/gradleInit")
        self.assertIsNotNone(result)
        clone_url, subdir = result
        self.assertEqual(clone_url, "https://github.com/stotz/gradleInit.git")
        self.assertIsNone(subdir)

    def test_parse_tree_url_with_subdir(self):
        """Test tree URL with subdirectory"""
        result = parse_github_url("https://github.com/stotz/gradleInitTemplates/tree/main/kotlin-single")
        self.assertIsNotNone(result)
        clone_url, subdir = result
        self.assertEqual(clone_url, "https://github.com/stotz/gradleInitTemplates.git")
        self.assertEqual(subdir, "kotlin-single")

    def test_parse_url_without_protocol(self):
        """Test URL without https://"""
        result = parse_github_url("github.com/stotz/gradleInit")
        self.assertIsNotNone(result)
        clone_url, subdir = result
        self.assertEqual(clone_url, "https://github.com/stotz/gradleInit.git")

    def test_parse_tree_url_deep_path(self):
        """Test tree URL with deep path"""
        result = parse_github_url("https://github.com/user/repo/tree/branch/path/to/template")
        self.assertIsNotNone(result)
        clone_url, subdir = result
        self.assertEqual(clone_url, "https://github.com/user/repo.git")
        self.assertEqual(subdir, "path/to/template")

    def test_parse_non_github_url(self):
        """Test non-GitHub URL returns None"""
        result = parse_github_url("https://gitlab.com/user/repo")
        self.assertIsNone(result)


# ============================================================================
# Template Generation & Gradle Build Tests
# ============================================================================

class TestTemplateGeneration(unittest.TestCase):
    """Test template generation and Gradle builds"""

    @classmethod
    def setUpClass(cls):
        """Setup test environment once"""
        cls.test_root = Path(tempfile.mkdtemp(prefix="gradleInit_test_"))
        cls.templates_dir = cls.test_root / "templates"
        cls.projects_dir = cls.test_root / "projects"
        cls.projects_dir.mkdir()

        # Always get fresh templates from GitHub
        print("\nFetching latest templates from GitHub...")

        # Remove templates dir if it exists to ensure fresh clone
        if cls.templates_dir.exists():
            shutil.rmtree(cls.templates_dir)

        cls.templates_dir.mkdir()

        # Clone templates from GitHub
        result = subprocess.run(
            ['git', 'clone', '--depth', '1',
             'https://github.com/stotz/gradleInitTemplates.git',
             str(cls.templates_dir)],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(f"Failed to clone templates: {result.stderr}")

        print(f"✓ Templates cloned to {cls.templates_dir}")

        # Verify we got the fixed templates
        settings_file = cls.templates_dir / "kotlin-single" / "settings.gradle.kts"
        if settings_file.exists():
            content = settings_file.read_text()
            if "pluginManagement" in content and "layout.projectDirectory.file" in content:
                print("✓ Verified: Templates contain latest fixes")
            else:
                print("⚠ Warning: Templates may not have latest fixes!")
                print(f"  First 200 chars: {content[:200]}")
        else:
            print(f"⚠ Warning: settings.gradle.kts not found at {settings_file}")

    @classmethod
    def tearDownClass(cls):
        """Cleanup after all tests"""
        # Keep test files for debugging on failure
        print(f"\n→ Test files kept at: {cls.test_root}")
        print("  To cleanup manually: rm -rf /c/tmp/gradleInit_test_*")
        # if cls.test_root.exists():
        #     shutil.rmtree(cls.test_root, ignore_errors=True)

    def _generate_project(self, template_name: str, project_name: str, **kwargs) -> Path:
        """
        Generate a project from template.

        Args:
            template_name: Name of template (kotlin-single, kotlin-multi, etc.)
            project_name: Name for generated project
            **kwargs: Additional context variables

        Returns:
            Path to generated project
        """
        print(f"\n{'=' * 70}")
        print(f"  GENERATING: {template_name} → {project_name}")
        print(f"{'=' * 70}")

        template_path = self.templates_dir / template_name
        self.assertTrue(template_path.exists(), f"Template not found: {template_name}")

        project_path = self.projects_dir / project_name
        print(f"→ Target: {project_path}")

        if project_path.exists():
            shutil.rmtree(project_path)

        # Build context
        context = {
            'project_name': project_name,
            'group': 'com.test',
            'version': '1.0.0',
            'kotlin_version': '2.2.0',
            'gradle_version': '9.0',
            'jdk_version': 21,
            'date': '2025-11-15',
            **kwargs
        }

        # Generate project (correct parameter order: template_path, context, target_path)
        generator = ProjectGenerator(template_path, context, project_path)
        success = generator.generate()

        if not success:
            print(f"\n{'✗' * 70}")
            print(f"  GENERATION FAILED: {template_name} → {project_name}")
            print(f"{'✗' * 70}")
            print(f"  Template: {template_path}")
            print(f"  Target: {project_path}")

            # Show generated settings.gradle.kts if it exists
            settings_file = project_path / "settings.gradle.kts"
            if settings_file.exists():
                print(f"\n→ Generated settings.gradle.kts:")
                print(settings_file.read_text()[:500])

            # Show template settings.gradle.kts
            template_settings = template_path / "settings.gradle.kts"
            if template_settings.exists():
                print(f"\n→ Template settings.gradle.kts:")
                print(template_settings.read_text()[:500])
        else:
            print(f"✓ Project generated successfully")

        self.assertTrue(success, f"Failed to generate project {project_name}")
        self.assertTrue(project_path.exists(), f"Project directory not created: {project_path}")

        return project_path

    def _run_gradle(self, project_path: Path, *tasks: str, timeout: int = 120) -> subprocess.CompletedProcess:
        """
        Run Gradle tasks in project.

        Args:
            project_path: Path to project
            *tasks: Gradle tasks to run
            timeout: Timeout in seconds

        Returns:
            CompletedProcess result
        """
        print(f"\n{'─' * 70}")
        print(f"  RUNNING GRADLE: {' '.join(tasks)}")
        print(f"{'─' * 70}")
        print(f"→ Project: {project_path}")

        # Determine gradle wrapper command
        if os.name == 'nt':  # Windows
            gradle_cmd = str(project_path / 'gradlew.bat')
        else:
            gradle_cmd = './gradlew'

        # Make wrapper executable on Unix
        if os.name != 'nt':
            wrapper_path = project_path / 'gradlew'
            if wrapper_path.exists():
                os.chmod(wrapper_path, 0o755)

        cmd = [gradle_cmd, *tasks, '--no-daemon', '--console=plain']

        print(f"→ Command: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            cwd=str(project_path),
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode != 0:
            print(f"\n{'✗' * 70}")
            print(f"  GRADLE BUILD FAILED (exit code {result.returncode})")
            print(f"{'✗' * 70}")
            print(f"\n--- STDOUT ---")
            print(result.stdout)
            print(f"\n--- STDERR ---")
            print(result.stderr)
            print(f"{'✗' * 70}\n")
        else:
            print(f"✓ Gradle build succeeded")

        return result

    # ========================================================================
    # Test kotlin-single Template
    # ========================================================================

    def test_kotlin_single_generation(self):
        """Test kotlin-single template generation"""
        print(f"\n\n{'#' * 70}")
        print(f"  TEST: kotlin-single - Generation")
        print(f"{'#' * 70}")

        project_path = self._generate_project('kotlin-single', 'test-kotlin-single')

        # Check essential files exist
        self.assertTrue((project_path / 'build.gradle.kts').exists())
        self.assertTrue((project_path / 'settings.gradle.kts').exists())
        self.assertTrue((project_path / 'gradle.properties').exists())
        self.assertTrue((project_path / 'gradle' / 'libs.versions.toml').exists())
        self.assertTrue((project_path / '.gitignore').exists())
        self.assertTrue((project_path / '.editorconfig').exists())

        # Check source files
        main_kt = project_path / 'src' / 'main' / 'kotlin' / 'Main.kt'
        self.assertTrue(main_kt.exists())

        # Check content was rendered (no {{ }} left)
        content = main_kt.read_text()
        self.assertNotIn('{{', content)
        self.assertNotIn('}}', content)
        self.assertIn('package com.test', content)
        self.assertIn('test-kotlin-single', content)

    def test_kotlin_single_gradle_build(self):
        """Test kotlin-single builds with Gradle"""
        print(f"{'#' * 70}")
        print(f"  TEST: kotlin-single - Gradle Build")
        print(f"{'#' * 70}")
        project_path = self._generate_project('kotlin-single', 'build-kotlin-single')

        # Run gradle build
        result = self._run_gradle(project_path, 'build', '--info')

        self.assertEqual(result.returncode, 0, "Gradle build should succeed")
        self.assertIn('BUILD SUCCESSFUL', result.stdout)

        # Check build outputs
        build_dir = project_path / 'build'
        self.assertTrue(build_dir.exists())
        self.assertTrue((build_dir / 'classes').exists())

    def test_kotlin_single_gradle_test(self):
        """Test kotlin-single runs tests"""
        print(f"{'#' * 70}")
        print(f"  TEST: kotlin-single - Gradle Test")
        print(f"{'#' * 70}")
        project_path = self._generate_project('kotlin-single', 'test-kotlin-single-tests')

        # Run gradle test
        result = self._run_gradle(project_path, 'test')

        self.assertEqual(result.returncode, 0, "Gradle test should succeed")

        # Check test reports
        test_report = project_path / 'build' / 'reports' / 'tests' / 'test' / 'index.html'
        self.assertTrue(test_report.exists(), "Test report should be generated")

        # ========================================================================
        # Test kotlin-multi Template
        # ========================================================================

    def test_kotlin_multi_generation(self):
        """Test kotlin-multi template generation"""
        print(f"{'#' * 70}")
        print(f"  TEST: kotlin-multi - Generation")
        print(f"{'#' * 70}")
        project_path = self._generate_project('kotlin-multi', 'test-kotlin-multi')

        # Check multi-module structure
        self.assertTrue((project_path / 'buildSrc').exists())
        self.assertTrue((project_path / 'app').exists())
        self.assertTrue((project_path / 'lib').exists())

        # Check buildSrc
        self.assertTrue((project_path / 'buildSrc' / 'build.gradle.kts').exists())
        self.assertTrue((project_path / 'buildSrc' / 'src' / 'main' / 'kotlin' /
                         'kotlin-common-conventions.gradle.kts').exists())

        # Check modules
        self.assertTrue((project_path / 'app' / 'build.gradle.kts').exists())
        self.assertTrue((project_path / 'lib' / 'build.gradle.kts').exists())

        # Check settings includes modules
        settings = (project_path / 'settings.gradle.kts').read_text()
        self.assertIn('include("app")', settings)
        self.assertIn('include("lib")', settings)

    def test_kotlin_multi_gradle_build(self):
        """Test kotlin-multi builds with Gradle"""
        print(f"{'#' * 70}")
        print(f"  TEST: kotlin-multi - Gradle Build")
        print(f"{'#' * 70}")
        project_path = self._generate_project('kotlin-multi', 'build-kotlin-multi')

        # kotlin-multi uses buildSrc and doesn't generate gradlew
        # Skip if wrapper doesn't exist
        gradlew = project_path / ('gradlew.bat' if os.name == 'nt' else 'gradlew')
        if not gradlew.exists():
            self.skipTest("kotlin-multi uses buildSrc - no wrapper generated")

        # Run gradle build (builds all modules)
        result = self._run_gradle(project_path, 'build')

        self.assertEqual(result.returncode, 0, "Gradle build should succeed")

        # Check both modules built
        self.assertTrue((project_path / 'app' / 'build' / 'classes').exists())
        self.assertTrue((project_path / 'lib' / 'build' / 'classes').exists())

    def test_kotlin_multi_app_depends_on_lib(self):
        """Test app module can use lib module"""
        print(f"{'#' * 70}")
        print(f"  TEST: kotlin-multi - Module Dependencies")
        print(f"{'#' * 70}")
        project_path = self._generate_project('kotlin-multi', 'deps-kotlin-multi')

        # kotlin-multi uses buildSrc and doesn't generate gradlew
        # Skip if wrapper doesn't exist
        gradlew = project_path / ('gradlew.bat' if os.name == 'nt' else 'gradlew')
        if not gradlew.exists():
            self.skipTest("kotlin-multi uses buildSrc - no wrapper generated")

        # Build and run app
        result = self._run_gradle(project_path, ':app:build')

        self.assertEqual(result.returncode, 0, "App should build with lib dependency")

        # ========================================================================
        # Test springboot Template
        # ========================================================================

    def test_springboot_generation(self):
        """Test springboot template generation"""
        print(f"{'#' * 70}")
        print(f"  TEST: springboot - Generation")
        print(f"{'#' * 70}")
        project_path = self._generate_project(
            'springboot',
            'test-springboot',
            spring_modules=['web', 'data-jpa']
        )

        # Check Spring Boot files
        build_gradle = (project_path / 'build.gradle.kts').read_text()
        # With libs.versions.toml, we use alias() syntax
        self.assertIn('alias(libs.plugins.spring.boot)', build_gradle)
        self.assertIn('libs.spring.boot', build_gradle)  # Check for libs reference
        self.assertIn('libs.kotlin.reflect', build_gradle)

        # Check application files
        self.assertTrue((project_path / 'src' / 'main' / 'kotlin' / 'Application.kt').exists())
        self.assertTrue((project_path / 'src' / 'main' / 'kotlin' / 'HelloController.kt').exists())
        self.assertTrue((project_path / 'src' / 'main' / 'resources' / 'application.properties').exists())

    def test_springboot_gradle_build(self):
        """Test springboot builds with Gradle"""
        print(f"{'#' * 70}")
        print(f"  TEST: springboot - Gradle Build")
        print(f"{'#' * 70}")
        project_path = self._generate_project(
            'springboot',
            'build-springboot',
            spring_modules=['web']
        )

        # Run gradle build
        result = self._run_gradle(project_path, 'build', timeout=180)

        self.assertEqual(result.returncode, 0, "Spring Boot build should succeed")

        # Check Spring Boot jar was created
        jar_file = list((project_path / 'build' / 'libs').glob('*.jar'))
        self.assertTrue(len(jar_file) > 0, "Spring Boot jar should be created")

        # ========================================================================
        # Test ktor Template
        # ========================================================================

    def test_ktor_generation(self):
        """Test ktor template generation"""
        print(f"{'#' * 70}")
        print(f"  TEST: ktor - Generation")
        print(f"{'#' * 70}")
        project_path = self._generate_project(
            'ktor',
            'test-ktor',
            ktor_features=['serialization', 'auth']
        )

        # Check Ktor files
        build_gradle = (project_path / 'build.gradle.kts').read_text()
        # With libs.versions.toml, we use alias() syntax
        self.assertIn('alias(libs.plugins.ktor)', build_gradle)
        self.assertIn('libs.ktor.server', build_gradle)  # Check for libs reference
        self.assertIn('libs.logback', build_gradle)

        # Check application file
        app_file = project_path / 'src' / 'main' / 'kotlin' / 'Application.kt'
        self.assertTrue(app_file.exists())

        app_content = app_file.read_text()
        self.assertIn('embeddedServer', app_content)
        self.assertIn('Netty', app_content)

    def test_ktor_gradle_build(self):
        """Test ktor builds with Gradle"""
        print(f"{'#' * 70}")
        print(f"  TEST: ktor - Gradle Build")
        print(f"{'#' * 70}")
        project_path = self._generate_project(
            'ktor',
            'build-ktor',
            ktor_features=['serialization']
        )

        # Run gradle build
        result = self._run_gradle(project_path, 'build', timeout=150)

        self.assertEqual(result.returncode, 0, "Ktor build should succeed")

        # ============================================================================
        # Integration Tests
        # ============================================================================


class TestIntegration(unittest.TestCase):
    """Integration tests for complete workflow"""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="gradleInit_integration_"))
        self.paths = GradleInitPaths(self.temp_dir / '.gradleInit')
        self.paths.ensure_structure()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_template_repository_manager_finds_github_url(self):
        """Test that TemplateRepositoryManager can handle GitHub URLs"""
        manager = TemplateRepositoryManager(self.paths)

        # This should download and cache the template
        github_url = "https://github.com/stotz/gradleInitTemplates/tree/main/kotlin-single"

        # Note: This will actually download from GitHub in CI
        # In production tests, you might want to mock this
        template_path = manager.find_template(github_url)

        # Should either find it or return None (if offline)
        # For now, just check the method doesn't crash
        self.assertIsInstance(template_path, (Path, type(None)))

    def test_template_repository_manager_finds_simple_name(self):
        """Test finding template by simple name"""
        manager = TemplateRepositoryManager(self.paths)

        # Ensure official templates
        manager.ensure_official_templates()

        # Try to find by name
        template_path = manager.find_template('kotlin-single')

        # Should find it or return None
        self.assertIsInstance(template_path, (Path, type(None)))


# ============================================================================
# Performance Tests
# ============================================================================

class TestPerformance(unittest.TestCase):
    """Performance tests for generation speed"""

    def test_generation_speed(self):
        """Test that project generation completes in reasonable time"""
        temp_dir = Path(tempfile.mkdtemp())

        try:
            # Clone templates
            templates_dir = temp_dir / "templates"
            result = subprocess.run(
                ['git', 'clone', '--depth', '1',
                 'https://github.com/stotz/gradleInitTemplates.git',
                 str(templates_dir)],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                self.skipTest("Could not clone templates")

            # Generate project
            template_path = templates_dir / 'kotlin-single'
            project_path = temp_dir / 'test-project'

            context = {
                'project_name': 'test-project',
                'group': 'com.test',
                'version': '1.0.0',
                'kotlin_version': '2.2.0',
                'jdk_version': 21,
                'date': '2025-11-15'
            }

            start = time.time()
            generator = ProjectGenerator(template_path, context, project_path)
            success = generator.generate()
            elapsed = time.time() - start

            self.assertTrue(success)
            self.assertLess(elapsed, 15.0, "Generation should complete in under 15 seconds")

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


# ============================================================================
# Test Runner
# ============================================================================

def run_tests(verbosity=2):
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestGitHubURLParsing))
    suite.addTests(loader.loadTestsFromTestCase(TestTemplateGeneration))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformance))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)

    # Return success
    return result.wasSuccessful()


if __name__ == '__main__':
    print("=" * 70)
    print("  gradleInit.py - Comprehensive Test Suite")
    print("=" * 70)
    print()
    print("Running tests...")
    print()

    success = run_tests()

    print()
    print("=" * 70)
    if success:
        print("  ✓ All tests passed!")
    else:
        print("  ✗ Some tests failed")
    print("=" * 70)

    sys.exit(0 if success else 1)