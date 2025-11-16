#!/usr/bin/env python3
"""
test_config_loading.py - Explicit Config Loading Tests

Tests that specifically verify config file is loaded and used.
This test suite was created to catch the bug where config values
were not being used in interactive mode.
"""

import os
import sys
import tempfile
from pathlib import Path
import shutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import after path is set
from gradleInit import load_config, get_config_default, GradleInitPaths


def test_load_config_from_file():
    """Test that load_config actually loads a config file"""
    print("\n" + "="*70)
    print("TEST: load_config loads file content")
    print("="*70)
    
    # Create temp config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
        f.write("""
[defaults]
group = "ch.typedef"
version = "0.0.1"
jdk_version = "21"

[custom]
author = "Test Author"
email = "test@example.com"
""")
        config_file = Path(f.name)
    
    try:
        # Load config
        config = load_config(config_file)
        
        # Verify structure
        assert 'defaults' in config, "Config missing 'defaults' section"
        assert 'custom' in config, "Config missing 'custom' section"
        
        # Verify values
        assert config['defaults']['group'] == 'ch.typedef', f"Expected 'ch.typedef', got {config['defaults']['group']}"
        assert config['defaults']['version'] == '0.0.1', f"Expected '0.0.1', got {config['defaults']['version']}"
        assert config['defaults']['jdk_version'] == '21', f"Expected '21', got {config['defaults']['jdk_version']}"
        assert config['custom']['author'] == 'Test Author', f"Expected 'Test Author', got {config['custom']['author']}"
        
        print("[OK] Config file loaded correctly")
        print(f"     Loaded: {config}")
        
    finally:
        config_file.unlink()


def test_get_config_default_returns_config_values():
    """Test that get_config_default returns config values"""
    print("\n" + "="*70)
    print("TEST: get_config_default returns config values")
    print("="*70)
    
    config = {
        'defaults': {
            'group': 'ch.typedef',
            'version': '0.0.1',
            'jdk_version': '21'
        },
        'custom': {
            'author': 'Test Author'
        }
    }
    
    # Test defaults section
    group = get_config_default(config, 'group', 'com.example')
    assert group == 'ch.typedef', f"Expected 'ch.typedef', got '{group}'"
    
    version = get_config_default(config, 'version', '1.0.0')
    assert version == '0.0.1', f"Expected '0.0.1', got '{version}'"
    
    jdk = get_config_default(config, 'jdk_version', '17')
    assert jdk == '21', f"Expected '21', got '{jdk}'"
    
    # Test custom section
    author = get_config_default(config, 'author', 'Unknown')
    assert author == 'Test Author', f"Expected 'Test Author', got '{author}'"
    
    # Test fallback
    missing = get_config_default(config, 'nonexistent', 'fallback')
    assert missing == 'fallback', f"Expected 'fallback', got '{missing}'"
    
    print("[OK] get_config_default works correctly")
    print(f"     group: {group}")
    print(f"     version: {version}")
    print(f"     jdk_version: {jdk}")
    print(f"     author: {author}")
    print(f"     missing: {missing}")


def test_gradle_init_paths_finds_config():
    """Test that GradleInitPaths correctly locates config file"""
    print("\n" + "="*70)
    print("TEST: GradleInitPaths finds config file")
    print("="*70)
    
    # Create temp home directory
    test_dir = tempfile.mkdtemp(prefix="gradleInit_paths_test_")
    
    try:
        # Create GradleInitPaths with custom base
        base_dir = Path(test_dir) / ".gradleInit"
        paths = GradleInitPaths(base_dir=base_dir)
        paths.ensure_structure()
        
        # Verify config file path
        expected_config = base_dir / "config"
        assert paths.config_file == expected_config, \
            f"Expected {expected_config}, got {paths.config_file}"
        
        # Verify default config was created
        assert paths.config_file.exists(), "Config file not created"
        
        # Load and verify default config
        config = load_config(paths.config_file)
        assert 'defaults' in config, "Default config missing 'defaults' section"
        assert 'group' in config['defaults'], "Default config missing 'group'"
        
        print("[OK] GradleInitPaths finds config correctly")
        print(f"     Config path: {paths.config_file}")
        print(f"     Config exists: {paths.config_file.exists()}")
        print(f"     Config content: {config.get('defaults', {})}")
        
    finally:
        if Path(test_dir).exists():
            shutil.rmtree(test_dir)


def test_config_priority_order():
    """Test that config values have correct priority"""
    print("\n" + "="*70)
    print("TEST: Config priority order")
    print("="*70)
    
    # Simulate: defaults section value should be returned
    config = {
        'defaults': {
            'group': 'from.defaults'
        }
    }
    
    result = get_config_default(config, 'group', 'fallback')
    assert result == 'from.defaults', \
        f"Expected defaults value 'from.defaults', got '{result}'"
    print("[OK] Defaults section has priority")
    
    # Simulate: custom section value should be returned if key not in defaults
    config = {
        'defaults': {
            'group': 'from.defaults'
        },
        'custom': {
            'author': 'from.custom'
        }
    }
    
    result = get_config_default(config, 'author', 'fallback')
    assert result == 'from.custom', \
        f"Expected custom value 'from.custom', got '{result}'"
    print("[OK] Custom section used when key not in defaults")
    
    # Simulate: fallback should be used if key in neither section
    result = get_config_default(config, 'missing', 'fallback')
    assert result == 'fallback', \
        f"Expected fallback value 'fallback', got '{result}'"
    print("[OK] Fallback used when key not found")
    
    # Simulate: defaults should win over custom for same key
    config = {
        'defaults': {
            'group': 'from.defaults'
        },
        'custom': {
            'group': 'from.custom'  # This should be ignored
        }
    }
    
    result = get_config_default(config, 'group', 'fallback')
    assert result == 'from.defaults', \
        f"Expected defaults to win: 'from.defaults', got '{result}'"
    print("[OK] Defaults section has priority over custom section")


def test_empty_config_uses_fallbacks():
    """Test that empty config uses fallback values"""
    print("\n" + "="*70)
    print("TEST: Empty config uses fallbacks")
    print("="*70)
    
    config = {}
    
    group = get_config_default(config, 'group', 'com.example')
    version = get_config_default(config, 'version', '1.0.0')
    jdk = get_config_default(config, 'jdk_version', '21')
    
    assert group == 'com.example', f"Expected fallback 'com.example', got '{group}'"
    assert version == '1.0.0', f"Expected fallback '1.0.0', got '{version}'"
    assert jdk == '21', f"Expected fallback '21', got '{jdk}'"
    
    print("[OK] Empty config correctly uses fallbacks")
    print(f"     group: {group}")
    print(f"     version: {version}")
    print(f"     jdk_version: {jdk}")


def run_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("RUNNING CONFIG LOADING TESTS")
    print("="*70)
    
    tests = [
        test_load_config_from_file,
        test_get_config_default_returns_config_values,
        test_gradle_init_paths_finds_config,
        test_config_priority_order,
        test_empty_config_uses_fallbacks
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"[ERROR] {test.__name__}: {e}")
            failed += 1
    
    print("\n" + "="*70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*70)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_tests())
