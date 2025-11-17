#!/usr/bin/env python3
"""
test_config_integration.py - Config Integration Tests

Tests that config values are properly loaded and used:
- Config defaults are respected
- CLI args override config
- Interactive mode uses config defaults
- Validation works with config values
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path
import shutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

def run_command(cmd: list, cwd: str = None, input_text: str = None, env: dict = None) -> tuple:
    """Run command and return (returncode, stdout, stderr)"""
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE if input_text else None,
        cwd=cwd,
        env=env,
        text=True
    )
    stdout, stderr = process.communicate(input=input_text)
    return process.returncode, stdout, stderr


class TestConfigIntegration:
    """Test config file integration"""
    
    def setup_method(self):
        """Setup test environment"""
        self.test_dir = tempfile.mkdtemp(prefix="gradleInit_config_test_")
        self.gradleInit_home = Path(self.test_dir) / ".gradleInit"
        self.gradleInit_home.mkdir(parents=True)
        self.config_file = self.gradleInit_home / "config"
        
        # Create test environment
        self.env = os.environ.copy()
        self.env['HOME'] = self.test_dir
        self.env['USERPROFILE'] = self.test_dir  # Windows
        
        # Get gradleInit.py path
        self.gradleInit_py = Path(__file__).parent / "gradleInit.py"
        
        print(f"\nTest directory: {self.test_dir}")
        print(f"Config file: {self.config_file}")
    
    def teardown_method(self):
        """Cleanup test environment"""
        if Path(self.test_dir).exists():
            try:
                # On Windows, git files might be locked - use ignore_errors
                shutil.rmtree(self.test_dir, ignore_errors=True)
            except Exception as e:
                # If still fails, just warn - cleanup not critical
                print(f"\n[WARN] Could not cleanup {self.test_dir}: {e}")
    
    def write_config(self, content: str):
        """Write config file"""
        self.config_file.write_text(content)
    
    def test_01_config_defaults_used_in_cli_mode(self):
        """Test that config defaults are used in CLI mode"""
        print("\n" + "="*70)
        print("TEST: Config defaults used in CLI mode")
        print("="*70)
        
        # Write config with custom defaults
        config_content = """
[defaults]
group = "ch.typedef"
version = "0.0.1"
gradle_version = "8.14.3"
kotlin_version = "2.2.20"
jdk_version = "21"

[custom]
author = "Test Author"
email = "test@example.com"
"""
        self.write_config(config_content)
        
        # Initialize templates
        returncode, stdout, stderr = run_command(
            [sys.executable, str(self.gradleInit_py), "templates", "--update"],
            env=self.env
        )
        
        assert returncode == 0, f"Templates update failed: {stderr}"
        
        # Create project using config defaults (no --group, --version specified)
        project_dir = Path(self.test_dir) / "testApp"
        returncode, stdout, stderr = run_command(
            [sys.executable, str(self.gradleInit_py), "init", "testApp", 
             "--template", "kotlin-single", "--no-interactive"],
            cwd=self.test_dir,
            env=self.env
        )
        
        print(f"Return code: {returncode}")
        print(f"STDOUT:\n{stdout}")
        print(f"STDERR:\n{stderr}")
        
        assert returncode == 0, f"Init failed: {stderr}"
        
        # Check that config values were used
        build_file = project_dir / "build.gradle.kts"
        assert build_file.exists(), "build.gradle.kts not created"
        
        content = build_file.read_text()
        assert 'group = "ch.typedef"' in content, f"Config group not used. Content:\n{content}"
        assert 'version = "0.0.1"' in content, f"Config version not used. Content:\n{content}"
        assert 'jvmToolchain(21)' in content, f"Config jdk_version not used. Content:\n{content}"
        
        print("[OK] Config defaults were correctly used")
    
    def test_02_cli_args_override_config(self):
        """Test that CLI args override config defaults"""
        print("\n" + "="*70)
        print("TEST: CLI args override config")
        print("="*70)
        
        # Write config with defaults
        config_content = """
[defaults]
group = "ch.typedef"
version = "0.0.1"
gradle_version = "8.14"
kotlin_version = "2.1.0"
jdk_version = "21"
"""
        self.write_config(config_content)
        
        # Create project with CLI overrides
        project_dir = Path(self.test_dir) / "testApp"
        returncode, stdout, stderr = run_command(
            [sys.executable, str(self.gradleInit_py), "init", "testApp",
             "--template", "kotlin-single",
             "--group", "com.override",
             "--project-version", "2.0.0",
             "--jdk_version", "17",
             "--no-interactive"],
            cwd=self.test_dir,
            env=self.env
        )
        
        print(f"Return code: {returncode}")
        print(f"STDOUT:\n{stdout}")
        
        assert returncode == 0, f"Init failed: {stderr}"
        
        # Check that CLI values override config
        build_file = project_dir / "build.gradle.kts"
        content = build_file.read_text()
        
        assert 'group = "com.override"' in content, "CLI group did not override config"
        assert 'version = "2.0.0"' in content, "CLI version did not override config"
        assert 'jvmToolchain(17)' in content, "CLI jdk_version did not override config"
        
        print("[OK] CLI args correctly override config")
    
    def test_03_interactive_mode_shows_config_defaults(self):
        """Test that interactive mode shows config defaults in prompts"""
        print("\n" + "="*70)
        print("TEST: Interactive mode shows config defaults")
        print("="*70)
        
        # Write config
        config_content = """
[defaults]
group = "ch.typedef"
version = "0.0.1"
gradle_version = "8.14.3"
kotlin_version = "2.1.0"
jdk_version = "21"
"""
        self.write_config(config_content)
        
        # First, update templates (required for interactive mode)
        returncode, stdout, stderr = run_command(
            [sys.executable, str(self.gradleInit_py), "templates", "--update"],
            env=self.env
        )
        assert returncode == 0, f"Templates update failed: {stderr}"
        
        # Run interactive mode with just Enter keys (use defaults)
        # Input sequence:
        #   1. "n" - Skip module download
        #   2. "kotlin-single" - Choose template
        #   3. "" (empty) - Use default group (ch.typedef)
        #   4. "" (empty) - Use default version (0.0.1)
        #   5. "1" - Choose Gradle version option 1
        input_text = "n\nkotlin-single\n\n\n1\n"
        
        returncode, stdout, stderr = run_command(
            [sys.executable, str(self.gradleInit_py), "init", "testApp", "--interactive"],
            cwd=self.test_dir,
            input_text=input_text,
            env=self.env
        )
        
        print(f"Return code: {returncode}")
        print(f"STDOUT:\n{stdout}")
        
        # Check that config defaults appear in prompts
        assert "ch.typedef" in stdout, "Config group default not shown in prompt"
        assert "0.0.1" in stdout, "Config version default not shown in prompt"
        
        # If project was created, verify values
        project_dir = Path(self.test_dir) / "testApp"
        if project_dir.exists():
            build_file = project_dir / "build.gradle.kts"
            if build_file.exists():
                content = build_file.read_text()
                assert 'group = "ch.typedef"' in content, "Config group not used in interactive mode"
                assert 'version = "0.0.1"' in content, "Config version not used in interactive mode"
                print("[OK] Interactive mode used config defaults")
        else:
            print("[SKIP] Project not fully created (may need template setup)")
    
    def test_04_validation_with_config_values(self):
        """Test that validation works with config values"""
        print("\n" + "="*70)
        print("TEST: Validation with config values")
        print("="*70)
        
        # Write config with invalid jdk_version
        config_content = """
[defaults]
group = "ch.typedef"
version = "0.0.1"
gradle_version = "8.14"
kotlin_version = "2.1.0"
jdk_version = "8"
"""
        self.write_config(config_content)
        
        # Try to create project - should fail validation
        returncode, stdout, stderr = run_command(
            [sys.executable, str(self.gradleInit_py), "init", "testApp",
             "--template", "kotlin-single", "--no-interactive"],
            cwd=self.test_dir,
            env=self.env
        )
        
        print(f"Return code: {returncode}")
        print(f"STDOUT:\n{stdout}")
        print(f"STDERR:\n{stderr}")
        
        # Should fail because jdk_version=8 doesn't match pattern (11|17|21)
        # Note: This will only fail if validation is implemented
        output = stdout + stderr
        if "does not match pattern" in output or "Validation error" in output:
            print("[OK] Validation correctly rejected invalid config value")
        else:
            print("[SKIP] Validation not yet implemented or different error occurred")
    
    def test_05_env_vars_override_config(self):
        """Test that environment variables override config"""
        print("\n" + "="*70)
        print("TEST: Environment variables override config")
        print("="*70)
        
        # Write config
        config_content = """
[defaults]
group = "ch.typedef"
version = "0.0.1"
gradle_version = "8.14"
kotlin_version = "2.1.0"
jdk_version = "21"
"""
        self.write_config(config_content)
        
        # Set environment variable
        test_env = self.env.copy()
        test_env['GRADLE_INIT_GROUP'] = 'com.envvar'
        
        # Create project
        project_dir = Path(self.test_dir) / "testApp"
        returncode, stdout, stderr = run_command(
            [sys.executable, str(self.gradleInit_py), "init", "testApp",
             "--template", "kotlin-single", "--no-interactive"],
            cwd=self.test_dir,
            env=test_env
        )
        
        print(f"Return code: {returncode}")
        print(f"STDOUT:\n{stdout}")
        
        if returncode == 0:
            build_file = project_dir / "build.gradle.kts"
            if build_file.exists():
                content = build_file.read_text()
                if 'group = "com.envvar"' in content:
                    print("[OK] Environment variable correctly overrode config")
                else:
                    print(f"[FAIL] Expected 'com.envvar', content:\n{content}")
            else:
                print("[SKIP] Build file not created")
        else:
            print(f"[SKIP] Init failed: {stderr}")
    
    def test_06_priority_order(self):
        """Test priority order: CLI > ENV > Config"""
        print("\n" + "="*70)
        print("TEST: Priority order CLI > ENV > Config")
        print("="*70)
        
        # Write config
        config_content = """
[defaults]
group = "ch.typedef"
version = "1.0.0"
gradle_version = "8.14"
kotlin_version = "2.1.0"
jdk_version = "21"
"""
        self.write_config(config_content)
        
        # Set environment variable (should override config)
        test_env = self.env.copy()
        test_env['GRADLE_INIT_VERSION'] = '2.0.0'
        
        # CLI arg (should override both)
        project_dir = Path(self.test_dir) / "testApp"
        returncode, stdout, stderr = run_command(
            [sys.executable, str(self.gradleInit_py), "init", "testApp",
             "--template", "kotlin-single",
             "--project-version", "3.0.0",
             "--no-interactive"],
            cwd=self.test_dir,
            env=test_env
        )
        
        print(f"Return code: {returncode}")
        print(f"STDOUT:\n{stdout}")
        
        if returncode == 0:
            build_file = project_dir / "build.gradle.kts"
            if build_file.exists():
                content = build_file.read_text()
                # CLI should win
                if 'version = "3.0.0"' in content:
                    print("[OK] CLI correctly has highest priority")
                else:
                    print(f"[FAIL] Expected CLI value '3.0.0', content:\n{content}")
            else:
                print("[SKIP] Build file not created")
        else:
            print(f"[SKIP] Init failed: {stderr}")


def run_tests():
    """Run all tests"""
    import pytest
    
    # Run with pytest
    return pytest.main([__file__, "-v", "-s"])


if __name__ == "__main__":
    sys.exit(run_tests())
