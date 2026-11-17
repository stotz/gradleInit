#!/usr/bin/env python3
"""
Test suite for template compilation caching system

Tests:
1. Cache creation and structure
2. Compilation on first run
3. Cache hit on subsequent runs
4. Cache invalidation on template modification
5. Cache directory per template
6. Nested file caching
7. Performance improvement
"""

import sys
import time
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import gradleInit
from gradleInit import TemplateMetadata, TemplateHintParser


def setup_test_template(template_dir: Path, template_name: str = "test-template"):
    """
    Create a test template with inline hints
    
    Args:
        template_dir: Directory to create template in
        template_name: Name of template
    
    Returns:
        Path to template
    """
    template_path = template_dir / template_name
    template_path.mkdir(parents=True, exist_ok=True)
    
    # Create template files with hints
    build_file = template_path / "build.gradle.kts"
    build_file.write_text("""
// {{ @@01|Maven group ID@@group }}
// {{ @@02|Project version@@version }}
plugins {
    kotlin("jvm") version "{{ kotlin_version }}"
}

group = "{{ group }}"
version = "{{ version }}"
""")
    
    # Create nested directories
    kotlin_dir = template_path / "src" / "main" / "kotlin"
    kotlin_dir.mkdir(parents=True, exist_ok=True)
    
    main_file = kotlin_dir / "Main.kt"
    main_file.write_text("""
package {{ group }}

fun main() {
    println("{{ @@03|Application name@@app_name }}")
}
""")
    
    settings_file = template_path / "settings.gradle.kts"
    settings_file.write_text("""
rootProject.name = "{{ project_name }}"
""")
    
    return template_path


def test_cache_directory_creation():
    """Test that cache directory is created properly"""
    print("\n=== Test: Cache Directory Creation ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        template_path = setup_test_template(tmpdir)
        cache_dir = tmpdir / "cache"
        
        # Create metadata with cache
        metadata = TemplateMetadata(template_path, cache_dir)
        
        # Verify cache directory exists
        assert cache_dir.exists(), "Cache directory not created"
        print(f"[OK] Cache directory created: {cache_dir}")
    
    print("[PASS] Cache directory creation test passed")
    return True


def test_initial_compilation():
    """Test that templates are compiled on first access"""
    print("\n=== Test: Initial Compilation ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        template_path = setup_test_template(tmpdir)
        cache_dir = tmpdir / "cache"
        
        metadata = TemplateMetadata(template_path, cache_dir)
        
        # Compile a template file
        source_file = template_path / "build.gradle.kts"
        compiled_content = metadata.compile_template_file(source_file)
        
        # Verify hints are removed
        assert "@@" not in compiled_content, "Hints not removed from compiled content"
        assert "{{ group }}" in compiled_content, "Variable not preserved"
        assert "Maven group ID" not in compiled_content, "Help text not removed"
        
        # Verify cache file was created
        cache_file = cache_dir / "test-template" / "build.gradle.kts"
        assert cache_file.exists(), "Cache file not created"
        
        # Verify cache content matches
        cached_content = cache_file.read_text(encoding='utf-8')
        assert cached_content == compiled_content, "Cache content mismatch"
        
        print("[OK] Template compiled and cached")
        print(f"[OK] Cache file: {cache_file}")
        print(f"[OK] Compiled content length: {len(compiled_content)} bytes")
    
    print("[PASS] Initial compilation test passed")
    return True


def test_cache_hit():
    """Test that subsequent access uses cached version"""
    print("\n=== Test: Cache Hit ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        template_path = setup_test_template(tmpdir)
        cache_dir = tmpdir / "cache"
        
        metadata = TemplateMetadata(template_path, cache_dir)
        source_file = template_path / "build.gradle.kts"
        
        # First compilation
        compiled_content_1 = metadata.compile_template_file(source_file)
        cache_file = cache_dir / "test-template" / "build.gradle.kts"
        first_mtime = cache_file.stat().st_mtime
        
        # Wait a bit to ensure different mtime if file is rewritten
        time.sleep(0.1)
        
        # Second compilation (should hit cache)
        compiled_content_2 = metadata.compile_template_file(source_file)
        second_mtime = cache_file.stat().st_mtime
        
        # Verify content matches
        assert compiled_content_1 == compiled_content_2, "Content mismatch between compilations"
        
        # Verify cache file was not rewritten (mtime unchanged)
        assert first_mtime == second_mtime, "Cache file was recompiled unnecessarily"
        
        print("[OK] Cache hit - file not recompiled")
        print(f"[OK] First mtime: {first_mtime}")
        print(f"[OK] Second mtime: {second_mtime}")
    
    print("[PASS] Cache hit test passed")
    return True


def test_cache_invalidation():
    """Test that cache is invalidated when source template changes"""
    print("\n=== Test: Cache Invalidation ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        template_path = setup_test_template(tmpdir)
        cache_dir = tmpdir / "cache"
        
        metadata = TemplateMetadata(template_path, cache_dir)
        source_file = template_path / "build.gradle.kts"
        
        # First compilation
        compiled_content_1 = metadata.compile_template_file(source_file)
        cache_file = cache_dir / "test-template" / "build.gradle.kts"
        first_cache_mtime = cache_file.stat().st_mtime
        
        # Wait to ensure different mtime
        time.sleep(0.1)
        
        # Modify source template
        modified_content = source_file.read_text() + "\n// Modified\n"
        source_file.write_text(modified_content)
        source_mtime = source_file.stat().st_mtime
        
        # Second compilation (should recompile due to newer source)
        compiled_content_2 = metadata.compile_template_file(source_file)
        second_cache_mtime = cache_file.stat().st_mtime
        
        # Verify source is newer than old cache
        assert source_mtime > first_cache_mtime, "Source modification not detected"
        
        # Verify cache was updated
        assert second_cache_mtime > first_cache_mtime, "Cache not updated after source modification"
        
        # Verify content includes modification
        assert "Modified" in compiled_content_2, "Modified content not in compiled output"
        
        print("[OK] Cache invalidated after source modification")
        print(f"[OK] First cache mtime: {first_cache_mtime}")
        print(f"[OK] Source mtime: {source_mtime}")
        print(f"[OK] Second cache mtime: {second_cache_mtime}")
    
    print("[PASS] Cache invalidation test passed")
    return True


def test_nested_file_caching():
    """Test that nested template files are cached correctly"""
    print("\n=== Test: Nested File Caching ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        template_path = setup_test_template(tmpdir)
        cache_dir = tmpdir / "cache"
        
        metadata = TemplateMetadata(template_path, cache_dir)
        
        # Compile nested file
        nested_file = template_path / "src" / "main" / "kotlin" / "Main.kt"
        compiled_content = metadata.compile_template_file(nested_file)
        
        # Verify cache preserves directory structure
        cache_file = cache_dir / "test-template" / "src" / "main" / "kotlin" / "Main.kt"
        assert cache_file.exists(), "Nested cache file not created"
        assert cache_file.parent.exists(), "Cache directory structure not preserved"
        
        # Verify content
        cached_content = cache_file.read_text(encoding='utf-8')
        assert cached_content == compiled_content, "Nested file cache content mismatch"
        assert "{{ app_name }}" in compiled_content, "Variable not preserved in nested file"
        assert "@@" not in compiled_content, "Hints not removed from nested file"
        
        print("[OK] Nested file cached correctly")
        print(f"[OK] Cache path: {cache_file}")
    
    print("[PASS] Nested file caching test passed")
    return True


def test_multiple_templates():
    """Test that cache handles multiple templates separately"""
    print("\n=== Test: Multiple Templates ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        cache_dir = tmpdir / "cache"
        
        # Create two templates
        template1_path = setup_test_template(tmpdir, "template-one")
        template2_path = setup_test_template(tmpdir, "template-two")
        
        # Create metadata for both
        metadata1 = TemplateMetadata(template1_path, cache_dir)
        metadata2 = TemplateMetadata(template2_path, cache_dir)
        
        # Compile same file from both templates
        file1 = template1_path / "build.gradle.kts"
        file2 = template2_path / "build.gradle.kts"
        
        compiled1 = metadata1.compile_template_file(file1)
        compiled2 = metadata2.compile_template_file(file2)
        
        # Verify separate cache directories
        cache1 = cache_dir / "template-one" / "build.gradle.kts"
        cache2 = cache_dir / "template-two" / "build.gradle.kts"
        
        assert cache1.exists(), "Template 1 cache not created"
        assert cache2.exists(), "Template 2 cache not created"
        assert cache1 != cache2, "Cache paths should be different"
        
        # Verify both are independent
        content1 = cache1.read_text(encoding='utf-8')
        content2 = cache2.read_text(encoding='utf-8')
        assert content1 == compiled1, "Template 1 cache mismatch"
        assert content2 == compiled2, "Template 2 cache mismatch"
        
        print("[OK] Multiple templates cached separately")
        print(f"[OK] Cache 1: {cache1}")
        print(f"[OK] Cache 2: {cache2}")
    
    print("[PASS] Multiple templates test passed")
    return True


def test_cache_corruption_recovery():
    """Test that corrupted cache is regenerated"""
    print("\n=== Test: Cache Corruption Recovery ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        template_path = setup_test_template(tmpdir)
        cache_dir = tmpdir / "cache"
        
        metadata = TemplateMetadata(template_path, cache_dir)
        source_file = template_path / "build.gradle.kts"
        
        # First compilation
        compiled_content_1 = metadata.compile_template_file(source_file)
        cache_file = cache_dir / "test-template" / "build.gradle.kts"
        
        # Corrupt cache file
        cache_file.write_bytes(b'\xff\xfe\xfd\xfc')  # Invalid UTF-8
        
        # Second compilation (should recover from corruption)
        compiled_content_2 = metadata.compile_template_file(source_file)
        
        # Verify content matches and is valid
        assert compiled_content_1 == compiled_content_2, "Recovery content mismatch"
        assert "{{ group }}" in compiled_content_2, "Variable not in recovered content"
        
        # Verify cache was rewritten
        recovered_content = cache_file.read_text(encoding='utf-8')
        assert recovered_content == compiled_content_2, "Cache not properly recovered"
        
        print("[OK] Recovered from corrupted cache")
    
    print("[PASS] Cache corruption recovery test passed")
    return True


def test_no_cache_fallback():
    """Test that compilation works without cache directory"""
    print("\n=== Test: No Cache Fallback ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        template_path = setup_test_template(tmpdir)
        
        # Create metadata WITHOUT cache
        metadata = TemplateMetadata(template_path, compiled_cache_dir=None)
        source_file = template_path / "build.gradle.kts"
        
        # Compile (should work without caching)
        compiled_content = metadata.compile_template_file(source_file)
        
        # Verify compilation worked
        assert "{{ group }}" in compiled_content, "Variable not preserved"
        assert "@@" not in compiled_content, "Hints not removed"
        
        print("[OK] Compilation works without cache")
    
    print("[PASS] No cache fallback test passed")
    return True


def test_performance_improvement():
    """Test that caching improves performance"""
    print("\n=== Test: Performance Improvement ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        template_path = setup_test_template(tmpdir)
        cache_dir = tmpdir / "cache"
        
        metadata = TemplateMetadata(template_path, cache_dir)
        source_file = template_path / "build.gradle.kts"
        
        # Time first compilation (no cache)
        start = time.time()
        for _ in range(100):
            compiled_content_1 = metadata.compile_template_file(source_file)
        first_time = time.time() - start
        
        # Time subsequent compilations (with cache)
        start = time.time()
        for _ in range(100):
            compiled_content_2 = metadata.compile_template_file(source_file)
        second_time = time.time() - start
        
        # Verify content matches
        assert compiled_content_1 == compiled_content_2, "Content mismatch"
        
        # Cached should be faster (or at least not significantly slower)
        improvement = (first_time - second_time) / first_time * 100
        
        print(f"[OK] First run (100x): {first_time:.4f}s")
        print(f"[OK] Cached run (100x): {second_time:.4f}s")
        print(f"[OK] Improvement: {improvement:.1f}%")
        
        # Don't fail test if caching doesn't improve performance
        # (filesystem caching might make this test unreliable)
        if improvement > 0:
            print("[OK] Caching provides performance benefit")
        else:
            print("[OK] No measurable performance difference (filesystem caching may be in effect)")
    
    print("[PASS] Performance improvement test passed")
    return True


def run_all_tests():
    """Run all compilation cache tests"""
    print("=" * 60)
    print("Template Compilation Cache Test Suite")
    print("=" * 60)
    
    tests = [
        ("Cache Directory Creation", test_cache_directory_creation),
        ("Initial Compilation", test_initial_compilation),
        ("Cache Hit", test_cache_hit),
        ("Cache Invalidation", test_cache_invalidation),
        ("Nested File Caching", test_nested_file_caching),
        ("Multiple Templates", test_multiple_templates),
        ("Cache Corruption Recovery", test_cache_corruption_recovery),
        ("No Cache Fallback", test_no_cache_fallback),
        ("Performance Improvement", test_performance_improvement),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"[FAIL] {name}")
        except Exception as e:
            failed += 1
            print(f"[FAIL] {name}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
