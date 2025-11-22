#!/usr/bin/env python3
"""
Tests for template compilation and caching system
"""

import json
import shutil
import tempfile
import time
import unittest
from pathlib import Path

# Import from gradleInit
import sys
sys.path.insert(0, str(Path(__file__).parent))

from gradleInit import (
    GradleInitPaths,
    TemplateCompiler,
    TemplateHintParser,
)


class TestTemplateCompilation(unittest.TestCase):
    """Test template compilation and caching"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.paths = GradleInitPaths(base_dir=self.test_dir / '.gradleInit')
        self.paths.ensure_structure()
        
        # Create a test template
        self.template_name = 'test-template'
        self.template_dir = self.test_dir / 'templates' / self.template_name
        self.template_dir.mkdir(parents=True)

    def tearDown(self):
        """Clean up test environment"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def _create_template_file(self, filename: str, content: str):
        """Helper to create a template file"""
        file_path = self.template_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding='utf-8')
        return file_path

    def test_basic_compilation(self):
        """Test basic template compilation"""
        # Create template with hints
        self._create_template_file(
            'build.gradle.kts',
            'group = "{{ @@01|Maven group ID=com.example@@group }}"\n'
            'version = "{{ @@02|Version=1.0.0@@version }}"\n'
        )

        # Compile template
        compiler = TemplateCompiler(self.paths, self.template_dir, self.template_name)
        compiled_path = compiler.get_compiled_template_path()

        # Check compiled directory exists
        self.assertTrue(compiled_path.exists())
        self.assertTrue((compiled_path / 'build.gradle.kts').exists())

        # Check hints are removed
        compiled_content = (compiled_path / 'build.gradle.kts').read_text()
        self.assertEqual(
            compiled_content,
            'group = "{{ group }}"\nversion = "{{ version }}"\n'
        )

        # Check cache info exists
        cache_info_file = compiled_path / '.cache_info.json'
        self.assertTrue(cache_info_file.exists())

        cache_info = json.loads(cache_info_file.read_text())
        self.assertEqual(cache_info['template_name'], self.template_name)
        self.assertEqual(cache_info['files_compiled'], 1)

    def test_cache_reuse(self):
        """Test that cache is reused when templates haven't changed"""
        # Create template
        self._create_template_file(
            'settings.gradle.kts',
            'rootProject.name = "{{ @@01|Project name=myapp@@project_name }}"\n'
        )

        # First compilation
        compiler1 = TemplateCompiler(self.paths, self.template_dir, self.template_name)
        compiled_path1 = compiler1.get_compiled_template_path()
        cache_info1 = json.loads((compiled_path1 / '.cache_info.json').read_text())
        compiled_at1 = cache_info1['compiled_at']

        # Wait a bit to ensure timestamps differ
        time.sleep(0.1)

        # Second compilation (should use cache)
        compiler2 = TemplateCompiler(self.paths, self.template_dir, self.template_name)
        compiled_path2 = compiler2.get_compiled_template_path()
        cache_info2 = json.loads((compiled_path2 / '.cache_info.json').read_text())
        compiled_at2 = cache_info2['compiled_at']

        # Cache timestamp should be the same (cache was reused)
        self.assertEqual(compiled_at1, compiled_at2)

    def test_cache_invalidation_on_file_change(self):
        """Test that cache is invalidated when source files change"""
        # Create template
        template_file = self._create_template_file(
            'README.md',
            '# {{ @@01|Project name=MyApp@@project_name }}\n'
        )

        # First compilation
        compiler1 = TemplateCompiler(self.paths, self.template_dir, self.template_name)
        compiled_path1 = compiler1.get_compiled_template_path()
        cache_info1 = json.loads((compiled_path1 / '.cache_info.json').read_text())
        compiled_at1 = cache_info1['compiled_at']

        # Wait to ensure different timestamp
        time.sleep(0.1)

        # Modify source template
        template_file.write_text(
            '# {{ @@01|Project name=MyApp@@project_name }}\n'
            '## Updated\n',
            encoding='utf-8'
        )

        # Second compilation (should recompile)
        compiler2 = TemplateCompiler(self.paths, self.template_dir, self.template_name)
        compiled_path2 = compiler2.get_compiled_template_path()
        cache_info2 = json.loads((compiled_path2 / '.cache_info.json').read_text())
        compiled_at2 = cache_info2['compiled_at']

        # Cache timestamp should be different (cache was regenerated)
        self.assertNotEqual(compiled_at1, compiled_at2)
        self.assertGreater(compiled_at2, compiled_at1)

        # Check new content is compiled
        compiled_content = (compiled_path2 / 'README.md').read_text()
        self.assertEqual(compiled_content, '# {{ project_name }}\n## Updated\n')

    def test_force_recompile(self):
        """Test force recompilation"""
        # Create template
        self._create_template_file(
            'gradle.properties',
            'kotlin.version={{ @@01|Kotlin version=2.1.0@@kotlin_version }}\n'
        )

        # First compilation
        compiler1 = TemplateCompiler(self.paths, self.template_dir, self.template_name)
        compiled_path1 = compiler1.get_compiled_template_path()
        cache_info1 = json.loads((compiled_path1 / '.cache_info.json').read_text())
        compiled_at1 = cache_info1['compiled_at']

        # Wait a bit
        time.sleep(0.1)

        # Force recompile
        compiler2 = TemplateCompiler(self.paths, self.template_dir, self.template_name)
        compiled_path2 = compiler2.get_compiled_template_path(force_recompile=True)
        cache_info2 = json.loads((compiled_path2 / '.cache_info.json').read_text())
        compiled_at2 = cache_info2['compiled_at']

        # Cache should be regenerated
        self.assertNotEqual(compiled_at1, compiled_at2)
        self.assertGreater(compiled_at2, compiled_at1)

    def test_multiple_files_compilation(self):
        """Test compilation of multiple files in directory structure"""
        # Create multiple template files
        self._create_template_file(
            'build.gradle.kts',
            'group = "{{ @@01|Group@@group }}"\n'
        )
        self._create_template_file(
            'settings.gradle.kts',
            'rootProject.name = "{{ @@02|Name@@project_name }}"\n'
        )
        self._create_template_file(
            'src/main/kotlin/Main.kt',
            'package {{ @@03|Package@@package }}\n'
            'fun main() {\n'
            '    println("{{ @@04|Message=Hello@@message }}")\n'
            '}\n'
        )

        # Compile
        compiler = TemplateCompiler(self.paths, self.template_dir, self.template_name)
        compiled_path = compiler.get_compiled_template_path()

        # Check all files are compiled
        self.assertTrue((compiled_path / 'build.gradle.kts').exists())
        self.assertTrue((compiled_path / 'settings.gradle.kts').exists())
        self.assertTrue((compiled_path / 'src/main/kotlin/Main.kt').exists())

        # Check hints are removed from all files
        main_kt = (compiled_path / 'src/main/kotlin/Main.kt').read_text()
        self.assertIn('package {{ package }}', main_kt)
        self.assertIn('println("{{ message }}")', main_kt)
        self.assertNotIn('@@', main_kt)

        # Check cache info
        cache_info = json.loads((compiled_path / '.cache_info.json').read_text())
        self.assertEqual(cache_info['files_compiled'], 3)

    def test_binary_files_copied(self):
        """Test that binary files are copied as-is"""
        # Create text and binary files
        self._create_template_file('text.txt', 'Text content with {{ @@01|Var@@var }}\n')
        
        # Create a simple binary file (PNG header)
        binary_file = self.template_dir / 'image.png'
        binary_file.write_bytes(b'\x89PNG\r\n\x1a\n')

        # Compile
        compiler = TemplateCompiler(self.paths, self.template_dir, self.template_name)
        compiled_path = compiler.get_compiled_template_path()

        # Check text file is compiled
        text_content = (compiled_path / 'text.txt').read_text()
        self.assertEqual(text_content, 'Text content with {{ var }}\n')

        # Check binary file is copied unchanged
        binary_content = (compiled_path / 'image.png').read_bytes()
        self.assertEqual(binary_content, b'\x89PNG\r\n\x1a\n')

    def test_skip_git_directory(self):
        """Test that .git directory is skipped during compilation"""
        # Create template with .git directory
        self._create_template_file('build.gradle.kts', 'version = "{{ @@01|Ver@@version }}"\n')
        
        git_dir = self.template_dir / '.git'
        git_dir.mkdir(parents=True)
        (git_dir / 'config').write_text('[core]\n')

        # Compile
        compiler = TemplateCompiler(self.paths, self.template_dir, self.template_name)
        compiled_path = compiler.get_compiled_template_path()

        # Check .git is not in compiled directory
        self.assertFalse((compiled_path / '.git').exists())
        
        # But build.gradle.kts should be there
        self.assertTrue((compiled_path / 'build.gradle.kts').exists())

    def test_enhanced_hints_compilation(self):
        """Test compilation of enhanced hints with regex and defaults"""
        # Create template with enhanced hints
        self._create_template_file(
            'config.properties',
            'jdk.version={{ @@01|(11|17|21)|JDK version=21@@jdk_version }}\n'
            'db.type={{ @@02|(h2|postgres|mysql)|Database=h2@@db_type }}\n'
            'install.dir={{ @@03|(c:\\\\user|c:\\\\home)|Install Dir=c:\\\\home@@install_dir }}\n'
        )

        # Compile
        compiler = TemplateCompiler(self.paths, self.template_dir, self.template_name)
        compiled_path = compiler.get_compiled_template_path()

        # Check all hints are removed
        compiled_content = (compiled_path / 'config.properties').read_text()
        expected = (
            'jdk.version={{ jdk_version }}\n'
            'db.type={{ db_type }}\n'
            'install.dir={{ install_dir }}\n'
        )
        self.assertEqual(compiled_content, expected)

    def test_plain_jinja2_variables_preserved(self):
        """Test that plain Jinja2 variables (without hints) are preserved"""
        # Create template with mix of plain and hint variables
        self._create_template_file(
            'mixed.txt',
            'Enhanced: {{ @@01|Name@@enhanced_var }}\n'
            'Plain: {{ plain_var }}\n'
            'Another: {{ @@02|Value@@another_enhanced }}\n'
            'Also plain: {{ another_plain }}\n'
        )

        # Compile
        compiler = TemplateCompiler(self.paths, self.template_dir, self.template_name)
        compiled_path = compiler.get_compiled_template_path()

        # Check both types are handled correctly
        compiled_content = (compiled_path / 'mixed.txt').read_text()
        expected = (
            'Enhanced: {{ enhanced_var }}\n'
            'Plain: {{ plain_var }}\n'
            'Another: {{ another_enhanced }}\n'
            'Also plain: {{ another_plain }}\n'
        )
        self.assertEqual(compiled_content, expected)

    def test_cache_info_structure(self):
        """Test cache info JSON structure"""
        # Create simple template
        self._create_template_file('test.txt', '{{ @@01|Test@@test_var }}\n')

        # Compile
        compiler = TemplateCompiler(self.paths, self.template_dir, self.template_name)
        compiled_path = compiler.get_compiled_template_path()

        # Check cache info structure
        cache_info_file = compiled_path / '.cache_info.json'
        self.assertTrue(cache_info_file.exists())

        cache_info = json.loads(cache_info_file.read_text())
        
        # Check required fields
        self.assertIn('template_name', cache_info)
        self.assertIn('source_path', cache_info)
        self.assertIn('compiled_at', cache_info)
        self.assertIn('files_compiled', cache_info)

        # Check values
        self.assertEqual(cache_info['template_name'], self.template_name)
        self.assertEqual(cache_info['source_path'], str(self.template_dir))
        self.assertIsInstance(cache_info['compiled_at'], float)
        self.assertIsInstance(cache_info['files_compiled'], int)
        self.assertGreater(cache_info['files_compiled'], 0)


class TestTemplateCompilerIntegration(unittest.TestCase):
    """Integration tests for template compiler with real templates"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.paths = GradleInitPaths(base_dir=self.test_dir / '.gradleInit')
        self.paths.ensure_structure()

    def tearDown(self):
        """Clean up test environment"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_kotlin_single_template_structure(self):
        """Test compilation of kotlin-single-like template structure"""
        template_name = 'kotlin-single'
        template_dir = self.test_dir / 'templates' / template_name
        
        # Create structure similar to kotlin-single
        (template_dir / 'src/main/kotlin').mkdir(parents=True)
        (template_dir / 'src/test/kotlin').mkdir(parents=True)
        
        # Create files
        (template_dir / 'build.gradle.kts').write_text(
            'plugins {\n'
            '    kotlin("jvm") version "{{ @@01|Kotlin version@@kotlin_version }}"\n'
            '}\n'
            'group = "{{ @@02|Group=com.example@@group }}"\n'
            'version = "{{ @@03|Version=1.0.0@@version }}"\n',
            encoding='utf-8'
        )
        
        (template_dir / 'settings.gradle.kts').write_text(
            'rootProject.name = "{{ @@04|Project name@@project_name }}"\n',
            encoding='utf-8'
        )
        
        (template_dir / 'src/main/kotlin/Main.kt').write_text(
            'package {{ @@05|Package@@package }}\n'
            '\n'
            'fun main() {\n'
            '    println("{{ @@06|Message=Hello World@@message }}")\n'
            '}\n',
            encoding='utf-8'
        )

        # Compile
        compiler = TemplateCompiler(self.paths, template_dir, template_name)
        compiled_path = compiler.get_compiled_template_path()

        # Verify structure is preserved
        self.assertTrue((compiled_path / 'src/main/kotlin').is_dir())
        self.assertTrue((compiled_path / 'src/test/kotlin').is_dir())
        
        # Verify files are compiled correctly
        build_content = (compiled_path / 'build.gradle.kts').read_text()
        self.assertIn('version "{{ kotlin_version }}"', build_content)
        self.assertIn('group = "{{ group }}"', build_content)
        self.assertNotIn('@@', build_content)
        
        main_content = (compiled_path / 'src/main/kotlin/Main.kt').read_text()
        self.assertIn('package {{ package }}', main_content)
        self.assertIn('println("{{ message }}")', main_content)
        self.assertNotIn('@@', main_content)


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestTemplateCompilation))
    suite.addTests(loader.loadTestsFromTestCase(TestTemplateCompilerIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
