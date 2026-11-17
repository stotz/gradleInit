#!/usr/bin/env python3
"""Quick test with local templates"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from gradleInit import TemplateMetadata, ProjectGenerator

def test():
    # Use ~/.gradleInit/templates/official/kotlin-single if available
    home = Path.home()
    template_path = home / '.gradleInit' / 'templates' / 'official' / 'kotlin-single'
    
    if not template_path.exists():
        print(f"Template not found: {template_path}")
        print("Run: gradleInit.py templates --update")
        return False
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        cache_dir = tmpdir / 'cache'
        cache_dir.mkdir()
        
        # Create metadata
        metadata = TemplateMetadata(template_path, cache_dir)
        
        # Compile build.gradle.kts
        build_file = template_path / 'build.gradle.kts'
        compiled = metadata.compile_template_file(build_file)
        
        print(f"Original has hints: {'@@' in build_file.read_text()}")
        print(f"Compiled has hints: {'@@' in compiled}")
        print(f"Compiled has variables: {'{{ group }}' in compiled}")
        
        # Generate project
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
        
        print(f"Generation success: {success}")
        
        if success:
            gen_build = project_path / 'build.gradle.kts'
            gen_content = gen_build.read_text()
            print(f"Generated has hints: {'@@' in gen_content}")
            print(f"Generated has variables: {'{{ group }}' in gen_content}")
            print(f"Generated has context value: {'com.test' in gen_content}")
        
        return success

if __name__ == '__main__':
    success = test()
    sys.exit(0 if success else 1)
