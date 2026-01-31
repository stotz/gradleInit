#!/usr/bin/env python3
"""
Quick test to verify template compilation with real templates
"""
import sys
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from gradleInit import TemplateMetadata, ProjectGenerator, TemplateRepository

def test_real_template_compilation():
    """Test compilation with actual kotlin-single template"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Clone templates
        templates_dir = tmpdir / "templates"
        repo = TemplateRepository('test', templates_dir, 'https://github.com/stotz/gradleInitTemplates.git')
        
        print("Cloning templates...")
        if not repo.clone():
            print("[FAIL] Could not clone templates")
            return False
        
        template_path = templates_dir / 'kotlin-single'
        if not template_path.exists():
            print(f"[FAIL] Template not found: {template_path}")
            return False
        
        # Create cache directory
        cache_dir = tmpdir / 'cache'
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Create metadata with cache
        print("Creating metadata with cache...")
        metadata = TemplateMetadata(template_path, cache_dir)
        
        # Check one file
        build_file = template_path / 'build.gradle.kts'
        print(f"Checking: {build_file}")
        
        # Read original
        original = build_file.read_text(encoding='utf-8')
        print(f"Original has hints: {'@@' in original}")
        
        # Compile
        print("Compiling template...")
        compiled = metadata.compile_template_file(build_file)
        print(f"Compiled has hints: {'@@' in compiled}")
        print(f"Compiled has variables: {'{{ group }}' in compiled}")
        
        # Verify
        if '@@' in compiled:
            print("[FAIL] Hints not removed from compiled template!")
            print(f"First 200 chars of compiled:\n{compiled[:200]}")
            return False
        
        if '{{ group }}' not in compiled:
            print("[FAIL] Variables not preserved in compiled template!")
            print(f"First 200 chars of compiled:\n{compiled[:200]}")
            return False
        
        print("[OK] Template compiled correctly")
        
        # Now test full generation
        print("\nTesting full project generation...")
        project_path = tmpdir / 'test-project'
        
        context = {
            'project_name': 'test-project',
            'group': 'com.test',
            'version': '1.0.0',
            'kotlin_version': '2.2.0',
            'gradle_version': '9.0',
            'jdk_version': '21',
            'vendor': 'Test Vendor'
        }
        
        generator = ProjectGenerator(template_path, context, project_path, metadata)
        success = generator.generate()
        
        if not success:
            print("[FAIL] Project generation failed")
            return False
        
        # Check generated build.gradle.kts
        generated_build = project_path / 'build.gradle.kts'
        if not generated_build.exists():
            print("[FAIL] Generated build.gradle.kts not found")
            return False
        
        generated_content = generated_build.read_text(encoding='utf-8')
        
        # Should have actual values, not variables
        if '{{ group }}' in generated_content:
            print("[FAIL] Variables not replaced in generated file!")
            print(f"First 200 chars:\n{generated_content[:200]}")
            return False
        
        if '@@' in generated_content:
            print("[FAIL] Hints found in generated file!")
            print(f"First 200 chars:\n{generated_content[:200]}")
            return False
        
        if 'com.test' not in generated_content:
            print("[FAIL] Context values not in generated file!")
            print(f"First 200 chars:\n{generated_content[:200]}")
            return False
        
        print("[OK] Project generated correctly")
        print(f"[OK] Generated project at: {project_path}")
        
        return True

if __name__ == '__main__':
    print("=" * 60)
    print("Real Template Compilation Test")
    print("=" * 60)
    
    success = test_real_template_compilation()
    
    if success:
        print("\n" + "=" * 60)
        print("[PASS] All checks passed!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("[FAIL] Test failed!")
        print("=" * 60)
        sys.exit(1)
