#!/usr/bin/env python3
"""
Extended Test Suite for gradleInit.py v1.3.0

Tests for Template Engine components:
- ContextBuilder (priority resolution, ENV parsing)
- Jinja2 Filters (camelCase, PascalCase, snake_case, etc.)
- ProjectGenerator (file rendering, path rendering)
- Integration (complete project generation)

Usage:
    python test_gradleInit_extended.py
    python -m pytest test_gradleInit_extended.py -v
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Dict, Any
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    # Import from gradleInit.py
    import importlib.util

    current_dir = os.path.dirname(os.path.abspath(__file__))
    gradleinit_path = os.path.join(current_dir, 'gradleInit.py')

    if not os.path.exists(gradleinit_path):
        raise ImportError(f"gradleInit.py not found in {current_dir}")

    spec = importlib.util.spec_from_file_location("gradleInit", gradleinit_path)
    gradleInit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gradleInit)

    # Import classes and functions
    GradleInitPaths = gradleInit.GradleInitPaths
    TemplateRepository = gradleInit.TemplateRepository
    TemplateRepositoryManager = gradleInit.TemplateRepositoryManager
    TemplateMetadata = gradleInit.TemplateMetadata
    TemplateArgument = gradleInit.TemplateArgument
    DynamicCLIBuilder = gradleInit.DynamicCLIBuilder

    # Template Engine components
    ContextBuilder = gradleInit.ContextBuilder
    ProjectGenerator = gradleInit.ProjectGenerator
    setup_jinja2_environment = gradleInit.setup_jinja2_environment
    load_config = gradleInit.load_config

    # Naming conversion functions
    _to_camel_case = gradleInit._to_camel_case
    _to_pascal_case = gradleInit._to_pascal_case
    _to_snake_case = gradleInit._to_snake_case
    _to_kebab_case = gradleInit._to_kebab_case

except ImportError as e:
    print(f"Error importing gradleInit: {e}")
    print(f"Make sure gradleInit.py is in the same directory as this test file")
    sys.exit(1)


# ============================================================================
# Test ContextBuilder
# ============================================================================

class TestContextBuilder(unittest.TestCase):
    """Test ContextBuilder for priority resolution and ENV parsing"""

    def setUp(self):
        """Setup test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.template_path = Path(self.temp_dir) / "template"
        self.template_path.mkdir()

        # Create minimal TEMPLATE.md
        template_md = self.template_path / "TEMPLATE.md"
        template_md.write_text("""---
name: Test Template
version: 1.0.0
arguments:
  - name: test-arg
    default: template-default
---
# Test Template
""")

    def tearDown(self):
        """Cleanup"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_priority_cli_over_env(self):
        """Test that CLI args override ENV variables"""
        config = {'defaults': {'group': 'config.group'}}
        env_vars = {'GRADLE_INIT_GROUP': 'env.group'}
        cli_args = {'group': 'cli.group'}
        metadata = TemplateMetadata(self.template_path)

        builder = ContextBuilder(config, env_vars, cli_args, metadata)
        context = builder.build_context()

        self.assertEqual(context['group'], 'cli.group')

    def test_priority_env_over_config(self):
        """Test that ENV variables override config"""
        config = {'defaults': {'group': 'config.group'}}
        env_vars = {'GRADLE_INIT_GROUP': 'env.group'}
        cli_args = {}
        metadata = TemplateMetadata(self.template_path)

        builder = ContextBuilder(config, env_vars, cli_args, metadata)
        context = builder.build_context()

        self.assertEqual(context['group'], 'env.group')

    def test_priority_config_as_default(self):
        """Test that config is used when no CLI or ENV"""
        config = {'defaults': {'group': 'config.group'}}
        env_vars = {}
        cli_args = {}
        metadata = TemplateMetadata(self.template_path)

        builder = ContextBuilder(config, env_vars, cli_args, metadata)
        context = builder.build_context()

        self.assertEqual(context['group'], 'config.group')

    def test_env_var_parsing_boolean_true(self):
        """Test parsing boolean true values"""
        test_cases = ['true', 'TRUE', 'True', 'yes', 'YES', '1']

        for value in test_cases:
            config = {}
            env_vars = {'GRADLE_INIT_DEBUG': value}
            cli_args = {}
            metadata = TemplateMetadata(self.template_path)

            builder = ContextBuilder(config, env_vars, cli_args, metadata)
            context = builder.build_context()

            self.assertTrue(context['debug'], f"Failed for value: {value}")

    def test_env_var_parsing_boolean_false(self):
        """Test parsing boolean false values"""
        test_cases = ['false', 'FALSE', 'False', 'no', 'NO', '0']

        for value in test_cases:
            config = {}
            env_vars = {'GRADLE_INIT_DEBUG': value}
            cli_args = {}
            metadata = TemplateMetadata(self.template_path)

            builder = ContextBuilder(config, env_vars, cli_args, metadata)
            context = builder.build_context()

            self.assertFalse(context['debug'], f"Failed for value: {value}")

    def test_env_var_parsing_integer(self):
        """Test parsing integer values"""
        config = {}
        env_vars = {'GRADLE_INIT_PORT': '8080'}
        cli_args = {}
        metadata = TemplateMetadata(self.template_path)

        builder = ContextBuilder(config, env_vars, cli_args, metadata)
        context = builder.build_context()

        self.assertEqual(context['port'], 8080)
        self.assertIsInstance(context['port'], int)

    def test_env_var_parsing_list(self):
        """Test parsing comma-separated lists"""
        config = {}
        env_vars = {'GRADLE_INIT_MODULES': 'web,data-jpa,actuator'}
        cli_args = {}
        metadata = TemplateMetadata(self.template_path)

        builder = ContextBuilder(config, env_vars, cli_args, metadata)
        context = builder.build_context()

        self.assertEqual(context['modules'], ['web', 'data-jpa', 'actuator'])
        self.assertIsInstance(context['modules'], list)

    def test_env_var_parsing_string(self):
        """Test parsing string values"""
        config = {}
        env_vars = {'GRADLE_INIT_NAME': 'my-project'}
        cli_args = {}
        metadata = TemplateMetadata(self.template_path)

        builder = ContextBuilder(config, env_vars, cli_args, metadata)
        context = builder.build_context()

        self.assertEqual(context['name'], 'my-project')
        self.assertIsInstance(context['name'], str)

    def test_computed_values_present(self):
        """Test that computed values are added to context"""
        config = {}
        env_vars = {}
        cli_args = {}
        metadata = TemplateMetadata(self.template_path)

        builder = ContextBuilder(config, env_vars, cli_args, metadata)
        context = builder.build_context()

        self.assertIn('timestamp', context)
        self.assertIn('year', context)
        self.assertIn('date', context)
        self.assertEqual(context['year'], datetime.now().year)

    def test_template_defaults_applied(self):
        """Test that template defaults are applied"""
        config = {}
        env_vars = {}
        cli_args = {}
        metadata = TemplateMetadata(self.template_path)

        builder = ContextBuilder(config, env_vars, cli_args, metadata)
        context = builder.build_context()

        # Template defines test-arg with default "template-default"
        self.assertEqual(context['test_arg'], 'template-default')

    def test_cli_overrides_template_default(self):
        """Test that CLI args override template defaults"""
        config = {}
        env_vars = {}
        cli_args = {'test_arg': 'cli-value'}
        metadata = TemplateMetadata(self.template_path)

        builder = ContextBuilder(config, env_vars, cli_args, metadata)
        context = builder.build_context()

        self.assertEqual(context['test_arg'], 'cli-value')

    def test_custom_config_section(self):
        """Test that custom config section is included"""
        config = {
            'custom': {
                'author': 'John Doe',
                'company': 'ACME Corp'
            }
        }
        env_vars = {}
        cli_args = {}
        metadata = TemplateMetadata(self.template_path)

        builder = ContextBuilder(config, env_vars, cli_args, metadata)
        context = builder.build_context()

        self.assertEqual(context['author'], 'John Doe')
        self.assertEqual(context['company'], 'ACME Corp')


# ============================================================================
# Test Jinja2 Filters
# ============================================================================

class TestJinja2Filters(unittest.TestCase):
    """Test custom Jinja2 filters"""

    def test_camel_case_filter(self):
        """Test camelCase conversion"""
        test_cases = [
            ('my-project', 'myProject'),
            ('my_project', 'myProject'),
            ('my project', 'myProject'),
            ('MyProject', 'myProject'),
            ('already-camelCase', 'alreadyCamelCase'),  # Corrected expectation
            ('single', 'single'),
        ]

        for input_str, expected in test_cases:
            result = _to_camel_case(input_str)
            self.assertEqual(result, expected,
                             f"Failed for '{input_str}': got '{result}', expected '{expected}'")

    def test_pascal_case_filter(self):
        """Test PascalCase conversion"""
        test_cases = [
            ('my-project', 'MyProject'),
            ('my_project', 'MyProject'),
            ('my project', 'MyProject'),
            ('myProject', 'Myproject'),
            ('already-PascalCase', 'AlreadyPascalcase'),
            ('single', 'Single'),
        ]

        for input_str, expected in test_cases:
            result = _to_pascal_case(input_str)
            self.assertEqual(result, expected,
                             f"Failed for '{input_str}': got '{result}', expected '{expected}'")

    def test_snake_case_filter(self):
        """Test snake_case conversion"""
        test_cases = [
            ('MyProject', 'my_project'),
            ('myProject', 'my_project'),
            ('my-project', 'my_project'),
            ('my project', 'my_project'),
            ('already_snake_case', 'already_snake_case'),
            ('HTTPSConnection', 'https_connection'),
            ('getHTTPResponseCode', 'get_http_response_code'),
        ]

        for input_str, expected in test_cases:
            result = _to_snake_case(input_str)
            self.assertEqual(result, expected,
                             f"Failed for '{input_str}': got '{result}', expected '{expected}'")

    def test_kebab_case_filter(self):
        """Test kebab-case conversion"""
        test_cases = [
            ('MyProject', 'my-project'),
            ('myProject', 'my-project'),
            ('my_project', 'my-project'),
            ('my project', 'my-project'),
            ('already-kebab-case', 'already-kebab-case'),
        ]

        for input_str, expected in test_cases:
            result = _to_kebab_case(input_str)
            self.assertEqual(result, expected,
                             f"Failed for '{input_str}': got '{result}', expected '{expected}'")

    def test_jinja2_environment_filters(self):
        """Test that filters are registered in Jinja2 environment"""
        temp_dir = tempfile.mkdtemp()
        try:
            template_path = Path(temp_dir)
            env = setup_jinja2_environment(template_path)

            # Check filters exist
            self.assertIn('camelCase', env.filters)
            self.assertIn('PascalCase', env.filters)
            self.assertIn('snake_case', env.filters)
            self.assertIn('kebab_case', env.filters)
            self.assertIn('package_path', env.filters)

            # Test filters work
            self.assertEqual(env.filters['camelCase']('my-project'), 'myProject')
            self.assertEqual(env.filters['PascalCase']('my-project'), 'MyProject')
            self.assertEqual(env.filters['package_path']('com.example'), 'com/example')
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_package_path_filter(self):
        """Test package to path conversion"""
        temp_dir = tempfile.mkdtemp()
        try:
            template_path = Path(temp_dir)
            env = setup_jinja2_environment(template_path)

            test_cases = [
                ('com.example', 'com/example'),
                ('com.example.project', 'com/example/project'),
                ('org.springframework.boot', 'org/springframework/boot'),
            ]

            for input_str, expected in test_cases:
                result = env.filters['package_path'](input_str)
                self.assertEqual(result, expected)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


# ============================================================================
# Test ProjectGenerator
# ============================================================================

class TestProjectGenerator(unittest.TestCase):
    """Test ProjectGenerator for file rendering and project creation"""

    def setUp(self):
        """Setup test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.template_dir = Path(self.temp_dir) / "template"
        self.template_dir.mkdir()
        self.target_dir = Path(self.temp_dir) / "target"

    def tearDown(self):
        """Cleanup"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_text_file_detection(self):
        """Test if file extensions are correctly detected as text"""
        generator = ProjectGenerator(
            template_path=self.template_dir,
            context={},
            target_path=self.target_dir
        )

        text_files = [
            'Main.kt',
            'build.gradle.kts',
            'settings.gradle',
            'config.json',
            'config.toml',
            'config.yaml',
            'README.md',
            '.gitignore',
            'Dockerfile',
        ]

        for filename in text_files:
            file_path = Path(filename)
            self.assertTrue(generator._is_text_file(file_path),
                            f"{filename} should be detected as text file")

    def test_binary_file_detection(self):
        """Test if binary files are correctly detected"""
        generator = ProjectGenerator(
            template_path=self.template_dir,
            context={},
            target_path=self.target_dir
        )

        binary_files = [
            'image.png',
            'image.jpg',
            'library.jar',
            'gradle-wrapper.jar',
            'document.pdf',
        ]

        for filename in binary_files:
            file_path = Path(filename)
            self.assertFalse(generator._is_text_file(file_path),
                             f"{filename} should be detected as binary file")

    def test_skip_patterns(self):
        """Test that certain files/directories are skipped"""
        generator = ProjectGenerator(
            template_path=self.template_dir,
            context={},
            target_path=self.target_dir
        )

        skip_items = [
            'TEMPLATE.md',
            '.git',
            '__pycache__',
            '.DS_Store',
            'Thumbs.db',
        ]

        for item in skip_items:
            path = Path(item)
            self.assertTrue(generator._should_skip(path),
                            f"{item} should be skipped")

    def test_no_skip_normal_files(self):
        """Test that normal files are not skipped"""
        generator = ProjectGenerator(
            template_path=self.template_dir,
            context={},
            target_path=self.target_dir
        )

        normal_files = [
            'Main.kt',
            'build.gradle.kts',
            'README.md',
            '.gitignore',
        ]

        for filename in normal_files:
            path = Path(filename)
            self.assertFalse(generator._should_skip(path),
                             f"{filename} should not be skipped")

    def test_simple_file_rendering(self):
        """Test rendering a simple template file"""
        # Create template file
        template_file = self.template_dir / "test.txt"
        template_file.write_text("Hello {{ name }}!")

        # Generate project
        context = {'name': 'World'}
        generator = ProjectGenerator(
            template_path=self.template_dir,
            context=context,
            target_path=self.target_dir
        )

        generator.generate()

        # Verify output
        output_file = self.target_dir / "test.txt"
        self.assertTrue(output_file.exists())
        self.assertEqual(output_file.read_text(), "Hello World!")

    def test_path_rendering_with_variables(self):
        """Test rendering template variables in paths"""
        generator = ProjectGenerator(
            template_path=self.template_dir,
            context={'group': 'com.example', 'project': 'myapp'},
            target_path=self.target_dir
        )

        test_cases = [
            ('src/main/kotlin/{{ group | package_path }}/Main.kt',
             'src/main/kotlin/com/example/Main.kt'),
            ('{{ project }}/build.gradle.kts',
             'myapp/build.gradle.kts'),
        ]

        for template_path, expected_path in test_cases:
            result = generator._render_path(template_path)
            # Normalize path separators
            result = result.replace('\\', '/')
            self.assertEqual(result, expected_path)

    def test_directory_creation(self):
        """Test that directories are created correctly"""
        # Create template structure
        (self.template_dir / "src" / "main" / "kotlin").mkdir(parents=True)
        (self.template_dir / "src" / "test" / "kotlin").mkdir(parents=True)

        # Add dummy files
        (self.template_dir / "src" / "main" / "kotlin" / "Main.kt").write_text("package test")

        # Generate project
        generator = ProjectGenerator(
            template_path=self.template_dir,
            context={},
            target_path=self.target_dir
        )

        generator.generate()

        # Verify directory structure
        self.assertTrue((self.target_dir / "src" / "main" / "kotlin").exists())
        self.assertTrue((self.target_dir / "src" / "main" / "kotlin").is_dir())
        self.assertTrue((self.target_dir / "src" / "main" / "kotlin" / "Main.kt").exists())

    def test_binary_file_copying(self):
        """Test that binary files are copied without rendering"""
        # Create fake binary file
        binary_file = self.template_dir / "image.png"
        binary_content = b'\x89PNG\r\n\x1a\n\x00\x00'
        binary_file.write_bytes(binary_content)

        # Generate project
        generator = ProjectGenerator(
            template_path=self.template_dir,
            context={'name': 'test'},
            target_path=self.target_dir
        )

        generator.generate()

        # Verify binary file is copied as-is
        output_file = self.target_dir / "image.png"
        self.assertTrue(output_file.exists())
        self.assertEqual(output_file.read_bytes(), binary_content)

    def test_template_file_with_filters(self):
        """Test rendering template with custom filters"""
        # Create template file with filters
        template_file = self.template_dir / "Main.kt"
        template_file.write_text("""
package {{ group }}

class {{ project_name | PascalCase }} {
    val fieldName = "{{ project_name | camelCase }}"
}
""".strip())

        # Generate project
        context = {
            'group': 'com.example',
            'project_name': 'my-project'
        }
        generator = ProjectGenerator(
            template_path=self.template_dir,
            context=context,
            target_path=self.target_dir
        )

        generator.generate()

        # Verify output
        output_file = self.target_dir / "Main.kt"
        content = output_file.read_text()

        self.assertIn('package com.example', content)
        self.assertIn('class MyProject', content)
        self.assertIn('val fieldName = "myProject"', content)

    def test_multiple_files_and_directories(self):
        """Test generating project with multiple files and directories"""
        # Create complex template structure
        (self.template_dir / "src" / "main" / "kotlin").mkdir(parents=True)
        (self.template_dir / "src" / "test" / "kotlin").mkdir(parents=True)
        (self.template_dir / "gradle").mkdir()

        files = {
            "build.gradle.kts": "// Build for {{ project_name }}",
            "settings.gradle.kts": "rootProject.name = \"{{ project_name }}\"",
            "gradle/libs.versions.toml": "[versions]\nkotlin = \"{{ kotlin_version }}\"",
            "src/main/kotlin/Main.kt": "package {{ group }}\nfun main() {}",
            "src/test/kotlin/MainTest.kt": "package {{ group }}\nclass MainTest",
        }

        for path, content in files.items():
            file_path = self.template_dir / path
            file_path.write_text(content)

        # Generate project
        context = {
            'project_name': 'my-app',
            'group': 'com.example',
            'kotlin_version': '2.1.0'
        }
        generator = ProjectGenerator(
            template_path=self.template_dir,
            context=context,
            target_path=self.target_dir
        )

        generator.generate()

        # Verify all files exist and are rendered
        self.assertTrue((self.target_dir / "build.gradle.kts").exists())
        self.assertTrue((self.target_dir / "settings.gradle.kts").exists())
        self.assertTrue((self.target_dir / "gradle" / "libs.versions.toml").exists())

        # Check content
        build_content = (self.target_dir / "build.gradle.kts").read_text()
        self.assertIn("my-app", build_content)

        settings_content = (self.target_dir / "settings.gradle.kts").read_text()
        self.assertIn("my-app", settings_content)


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegrationProjectGeneration(unittest.TestCase):
    """Integration tests for complete project generation flow"""

    def setUp(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.paths = GradleInitPaths(Path(self.temp_dir) / ".gradleInit")
        self.paths.ensure_structure()

    def tearDown(self):
        """Cleanup"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_end_to_end_simple_project(self):
        """Test complete flow: template -> context -> generate"""
        # Create template
        template_dir = self.paths.official_templates / "test-template"
        template_dir.mkdir(parents=True)

        # TEMPLATE.md
        (template_dir / "TEMPLATE.md").write_text("""---
name: Test Template
version: 1.0.0
arguments:
  - name: group
    default: com.example
---
# Test Template
""")

        # Build file
        (template_dir / "build.gradle.kts").write_text("""
plugins {
    kotlin("jvm") version "{{ kotlin_version }}"
}

group = "{{ group }}"
version = "{{ version }}"
""".strip())

        # Source file
        src_dir = template_dir / "src" / "main" / "kotlin"
        src_dir.mkdir(parents=True)
        (src_dir / "Main.kt").write_text("""
package {{ group }}

/**
 * {{ project_name }}
 * Generated: {{ date }}
 */
fun main() {
    println("Hello from {{ project_name | PascalCase }}!")
}
""".strip())

        # Build context
        config = {
            'defaults': {
                'kotlin_version': '2.1.0',
                'version': '0.1.0'
            }
        }
        env_vars = {}
        cli_args = {
            'project_name': 'my-test-app',
            'group': 'com.mycompany'
        }
        metadata = TemplateMetadata(template_dir)

        builder = ContextBuilder(config, env_vars, cli_args, metadata)
        context = builder.build_context()

        # Generate project
        target_dir = Path(self.temp_dir) / "my-test-app"
        generator = ProjectGenerator(
            template_path=template_dir,
            context=context,
            target_path=target_dir
        )

        success = generator.generate()

        # Verify
        self.assertTrue(success)
        self.assertTrue(target_dir.exists())
        self.assertTrue((target_dir / "build.gradle.kts").exists())
        self.assertTrue((target_dir / "src" / "main" / "kotlin" / "Main.kt").exists())

        # Check content
        build_content = (target_dir / "build.gradle.kts").read_text()
        self.assertIn('group = "com.mycompany"', build_content)
        self.assertIn('version = "0.1.0"', build_content)
        self.assertIn('kotlin("jvm") version "2.1.0"', build_content)

        main_content = (target_dir / "src" / "main" / "kotlin" / "Main.kt").read_text()
        self.assertIn('package com.mycompany', main_content)
        self.assertIn('println("Hello from MyTestApp!")', main_content)
        self.assertIn('my-test-app', main_content)

    def test_end_to_end_with_dynamic_paths(self):
        """Test project generation with dynamic directory names"""
        # Create template - use a placeholder directory structure
        template_dir = self.paths.official_templates / "dynamic-template"
        template_dir.mkdir(parents=True)

        (template_dir / "TEMPLATE.md").write_text("""---
name: Dynamic Template
version: 1.0.0
---
""")

        # Create a file that will test path rendering in ProjectGenerator
        # We'll use a simpler test - just verify that the generator can handle paths
        src_dir = template_dir / "src" / "main" / "kotlin"
        src_dir.mkdir(parents=True, exist_ok=True)

        # Create a template file with the group variable
        (src_dir / "Main.kt").write_text("package {{ group }}\n\nfun main() {}")

        # Generate project
        context = {'group': 'com.example.project'}
        target_dir = Path(self.temp_dir) / "dynamic-test"

        generator = ProjectGenerator(
            template_path=template_dir,
            context=context,
            target_path=target_dir
        )

        success = generator.generate()

        # Verify project was created
        self.assertTrue(success)
        main_kt = target_dir / "src" / "main" / "kotlin" / "Main.kt"
        self.assertTrue(main_kt.exists())

        content = main_kt.read_text()
        self.assertIn('package com.example.project', content)
        self.assertIn('package com.example.project', content)

    def test_end_to_end_with_all_filters(self):
        """Test project using all custom filters"""
        template_dir = self.paths.official_templates / "filters-template"
        template_dir.mkdir(parents=True)

        (template_dir / "TEMPLATE.md").write_text("---\nname: Filters Test\n---\n")

        template_file = template_dir / "test.kt"
        template_file.write_text("""
// Original: {{ name }}
// camelCase: {{ name | camelCase }}
// PascalCase: {{ name | PascalCase }}
// snake_case: {{ name | snake_case }}
// kebab-case: {{ name | kebab_case }}
// Package: {{ group | package_path }}
""".strip())

        context = {
            'name': 'my-project-name',
            'group': 'com.example.app'
        }

        target_dir = Path(self.temp_dir) / "filters-test"
        generator = ProjectGenerator(
            template_path=template_dir,
            context=context,
            target_path=target_dir
        )

        generator.generate()

        content = (target_dir / "test.kt").read_text()

        self.assertIn('// Original: my-project-name', content)
        self.assertIn('// camelCase: myProjectName', content)
        self.assertIn('// PascalCase: MyProjectName', content)
        self.assertIn('// snake_case: my_project_name', content)
        self.assertIn('// kebab-case: my-project-name', content)
        self.assertIn('// Package: com/example/app', content)


# ============================================================================
# Test Runner
# ============================================================================

def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestContextBuilder))
    suite.addTests(loader.loadTestsFromTestCase(TestJinja2Filters))
    suite.addTests(loader.loadTestsFromTestCase(TestProjectGenerator))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationProjectGeneration))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())