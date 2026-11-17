#!/usr/bin/env python3
"""
Fast Unit Tests for gradleInit.py CLI Commands

Tests all CLI commands (init, templates, config) without heavy Gradle builds.
Focuses on:
- Argument parsing
- Variable substitution
- File generation
- Configuration management
- Template processing

Usage:
    python test_cli.py
    python -m pytest test_cli.py -v
    python -m pytest test_cli.py -v -k test_init  # Run only init tests
"""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
import sys
import re

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

except ImportError as e:
    print(f"Error importing gradleInit: {e}")
    sys.exit(1)


# ============================================================================
# Helper Functions
# ============================================================================

def run_gradleinit(args: list, cwd=None, interactive=False) -> subprocess.CompletedProcess:
    """Run gradleInit.py with given arguments"""
    gradleinit_path = Path(__file__).parent / 'gradleInit.py'
    
    # Add --no-interactive by default for init command tests (unless interactive=True)
    # Only add it if we're running an 'init' command
    if not interactive and '--no-interactive' not in args and len(args) > 0 and args[0] == 'init':
        # Insert after 'init' command
        args = ['init', '--no-interactive'] + args[1:]
    
    cmd = [sys.executable, str(gradleinit_path)] + args

    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=30
    )


def check_file_contains(file_path: Path, patterns: list) -> tuple:
    """Check if file contains all patterns"""
    if not file_path.exists():
        return False, f"File not found: {file_path}"

    content = file_path.read_text(encoding='utf-8')

    for pattern in patterns:
        if isinstance(pattern, str):
            if pattern not in content:
                return False, f"Pattern not found: {pattern}"
        else:  # regex
            if not pattern.search(content):
                return False, f"Regex not found: {pattern.pattern}"

    return True, "OK"


# ============================================================================
# Test Templates Command
# ============================================================================

class TestTemplatesCommand(unittest.TestCase):
    """Test 'templates' command"""

    @classmethod
    def setUpClass(cls):
        """Setup test environment once"""
        cls.test_root = Path(tempfile.mkdtemp(prefix="gradleInit_cli_test_"))
        cls.home_dir = cls.test_root / "home"
        cls.home_dir.mkdir()

        # Set HOME to test directory
        os.environ['HOME'] = str(cls.home_dir)
        if sys.platform.startswith('win'):
            os.environ['USERPROFILE'] = str(cls.home_dir)

    @classmethod
    def tearDownClass(cls):
        """Cleanup after all tests"""
        if cls.test_root.exists():
            shutil.rmtree(cls.test_root, ignore_errors=True)

    def test_templates_update(self):
        """Test templates --update"""
        result = run_gradleinit(['templates', '--update'])

        self.assertEqual(result.returncode, 0, f"Command failed: {result.stderr}")

        # Check templates directory was created
        templates_dir = self.home_dir / '.gradleInit' / 'templates' / 'official'
        self.assertTrue(templates_dir.exists(), "Templates directory not created")

        # Check at least one template exists
        templates = [d for d in templates_dir.iterdir() if d.is_dir()]
        self.assertGreater(len(templates), 0, "No templates downloaded")

    def test_templates_list(self):
        """Test templates --list"""
        # First update
        run_gradleinit(['templates', '--update'])

        # Then list
        result = run_gradleinit(['templates', '--list'])

        self.assertEqual(result.returncode, 0)
        self.assertIn('kotlin-single', result.stdout)
        self.assertIn('kotlin-multi', result.stdout)
        self.assertIn('springboot', result.stdout)
        self.assertIn('ktor', result.stdout)

    def test_templates_info(self):
        """Test templates --info"""
        # Update first
        run_gradleinit(['templates', '--update'])

        # Get info
        result = run_gradleinit(['templates', '--info', 'kotlin-single'])

        self.assertEqual(result.returncode, 0)
        # Should contain template information
        self.assertIn('kotlin', result.stdout.lower())


# ============================================================================
# Test Config Command
# ============================================================================

class TestConfigCommand(unittest.TestCase):
    """Test 'config' command"""

    @classmethod
    def setUpClass(cls):
        """Setup test environment once"""
        cls.test_root = Path(tempfile.mkdtemp(prefix="gradleInit_config_test_"))
        cls.home_dir = cls.test_root / "home"
        cls.home_dir.mkdir()

        # Set HOME to test directory
        os.environ['HOME'] = str(cls.home_dir)
        if sys.platform.startswith('win'):
            os.environ['USERPROFILE'] = str(cls.home_dir)

    @classmethod
    def tearDownClass(cls):
        """Cleanup after all tests"""
        if cls.test_root.exists():
            shutil.rmtree(cls.test_root, ignore_errors=True)

    def test_config_show(self):
        """Test config --show"""
        result = run_gradleinit(['config', '--show'])

        self.assertEqual(result.returncode, 0)

        # Should show config sections
        self.assertIn('[templates]', result.stdout)
        self.assertIn('[defaults]', result.stdout)
        self.assertIn('gradle_version', result.stdout)

    def test_config_init(self):
        """Test config --init"""
        result = run_gradleinit(['config', '--init'])

        self.assertEqual(result.returncode, 0)

        # Check config file was created
        config_file = self.home_dir / '.gradleInit' / 'config'
        self.assertTrue(config_file.exists(), "Config file not created")

        # Check config content
        content = config_file.read_text()
        self.assertIn('[templates]', content)
        self.assertIn('[defaults]', content)


# ============================================================================
# Test Init Command - Project Generation
# ============================================================================

class TestInitCommand(unittest.TestCase):
    """Test 'init' command - project generation"""

    @classmethod
    def setUpClass(cls):
        """Setup test environment once"""
        cls.test_root = Path(tempfile.mkdtemp(prefix="gradleInit_init_test_"))
        cls.home_dir = cls.test_root / "home"
        cls.projects_dir = cls.test_root / "projects"
        cls.home_dir.mkdir()
        cls.projects_dir.mkdir()

        # Set HOME to test directory
        os.environ['HOME'] = str(cls.home_dir)
        if sys.platform.startswith('win'):
            os.environ['USERPROFILE'] = str(cls.home_dir)

        # Download templates once
        print("\n==> Downloading templates for init tests...")
        result = run_gradleinit(['templates', '--update'])
        if result.returncode != 0:
            raise RuntimeError(f"Failed to download templates: {result.stderr}")

    @classmethod
    def tearDownClass(cls):
        """Cleanup after all tests"""
        if cls.test_root.exists():
            shutil.rmtree(cls.test_root, ignore_errors=True)

    def test_init_basic_kotlin_single(self):
        """Test basic project creation with kotlin-single"""
        project_name = "test-basic"
        project_dir = self.projects_dir / project_name

        result = run_gradleinit([
            'init', project_name,
            '--template', 'kotlin-single',
            '--group', 'com.test',
        ], cwd=self.projects_dir)

        self.assertEqual(result.returncode, 0, f"Init failed: {result.stderr}")
        self.assertTrue(project_dir.exists(), "Project directory not created")

        # Check essential files exist
        self.assertTrue((project_dir / 'build.gradle.kts').exists())
        self.assertTrue((project_dir / 'settings.gradle.kts').exists())
        self.assertTrue((project_dir / 'gradle.properties').exists())
        self.assertTrue((project_dir / 'gradle' / 'libs.versions.toml').exists())
        self.assertTrue((project_dir / '.gitignore').exists())
        self.assertTrue((project_dir / 'src' / 'main' / 'kotlin' / 'Main.kt').exists())

    def test_init_with_custom_group(self):
        """Test that custom group is applied"""
        project_name = "test-custom-group"
        project_dir = self.projects_dir / project_name

        result = run_gradleinit([
            'init', project_name,
            '--template', 'kotlin-single',
            '--group', 'ch.typedef',
        ], cwd=self.projects_dir)

        self.assertEqual(result.returncode, 0)

        # Check build.gradle.kts contains correct group
        build_gradle = project_dir / 'build.gradle.kts'
        ok, msg = check_file_contains(build_gradle, [
            'group = "ch.typedef"'
        ])
        self.assertTrue(ok, msg)

    def test_init_with_custom_version(self):
        """Test that custom version is applied"""
        project_name = "test-custom-version"
        project_dir = self.projects_dir / project_name

        result = run_gradleinit([
            'init', project_name,
            '--template', 'kotlin-single',
            '--group', 'com.test',
            '--project-version', '2.0.0',
        ], cwd=self.projects_dir)

        self.assertEqual(result.returncode, 0)

        # Check build.gradle.kts contains correct version (after template rendering)
        build_gradle = project_dir / 'build.gradle.kts'
        content = build_gradle.read_text(encoding='utf-8')
        
        # The template variable {{ version }} should be replaced with the actual value
        self.assertIn('version =', content, "build.gradle.kts should have version declaration")
        self.assertIn('2.0.0', content, "Custom version 2.0.0 should be in build.gradle.kts")

    def test_init_with_gradle_version(self):
        """Test that gradle version can be specified"""
        project_name = "test-gradle-version"
        project_dir = self.projects_dir / project_name

        result = run_gradleinit([
            'init', project_name,
            '--template', 'kotlin-single',
            '--group', 'com.test',
            '--config', 'gradle_version=8.11',
        ], cwd=self.projects_dir)

        self.assertEqual(result.returncode, 0)

        # Check gradle wrapper properties
        wrapper_props = project_dir / 'gradle' / 'wrapper' / 'gradle-wrapper.properties'
        if wrapper_props.exists():
            ok, msg = check_file_contains(wrapper_props, [
                'gradle-8.11-bin.zip'
            ])
            self.assertTrue(ok, msg)

    def test_init_project_name_in_files(self):
        """Test that project name appears in generated files"""
        project_name = "my-awesome-app"
        project_dir = self.projects_dir / project_name

        result = run_gradleinit([
            'init', project_name,
            '--template', 'kotlin-single',
            '--group', 'com.test',
        ], cwd=self.projects_dir)

        self.assertEqual(result.returncode, 0)

        # Check settings.gradle.kts
        settings = project_dir / 'settings.gradle.kts'
        ok, msg = check_file_contains(settings, [
            f'rootProject.name = "{project_name}"'
        ])
        self.assertTrue(ok, msg)

        # Check Main.kt contains project name
        main_kt = project_dir / 'src' / 'main' / 'kotlin' / 'Main.kt'
        content = main_kt.read_text()
        # Project name should appear somewhere (in message or comment)
        self.assertIn(project_name, content,
                      f"Project name '{project_name}' not found in Main.kt")

    def test_init_no_template_variables_left(self):
        """Test that all template variables are replaced"""
        project_name = "test-no-vars"
        project_dir = self.projects_dir / project_name

        result = run_gradleinit([
            'init', project_name,
            '--template', 'kotlin-single',
            '--group', 'com.test',
        ], cwd=self.projects_dir)

        self.assertEqual(result.returncode, 0)

        # Check no {{ }} left in key files
        files_to_check = [
            project_dir / 'build.gradle.kts',
            project_dir / 'settings.gradle.kts',
            project_dir / 'gradle.properties',
            project_dir / 'src' / 'main' / 'kotlin' / 'Main.kt',
        ]

        for file_path in files_to_check:
            if file_path.exists():
                content = file_path.read_text()
                self.assertNotIn('{{', content,
                                 f"Unreplaced template variable in {file_path.name}")
                self.assertNotIn('}}', content,
                                 f"Unreplaced template variable in {file_path.name}")

    def test_init_git_repository_created(self):
        """Test that git repository is initialized"""
        project_name = "test-git"
        project_dir = self.projects_dir / project_name

        result = run_gradleinit([
            'init', project_name,
            '--template', 'kotlin-single',
            '--group', 'com.test',
        ], cwd=self.projects_dir)

        self.assertEqual(result.returncode, 0)

        # Check .git directory exists
        git_dir = project_dir / '.git'
        self.assertTrue(git_dir.exists(), "Git repository not initialized")

        # Check initial commit exists
        git_log = subprocess.run(
            ['git', 'log', '--oneline'],
            cwd=project_dir,
            capture_output=True,
            text=True
        )

        if git_log.returncode == 0:
            self.assertIn('Initial commit', git_log.stdout)

    def test_init_gitignore_correct(self):
        """Test that .gitignore contains correct patterns"""
        project_name = "test-gitignore"
        project_dir = self.projects_dir / project_name

        result = run_gradleinit([
            'init', project_name,
            '--template', 'kotlin-single',
            '--group', 'com.test',
        ], cwd=self.projects_dir)

        self.assertEqual(result.returncode, 0)

        # Check .gitignore content
        gitignore = project_dir / '.gitignore'
        ok, msg = check_file_contains(gitignore, [
            '.gradle/',
            'build/',
            '!gradle/wrapper/gradle-wrapper.jar',
            '.idea/',
            '*.class',
        ])
        self.assertTrue(ok, msg)

    def test_init_version_catalog_structure(self):
        """Test that version catalog is properly structured"""
        project_name = "test-catalog"
        project_dir = self.projects_dir / project_name

        result = run_gradleinit([
            'init', project_name,
            '--template', 'kotlin-single',
            '--group', 'com.test',
        ], cwd=self.projects_dir)

        self.assertEqual(result.returncode, 0)

        # Check libs.versions.toml
        catalog = project_dir / 'gradle' / 'libs.versions.toml'
        ok, msg = check_file_contains(catalog, [
            '[versions]',
            '[libraries]',
            '[plugins]',
            'kotlin =',
        ])
        self.assertTrue(ok, msg)

    def test_init_editorconfig_present(self):
        """Test that .editorconfig is created"""
        project_name = "test-editorconfig"
        project_dir = self.projects_dir / project_name

        result = run_gradleinit([
            'init', project_name,
            '--template', 'kotlin-single',
            '--group', 'com.test',
        ], cwd=self.projects_dir)

        self.assertEqual(result.returncode, 0)

        # Check .editorconfig exists and has content
        editorconfig = project_dir / '.editorconfig'
        self.assertTrue(editorconfig.exists())

        # Check that editorconfig has Kotlin configuration
        content = editorconfig.read_text(encoding='utf-8')
        self.assertIn('root = true', content)
        # Accept both specific and grouped Kotlin sections
        has_kotlin = '.kt' in content and '[*.' in content
        self.assertTrue(has_kotlin, 
                       ".editorconfig should have Kotlin file configuration")


# ============================================================================
# Test Init Command - Arguments & Configuration
# ============================================================================

class TestInitArguments(unittest.TestCase):
    """Test init command argument handling"""

    @classmethod
    def setUpClass(cls):
        """Setup test environment once"""
        cls.test_root = Path(tempfile.mkdtemp(prefix="gradleInit_args_test_"))
        cls.home_dir = cls.test_root / "home"
        cls.projects_dir = cls.test_root / "projects"
        cls.home_dir.mkdir()
        cls.projects_dir.mkdir()

        os.environ['HOME'] = str(cls.home_dir)
        if sys.platform.startswith('win'):
            os.environ['USERPROFILE'] = str(cls.home_dir)

        # Download templates
        print("\n==> Downloading templates for argument tests...")
        run_gradleinit(['templates', '--update'])

    @classmethod
    def tearDownClass(cls):
        """Cleanup"""
        if cls.test_root.exists():
            shutil.rmtree(cls.test_root, ignore_errors=True)

    def test_init_requires_project_name(self):
        """Test that init requires project name"""
        result = run_gradleinit([
            'init',
            '--template', 'kotlin-single',
        ], cwd=self.projects_dir)

        self.assertNotEqual(result.returncode, 0, "Should fail without project name")
        self.assertIn('required', result.stdout.lower() + result.stderr.lower())

    def test_init_requires_template(self):
        """Test that init requires template"""
        result = run_gradleinit([
            'init', 'test-project',
        ], cwd=self.projects_dir)

        self.assertNotEqual(result.returncode, 0, "Should fail without template")
        self.assertIn('template', result.stdout.lower() + result.stderr.lower())

    def test_init_config_values_work(self):
        """Test that --config KEY=VALUE works"""
        project_name = "test-config-values"
        project_dir = self.projects_dir / project_name

        result = run_gradleinit([
            'init', project_name,
            '--template', 'kotlin-single',
            '--group', 'com.test',
            '--config', 'kotlin_version=2.0.0',
            '--config', 'jdk_version=17',
        ], cwd=self.projects_dir)

        self.assertEqual(result.returncode, 0)

        # Check that config values were used
        catalog = project_dir / 'gradle' / 'libs.versions.toml'
        if catalog.exists():
            content = catalog.read_text()
            # kotlin_version should be in catalog
            self.assertIn('2.0', content)


# ============================================================================
# Test Commands Without Arguments
# ============================================================================

class TestCommandsWithoutArgs(unittest.TestCase):
    """Test that commands show help when called without arguments"""

    def test_01_version_flag(self):
        """Test --version flag"""
        cmd = [sys.executable, str(Path(__file__).parent / 'gradleInit.py'), '--version']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        self.assertEqual(result.returncode, 0, f"stderr: {result.stderr}")
        self.assertIn('gradleInit v', result.stdout)
        self.assertNotIn('usage:', result.stdout.lower())

    def test_02_v_short_flag(self):
        """Test -v short flag"""
        cmd = [sys.executable, str(Path(__file__).parent / 'gradleInit.py'), '-v']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        self.assertEqual(result.returncode, 0, f"stderr: {result.stderr}")
        self.assertIn('gradleInit v', result.stdout)
        self.assertNotIn('usage:', result.stdout.lower())

    def test_03_templates_no_args(self):
        """Test 'templates' without arguments shows help"""
        cmd = [sys.executable, str(Path(__file__).parent / 'gradleInit.py'), 'templates']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        self.assertEqual(result.returncode, 0, f"stderr: {result.stderr}")
        self.assertIn('Templates Command', result.stdout)
        self.assertIn('--list', result.stdout)
        self.assertIn('--update', result.stdout)

    def test_04_config_no_args(self):
        """Test 'config' without arguments shows help"""
        cmd = [sys.executable, str(Path(__file__).parent / 'gradleInit.py'), 'config']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        self.assertEqual(result.returncode, 0, f"stderr: {result.stderr}")
        self.assertIn('Config Command', result.stdout)
        self.assertIn('--show', result.stdout)
        self.assertIn('--init', result.stdout)


# ============================================================================
# Test Runner
# ============================================================================

def run_tests(verbosity=2):
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestTemplatesCommand))
    suite.addTests(loader.loadTestsFromTestCase(TestConfigCommand))
    suite.addTests(loader.loadTestsFromTestCase(TestInitCommand))
    suite.addTests(loader.loadTestsFromTestCase(TestInitArguments))
    suite.addTests(loader.loadTestsFromTestCase(TestCommandsWithoutArgs))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == '__main__':
    print("=" * 70)
    print("  gradleInit.py - Fast CLI Tests")
    print("=" * 70)
    print()
    print("Testing CLI commands: init, templates, config")
    print("Focus: Argument parsing, variable substitution, file generation")
    print()

    success = run_tests()

    print()
    print("=" * 70)
    if success:
        print("  [OK] All CLI tests passed!")
    else:
        print("  [ERROR] Some tests failed")
    print("=" * 70)

    sys.exit(0 if success else 1)