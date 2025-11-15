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

SCRIPT_VERSION = "1.3.0"
MODULES_REPO = "https://github.com/stotz/gradleInitModules.git"
TEMPLATES_REPO = "https://github.com/stotz/gradleInitTemplates.git"
MODULES_VERSION = "v1.3.0"  # Or "main" for latest


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
            print(f"  • {pkg}")
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
    print(f"✓ {message}")


def print_error(message: str):
    """Print error message"""
    print(f"✗ {message}", file=sys.stderr)


def print_info(message: str):
    """Print info message"""
    print(f"→ {message}")


def print_warning(message: str):
    """Print warning message"""
    print(f"⚠ {message}")


# ============================================================================
# Configuration Paths
# ============================================================================

class GradleInitPaths:
    """Manage ~/.gradleInit/ directory structure"""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or (Path.home() / '.gradleInit')

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

    def ensure_structure(self):
        """Create directory structure if it doesn't exist"""
        self.base_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)
        self.official_templates.mkdir(exist_ok=True)  # Create official templates dir
        self.cache_dir.mkdir(exist_ok=True)
        self.remote_cache.mkdir(exist_ok=True)
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
        print("┌─────────────────────────────────────────────────┐")
        print("│ Optional Advanced Features Available            │")
        print("├─────────────────────────────────────────────────┤")
        print("│ • Maven Central integration                     │")
        print("│ • Spring Boot BOM support                       │")
        print("│ • Advanced dependency updates                   │")
        print("│                                                 │")
        print("│ Size: ~50 KB (one-time download)                │")
        print("└─────────────────────────────────────────────────┘")
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
        print("┌──────────────────────────────────────────┐")
        print("│ Maven Central Integration Not Available │")
        print("├──────────────────────────────────────────┤")
        print("│ To enable:                               │")
        print("│   gradleInit.py --download-modules       │")
        print("└──────────────────────────────────────────┘")
        print()


class SpringBootBOMStub:
    """Stub when Spring Boot BOM module not available"""

    def __init__(self):
        self._show_message()

    def _show_message(self):
        print()
        print("┌──────────────────────────────────────────┐")
        print("│ Spring Boot BOM Support Not Available   │")
        print("├──────────────────────────────────────────┤")
        print("│ To enable:                               │")
        print("│   gradleInit.py --download-modules       │")
        print("└──────────────────────────────────────────┘")
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
        """Clone repository if not exists"""
        if self.path.exists():
            return True

        if not self.url:
            return False

        print_info(f"Cloning {self.name} templates from {self.url}...")

        try:
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

    def update(self) -> bool:
        """Update repository via git pull"""
        if not self.is_git:
            print_error(f"{self.name} is not a git repository")
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

            # Pull updates
            subprocess.run(
                ['git', '-C', str(self.path), 'pull'],
                check=True,
                capture_output=True,
                text=True
            )

            print_success(f"Updated {self.name} templates ({behind_count} new commits)")
            return True

        except subprocess.CalledProcessError as e:
            print_error(f"Failed to update: {e.stderr}")
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
        if not official.path.exists():
            return official.clone()
        return True

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

    def find_template(self, template_name: str) -> Optional[Path]:
        """Find template by name across all repositories"""
        # Try official first
        if 'official' in self.repositories:
            path = self.repositories['official'].get_template_path(template_name)
            if path:
                return path

        # Try custom repositories
        for repo in self.repositories.values():
            path = repo.get_template_path(template_name)
            if path:
                return path

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


class TemplateMetadata:
    """Parse and manage template metadata from TEMPLATE.md"""

    def __init__(self, template_path: Path):
        self.template_path = template_path
        self.metadata = self._parse_metadata()

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
        """Get template-specific arguments"""
        args_data = self.metadata.get('arguments', [])

        if not args_data:
            return []

        arguments = []
        for arg_data in args_data:
            if not isinstance(arg_data, dict):
                continue

            arguments.append(TemplateArgument(
                name=arg_data.get('name', ''),
                type=arg_data.get('type', 'string'),
                help=arg_data.get('help', ''),
                context_key=arg_data.get('context_key', arg_data.get('name', '').replace('-', '_')),
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

        parser.add_argument('--version', action='version',
                            version=f'gradleInit {SCRIPT_VERSION}')

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
        base_group.add_argument('--version', dest='project_version',
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
                                    help='Gradle version')
        versions_group.add_argument('--kotlin-version',
                                    help='Kotlin version')
        versions_group.add_argument('--jdk-version',
                                    help='JDK version')

        # Control flags
        control_group = init_parser.add_argument_group('Control flags')
        control_group.add_argument('--config', action='append',
                                   metavar='KEY=VALUE',
                                   help='Set configuration value (can be used multiple times)')
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
                if arg.default:
                    kwargs['default'] = arg.default
            elif arg.type == 'choice':
                kwargs['choices'] = arg.choices
                kwargs['default'] = arg.default
                if arg.choices:
                    kwargs['metavar'] = '{' + ','.join(arg.choices) + '}'
            elif arg.type == 'string':
                kwargs['type'] = str
                kwargs['default'] = arg.default
            elif arg.type == 'integer':
                kwargs['type'] = int
                kwargs['default'] = arg.default

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
            if arg.context_key not in context and arg.default is not None:
                context[arg.context_key] = arg.default

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

def setup_jinja2_environment(template_path: Path) -> jinja2.Environment:
    """
    Setup Jinja2 environment with custom filters and tests

    Args:
        template_path: Path to template directory

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

    # Custom tests
    env.tests['springboot'] = lambda x: 'springboot' in str(x).lower()
    env.tests['ktor'] = lambda x: 'ktor' in str(x).lower()

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

    def __init__(self,
                 template_path: Path,
                 context: Dict[str, Any],
                 target_path: Path):
        """
        Initialize project generator

        Args:
            template_path: Path to template directory
            context: Rendering context
            target_path: Where to create the project
        """
        self.template_path = template_path
        self.context = context
        self.target_path = target_path
        self.jinja_env = setup_jinja2_environment(template_path)

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
        # Ensure parent directory exists
        target_file.parent.mkdir(parents=True, exist_ok=True)

        # Check if file should be rendered as text
        if self._is_text_file(source_file):
            self._render_text_file(source_file, target_file)
        else:
            self._copy_binary_file(source_file, target_file)

    def _render_text_file(self, source_file: Path, target_file: Path):
        """
        Render text file with Jinja2

        Args:
            source_file: Source template file
            target_file: Target project file
        """
        try:
            # Get template relative path
            rel_path = source_file.relative_to(self.template_path)

            # Convert to forward slashes for Jinja2 (cross-platform)
            template_name = str(rel_path).replace('\\', '/')

            # Load and render template
            template = self.jinja_env.get_template(template_name)
            content = template.render(**self.context)

            # Write rendered content
            target_file.write_text(content, encoding='utf-8')

            print_info(f"  ✓ {rel_path}")

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
        print_info(f"  → {rel_path}")

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
        return path.name in self.SKIP_PATTERNS

    def _run_post_generation_tasks(self):
        """Run post-generation tasks (git init, etc.)"""
        print_info("Running post-generation tasks...")

        # Initialize git repository
        if GIT_AVAILABLE:
            try:
                # Git init
                result = subprocess.run(
                    ['git', 'init'],
                    cwd=self.target_path,
                    capture_output=True,
                    text=True,
                    check=True
                )

                # Git add
                subprocess.run(
                    ['git', 'add', '.'],
                    cwd=self.target_path,
                    capture_output=True,
                    text=True,
                    check=True
                )

                # Git commit
                subprocess.run(
                    ['git', 'commit', '-m', 'Initial commit from gradleInit'],
                    cwd=self.target_path,
                    capture_output=True,
                    text=True,
                    check=True
                )

                print_success("Git repository initialized")

            except subprocess.CalledProcessError as e:
                print_warning(f"Git initialization failed: {e.stderr}")
        else:
            print_info("Git not available - skipping repository initialization")


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
        return toml.loads(config_file.read_text())
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
            print("Run: gradleInit.py templates --update")
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

        if not repo_manager.ensure_official_templates():
            print_error("Failed to clone official templates")
            return 1

        results = repo_manager.update_all()

        print()
        for repo_name, success in results.items():
            if success:
                print_success(f"{repo_name} updated")
            else:
                print_error(f"{repo_name} update failed")

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

    return 0


def handle_init_command(args: argparse.Namespace,
                        paths: GradleInitPaths,
                        repo_manager: TemplateRepositoryManager) -> int:
    """Handle init command - Create project from template"""

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
        print("  --version VERSION         Project version (e.g., 0.1.0)")
        print("  --config KEY=VALUE        Set template configuration")
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

    # Validate required arguments
    if not args.project_name:
        print_error("Project name required")
        print_info("Usage: gradleInit.py init PROJECT_NAME --template TEMPLATE")
        return 1

    if not args.template:
        print_error("Template required. Use --template <n>")
        print_info("Run: gradleInit.py templates --list")
        return 1

    # Find template
    template_path = repo_manager.find_template(args.template)

    if not template_path:
        print_error(f"Template not found: {args.template}")
        print_info("Run: gradleInit.py templates --list")
        return 1

    # Display project info
    print_header(f"Creating Project: {args.project_name}")
    print_info(f"Template: {args.template}")
    print_info(f"Template path: {template_path}")
    print()

    try:
        # Load template metadata
        metadata = TemplateMetadata(template_path)

        # Validate requirements
        requirements = metadata.get_requirements()
        if requirements:
            print_info("Template requirements:")
            for req_name, req_version in requirements.items():
                print(f"  • {req_name}: {req_version}")
            print()

        # Build rendering context
        config = load_config(paths.config_file)
        context_builder = ContextBuilder(
            config=config,
            env_vars=dict(os.environ),
            cli_args=vars(args),
            template_metadata=metadata
        )
        context = context_builder.build_context()

        # Show context summary
        print_info("Context values:")
        important_keys = ['project_name', 'group', 'version', 'kotlin_version', 'gradle_version']
        for key in important_keys:
            if key in context:
                print(f"  • {key}: {context[key]}")
        print()

        # Generate project
        target_path = Path.cwd() / args.project_name
        generator = ProjectGenerator(
            template_path=template_path,
            context=context,
            target_path=target_path
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

    print(f"gradleInit v{SCRIPT_VERSION}")
    print()

    # Check git availability
    if not GIT_AVAILABLE:
        print_warning("Git not found!")
        print()
        print("gradleInit requires git for:")
        print("  • Template repository management")
        print("  • Template updates")
        print("  • Custom template repositories")
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
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--download-modules', action='store_true')
    parser.add_argument('--update-modules', action='store_true')
    parser.add_argument('--modules-info', action='store_true')
    parser.add_argument('command', nargs='?')
    parser.add_argument('--template')

    phase1_args, remaining = parser.parse_known_args()

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

    # Load modules (auto-download on demand for init command)
    if phase1_args.command == 'init':
        module_loader.ensure_modules(auto_download=True)

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
        print("\n✗ Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)