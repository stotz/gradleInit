#!/usr/bin/env python3
"""Debug test for config version issue"""
import sys
import tempfile
import subprocess
from pathlib import Path

# Create temp directory
test_dir = Path(tempfile.mkdtemp(prefix='gradleInit_debug_'))
print(f"Test directory: {test_dir}")

# Create config file
config_dir = test_dir / '.gradleInit'
config_dir.mkdir(parents=True, exist_ok=True)
config_file = config_dir / 'config'

config_content = """[defaults]
group = "ch.typedef"
version = "0.0.1"
gradle_version = "8.14.3"
kotlin_version = "2.2.20"
jdk_version = "21"

[custom]
author = "Test Author"
email = "test@example.com"
"""

config_file.write_text(config_content, encoding='utf-8')
print(f"Config file: {config_file}")
print(f"Config content:\n{config_content}")

# Run gradleInit
gradleInit_py = Path(__file__).parent / 'gradleInit.py'
cmd = [
    sys.executable, str(gradleInit_py), 
    "init", "testApp",
    "--template", "kotlin-single", 
    "--no-interactive"
]

print(f"\nRunning: {' '.join(cmd)}")
print(f"Working directory: {test_dir}\n")

env = dict(HOME=str(test_dir))
result = subprocess.run(
    cmd,
    cwd=test_dir,
    capture_output=True,
    text=True,
    env=env
)

print("=" * 70)
print("STDOUT:")
print("=" * 70)
print(result.stdout)

print("\n" + "=" * 70)
print("STDERR (Debug output):")
print("=" * 70)
print(result.stderr)

print("\n" + "=" * 70)
print(f"Return code: {result.returncode}")
print("=" * 70)

# Check build.gradle.kts
build_file = test_dir / 'testApp' / 'build.gradle.kts'
if build_file.exists():
    content = build_file.read_text()
    print("\nbuild.gradle.kts version line:")
    for line in content.split('\n'):
        if 'version =' in line:
            print(f"  {line}")
