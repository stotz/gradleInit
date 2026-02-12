#!/usr/bin/env python3
"""
gradleInit.py - Modern Kotlin/Gradle Project Initializer

Architecture: Core + Optional Modules
- Core features embedded (~1200 lines)
- Optional modules from ~/.gradleInit/modules/ (~600 lines)
- Git required for templates (already a requirement)
- Modules auto-download on demand

Version: 1.3.0
Author: Urs Stotz
License: MIT
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# ============================================================================
# Version & Constants
# ============================================================================

SCRIPT_VERSION = "1.6.1"
MODULES_REPO = "https://github.com/stotz/gradleInitModules.git"
TEMPLATES_REPO = "https://github.com/stotz/gradleInitTemplates.git"
MODULES_VERSION = "main"  # Use main branch (v1.3.0 tag doesn't exist yet)

# Platform detection
IS_WINDOWS = sys.platform.startswith('win')

# Scoop detection
SCOOP_DIR = os.environ.get('SCOOP')
SCOOP_SHIMS_DIR = os.path.join(SCOOP_DIR, 'shims') if SCOOP_DIR else None

# Default Gradle version
DEFAULT_GRADLE_VERSION = "8.14"
GRADLE_VERSIONS_URL = "https://services.gradle.org/versions/all"


# ============================================================================
# Gradle Version Management
# ============================================================================

def fetch_gradle_versions(include_rc: bool = False, include_nightly: bool = False) -> List[str]:
    """
    Fetch available Gradle versions from services.gradle.org

    Args:
        include_rc: Include release candidates
        include_nightly: Include nightly builds

    Returns:
        List of version strings, sorted newest first
    """
    try:
        import urllib.request

        with urllib.request.urlopen(GRADLE_VERSIONS_URL, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))

        versions = []
        for item in data:
            version = item.get('version', '')
            if not version:
                continue

            # Filter based on preferences
            if 'nightly' in version.lower() and not include_nightly:
                continue
            if 'rc' in version.lower() and not include_rc:
                continue

            versions.append(version)

        return versions

    except Exception as e:
        print_warning(f"Could not fetch Gradle versions: {e}")
        return []


def get_latest_gradle_version(include_rc: bool = False) -> Optional[str]:
    """
    Get the latest stable Gradle version

    Args:
        include_rc: Include release candidates

    Returns:
        Latest version string or None if fetch failed
    """
    versions = fetch_gradle_versions(include_rc=include_rc, include_nightly=False)

    # Filter for stable releases (no rc, no milestone)
    if not include_rc:
        stable_versions = [v for v in versions
                           if not any(x in v.lower() for x in ['rc', 'milestone', 'beta', 'alpha'])]
        if stable_versions:
            return stable_versions[0]

    return versions[0] if versions else None


def select_gradle_version_interactive() -> str:
    """
    Interactive Gradle version selection

    Returns:
        Selected version string
    """
    print()
    print("=" * 70)
    print("  Select Gradle Version")
    print("=" * 70)
    print()
    print("Fetching available Gradle versions...")

    versions = fetch_gradle_versions(include_rc=False, include_nightly=False)

    if not versions:
        print_warning("Could not fetch versions from gradle.org")
        print_info(f"Using default: {DEFAULT_GRADLE_VERSION}")
        return DEFAULT_GRADLE_VERSION

    # Show top 15 versions
    print()
    print("Available versions (showing latest 15 stable releases):")
    print()

    display_versions = versions[:15]
    for i, version in enumerate(display_versions, 1):
        marker = " (latest)" if i == 1 else ""
        print(f"  {i:2}. {version}{marker}")

    print()
    print(f"  0. Use default ({DEFAULT_GRADLE_VERSION})")
    print()

    while True:
        try:
            choice = input("Enter number (0-15) or version string: ").strip()

            # Direct version string
            if '.' in choice:
                return choice

            # Number selection
            num = int(choice)
            if num == 0:
                return DEFAULT_GRADLE_VERSION
            if 1 <= num <= len(display_versions):
                return display_versions[num - 1]

            print_error(f"Invalid selection. Please enter 0-{len(display_versions)}")

        except ValueError:
            print_error("Invalid input. Enter a number or version string")
        except KeyboardInterrupt:
            print()
            print_info(f"Using default: {DEFAULT_GRADLE_VERSION}")
            return DEFAULT_GRADLE_VERSION


# ============================================================================
# Verbose Command Execution
# ============================================================================

def run_command(cmd: list, cwd: Path = None, check: bool = True,
                capture_output: bool = True, verbose: bool = True) -> subprocess.CompletedProcess:
    """
    Run command with optional verbose output.

    Args:
        cmd: Command as list of strings
        cwd: Working directory
        check: Raise on non-zero exit
        capture_output: Capture stdout/stderr
        verbose: Show command being executed

    Returns:
        CompletedProcess result
    """
    if verbose:
        print_info(f"Executing: {' '.join(cmd)}")
        if cwd:
            print_info(f"Working directory: {cwd}")

    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        check=check,
        capture_output=capture_output,
        text=True
    )


# ============================================================================
# Scoop Shims Support
# ============================================================================

def get_scoop_shim_paths() -> Tuple[Optional[Path], Optional[Path]]:
    """Get paths to Scoop shim files if Scoop is available"""
    if not SCOOP_SHIMS_DIR:
        return None, None

    shims_dir = Path(SCOOP_SHIMS_DIR)
    if not shims_dir.exists():
        return None, None

    cmd_shim = shims_dir / 'gradleInit.cmd'
    sh_shim = shims_dir / 'gradleInit'

    return cmd_shim, sh_shim


def are_scoop_shims_installed() -> bool:
    """Check if Scoop shims are installed"""
    cmd_shim, sh_shim = get_scoop_shim_paths()
    if not cmd_shim or not sh_shim:
        return False
    return cmd_shim.exists() and sh_shim.exists()


def install_scoop_shims() -> bool:
    """Install Scoop shims for gradleInit"""
    if not SCOOP_SHIMS_DIR:
        print_error("SCOOP environment variable not set")
        print_info("Scoop is not installed or not configured")
        return False

    shims_dir = Path(SCOOP_SHIMS_DIR)
    if not shims_dir.exists():
        print_error(f"Scoop shims directory not found: {shims_dir}")
        return False

    # Get current script path
    script_path = Path(__file__).resolve()

    # Convert to Unix-style path for Git Bash compatibility
    script_path_unix = str(script_path).replace('\\', '/')
    if script_path_unix[1] == ':':
        # C:\path\to\file -> /c/path/to/file
        script_path_unix = '/' + script_path_unix[0].lower() + script_path_unix[2:]

    # Windows CMD shim
    cmd_shim = shims_dir / 'gradleInit.cmd'
    cmd_content = f"""@echo off
REM Scoop shim for gradleInit
REM Auto-generated by gradleInit.py --scoop-shims-install
REM Forwards all arguments to the Python script

python3 "{script_path}" %*
"""

    # Unix shell shim (for Git Bash, MSYS2, etc.)
    sh_shim = shims_dir / 'gradleInit'
    sh_content = f"""#!/bin/sh
# Scoop shim for gradleInit
# Auto-generated by gradleInit.py --scoop-shims-install
# Forwards all arguments to the Python script

python3 {script_path_unix} "$@"
"""

    try:
        # Write CMD shim
        print_info(f"Creating: {cmd_shim}")
        cmd_shim.write_text(cmd_content, encoding='utf-8')

        # Write shell shim
        print_info(f"Creating: {sh_shim}")
        sh_shim.write_text(sh_content, encoding='utf-8')

        # Make shell shim executable (doesn't hurt on Windows)
        try:
            os.chmod(sh_shim, 0o755)
        except Exception:
            pass  # Ignore on Windows

        print_success("Scoop shims installed successfully!")
        print()
        print_info("You can now run gradleInit from anywhere:")
        print("  gradleInit init my-project --template kotlin-single")
        print()
        print_info("To uninstall shims:")
        print("  gradleInit --scoop-shims-uninstall")

        return True

    except Exception as e:
        print_error(f"Failed to install Scoop shims: {e}")
        return False


def uninstall_scoop_shims() -> bool:
    """Uninstall Scoop shims for gradleInit"""
    cmd_shim, sh_shim = get_scoop_shim_paths()

    if not cmd_shim or not sh_shim:
        print_error("SCOOP environment variable not set")
        return False

    if not cmd_shim.exists() and not sh_shim.exists():
        print_warning("Scoop shims are not installed")
        return True

    try:
        removed = []

        if cmd_shim.exists():
            print_info(f"Removing: {cmd_shim}")
            cmd_shim.unlink()
            removed.append('gradleInit.cmd')

        if sh_shim.exists():
            print_info(f"Removing: {sh_shim}")
            sh_shim.unlink()
            removed.append('gradleInit')

        if removed:
            print_success(f"Scoop shims uninstalled: {', '.join(removed)}")

        return True

    except Exception as e:
        print_error(f"Failed to uninstall Scoop shims: {e}")
        return False


# ============================================================================
# Dependency Check
# ============================================================================

def check_dependencies():
    """Check and report missing Python dependencies"""

    missing = []
    optional_missing = []

    # Required packages
    required = {
        'toml': 'toml',
        'jinja2': 'jinja2',
    }

    # Optional packages (improve functionality)
    optional = {
        'yaml': 'pyyaml',
    }

    # Check required
    for module_name, package_name in required.items():
        try:
            __import__(module_name)
        except ImportError:
            missing.append(package_name)

    # Check optional
    for module_name, package_name in optional.items():
        try:
            __import__(module_name)
        except ImportError:
            optional_missing.append(package_name)

    # Report missing dependencies
    if missing:
        print("=" * 70)
        print("  Missing Required Dependencies")
        print("=" * 70)
        print()
        print("gradleInit requires the following Python packages:")
        for pkg in missing:
            print(f"  * {pkg}")
        print()
        print("Install with:")
        print()
        print(f"  pip install {' '.join(missing)}")
        print()
        print("Or install for current user only:")
        print()
        print(f"  pip install --user {' '.join(missing)}")
        print()
        if optional_missing:
            print("Optional packages (recommended):")
            print(f"  pip install {' '.join(optional_missing)}")
            print()
        print("=" * 70)
        sys.exit(1)

    if optional_missing:
        print(f"Note: Optional package not installed: {', '.join(optional_missing)}")
        print(f"      For better YAML support: pip install {' '.join(optional_missing)}")
        print()

    return True


# Check dependencies before importing
check_dependencies()

# Now safe to import
import toml
import jinja2

try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False


# ============================================================================
# Git Availability Check
# ============================================================================

def check_git_available() -> bool:
    """Check if git is installed"""
    try:
        subprocess.run(['git', '--version'],
                       capture_output=True,
                       check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


GIT_AVAILABLE = check_git_available()


# ============================================================================
# Utility Functions
# ============================================================================

def print_header(message: str):
    """Print header message"""
    print(f"\n{'=' * 70}")
    print(f"  {message}")
    print(f"{'=' * 70}\n")


def print_success(message: str):
    """Print success message"""
    print(f"[OK] {message}")


def print_error(message: str):
    """Print error message"""
    print(f"[ERROR] {message}", file=sys.stderr)


def print_info(message: str):
    """Print info message"""
    print(f"-> {message}")


def print_warning(message: str):
    """Print warning message"""
    print(f"[WARN] {message}")


def parse_github_url(url: str) -> Optional[Tuple[str, Optional[str]]]:
    """
    Parse GitHub URL and extract clone URL and subdirectory.

    Supports formats:
    - https://github.com/user/repo
    - https://github.com/user/repo.git
    - https://github.com/user/repo/tree/branch/subdir
    - github.com/user/repo/tree/branch/path/to/template

    Args:
        url: GitHub URL

    Returns:
        Tuple of (clone_url, subdir_path) or None if not a GitHub URL

    Examples:
        >>> parse_github_url("https://github.com/stotz/gradleInitTemplates/tree/main/kotlin-single")
        ('https://github.com/stotz/gradleInitTemplates.git', 'kotlin-single')

        >>> parse_github_url("https://github.com/stotz/gradleInitTemplates")
        ('https://github.com/stotz/gradleInitTemplates.git', None)
    """
    # Pattern: github.com/user/repo(/tree/branch/subdir)?
    pattern = r'(?:https?://)?github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/tree/[^/]+/(.+))?/?$'
    match = re.match(pattern, url)

    if not match:
        return None

    user, repo, subdir = match.groups()
    clone_url = f"https://github.com/{user}/{repo}.git"

    return (clone_url, subdir if subdir else None)


# ============================================================================
# Configuration Paths
# ============================================================================

class GradleInitPaths:
    """Manage ~/.gradleInit/ directory structure"""

    def __init__(self, base_dir: Optional[Path] = None):
        # Ensure base_dir is always a Path object
        if base_dir:
            self.base_dir = Path(base_dir) if not isinstance(base_dir, Path) else base_dir
        else:
            # Respect HOME environment variable for testing
            import os
            home = os.environ.get('HOME')
            if home:
                self.base_dir = Path(home) / '.gradleInit'
            else:
                self.base_dir = Path.home() / '.gradleInit'

        # Subdirectories
        self.config_file = self.base_dir / 'config'
        self.templates_dir = self.base_dir / 'templates'
        self.modules_dir = self.base_dir / 'modules'
        self.cache_dir = self.base_dir / 'cache'

        # Template repositories
        self.official_templates = self.templates_dir / 'official'
        self.custom_templates = self.templates_dir / 'custom'

        # Cache subdirectories
        self.remote_cache = self.cache_dir / 'remote'
        self.compiled_templates = self.cache_dir / 'compiled'

    def ensure_structure(self):
        """Create directory structure if it doesn't exist"""
        self.base_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)
        self.official_templates.mkdir(exist_ok=True)  # Create official templates dir
        self.cache_dir.mkdir(exist_ok=True)
        self.remote_cache.mkdir(exist_ok=True)
        self.compiled_templates.mkdir(exist_ok=True)
        self.custom_templates.mkdir(exist_ok=True)

        # Create default config if not exists
        if not self.config_file.exists():
            self._create_default_config()

    def _create_default_config(self):
        """Create default config file"""
        default_config = {
            'templates': {
                'official_repo': TEMPLATES_REPO,
                'auto_update': False,
                'update_interval': 'weekly'
            },
            'modules': {
                'repo': MODULES_REPO,
                'auto_load': True,
                'version': MODULES_VERSION
            },
            'defaults': {
                'group': 'com.example',
                'version': '0.1.0',
                'gradle_version': '8.11',
                'kotlin_version': '2.1.0',
                'jdk_version': '21'
            },
            'custom': {
                'author': '',
                'email': '',
                'company': '',
                'license': 'MIT'
            }
        }

        self.config_file.write_text(toml.dumps(default_config))
        print_success(f"Created default config: {self.config_file}")


# ============================================================================
# Module Loader (Optional Modules)
# ============================================================================

class ModuleLoader:
    """
    Load optional modules from ~/.gradleInit/modules/

    Features enabled by modules:
    - Maven Central integration
    - Spring Boot BOM support
    - Advanced update manager
    """

    def __init__(self, paths: GradleInitPaths):
        self.paths = paths
        self.modules_dir = paths.modules_dir

        # Feature flags
        self.maven_central_available = False
        self.spring_boot_available = False
        self.updater_available = False

    def ensure_modules(self, auto_download: bool = True) -> bool:
        """
        Ensure modules are available

        Args:
            auto_download: If True, offer to download modules on first run

        Returns:
            True if modules loaded, False if not available
        """
        # Check if modules already exist
        if self._modules_exist():
            return self._load_modules()

        # Modules don't exist
        if not auto_download:
            return False

        # Check git availability
        if not GIT_AVAILABLE:
            print_warning("Git not available - advanced features disabled")
            print_info("Install git to enable Maven Central, Spring Boot BOM")
            return False

        # First run - offer to download modules
        self._show_modules_prompt()

        response = input("Download optional modules? [Y/n]: ").strip().lower()

        if response in ['', 'y', 'yes', 'j', 'ja']:
            return self._download_modules()

        print_info("Continuing without advanced features")
        print_info("You can download later: gradleInit.py --download-modules")
        return False

    def _show_modules_prompt(self):
        """Show user-friendly prompt for module download"""
        print()
        print("+-------------------------------------------------+")
        print("| Optional Advanced Features Available            |")
        print("+-------------------------------------------------+")
        print("| * Maven Central integration                     |")
        print("| * Spring Boot BOM support                       |")
        print("| * Advanced dependency updates                   |")
        print("|                                                 |")
        print("| Size: ~50 KB (one-time download)                |")
        print("+-------------------------------------------------+")
        print()

    def _modules_exist(self) -> bool:
        """Check if modules directory exists and is valid"""
        return (
                self.modules_dir.exists() and
                (self.modules_dir / '.git').exists() and
                (self.modules_dir / 'dependencies').exists()
        )

    def _download_modules(self) -> bool:
        """Download modules from GitHub"""
        print_info(f"Downloading modules from {MODULES_REPO}...")

        try:
            # Create parent directory
            self.modules_dir.parent.mkdir(parents=True, exist_ok=True)

            # Clone repository
            cmd = ['git', 'clone', '--depth', '1']

            # Pin to specific version if not "main"
            if MODULES_VERSION != "main":
                cmd.extend(['--branch', MODULES_VERSION])

            cmd.extend([MODULES_REPO, str(self.modules_dir)])

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                print_error(f"Failed to download modules: {result.stderr}")
                print_warning("Continuing without advanced features")
                return False

            print_success("Modules downloaded successfully")
            return self._load_modules()

        except Exception as e:
            print_error(f"Error downloading modules: {e}")
            print_warning("Continuing without advanced features")
            return False

    def _load_modules(self) -> bool:
        """Load modules into Python path"""
        try:
            # Add modules directory to Python path
            if str(self.modules_dir) not in sys.path:
                sys.path.insert(0, str(self.modules_dir))

            # Try loading each module
            features_enabled = []

            # Maven Central
            try:
                import dependencies.maven_central
                self.maven_central_available = True
                features_enabled.append("Maven Central")
            except ImportError:
                pass

            # Spring Boot BOM
            try:
                import dependencies.spring_boot
                self.spring_boot_available = True
                features_enabled.append("Spring Boot BOM")
            except ImportError:
                pass

            # Update Manager
            try:
                import dependencies.updater
                self.updater_available = True
                features_enabled.append("Update Manager")
            except ImportError:
                pass

            if features_enabled:
                print_success(f"Advanced features enabled: {', '.join(features_enabled)}")

            return True

        except Exception as e:
            print_warning(f"Could not load modules: {e}")
            return False

    def update_modules(self) -> bool:
        """Update modules via git pull"""
        if not self._modules_exist():
            print_error("Modules not installed")
            print_info("Run: gradleInit.py --download-modules")
            return False

        print_info("Updating modules...")

        try:
            result = subprocess.run(
                ['git', '-C', str(self.modules_dir), 'pull'],
                capture_output=True,
                text=True,
                check=True
            )

            print_success("Modules updated")
            return True

        except subprocess.CalledProcessError as e:
            print_error(f"Failed to update modules: {e.stderr}")
            return False

    def get_modules_info(self) -> Dict[str, Any]:
        """Get information about installed modules"""
        if not self._modules_exist():
            return {'installed': False}

        info = {
            'installed': True,
            'path': str(self.modules_dir),
            'maven_central': self.maven_central_available,
            'spring_boot': self.spring_boot_available,
            'updater': self.updater_available
        }

        try:
            # Get current commit
            result = subprocess.run(
                ['git', '-C', str(self.modules_dir), 'rev-parse', '--short', 'HEAD'],
                capture_output=True,
                text=True,
                check=True
            )
            info['commit'] = result.stdout.strip()

            # Get version
            result = subprocess.run(
                ['git', '-C', str(self.modules_dir), 'describe', '--tags', '--always'],
                capture_output=True,
                text=True,
                check=True
            )
            info['version'] = result.stdout.strip()

        except subprocess.CalledProcessError:
            pass

        return info


# ============================================================================
# Feature Stubs (When Modules Not Available)
# ============================================================================

class MavenCentralStub:
    """Stub when Maven Central module not available"""

    def __init__(self):
        self._show_message()

    def _show_message(self):
        print()
        print("+------------------------------------------+")
        print("| Maven Central Integration Not Available |")
        print("+------------------------------------------+")
        print("| To enable:                               |")
        print("|   gradleInit.py --download-modules       |")
        print("+------------------------------------------+")
        print()


class SpringBootBOMStub:
    """Stub when Spring Boot BOM module not available"""

    def __init__(self):
        self._show_message()

    def _show_message(self):
        print()
        print("+------------------------------------------+")
        print("| Spring Boot BOM Support Not Available   |")
        print("+------------------------------------------+")
        print("| To enable:                               |")
        print("|   gradleInit.py --download-modules       |")
        print("+------------------------------------------+")
        print()


# ============================================================================
# Template Repository (Git-based)
# ============================================================================

class TemplateRepository:
    """Manage a template repository (Git-based)"""

    def __init__(self, name: str, path: Path, url: Optional[str] = None):
        self.name = name
        self.path = path
        self.url = url
        self.is_git = (path / '.git').exists()

    def clone(self) -> bool:
        """Clone repository if not exists or if empty"""
        # Check if path exists and has content
        if self.path.exists():
            # Check if directory has any templates (subdirectories)
            has_templates = any(item.is_dir() for item in self.path.iterdir()
                                if not item.name.startswith('.'))
            if has_templates:
                return True
            # Directory exists but is empty - remove and clone
            shutil.rmtree(self.path)

        if not self.url:
            return False

        print_info(f"Cloning {self.name} templates from {self.url}...")

        try:
            # Check if it's a GitHub tree URL (e.g., .../tree/main/subdir)
            github_info = parse_github_url(self.url)

            if github_info:
                clone_url, subdir = github_info

                # If no subdirectory, clone directly to target
                if not subdir:
                    print_info(f"-> Cloning to: {self.path}")
                    run_command(
                        ['git', 'clone', '--depth', '1', clone_url, str(self.path)],
                        verbose=True
                    )

                    # Keep .git directory for updates (don't remove)
                    # git_dir = self.path / '.git'
                    # if git_dir.exists():
                    #     shutil.rmtree(git_dir, ignore_errors=True)

                    print_success(f"Cloned {self.name} templates")
                    return True

                # Clone to temporary directory (only if subdir specified)
                temp_dir = self.path.parent / f"{self.path.name}_temp"
                if temp_dir.exists():
                    shutil.rmtree(temp_dir, ignore_errors=True)

                print_info(f"-> Cloning to temp: {temp_dir}")
                print_info(f"-> Extracting subdir: {subdir}")
                run_command(
                    ['git', 'clone', '--depth', '1', clone_url, str(temp_dir)],
                    verbose=True
                )

                # Move subdirectory contents to target
                source = temp_dir / subdir
                if not source.exists():
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    print_error(f"Subdirectory '{subdir}' not found in repository")
                    return False

                # Move subdirectory contents to target
                shutil.copytree(source, self.path)
                shutil.rmtree(temp_dir, ignore_errors=True)

                print_success(f"Cloned {self.name} templates")
                return True
            else:
                # Regular git URL - direct clone
                subprocess.run(
                    ['git', 'clone', '--depth', '1', self.url, str(self.path)],
                    check=True,
                    capture_output=True,
                    text=True
                )
                print_success(f"Cloned {self.name} templates")
                return True

        except subprocess.CalledProcessError as e:
            print_error(f"Failed to clone: {e.stderr}")
            return False
        except Exception as e:
            print_error(f"Failed to clone: {e}")
            return False

    def update(self) -> bool:
        """Update repository via git pull"""

        # Check if directory exists first
        if not self.path.exists():
            print_warning(f"{self.name} templates not found at {self.path}")
            print_info("Attempting to clone...")
            return self.clone()

        if not self.is_git:
            print_error(f"{self.name} is not a git repository")
            print()
            print_info("Templates were likely installed manually from archive.")
            print_info("To enable updates:")
            print()
            print("  1. Remove current templates:")
            print(f"     rm -rf {self.path}")
            print()
            print("  2. Clone from Git:")
            print(f"     gradleInit templates --update")
            print()
            print("     OR manually:")
            print(f"     git clone {self.url or 'REPO_URL'} {self.path}")
            print()
            return False

        print_info(f"Updating {self.name} templates...")

        try:
            # Fetch first
            subprocess.run(
                ['git', '-C', str(self.path), 'fetch'],
                check=True,
                capture_output=True,
                text=True
            )

            # Check if behind remote
            result = subprocess.run(
                ['git', '-C', str(self.path), 'rev-list', '--count', 'HEAD..@{u}'],
                capture_output=True,
                text=True
            )

            behind_count = int(result.stdout.strip() or '0')

            if behind_count == 0:
                print_success(f"{self.name} templates already up to date")
                return True

            # Get commit details before pulling
            log_result = subprocess.run(
                ['git', '-C', str(self.path), 'log', '--oneline', 'HEAD..@{u}'],
                capture_output=True,
                text=True
            )
            commit_details = log_result.stdout.strip()

            # Pull updates
            subprocess.run(
                ['git', '-C', str(self.path), 'pull'],
                check=True,
                capture_output=True,
                text=True
            )

            print_success(f"Updated {self.name} templates ({behind_count} new commits)")
            
            # Show commit details
            if commit_details:
                print()
                print_info("Changes:")
                for line in commit_details.split('\n'):
                    if line.strip():
                        print(f"     {line}")
                print()
            
            return True

        except subprocess.CalledProcessError as e:
            stderr = e.stderr.strip() if e.stderr else str(e)
            print_error(f"Git command failed: {stderr}")
            print()
            print_info("This usually means templates are not a git repository.")
            print_info("To fix:")
            print()
            print("  1. Remove current templates:")
            print(f"     rm -rf {self.path}")
            print()
            print("  2. Clone from Git:")
            print("     gradleInit templates --update")
            print()
            return False
        except Exception as e:
            print_error(f"Update failed: {e}")
            return False

    def list_templates(self) -> List[str]:
        """List available templates in repository"""
        if not self.path.exists():
            return []

        templates = []
        for item in self.path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                if (item / 'TEMPLATE.md').exists() or list(item.glob('*.j2')):
                    templates.append(item.name)

        return sorted(templates)

    def get_template_path(self, template_name: str) -> Optional[Path]:
        """Get path to specific template"""
        template_path = self.path / template_name
        if template_path.exists() and template_path.is_dir():
            return template_path
        return None


class TemplateRepositoryManager:
    """Manage multiple template repositories"""

    def __init__(self, paths: GradleInitPaths):
        self.paths = paths
        self.repositories: Dict[str, TemplateRepository] = {}

        # Register official repository
        self.repositories['official'] = TemplateRepository(
            'official',
            paths.official_templates,
            TEMPLATES_REPO
        )

        # Scan for custom repositories
        self._scan_custom_repositories()

    def _scan_custom_repositories(self):
        """Scan custom templates directory"""
        if not self.paths.custom_templates.exists():
            return

        for item in self.paths.custom_templates.iterdir():
            if item.is_dir():
                repo = TemplateRepository(
                    f"custom/{item.name}",
                    item,
                    url=None
                )
                self.repositories[f"custom/{item.name}"] = repo

    def ensure_official_templates(self) -> bool:
        """Ensure official templates are cloned"""
        official = self.repositories['official']
        # clone() now handles checking if templates exist
        return official.clone()

    def update_all(self) -> Dict[str, bool]:
        """Update all git-based repositories"""
        results = {}
        for name, repo in self.repositories.items():
            if repo.is_git:
                results[name] = repo.update()
        return results

    def list_all_templates(self) -> List[Dict[str, str]]:
        """List all available templates from all repositories"""
        templates = []

        for repo_name, repo in self.repositories.items():
            for template_name in repo.list_templates():
                templates.append({
                    'name': template_name,
                    'repository': repo_name,
                    'path': str(repo.get_template_path(template_name))
                })

        return templates

    def find_template(self, template_spec: str) -> Optional[Path]:
        """
        Find template by name or URL across all repositories.

        Args:
            template_spec: Template name, local path, or GitHub URL

        Returns:
            Path to template directory or None
        """
        # 1. Check if it's a URL (GitHub or other git)
        if template_spec.startswith(('http://', 'https://', 'git@', 'github.com')):
            return self._handle_template_url(template_spec)

        # 2. Check if it's a local path
        path = Path(template_spec)
        if path.exists() and path.is_dir():
            if (path / "TEMPLATE.md").exists():
                return path.resolve()

        # 3. Try official repository
        self.ensure_official_templates()
        if 'official' in self.repositories:
            tmpl_path = self.repositories['official'].get_template_path(template_spec)
            if tmpl_path:
                return tmpl_path

        # 4. Try custom repositories
        for repo in self.repositories.values():
            tmpl_path = repo.get_template_path(template_spec)
            if tmpl_path:
                return tmpl_path

        return None

    def _handle_template_url(self, url: str) -> Optional[Path]:
        """Handle template from URL (GitHub or git)"""
        # Create cache directory name from URL hash
        cache_name = hashlib.md5(url.encode()).hexdigest()[:12]
        cache_dir = self.paths.cache_dir / cache_name

        # If already cached, return it
        if cache_dir.exists() and (cache_dir / "TEMPLATE.md").exists():
            print_info("Using cached template")
            return cache_dir

        # Download template
        print_info(f"Downloading template from {url}...")

        temp_repo = TemplateRepository("temp", cache_dir, url)
        if temp_repo.clone():
            if (cache_dir / "TEMPLATE.md").exists():
                return cache_dir
            else:
                print_error("Downloaded repository is not a valid template (missing TEMPLATE.md)")
                shutil.rmtree(cache_dir, ignore_errors=True)
                return None

        return None

    def add_custom_repository(self, name: str, url: str) -> bool:
        """Add a custom template repository"""
        repo_path = self.paths.custom_templates / name

        if repo_path.exists():
            print_error(f"Repository '{name}' already exists")
            return False

        repo = TemplateRepository(f"custom/{name}", repo_path, url)

        if repo.clone():
            self.repositories[f"custom/{name}"] = repo
            print_success(f"Added custom repository: {name}")
            return True

        return False


# ============================================================================
# Template Metadata & Arguments
# ============================================================================

@dataclass
class TemplateArgument:
    """Template-specific CLI argument definition"""
    name: str
    type: str
    help: str
    context_key: str
    default: Any = None
    choices: Optional[List[str]] = None
    required: bool = False


@dataclass
class TemplateVariable:
    """Template variable with metadata extracted from inline hints"""
    name: str                    # Variable name (e.g., "group")
    help_text: str              # Help text from hint
    sort_order: int             # Sort order for menu (default: 999)
    regex_pattern: Optional[str] = None  # Validation regex (e.g., "11|17|21")
    default_value: Optional[str] = None  # Default value
    locations: List[Tuple[Path, int]] = field(default_factory=list)  # [(file, line_number), ...]
    is_enhanced: bool = False   # True if has hint, False if plain {{ var }}
    
    def validate(self, value: str) -> Tuple[bool, str]:
        """
        Validate value against regex pattern
        
        Args:
            value: Value to validate
        
        Returns:
            (is_valid, error_message)
        """
        if not self.regex_pattern:
            return True, ""
        
        try:
            pattern = re.compile(f"^{self.regex_pattern}$")
            if pattern.match(str(value)):
                return True, ""
            else:
                return False, f"Value '{value}' does not match pattern: {self.regex_pattern}"
        except re.error as e:
            return False, f"Invalid regex pattern: {e}"


class TemplateHintParser:
    """
    Parse template files for variables with inline hints
    
    Supports two formats:
    1. Plain: {{ variable_name }}
    2. Enhanced: {{ @@[sort]|(regex)|[help_text]=[default]@@variable_name }}
    
    Enhanced format:
    - @@ markers delimit the hint
    - Optional sort order (e.g., 01|) for menu ordering
    - Optional regex pattern (e.g., |(11|17|21)|) for validation
    - Help text is shown in --help and interactive menu
    - Optional default value after = in help text
    - Variable name follows the second @@
    - | is used as separator (better than : for Windows paths, URLs, etc.)
    
    Examples:
        {{ @@01|Maven group ID (e.g. com.company)=com.example@@group }}
        {{ @@03|(11|17|21)|JDK version=21@@jdk_version }}
        {{ @@(h2|postgres|mysql)|Database type=h2@@db_type }}
        {{ @@04|(c:\\user|c:\\home)|Install Dir=c:\\home@@install_dir }}
        {{ @@02|Application version@@version }}
        {{ project_name }}
        
    Compiles to:
        {{ group }}, {{ jdk_version }}, {{ db_type }}, {{ install_dir }}, {{ version }}, {{ project_name }}
    """
    
    # Regex patterns
    ENHANCED_PATTERN = re.compile(
        r'\{\{\s*@@'                                # {{ @@
        r'(?:(\d+)\|)?'                             # Optional sort: 01|
        r'(?:\(([^)]+)\)\|)?'                       # Optional regex: (pattern)|
        r'([^@]+?)'                                 # Help text (non-greedy)
        r'@@'                                       # @@
        r'([a-zA-Z_][a-zA-Z0-9_]*)'                # Variable name
        r'\s*\}\}'                                  # }}
    )
    
    PLAIN_PATTERN = re.compile(
        r'\{\{\s*'                      # {{
        r'([a-zA-Z_][a-zA-Z0-9_]*)'    # Variable name
        r'\s*\}\}'                      # }}
    )
    
    def __init__(self, template_dir: Path):
        self.template_dir = template_dir
        self.variables: Dict[str, TemplateVariable] = {}
    
    def parse_templates(self) -> Dict[str, TemplateVariable]:
        """
        Parse all template files and extract variables
        
        Returns:
            Dict mapping variable name to TemplateVariable
        """
        # Find all template files
        template_files = self._find_template_files()
        
        # Parse each file
        for file_path in template_files:
            self._parse_file(file_path)
        
        return self.variables
    
    def _find_template_files(self) -> List[Path]:
        """Find all files that could contain Jinja2 templates"""
        extensions = [
            '.gradle.kts', '.gradle', '.kt', '.kts', 
            '.properties', '.yml', '.yaml', '.xml',
            '.toml', '.json', '.md', '.txt', '.sh'
        ]
        
        files = []
        for ext in extensions:
            files.extend(self.template_dir.rglob(f'*{ext}'))
        
        # Exclude certain directories
        exclude_dirs = {'.git', 'build', 'gradle', '.gradle'}
        files = [
            f for f in files 
            if not any(ex in f.parts for ex in exclude_dirs)
        ]
        
        return files
    
    def _parse_file(self, file_path: Path):
        """Parse a single file for template variables"""
        try:
            content = file_path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, PermissionError):
            return
        
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Try enhanced pattern first
            for match in self.ENHANCED_PATTERN.finditer(line):
                sort_str, regex_pattern, help_and_default, var_name = match.groups()
                sort_order = int(sort_str) if sort_str else 999
                
                # Extract help text and default value
                help_text = help_and_default.strip()
                default_value = None
                
                if '=' in help_text:
                    parts = help_text.rsplit('=', 1)  # Split from right to handle = in help text
                    help_text = parts[0].strip()
                    default_value = parts[1].strip() if len(parts) > 1 else None
                
                self._add_variable(
                    var_name=var_name,
                    help_text=help_text,
                    sort_order=sort_order,
                    regex_pattern=regex_pattern,
                    default_value=default_value,
                    file_path=file_path,
                    line_number=line_num,
                    is_enhanced=True
                )
            
            # Then check for plain variables (only if not already found as enhanced)
            for match in self.PLAIN_PATTERN.finditer(line):
                var_name = match.group(1)
                
                # Skip if already found as enhanced in this line
                if var_name not in self.variables or not self.variables[var_name].is_enhanced:
                    self._add_variable(
                        var_name=var_name,
                        help_text="",
                        sort_order=999,
                        regex_pattern=None,
                        default_value=None,
                        file_path=file_path,
                        line_number=line_num,
                        is_enhanced=False
                    )
    
    def _add_variable(self, var_name: str, help_text: str, sort_order: int,
                     regex_pattern: Optional[str], default_value: Optional[str],
                     file_path: Path, line_number: int, is_enhanced: bool):
        """Add or update a variable"""
        if var_name in self.variables:
            var = self.variables[var_name]
            var.locations.append((file_path, line_number))
            
            # If we found an enhanced version, upgrade plain to enhanced
            if is_enhanced and not var.is_enhanced:
                var.help_text = help_text
                var.sort_order = sort_order
                var.regex_pattern = regex_pattern
                var.default_value = default_value
                var.is_enhanced = True
        else:
            self.variables[var_name] = TemplateVariable(
                name=var_name,
                help_text=help_text,
                sort_order=sort_order,
                regex_pattern=regex_pattern,
                default_value=default_value,
                locations=[(file_path, line_number)],
                is_enhanced=is_enhanced
            )
    
    def get_sorted_variables(self) -> List[TemplateVariable]:
        """Get variables sorted by sort_order, then name"""
        return sorted(
            self.variables.values(),
            key=lambda v: (v.sort_order, v.name)
        )
    
    def compile_template(self, file_path: Path) -> str:
        """
        Compile template file by removing hints
        
        Converts:
          {{ @@01|(11|17|21)|Help text=default@@variable }}
        To:
          {{ variable }}
        
        Returns:
            Compiled template content
        """
        try:
            content = file_path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, PermissionError):
            return ""
        
        # Replace enhanced patterns with plain variables
        def replace_enhanced(match):
            _, _, _, var_name = match.groups()  # sort, regex, help, varname
            return '{{ ' + var_name + ' }}'
        
        compiled = self.ENHANCED_PATTERN.sub(replace_enhanced, content)
        return compiled


class TemplateMetadata:
    """
    Parse and manage template metadata
    
    Supports two sources:
    1. TEMPLATE.md YAML frontmatter (legacy)
    2. Inline hints in template files (new)
    
    Inline hints take precedence for discovered variables.
    
    Additionally manages compiled template cache to avoid
    re-compiling templates on every render.
    """

    def __init__(self, template_path: Path, compiled_cache_dir: Optional[Path] = None):
        self.template_path = template_path
        self.compiled_cache_dir = compiled_cache_dir
        self.metadata = self._parse_metadata()
        
        # Parse inline hints from template files
        self.hint_parser = TemplateHintParser(template_path)
        self.hint_variables = self.hint_parser.parse_templates()
        
        # Initialize compiled cache if provided
        if self.compiled_cache_dir:
            self._ensure_cache_structure()
    
    def _ensure_cache_structure(self):
        """Ensure compiled cache directory exists"""
        if self.compiled_cache_dir:
            self.compiled_cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_compiled_file_path(self, source_file: Path) -> Optional[Path]:
        """
        Get path for compiled version of template file
        
        Args:
            source_file: Original template file path
        
        Returns:
            Path to compiled file in cache, or None if no cache configured
        """
        if not self.compiled_cache_dir:
            return None
        
        # Create relative path from template root
        try:
            rel_path = source_file.relative_to(self.template_path)
        except ValueError:
            # File not in template directory
            return None
        
        # Create unique cache path based on template name and file path
        template_name = self.template_path.name
        cache_file = self.compiled_cache_dir / template_name / rel_path
        
        return cache_file
    
    def _is_cache_valid(self, source_file: Path, compiled_file: Path) -> bool:
        """
        Check if compiled cache is still valid
        
        Args:
            source_file: Original template file
            compiled_file: Compiled cache file
        
        Returns:
            True if cache is valid (compiled file is newer than source)
        """
        if not compiled_file.exists():
            return False
        
        source_mtime = source_file.stat().st_mtime
        compiled_mtime = compiled_file.stat().st_mtime
        
        return compiled_mtime >= source_mtime
    
    def get_compiled_content(self, source_file: Path) -> str:
        """
        Get compiled template content (cached or freshly compiled)
        
        This method handles caching logic:
        1. Check if compiled cache exists and is valid
        2. If valid, return cached content
        3. Otherwise, compile template and cache result
        
        Args:
            source_file: Original template file path
        
        Returns:
            Compiled template content (with hints removed)
        """
        # Get cache file path
        compiled_file = self._get_compiled_file_path(source_file)
        
        # If no cache configured, compile directly
        if not compiled_file:
            return self.hint_parser.compile_template(source_file)
        
        # Check if cache is valid
        if self._is_cache_valid(source_file, compiled_file):
            # Return cached content
            try:
                return compiled_file.read_text(encoding='utf-8')
            except (OSError, UnicodeDecodeError):
                # Cache corrupted, recompile
                pass
        
        # Compile template
        compiled_content = self.hint_parser.compile_template(source_file)
        
        # Cache compiled content
        try:
            compiled_file.parent.mkdir(parents=True, exist_ok=True)
            compiled_file.write_text(compiled_content, encoding='utf-8')
        except OSError:
            # Failed to cache, but we have compiled content
            pass
        
        return compiled_content

    def _parse_metadata(self) -> Dict[str, Any]:
        """Parse YAML frontmatter from TEMPLATE.md"""
        template_md = self.template_path / "TEMPLATE.md"

        if not template_md.exists():
            return {}

        content = template_md.read_text(encoding='utf-8')

        # Parse YAML frontmatter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = parts[1].strip()

                if HAS_YAML:
                    try:
                        return yaml.safe_load(frontmatter) or {}
                    except yaml.YAMLError:
                        pass

                # Fallback: simple parsing
                return self._parse_simple_frontmatter(frontmatter)

        return {}

    def _parse_simple_frontmatter(self, frontmatter: str) -> Dict[str, Any]:
        """Simple YAML-like parser (fallback)"""
        result = {}
        for line in frontmatter.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if ':' in line:
                key, value = line.split(':', 1)
                result[key.strip()] = value.strip().strip('"\'')

        return result

    def get_arguments(self) -> List[TemplateArgument]:
        """
        Get template-specific arguments
        
        Combines:
        1. Arguments from TEMPLATE.md (legacy)
        2. Variables from inline hints (new)
        
        Inline hints take precedence.
        """
        arguments = []
        seen_names = set()
        
        # First, add variables from inline hints
        for var in self.hint_parser.get_sorted_variables():
            arguments.append(TemplateArgument(
                name=var.name,
                type='string',
                help=var.help_text if var.is_enhanced else f"Set {var.name}",
                context_key=var.name,
                default=var.default_value,  # Use default from hint
                choices=None,
                required=False
            ))
            seen_names.add(var.name)
        
        # Then add from TEMPLATE.md (if not already added)
        args_data = self.metadata.get('arguments', [])
        for arg_data in args_data:
            if not isinstance(arg_data, dict):
                continue
            
            name = arg_data.get('name', '')
            if name and name not in seen_names:
                arguments.append(TemplateArgument(
                    name=name,
                    type=arg_data.get('type', 'string'),
                    help=arg_data.get('help', ''),
                    context_key=arg_data.get('context_key', name.replace('-', '_')),
                    default=arg_data.get('default'),
                    choices=arg_data.get('choices'),
                    required=arg_data.get('required', False)
                ))

        return arguments

    def get_name(self) -> str:
        return self.metadata.get('name', self.template_path.name)

    def get_description(self) -> str:
        return self.metadata.get('description', 'No description')

    def get_version(self) -> str:
        return self.metadata.get('version', '1.0.0')

    def get_tags(self) -> List[str]:
        tags = self.metadata.get('tags', [])
        if isinstance(tags, str):
            return [t.strip() for t in tags.split(',')]
        return tags

    def get_requirements(self) -> Dict[str, str]:
        """Get template requirements"""
        return self.metadata.get('requirements', {})
    
    def get_hint_variables(self) -> Dict[str, TemplateVariable]:
        """Get variables discovered from inline hints"""
        return self.hint_variables
    
    def get_template_hints(self) -> List[TemplateVariable]:
        """
        Get list of template variables with hints
        
        Returns sorted list of TemplateVariable objects from inline hints
        """
        return self.hint_parser.get_sorted_variables()
    
    def compile_template_file(self, file_path: Path) -> str:
        """
        Compile a template file by removing inline hints
        
        Uses caching to avoid recompiling unchanged templates.
        Cache is invalidated when source file is modified.
        
        Returns compiled content ready for Jinja2
        """
        return self.get_compiled_content(file_path)


# ============================================================================
# Dynamic CLI Builder
# ============================================================================

class DynamicCLIBuilder:
    """Build CLI parser with dynamic template-specific arguments"""

    @staticmethod
    def create_base_parser() -> argparse.ArgumentParser:
        """Create parser with base arguments"""
        parser = argparse.ArgumentParser(
            description=f'Gradle Project Initializer v{SCRIPT_VERSION}',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            add_help=True
        )
        
        # Add version argument
        parser.add_argument('-v', '--version', action='version',
                          version=f'gradleInit v{SCRIPT_VERSION}')

        # Scoop integration (only show if SCOOP env is set)
        if SCOOP_DIR:
            if are_scoop_shims_installed():
                parser.add_argument('--scoop-shims-uninstall', action='store_true',
                                    help='Uninstall Scoop shims')
            else:
                parser.add_argument('--scoop-shims-install', action='store_true',
                                    help='Install Scoop shims for system-wide access')

        subparsers = parser.add_subparsers(dest='command', help='Commands')

        # INIT COMMAND
        init_parser = subparsers.add_parser('init',
                                            help='Initialize new project',
                                            add_help=False)

        init_parser.add_argument('project_name', nargs='?',
                                 help='Project name')

        # Base arguments
        base_group = init_parser.add_argument_group('Base arguments')
        base_group.add_argument('--template',
                                help='Template name')
        base_group.add_argument('--group',
                                help='Project group ID')
        base_group.add_argument('--project-version', dest='project_version',
                                help='Project version')
        base_group.add_argument('--author',
                                help='Author name')
        base_group.add_argument('--email',
                                help='Author email')
        base_group.add_argument('--license',
                                choices=['MIT', 'Apache-2.0', 'GPL-3.0', 'Proprietary'],
                                help='License')

        # Version arguments
        versions_group = init_parser.add_argument_group('Version arguments')
        versions_group.add_argument('--gradle-version',
                                    help='Gradle version (e.g. 9.2.0) or "latest"')
        versions_group.add_argument('--select-gradle-version', action='store_true',
                                    help='Interactively select Gradle version')
        versions_group.add_argument('--kotlin-version',
                                    help='Kotlin version')
        versions_group.add_argument('--jdk-version',
                                    help='JDK version')

        # Control flags
        control_group = init_parser.add_argument_group('Control flags')
        control_group.add_argument('--config', action='append',
                                   metavar='KEY=VALUE',
                                   help='Set configuration value (can be used multiple times)')
        control_group.add_argument('--interactive', '-i', action='store_true',
                                   help='Enable interactive mode for prompts')
        control_group.add_argument('--no-interactive', action='store_true',
                                   help='Disable interactive mode')
        control_group.add_argument('--dry-run', action='store_true',
                                   help='Show what would be created')
        control_group.add_argument('-h', '--help', action='store_true',
                                   help='Show help')

        # TEMPLATES COMMAND
        templates_parser = subparsers.add_parser('templates',
                                                 help='Manage templates')
        templates_parser.add_argument('--list', action='store_true',
                                      help='List templates')
        templates_parser.add_argument('--info', metavar='NAME',
                                      help='Show template info')
        templates_parser.add_argument('--update', action='store_true',
                                      help='Update repositories')
        templates_parser.add_argument('--add-repo', nargs=2,
                                      metavar=('NAME', 'URL'),
                                      help='Add custom repository')

        # CONFIG COMMAND
        config_parser = subparsers.add_parser('config',
                                              help='Manage configuration')
        config_parser.add_argument('--show', action='store_true',
                                   help='Show configuration')
        config_parser.add_argument('--init', action='store_true',
                                   help='Initialize configuration')

        return parser

    @staticmethod
    def add_template_arguments(parser: argparse.ArgumentParser,
                               template_metadata: TemplateMetadata) -> argparse.ArgumentParser:
        """Add template-specific arguments"""

        arguments = template_metadata.get_arguments()

        if not arguments:
            return parser

        # Find init subparser
        for action in parser._subparsers._actions:
            if isinstance(action, argparse._SubParsersAction):
                init_parser = action.choices.get('init')
                if init_parser:
                    break
        else:
            return parser

        # Create argument group
        template_name = template_metadata.get_name()
        group = init_parser.add_argument_group(
            f'{template_name} arguments',
            f'Template-specific options for {template_name}'
        )

        for arg in arguments:
            if not arg.name:
                continue

            arg_name = f'--{arg.name}'
            kwargs = {'help': arg.help, 'dest': arg.context_key}

            if arg.type == 'boolean':
                kwargs['action'] = 'store_true'
                # Don't set default - let ContextBuilder handle it with proper priority
            elif arg.type == 'choice':
                kwargs['choices'] = arg.choices
                # Don't set default - let ContextBuilder handle it with proper priority
                if arg.choices:
                    kwargs['metavar'] = '{' + ','.join(arg.choices) + '}'
            elif arg.type == 'string':
                kwargs['type'] = str
                # Don't set default - let ContextBuilder handle it with proper priority
            elif arg.type == 'integer':
                kwargs['type'] = int
                # Don't set default - let ContextBuilder handle it with proper priority

            if arg.required:
                kwargs['required'] = True

            try:
                group.add_argument(arg_name, **kwargs)
            except argparse.ArgumentError:
                pass

        return parser


# ============================================================================
# Template Engine - Context Builder
# ============================================================================

class ContextBuilder:
    """Build Jinja2 rendering context with priority resolution"""

    def __init__(self,
                 config: Dict[str, Any],
                 env_vars: Dict[str, str],
                 cli_args: Dict[str, Any],
                 template_metadata: TemplateMetadata):
        """
        Initialize context builder

        Args:
            config: Configuration from .gradleInit file
            env_vars: Environment variables
            cli_args: CLI arguments
            template_metadata: Template metadata
        """
        self.config = config
        self.env_vars = env_vars
        self.cli_args = cli_args
        self.template_metadata = template_metadata

    def build_context(self) -> Dict[str, Any]:
        """
        Build complete rendering context with priority resolution

        Priority: CLI Args > ENV Vars > Config Defaults

        Returns:
            Complete context dictionary for Jinja2
        """
        context = {}

        # 1. Base defaults from config
        if 'defaults' in self.config:
            context.update(self.config['defaults'])

        # 2. Custom values from config
        if 'custom' in self.config:
            context.update(self.config['custom'])

        # 3. Environment variables (GRADLE_INIT_* prefix)
        for key, value in self.env_vars.items():
            if key.startswith('GRADLE_INIT_'):
                config_key = key[12:].lower()  # Remove GRADLE_INIT_ prefix
                context[config_key] = self._parse_env_value(value)

        # 4. CLI arguments (highest priority)
        for key, value in self.cli_args.items():
            if value is not None and key not in ['help', 'func', 'command', 'config']:
                context[key] = value

        # 4a. Process --config KEY=VALUE arguments
        if 'config' in self.cli_args and self.cli_args['config']:
            for config_str in self.cli_args['config']:
                if '=' in config_str:
                    key, value = config_str.split('=', 1)
                    # Support nested keys (e.g., spring.modules)
                    if '.' in key:
                        # Convert "spring.modules" to nested dict access
                        keys = key.split('.')
                        # For simplicity, flatten to underscore
                        flat_key = '_'.join(keys)
                        context[flat_key] = self._parse_env_value(value)
                    else:
                        context[key] = self._parse_env_value(value)

        # 5. Computed values
        context['timestamp'] = datetime.now().isoformat()
        context['year'] = datetime.now().year
        context['date'] = datetime.now().strftime('%Y-%m-%d')

        # 6. Template-specific defaults
        template_args = self.template_metadata.get_arguments()
        for arg in template_args:
            if arg.context_key not in context:
                if arg.default is not None:
                    context[arg.context_key] = arg.default
                else:
                    # Variables without defaults get empty string (allows optional variables)
                    context[arg.context_key] = ""

        return context

    @staticmethod
    def _parse_env_value(value: str) -> Any:
        """
        Parse environment variable value

        Supports:
        - Boolean: true/false (case-insensitive)
        - Integer: numeric values
        - List: comma-separated values
        - String: everything else

        Args:
            value: Environment variable value

        Returns:
            Parsed value
        """
        # Boolean
        if value.lower() in ('true', 'yes', '1'):
            return True
        if value.lower() in ('false', 'no', '0'):
            return False

        # Integer
        try:
            return int(value)
        except ValueError:
            pass

        # List (comma-separated)
        if ',' in value:
            return [v.strip() for v in value.split(',')]

        # String
        return value


# ============================================================================
# Template Engine - Jinja2 Setup
# ============================================================================

def setup_jinja2_environment(template_path: Path, context: Dict[str, Any] = None) -> jinja2.Environment:
    """
    Setup Jinja2 environment with custom filters and tests

    Args:
        template_path: Path to template directory
        context: Template context for config function

    Returns:
        Configured Jinja2 environment
    """
    loader = jinja2.FileSystemLoader(str(template_path))

    env = jinja2.Environment(
        loader=loader,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
        undefined=jinja2.StrictUndefined  # Fail on undefined variables
    )

    # Custom filters for naming conventions
    env.filters['camelCase'] = lambda s: _to_camel_case(s)
    env.filters['PascalCase'] = lambda s: _to_pascal_case(s)
    env.filters['snake_case'] = lambda s: _to_snake_case(s)
    env.filters['kebab_case'] = lambda s: _to_kebab_case(s)
    env.filters['package_path'] = lambda s: s.replace('.', '/')

    # Custom filters for text manipulation
    env.filters['capitalize_first'] = lambda s: s[0].upper() + s[1:] if s else s
    env.filters['lower_first'] = lambda s: s[0].lower() + s[1:] if s else s

    # Custom datetime filters
    def format_datetime(dt_str: str, fmt: str = '%Y-%m-%d %H:%M:%S') -> str:
        """Format a datetime string or datetime object"""
        try:
            if isinstance(dt_str, str):
                # Try parsing ISO format first
                dt = datetime.fromisoformat(dt_str)
            elif isinstance(dt_str, datetime):
                dt = dt_str
            else:
                return str(dt_str)
            return dt.strftime(fmt)
        except (ValueError, AttributeError):
            return str(dt_str)
    
    env.filters['datetime'] = format_datetime
    env.filters['date'] = lambda dt, fmt='%Y-%m-%d': format_datetime(dt, fmt)
    env.filters['time'] = lambda dt, fmt='%H:%M:%S': format_datetime(dt, fmt)

    # Custom tests
    env.tests['springboot'] = lambda x: 'springboot' in str(x).lower()
    env.tests['ktor'] = lambda x: 'ktor' in str(x).lower()

    # Add utility functions as globals
    env.globals['now'] = datetime.now
    env.globals['datetime'] = datetime
    
    # Add environment access
    import os as _os
    env.globals['env'] = _os.environ.get
    env.globals['getenv'] = _os.getenv

    # Add config function as global
    if context:
        def config(key: str, default: Any = None) -> Any:
            """
            Get config value by dot-notation key with default fallback
            Example: config('custom.company', 'Unknown')
            """
            keys = key.split('.')
            value = context
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            return value

        env.globals['config'] = config

    return env


def _to_camel_case(s: str) -> str:
    """Convert string to camelCase"""
    # Handle PascalCase/camelCase by inserting delimiters before uppercase
    s_with_delimiters = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', s)
    s_with_delimiters = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s_with_delimiters)

    # Split on delimiters
    parts = re.split(r'[-_\s]+', s_with_delimiters)
    if not parts:
        return s
    return parts[0].lower() + ''.join(p.capitalize() for p in parts[1:])


def _to_pascal_case(s: str) -> str:
    """Convert string to PascalCase"""
    parts = re.split(r'[-_\s]+', s)
    return ''.join(p.capitalize() for p in parts)


def _to_snake_case(s: str) -> str:
    """Convert string to snake_case"""
    # Insert underscore before uppercase letters
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', s)
    # Insert underscore before uppercase letters preceded by lowercase
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
    # Replace spaces and hyphens with underscores
    s3 = re.sub(r'[-\s]+', '_', s2)
    return s3.lower()


def _to_kebab_case(s: str) -> str:
    """Convert string to kebab-case"""
    snake = _to_snake_case(s)
    return snake.replace('_', '-')


# ============================================================================
# Template Engine - Project Generator
# ============================================================================

class ProjectGenerator:
    """Generate project from template using Jinja2"""

    # Text file extensions that should be rendered
    TEXT_EXTENSIONS = {
        '.kt', '.kts', '.java', '.scala',  # JVM languages
        '.xml', '.json', '.toml', '.yaml', '.yml', '.properties',  # Config
        '.gradle', '.gradle.kts',  # Gradle
        '.md', '.txt', '.adoc', '.rst',  # Documentation
        '.gitignore', '.gitattributes', '.editorconfig',  # Git/Editor
        '.sh', '.bat', '.ps1',  # Scripts
        '.html', '.css', '.js', '.ts',  # Web
        '.sql',  # Database
        ''  # Files without extension (like Dockerfile)
    }

    # Files/directories to skip
    SKIP_PATTERNS = {
        'TEMPLATE.md',  # Template metadata
        '.git',  # Git directory
        '__pycache__',  # Python cache
        '.DS_Store',  # macOS
        'Thumbs.db',  # Windows
    }

    # Suffix for raw files (copied without Jinja2 processing, suffix removed)
    RAW_SUFFIX = '.raw'

    def __init__(self,
                 template_path: Path,
                 context: Dict[str, Any],
                 target_path: Path,
                 template_metadata: Optional['TemplateMetadata'] = None):
        """
        Initialize project generator

        Args:
            template_path: Path to template directory
            context: Rendering context
            target_path: Where to create the project
            template_metadata: Optional template metadata for hint compilation
        """
        self.template_path = template_path
        self.context = context
        self.target_path = target_path
        self.template_metadata = template_metadata
        self.jinja_env = setup_jinja2_environment(template_path, context)

    def generate(self) -> bool:
        """
        Generate project from template

        Returns:
            True if successful

        Raises:
            Exception: If generation fails
        """
        try:
            # 1. Validate target doesn't exist or is empty
            if self.target_path.exists():
                if any(self.target_path.iterdir()):
                    print_error(f"Target directory not empty: {self.target_path}")
                    return False
            else:
                self.target_path.mkdir(parents=True, exist_ok=True)

            # 2. Process template files
            print_info("Processing template files...")
            self._process_directory(self.template_path, self.target_path)

            # 3. Post-generation tasks
            self._run_post_generation_tasks()

            print_success("Project structure created")
            return True

        except jinja2.TemplateError as e:
            print_error(f"Template rendering error: {e}")
            raise
        except Exception as e:
            print_error(f"Project generation failed: {e}")
            raise

    def _process_directory(self, source_dir: Path, target_dir: Path):
        """
        Recursively process template directory

        Args:
            source_dir: Source template directory
            target_dir: Target project directory
        """
        for item in source_dir.iterdir():
            # Skip unwanted files/directories
            if self._should_skip(item):
                continue

            # Calculate relative path
            rel_path = item.relative_to(self.template_path)

            # Render path (for dynamic names)
            rendered_rel_path = self._render_path(str(rel_path))
            target_item = self.target_path / rendered_rel_path

            if item.is_dir():
                # Create directory
                target_item.mkdir(parents=True, exist_ok=True)
                # Process subdirectory
                self._process_directory(item, target_item)
            else:
                # Process file
                self._process_file(item, target_item)

    def _process_file(self, source_file: Path, target_file: Path):
        """
        Process single template file

        Args:
            source_file: Source template file
            target_file: Target project file
        """
        # Check if this is a raw file (bypass Jinja2, remove .raw suffix)
        is_raw = source_file.name.endswith(self.RAW_SUFFIX)
        if is_raw:
            # Remove .raw suffix from target filename
            target_file = target_file.parent / target_file.name[:-len(self.RAW_SUFFIX)]

        # Ensure parent directory exists
        target_file.parent.mkdir(parents=True, exist_ok=True)

        if is_raw:
            # Raw files: copy without Jinja2 processing
            self._copy_raw_file(source_file, target_file)
        elif self._is_text_file(source_file):
            # Text files: render with Jinja2
            self._render_text_file(source_file, target_file)
        else:
            # Binary files: copy as-is
            self._copy_binary_file(source_file, target_file)

    def _render_text_file(self, source_file: Path, target_file: Path):
        """
        Render text file with Jinja2
        
        If template_metadata is available, compiles the template first
        to remove inline hints before Jinja2 rendering.

        Args:
            source_file: Source template file
            target_file: Target project file
        """
        try:
            # Get template relative path
            rel_path = source_file.relative_to(self.template_path)

            # Compile template if metadata available (removes inline hints)
            if self.template_metadata:
                compiled_content = self.template_metadata.compile_template_file(source_file)
                # Render directly from string
                template = self.jinja_env.from_string(compiled_content)
                content = template.render(**self.context)
            else:
                # Legacy: direct template rendering
                # Convert to forward slashes for Jinja2 (cross-platform)
                template_name = str(rel_path).replace('\\', '/')
                # Load and render template
                template = self.jinja_env.get_template(template_name)
                content = template.render(**self.context)

            # Write rendered content
            target_file.write_text(content, encoding='utf-8')

            print_info(f"  [OK] {rel_path}")

        except jinja2.UndefinedError as e:
            print_error(f"Undefined variable in {source_file.name}: {e}")
            raise
        except Exception as e:
            print_error(f"Error rendering {source_file.name}: {e}")
            raise

    def _copy_binary_file(self, source_file: Path, target_file: Path):
        """
        Copy binary file as-is

        Args:
            source_file: Source file
            target_file: Target file
        """
        shutil.copy2(source_file, target_file)
        rel_path = source_file.relative_to(self.template_path)
        print_info(f"  -> {rel_path}")

    def _copy_raw_file(self, source_file: Path, target_file: Path):
        """
        Copy raw file as-is (no Jinja2 processing, .raw suffix already removed from target)

        Raw files are used for scripts that contain shell syntax conflicting
        with Jinja2 (e.g., ${VAR} in bash scripts).

        Args:
            source_file: Source file (with .raw suffix)
            target_file: Target file (without .raw suffix)
        """
        shutil.copy2(source_file, target_file)
        rel_path = source_file.relative_to(self.template_path)
        # Show target name without .raw suffix
        target_name = target_file.name
        print_info(f"  -> {rel_path} -> {target_name}")

    def _render_path(self, path: str) -> str:
        """
        Render template variables in path

        Args:
            path: Path with potential template variables

        Returns:
            Rendered path
        """
        try:
            template = self.jinja_env.from_string(path)
            return template.render(**self.context)
        except jinja2.TemplateError:
            # If rendering fails, return original path
            return path

    def _is_text_file(self, file_path: Path) -> bool:
        """
        Check if file should be treated as text (rendered)

        Args:
            file_path: File to check

        Returns:
            True if file should be rendered as text
        """
        return file_path.suffix in self.TEXT_EXTENSIONS

    def _should_skip(self, path: Path) -> bool:
        """
        Check if file/directory should be skipped

        Args:
            path: Path to check

        Returns:
            True if should be skipped
        """
        # Skip known patterns
        if path.name in self.SKIP_PATTERNS:
            return True
        # Skip .subproject files (used only for subproject command)
        if path.name.endswith('.subproject'):
            return True
        return False

    def _run_post_generation_tasks(self):
        """Run post-generation tasks (gradle wrapper, git init, etc.)"""
        print_info("Running post-generation tasks...")
        print_info("*** gradleInit.py v010 - VERBOSE MODE ***")

        # Generate Gradle Wrapper if build.gradle.kts or build.gradle exists
        gradle_build = self.target_path / 'build.gradle.kts'
        if not gradle_build.exists():
            gradle_build = self.target_path / 'build.gradle'

        if gradle_build.exists():
            self._generate_gradle_wrapper()

        # Initialize git repository
        if GIT_AVAILABLE:
            try:
                # Git init
                print_info("Executing: git init")
                print_info(f"Working directory: {self.target_path}")
                result = subprocess.run(
                    ['git', 'init'],
                    cwd=self.target_path,
                    capture_output=True,
                    text=True,
                    check=True
                )
                if result.stdout.strip():
                    print(f"  {result.stdout.strip()}")

                # Git add
                print_info("Executing: git add .")
                result = subprocess.run(
                    ['git', 'add', '.'],
                    cwd=self.target_path,
                    capture_output=True,
                    text=True,
                    check=True
                )

                # Git commit
                print_info("Executing: git commit -m 'Initial commit from gradleInit'")
                result = subprocess.run(
                    ['git', 'commit', '-m', 'Initial commit from gradleInit'],
                    cwd=self.target_path,
                    capture_output=True,
                    text=True,
                    check=True
                )
                if result.stdout.strip():
                    print(f"  {result.stdout.strip()}")

                print_success("Git repository initialized")

            except subprocess.CalledProcessError as e:
                print_warning(f"Git initialization failed")
                if e.stderr:
                    print_info("Error output:")
                    for line in e.stderr.strip().split('\n'):
                        print(f"  {line}")
        else:
            print_info("Git not available - skipping repository initialization")

    def _generate_gradle_wrapper(self):
        """
        Generate Gradle Wrapper using the reliable empty-file method.

        This method:
        1. Creates empty build.gradle.kts and settings.gradle.kts
        2. Runs 'gradle wrapper' to generate wrapper files
        3. Deletes the empty placeholder files
        4. Lets the template system generate the real files

        This avoids Constructor errors from incomplete/complex build files.
        """

        # Check if wrapper already exists
        gradlew = self.target_path / ('gradlew.bat' if IS_WINDOWS else 'gradlew')
        if gradlew.exists():
            print_info("Gradle Wrapper already exists")
            return

        build_file = self.target_path / 'build.gradle.kts'
        settings_file = self.target_path / 'settings.gradle.kts'

        # Remember if files existed before (from templates)
        build_existed = build_file.exists()
        settings_existed = settings_file.exists()

        # Save content if files existed
        build_content = build_file.read_text() if build_existed else None
        settings_content = settings_file.read_text() if settings_existed else None

        try:
            # Get Gradle version from context (fallback to default)
            gradle_version = self.context.get('gradle_version', DEFAULT_GRADLE_VERSION)

            # Step 1: Create empty placeholder files
            if not build_existed:
                build_file.touch()
            else:
                # Temporarily replace with empty file
                build_file.write_text("")

            if not settings_existed:
                settings_file.touch()
            else:
                # Temporarily replace with empty file
                settings_file.write_text("")

            # Step 1.5: Stop Gradle daemon to clear cached Kotlin DSL
            # This is CRITICAL to avoid Constructor errors from cached compilations
            try:
                print_info("Stopping Gradle daemon to clear cache...")
                if IS_WINDOWS:
                    subprocess.run('gradle --stop', shell=True, capture_output=True, timeout=10)
                else:
                    subprocess.run(['gradle', '--stop'], capture_output=True, timeout=10)
            except Exception:
                pass  # Ignore errors - daemon might not be running

            # Step 2: Generate wrapper
            cmd_list = ['gradle', 'wrapper', '--gradle-version', gradle_version]
            print_info(f"Executing: {' '.join(cmd_list)}")
            print_info(f"Working directory: {self.target_path}")

            # On Windows, use shell=True and string command to handle shims/wrappers
            if IS_WINDOWS:
                cmd = ' '.join(cmd_list)
                result = subprocess.run(
                    cmd,
                    cwd=self.target_path,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    shell=True
                )
            else:
                result = subprocess.run(
                    cmd_list,
                    cwd=self.target_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )

            print_info(f"Process exit code: {result.returncode}")

            # Show stdout if present
            if result.stdout and result.stdout.strip():
                print_info("Standard output:")
                for line in result.stdout.strip().split('\n'):
                    print(f"  {line}")

            # Show stderr if present
            if result.stderr and result.stderr.strip():
                print_info("Error output:")
                for line in result.stderr.strip().split('\n'):
                    print(f"  {line}")

            if result.returncode == 0:
                print_success(f"Gradle Wrapper {gradle_version} generated")

                # Step 3: Restore original files or delete placeholders
                if build_existed and build_content:
                    build_file.write_text(build_content)
                elif not build_existed:
                    build_file.unlink()

                if settings_existed and settings_content:
                    settings_file.write_text(settings_content)
                elif not settings_existed:
                    settings_file.unlink()
            else:
                print_warning("Gradle wrapper generation failed")
                print_info(f"You can run manually: gradle wrapper --gradle-version {gradle_version}")

                # Restore original files on failure
                if build_existed and build_content:
                    build_file.write_text(build_content)
                if settings_existed and settings_content:
                    settings_file.write_text(settings_content)

        except FileNotFoundError as e:
            print_warning(f"Gradle not found in PATH: {e}")
            print_info("  Install Gradle: https://gradle.org/install/")
            gradle_version = self.context.get('gradle_version', DEFAULT_GRADLE_VERSION)
            print_info(f"  Or run manually: gradle wrapper --gradle-version {gradle_version}")

            # Restore original files on error
            if build_existed and build_content:
                build_file.write_text(build_content)
            if settings_existed and settings_content:
                settings_file.write_text(settings_content)

        except subprocess.TimeoutExpired:
            print_warning("Gradle wrapper generation timed out (60s)")
            gradle_version = self.context.get('gradle_version', DEFAULT_GRADLE_VERSION)
            print_info(f"  You can run manually: gradle wrapper --gradle-version {gradle_version}")

            # Restore original files on error
            if build_existed and build_content:
                build_file.write_text(build_content)
            if settings_existed and settings_content:
                settings_file.write_text(settings_content)

        except Exception as e:
            print_warning(f"Unexpected error: {e}")
            import traceback
            traceback.print_exc()

            # Restore original files on error
            if build_existed and build_content:
                build_file.write_text(build_content)
            if settings_existed and settings_content:
                settings_file.write_text(settings_content)


# ============================================================================
# Helper Function - Load Configuration
# ============================================================================

def load_config(config_file: Path) -> Dict[str, Any]:
    """
    Load configuration from .gradleInit file

    Args:
        config_file: Path to config file

    Returns:
        Configuration dictionary
    """
    if not config_file.exists():
        return {}

    try:
        config_text = config_file.read_text()
        return toml.loads(config_text)
    except Exception as e:
        print_warning(f"Failed to load config: {e}")
        return {}


# ============================================================================
# Command Handlers
# ============================================================================

def handle_templates_command(args: argparse.Namespace,
                             repo_manager: TemplateRepositoryManager) -> int:
    """Handle templates command"""

    if args.list:
        print_header("Available Templates")

        templates = repo_manager.list_all_templates()

        if not templates:
            print("No templates found.")
            print()
            print_info("To install templates:")
            print()
            print("  Option 1 - From Git (enables updates):")
            print("    gradleInit templates --update")
            print()
            print("  Option 2 - From archive (manual):")
            print("    tar -xjf gradleInitTemplates_v004.tar.bz2")
            print("    cp -r gradleInitTemplates/* ~/.gradleInit/templates/official/")
            print()
            return 0

        # Group by repository
        by_repo = {}
        for tmpl in templates:
            repo = tmpl['repository']
            if repo not in by_repo:
                by_repo[repo] = []
            by_repo[repo].append(tmpl)

        for repo_name in sorted(by_repo.keys()):
            print(f"\n{repo_name}:")
            for tmpl in by_repo[repo_name]:
                template_path = Path(tmpl['path'])
                metadata = TemplateMetadata(template_path)

                print(f"  {tmpl['name']:35} {metadata.get_description()}")

                tags = metadata.get_tags()
                if tags:
                    print(f"  {'':35} [{', '.join(tags)}]")

        print()
        return 0

    if args.update:
        print_header("Updating Template Repositories")

        # Check if official templates exist before trying to update
        official_exists = repo_manager.repositories['official'].path.exists()

        if not repo_manager.ensure_official_templates():
            print_error("Failed to clone official templates")
            return 1

        # Only run update if templates existed before (not just cloned)
        if official_exists:
            results = repo_manager.update_all()

            print()
            for repo_name, success in results.items():
                if success:
                    print_success(f"{repo_name} updated")
                else:
                    print_error(f"{repo_name} update failed")
        else:
            print()
            print_success("official templates cloned successfully")

        return 0

    if args.info:
        template_path = repo_manager.find_template(args.info)

        if not template_path:
            print_error(f"Template not found: {args.info}")
            return 1

        metadata = TemplateMetadata(template_path)

        print_header(f"Template: {metadata.get_name()}")
        print(f"Description: {metadata.get_description()}")
        print(f"Version: {metadata.get_version()}")
        print(f"Path: {template_path}")

        tags = metadata.get_tags()
        if tags:
            print(f"Tags: {', '.join(tags)}")

        arguments = metadata.get_arguments()
        if arguments:
            print("\nTemplate-specific arguments:")
            for arg in arguments:
                arg_str = f"  --{arg.name}"
                if arg.type == 'choice':
                    arg_str += f" {{{','.join(arg.choices)}}}"
                elif arg.type != 'boolean':
                    arg_str += f" <{arg.type.upper()}>"

                print(arg_str)
                print(f"      {arg.help}")
                if arg.default is not None:
                    print(f"      (default: {arg.default})")
                print()

        return 0

    if args.add_repo:
        name, url = args.add_repo
        success = repo_manager.add_custom_repository(name, url)
        return 0 if success else 1

    # No args - show help
    print_header("Templates Command")
    print("Manage project templates")
    print()
    print("Usage:")
    print("  gradleInit templates --list          List available templates")
    print("  gradleInit templates --update        Update/clone templates from Git")
    print("  gradleInit templates --info NAME     Show template details")
    print()
    print("Examples:")
    print("  gradleInit templates --list")
    print("  gradleInit templates --update")
    print("  gradleInit templates --info kotlin-single")
    print()
    return 0


def handle_config_command(args: argparse.Namespace, paths: GradleInitPaths) -> int:
    """Handle config command"""

    if args.init:
        paths.ensure_structure()
        print_success(f"Configuration initialized: {paths.base_dir}")
        print_info(f"Config file: {paths.config_file}")
        return 0

    if args.show:
        if not paths.config_file.exists():
            print_error("Configuration file not found")
            print_info("Run: gradleInit.py config --init")
            return 1

        print_header("Configuration")
        print(f"Directory: {paths.base_dir}")
        print(f"Config file: {paths.config_file}")
        print()

        config = toml.loads(paths.config_file.read_text())
        print(toml.dumps(config))

        return 0

    # No args - show help
    print_header("Config Command")
    print("Manage gradleInit configuration")
    print()
    print("Usage:")
    print("  gradleInit config --show      Show current configuration")
    print("  gradleInit config --init      Initialize configuration")
    print()
    print("Configuration file: ~/.gradleInit/config")
    print()
    return 0


# ============================================================================
# Config & Validation Helpers
# ============================================================================

def get_config_default(config: Dict[str, Any], key: str, fallback: Any = None) -> Any:
    """
    Get default value from config with fallback
    
    Checks in order:
    1. config['defaults'][key]
    2. config['custom'][key]
    3. fallback value
    
    Args:
        config: Loaded configuration dictionary
        key: Configuration key to look up
        fallback: Fallback value if not found
        
    Returns:
        Configuration value or fallback
    """
    # Check defaults section
    if 'defaults' in config and key in config['defaults']:
        return config['defaults'][key]
    
    # Check custom section
    if 'custom' in config and key in config['custom']:
        return config['custom'][key]
    
    # Return fallback
    return fallback


def validate_value_against_hint(value: str, hint: 'TemplateVariable') -> Tuple[bool, Optional[str]]:
    """
    Validate a value against a template hint's regex pattern
    
    Args:
        value: Value to validate
        hint: TemplateVariable with regex_pattern
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not hint.regex_pattern:
        return True, None
    
    try:
        if not re.match(f"^{hint.regex_pattern}$", str(value)):
            error_msg = f"Value '{value}' does not match pattern: {hint.regex_pattern}"
            if hint.help_text:
                error_msg += f"\n  Help: {hint.help_text}"
            return False, error_msg
    except re.error as e:
        # Invalid regex pattern in template
        print_warning(f"Invalid regex pattern in template: {e}")
        return True, None
    
    return True, None


def prompt_with_validation(prompt_text: str, 
                          default: Any, 
                          hint: Optional['TemplateVariable'] = None,
                          allow_empty: bool = True,
                          source: str = None) -> str:
    """
    Prompt user for input with validation and re-prompting on error
    
    Args:
        prompt_text: Text to display to user
        default: Default value if user enters nothing
        hint: Optional TemplateVariable for validation
        allow_empty: Allow empty input (uses default)
        source: Optional source description for default value (e.g., "from config")
        
    Returns:
        Validated user input or default
    """
    while True:
        # Show prompt with default
        if default is not None:
            full_prompt = f"{prompt_text} [{default}]: "
        else:
            full_prompt = f"{prompt_text}: "
        
        user_input = input(full_prompt).strip()
        
        # Handle empty input
        if not user_input:
            if allow_empty and default is not None:
                return str(default)
            elif not allow_empty:
                print_error("Value required")
                continue
            else:
                return user_input
        
        # Validate against hint if provided
        if hint:
            is_valid, error_msg = validate_value_against_hint(user_input, hint)
            if not is_valid:
                print_error(error_msg)
                if hint.default_value:
                    print_info(f"Press Enter to use default: {hint.default_value}")
                continue
        
        return user_input


def validate_cli_args_against_template(args: Dict[str, Any], 
                                       hints: List['TemplateVariable']) -> Tuple[bool, List[str]]:
    """
    Validate CLI arguments against template hints
    
    Args:
        args: Dictionary of CLI arguments
        hints: List of TemplateVariable hints from template
        
    Returns:
        Tuple of (all_valid, list_of_errors)
    """
    errors = []
    
    for hint in hints:
        # Get value from args using name
        value = args.get(hint.name)
        
        if value is None:
            continue
        
        # Validate against regex
        is_valid, error_msg = validate_value_against_hint(value, hint)
        if not is_valid:
            errors.append(f"Argument '--{hint.name}': {error_msg}")
    
    return len(errors) == 0, errors


def handle_init_command(args: argparse.Namespace,
                        paths: GradleInitPaths,
                        repo_manager: TemplateRepositoryManager) -> int:
    """Handle init command - Create project from template"""

    # Validate required arguments
    if not args.project_name:
        if args.interactive:
            # Interactive mode - prompt for project name
            args.project_name = input("Project name: ").strip()
            if not args.project_name:
                print_error("Project name required")
                return 1
        else:
            # Show helpful usage information instead of just error
            print_header("Init Command")
            print()
            print("Initialize a new Gradle/Kotlin project from template")
            print()
            print("Usage:")
            print("  gradleInit init PROJECT_NAME --template TEMPLATE [OPTIONS]")
            print()
            print("Required:")
            print("  PROJECT_NAME              Name of the project to create")
            print("  --template TEMPLATE       Template to use (kotlin-single, kotlin-multi, etc.)")
            print()
            print("Options:")
            print("  --group GROUP             Group ID (default: com.example)")
            print("  --project-version VER     Project version (default: 1.0.0)")
            print("  --gradle-version VER      Gradle version to use")
            print("  --kotlin-version VER      Kotlin version to use")
            print("  --jdk-version VER         JDK version (11, 17, 21)")
            print("  --interactive             Interactive mode with prompts")
            print("  --no-interactive          Non-interactive mode (default)")
            print()
            print("Examples:")
            print("  gradleInit init myApp --template kotlin-single")
            print("  gradleInit init myApp --template kotlin-single --group com.example")
            print("  gradleInit init myApp --template springboot --gradle-version 8.11")
            print("  gradleInit init myApp --interactive")
            print()
            print("List available templates:")
            print("  gradleInit templates --list")
            return 1

    if not args.template:
        if args.interactive:
            # Show available templates
            templates = repo_manager.list_all_templates()
            if not templates:
                print_error("No templates available")
                print_info("Run: gradleInit.py templates --update")
                return 1

            print_info("Available templates:")
            for i, tmpl in enumerate(templates, 1):
                metadata = TemplateMetadata(Path(tmpl['path']))
                print(f"  {i}. {tmpl['name']:20} - {metadata.get_description()}")

            print()
            choice = input(f"Select template (1-{len(templates)}): ").strip()
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(templates):
                    args.template = templates[idx]['name']
                else:
                    print_error("Invalid selection")
                    return 1
            except ValueError:
                # Try as template name
                args.template = choice
        else:
            # Show helpful message for missing template
            print_header("Init Command")
            print()
            print("Template required")
            print()
            print("Usage:")
            print("  gradleInit init PROJECT_NAME --template TEMPLATE")
            print()
            print("Examples:")
            print("  gradleInit init myApp --template kotlin-single")
            print("  gradleInit init myApp --template springboot")
            print()
            print("List available templates:")
            print("  gradleInit templates --list")
            print()
            print("Or use interactive mode:")
            print("  gradleInit init myApp --interactive")
            return 1

    # Load config BEFORE interactive prompts so we can use config defaults
    config = load_config(paths.config_file)
    
    # Find and load template early if provided (needed for template-aware help and validation)
    template_path = None
    metadata = None
    if args.template:
        template_path = repo_manager.find_template(args.template)
        if template_path:
            metadata = TemplateMetadata(template_path, paths.compiled_templates)
    
    # Template-aware help
    if args.help:
        print_header("Init Command Help")
        print("Create a new project from a template")
        print()
        print("Usage:")
        print("  gradleInit.py init PROJECT_NAME --template TEMPLATE [OPTIONS]")
        print()
        print("Required Arguments:")
        print("  PROJECT_NAME              Name of the project to create")
        print("  --template TEMPLATE       Template to use (name or URL)")
        print()
        print("Optional Arguments:")
        print("  --group GROUP             Maven group ID (e.g., com.example)")
        print("  --project-version VERSION Project version (e.g., 0.1.0)")
        print("  --config KEY=VALUE        Set template configuration")
        print()
        
        # Show template-specific variables if template is loaded
        if metadata:
            hints = metadata.get_template_hints()
            if hints:
                print("Template Variables:")
                for hint in sorted(hints, key=lambda h: h.sort_order):
                    # All variables are optional (required attribute not defined)
                    optional = " (optional)" if hint.default_value else ""
                    print(f"  --{hint.name:20} {hint.help_text}{optional}")
                    if hint.regex_pattern:
                        print(f"                           Pattern: {hint.regex_pattern}")
                    if hint.default_value:
                        print(f"                           Default: {hint.default_value}")
                print()
            
            # Show config options from TEMPLATE.md arguments
            template_args = metadata.get_arguments()
            config_args = [arg for arg in template_args if arg.type == 'boolean' or 
                          (arg.name not in ['group', 'version'] and arg.context_key not in ['group', 'version'])]
            if config_args:
                print("Config Options (--config KEY=VALUE):")
                for arg in config_args:
                    default_str = f" (default: {arg.default})" if arg.default is not None else ""
                    type_str = f"[{arg.type}]" if arg.type else ""
                    print(f"  {arg.name:24} {arg.help}{default_str} {type_str}")
                print()
        
        print("Examples:")
        print("  # Simple project")
        print("  gradleInit.py init my-app --template kotlin-single")
        print()
        print("  # With custom group")
        print("  gradleInit.py init my-app --template kotlin-single --group com.mycompany")
        print()
        print("  # Spring Boot with config")
        print("  gradleInit.py init my-api --template springboot \\")
        print("    --config spring.modules=web,data-jpa \\")
        print("    --config database.driver=postgresql")
        print()
        return 0

    # Interactive mode - prompt for missing values with config-aware defaults
    if args.interactive:
        # Get hints for validation if template is loaded
        hints_map = {}
        if metadata:
            for hint in metadata.get_template_hints():
                hints_map[hint.name] = hint
        
        # Prompt for group with config default
        if not args.group:
            default_group = get_config_default(config, 'group', 'com.example')
            hint = hints_map.get('group')
            source = "from config" if ('defaults' in config and 'group' in config['defaults']) else "fallback"
            args.group = prompt_with_validation("Group ID", default_group, hint, source=source)

        # Prompt for version with config default
        if not args.project_version:
            default_version = get_config_default(config, 'version', '0.1.0')
            hint = hints_map.get('version')
            source = "from config" if ('defaults' in config and 'version' in config['defaults']) else "fallback"
            args.project_version = prompt_with_validation("Version", default_version, hint, source=source)

        # Prompt for gradle_version if not set
        if not args.gradle_version:
            print()
            print_info(f"Gradle version selection:")
            print(f"  1. Use default ({DEFAULT_GRADLE_VERSION})")
            print(f"  2. Select from list")
            print(f"  3. Enter version manually")
            choice = input("Choice [1]: ").strip() or "1"

            if choice == "2":
                args.gradle_version = select_gradle_version_interactive()
            elif choice == "3":
                default_gradle = get_config_default(config, 'gradle_version', DEFAULT_GRADLE_VERSION)
                args.gradle_version = input(f"Gradle version [{default_gradle}]: ").strip() or default_gradle
            # else: use default (will be set later)
        
        # Prompt for any other template-specific variables with hints
        if metadata:
            for hint in sorted(hints_map.values(), key=lambda h: h.sort_order):
                # Skip already handled variables
                if hint.name in ['group', 'version', 'project_name', 'gradle_version', 'kotlin_version']:
                    continue
                
                # Check if CLI arg exists for this hint
                cli_value = getattr(args, hint.name, None)
                if cli_value is None:
                    # Get default from config or hint
                    default_value = get_config_default(config, hint.name, hint.default_value)
                    # Prompt for value (all variables are optional, allow empty input)
                    prompted_value = prompt_with_validation(
                        hint.help_text or hint.name,
                        default_value,
                        hint,
                        allow_empty=True  # All variables are optional
                    )
                    setattr(args, hint.name, prompted_value if prompted_value else default_value)

    # Find template if not already loaded
    if not template_path:
        template_path = repo_manager.find_template(args.template)

    if not template_path:
        print_error(f"Template not found: {args.template}")
        print_info("Run: gradleInit.py templates --list")
        return 1

    # Load template metadata if not already loaded
    if not metadata:
        metadata = TemplateMetadata(template_path, paths.compiled_templates)
    
    # CLI Validation - validate all CLI args against template hints
    if not args.interactive:
        # Only validate in non-interactive mode (interactive mode validates during prompts)
        hints = metadata.get_template_hints()
        if hints:
            cli_args_dict = vars(args)
            is_valid, errors = validate_cli_args_against_template(cli_args_dict, hints)
            if not is_valid:
                print_error("Validation errors:")
                for error in errors:
                    print(f"  - {error}")
                print()
                print_info("Run with --help to see valid values")
                return 1

    # Display project info
    print_header(f"Creating Project: {args.project_name}")
    print_info(f"Template: {args.template}")
    print_info(f"Template path: {template_path}")
    print()

    try:
        # Validate requirements
        requirements = metadata.get_requirements()
        if requirements:
            print_info("Template requirements:")
            for req_name, req_version in requirements.items():
                print(f"  * {req_name}: {req_version}")
            print()

        # Handle Gradle version selection
        gradle_version = None

        if args.select_gradle_version:
            # Interactive selection
            gradle_version = select_gradle_version_interactive()
        elif args.gradle_version:
            # Explicitly specified
            if args.gradle_version.lower() == 'latest':
                print_info("Fetching latest Gradle version...")
                gradle_version = get_latest_gradle_version()
                if not gradle_version:
                    print_warning("Could not fetch latest version")
                    gradle_version = get_config_default(config, 'gradle_version', DEFAULT_GRADLE_VERSION)
                print_success(f"Latest Gradle version: {gradle_version}")
            else:
                gradle_version = args.gradle_version
        else:
            # Use config default or hardcoded default
            gradle_version = get_config_default(config, 'gradle_version', DEFAULT_GRADLE_VERSION)

        # Override CLI args with selected version
        args.gradle_version = gradle_version
        print_info(f"Using Gradle version: {gradle_version}")
        print()

        # Build rendering context
        # Config already loaded earlier
        
        # Prepare CLI args dict and map project_version to version
        cli_args_dict = vars(args)
        
        # Map project_version to version, but ONLY if explicitly set
        if 'project_version' in cli_args_dict and cli_args_dict['project_version'] is not None:
            cli_args_dict['version'] = cli_args_dict['project_version']
        elif 'version' in cli_args_dict:
            # Remove version if it exists but project_version wasn't set
            # This allows config defaults to be used
            del cli_args_dict['version']
        
        context_builder = ContextBuilder(
            config=config,
            env_vars=dict(os.environ),
            cli_args=cli_args_dict,
            template_metadata=metadata
        )
        context = context_builder.build_context()

        # Show context summary
        print_info("Context values:")
        important_keys = ['project_name', 'group', 'version', 'kotlin_version', 'gradle_version']
        for key in important_keys:
            if key in context:
                print(f"  * {key}: {context[key]}")
        print()

        # Generate project
        target_path = Path.cwd() / args.project_name
        generator = ProjectGenerator(
            template_path=template_path,
            context=context,
            target_path=target_path,
            template_metadata=metadata  # Pass metadata for hint compilation
        )

        # Execute generation
        success = generator.generate()

        if success:
            print()
            print_success(f"Project created successfully: {target_path}")
            print()
            print_info("Next steps:")
            print(f"  cd {args.project_name}")
            print("  ./gradlew build")
            print()

            # GitHub push instructions
            print_header("Push to GitHub")
            print()
            print("Your project is ready to push to GitHub!")
            print()
            print("Option 1: Create new repository on GitHub")
            print("  1. Go to https://github.com/new")
            print(f"  2. Repository name: {args.project_name}")
            print("  3. DO NOT initialize with README, .gitignore, or license")
            print("  4. Click 'Create repository'")
            print("  5. Then run:")
            print()
            print(f"     cd {args.project_name}")
            print()
            print("     # Using HTTPS (easier, requires username/password or token)")
            print(f"     git remote add origin https://github.com/YOUR_USERNAME/{args.project_name}.git")
            print("     git branch -M main")
            print("     git push -u origin main")
            print()
            print("     # OR using SSH (recommended, requires SSH key setup)")
            print(f"     git remote add origin git@github.com:YOUR_USERNAME/{args.project_name}.git")
            print("     git branch -M main")
            print("     git push -u origin main")
            print()
            print("Option 2: Using GitHub CLI (recommended)")
            print(f"  cd {args.project_name}")
            print(f"  gh repo create {args.project_name} --public --source=. --push")
            print()
            print("Option 3: Push to existing repository")
            print(f"  cd {args.project_name}")
            print("  # HTTPS:")
            print("  git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git")
            print("  # OR SSH:")
            print("  git remote add origin git@github.com:YOUR_USERNAME/YOUR_REPO.git")
            print("  git branch -M main")
            print("  git push -u origin main")
            print()
            print("[TIP] SSH Setup: https://docs.github.com/en/authentication/connecting-to-github-with-ssh")
            print()
            print("[INFO] Verify committed files:")
            print("  git status        # Should be clean")
            print("  git log --oneline # Should show initial commit")
            print("  git ls-files      # Show all tracked files")
            print()
            return 0
        else:
            return 1

    except jinja2.UndefinedError as e:
        print()
        print_error(f"Template variable error: {e}")
        print_info("Check your template configuration or provide missing values via --config")
        return 1

    except Exception as e:
        print()
        print_error(f"Failed to create project: {e}")
        import traceback
        traceback.print_exc()
        return 1


# ============================================================================
# CLI Entry Point
# ============================================================================

def main():
    """Main entry point"""
    
    # If --version is requested, let argparse handle it (avoids double output)
    if '--version' in sys.argv or '-v' in sys.argv:
        # Argparse will handle version display and exit
        pass
    else:
        print(f"gradleInit v{SCRIPT_VERSION}")
        print()

    # Check git availability
    if not GIT_AVAILABLE:
        print_warning("Git not found!")
        print()
        print("gradleInit requires git for:")
        print("  * Template repository management")
        print("  * Template updates")
        print("  * Custom template repositories")
        print()
        print("Please install git:")
        print()
        print("  macOS:    brew install git")
        print("  Ubuntu:   sudo apt-get install git")
        print("  Windows:  https://git-scm.com/download/win")
        print()
        return 1

    # Initialize paths
    paths = GradleInitPaths()
    paths.ensure_structure()

    # Initialize module loader
    module_loader = ModuleLoader(paths)

    # Initialize repository manager
    repo_manager = TemplateRepositoryManager(paths)

    # Phase 1: Parse to get basic args and check for module commands
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    parser.add_argument('--download-modules', action='store_true')
    parser.add_argument('--update-modules', action='store_true')
    parser.add_argument('--modules-info', action='store_true')
    parser.add_argument('--scoop-shims-install', action='store_true')
    parser.add_argument('--scoop-shims-uninstall', action='store_true')
    parser.add_argument('--no-interactive', action='store_true')
    parser.add_argument('command', nargs='?')
    parser.add_argument('--template')

    phase1_args, remaining = parser.parse_known_args()

    # Handle Scoop shims commands first
    if phase1_args.scoop_shims_install:
        success = install_scoop_shims()
        return 0 if success else 1

    if phase1_args.scoop_shims_uninstall:
        success = uninstall_scoop_shims()
        return 0 if success else 1

    # Handle module commands first
    if phase1_args.download_modules:
        success = module_loader.ensure_modules(auto_download=True)
        return 0 if success else 1

    if phase1_args.update_modules:
        success = module_loader.update_modules()
        return 0 if success else 1

    if phase1_args.modules_info:
        info = module_loader.get_modules_info()

        print_header("Modules Information")
        print(f"Installed: {info.get('installed', False)}")

        if info.get('installed'):
            print(f"Path: {info.get('path')}")
            print(f"Version: {info.get('version', 'unknown')}")
            print(f"Commit: {info.get('commit', 'unknown')}")
            print()
            print("Available features:")
            print(f"  Maven Central: {info.get('maven_central', False)}")
            print(f"  Spring Boot BOM: {info.get('spring_boot', False)}")
            print(f"  Update Manager: {info.get('updater', False)}")
        else:
            print()
            print("Modules not installed")
            print("Run: gradleInit.py --download-modules")

        return 0

    # Load modules (auto-download on demand for init command, but not in non-interactive mode)
    if phase1_args.command == 'init':
        auto_download = not phase1_args.no_interactive
        module_loader.ensure_modules(auto_download=auto_download)

    # Phase 2: Create full parser
    full_parser = DynamicCLIBuilder.create_base_parser()

    # Add module management arguments to main parser
    full_parser.add_argument('--download-modules', action='store_true',
                             help='Download optional modules')
    full_parser.add_argument('--update-modules', action='store_true',
                             help='Update modules')
    full_parser.add_argument('--modules-info', action='store_true',
                             help='Show modules info')

    # If init command with template, add template-specific arguments
    if phase1_args.command == 'init' and phase1_args.template:
        template_path = repo_manager.find_template(phase1_args.template)
        if template_path:
            metadata = TemplateMetadata(template_path)
            full_parser = DynamicCLIBuilder.add_template_arguments(full_parser, metadata)

    # Parse all arguments
    args = full_parser.parse_args()

    # Route to command handlers
    if not args.command:
        full_parser.print_help()
        return 1

    if args.command == 'templates':
        return handle_templates_command(args, repo_manager)

    elif args.command == 'config':
        return handle_config_command(args, paths)

    elif args.command == 'init':
        return handle_init_command(args, paths, repo_manager)

    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[ERROR] Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)