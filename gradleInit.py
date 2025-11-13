#!/usr/bin/env python3
"""
gradleInit - Modern Kotlin/Gradle Project Initializer

A comprehensive tool for creating and managing Kotlin/Gradle multiproject builds
with template support from custom URLs, Jinja2 templating, Maven Central integration,
Spring Boot BOM support, and intelligent dependency management.

Features:
- Project initialization from templates (GitHub, HTTPS, file://)
- Jinja2 template engine with custom filters
- Shared version catalog support (URL or file-based)
- Maven Central integration with auto-updates
- Spring Boot BOM integration
- Environment variable support with defaults
- .gradleInit configuration (TOML-based)
- Version pinning with semantic versioning
- Intelligent update manager
- Self-update capability
- Priority: Args > ENV > .gradleInit

Author: gradleInit Contributors
License: MIT
Version: 1.1.0
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
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from urllib import request
from urllib.error import URLError
from urllib.parse import urlparse

# Check for required packages
REQUIRED_PACKAGES = {
    'jinja2': 'jinja2',
    'toml': 'toml'
}

MISSING_PACKAGES = []

for module_name, package_name in REQUIRED_PACKAGES.items():
    try:
        __import__(module_name)
    except ImportError:
        MISSING_PACKAGES.append(package_name)

if MISSING_PACKAGES:
    print(f"Missing required packages: {', '.join(MISSING_PACKAGES)}")
    print(f"\nInstall with: pip install {' '.join(MISSING_PACKAGES)}")
    print("\nOr using pipx for isolated installation:")
    print(f"  pipx install --include-deps {MISSING_PACKAGES[0]}")
    for pkg in MISSING_PACKAGES[1:]:
        print(f"  pipx inject gradleInit {pkg}")
    sys.exit(1)

import jinja2
import toml

# ============================================================================
# Constants
# ============================================================================

SCRIPT_VERSION = "1.1.0"
DEFAULT_TEMPLATE_URL = "https://github.com/stotz/gradleInit.git"
CONFIG_FILE_NAME = ".gradleInit"
GITHUB_RAW_URL = "https://raw.githubusercontent.com/stotz/gradleInit/main/gradleInit.py"
MAVEN_CENTRAL_API = "https://search.maven.org/solrsearch/select"
SPRING_BOOT_BOM_URL = "https://repo.maven.apache.org/maven2/org/springframework/boot/spring-boot-dependencies/{version}/spring-boot-dependencies-{version}.pom"


# ============================================================================
# Color Output Utilities
# ============================================================================

class Color:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_color(message: str, color: str = Color.END):
    """Print colored message."""
    print(f"{color}{message}{Color.END}")


def print_header(message: str):
    """Print header message."""
    print_color(f"\n{'=' * 70}", Color.BOLD)
    print_color(f"  {message}", Color.HEADER + Color.BOLD)
    print_color(f"{'=' * 70}\n", Color.BOLD)


def print_success(message: str):
    """Print success message."""
    print_color(f"✓ {message}", Color.GREEN)


def print_info(message: str):
    """Print info message."""
    print_color(f"→ {message}", Color.CYAN)


def print_warning(message: str):
    """Print warning message."""
    print_color(f"⚠ {message}", Color.YELLOW)


def print_error(message: str):
    """Print error message."""
    print_color(f"✗ {message}", Color.RED)


# ============================================================================
# Version Handling
# ============================================================================

@dataclass
class VersionInfo:
    """Represents a semantic version."""
    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None

    @staticmethod
    def parse(version_str: str) -> Optional['VersionInfo']:
        """Parse semantic version string."""
        # Remove 'v' prefix if present
        version_str = version_str.lstrip('v')

        # Pattern: major.minor.patch[-prerelease]
        pattern = r'^(\d+)\.(\d+)\.(\d+)(?:-(.+))?$'
        match = re.match(pattern, version_str)

        if not match:
            return None

        major, minor, patch, prerelease = match.groups()
        return VersionInfo(
            major=int(major),
            minor=int(minor),
            patch=int(patch),
            prerelease=prerelease
        )

    def is_stable(self) -> bool:
        """Check if version is stable (no prerelease)."""
        return self.prerelease is None

    def __str__(self) -> str:
        """String representation."""
        base = f"{self.major}.{self.minor}.{self.patch}"
        return f"{base}-{self.prerelease}" if self.prerelease else base

    def __lt__(self, other: 'VersionInfo') -> bool:
        """Compare versions."""
        if (self.major, self.minor, self.patch) != (other.major, other.minor, other.patch):
            return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

        # Stable > Prerelease
        if self.is_stable() and not other.is_stable():
            return False
        if not self.is_stable() and other.is_stable():
            return True

        # Both prerelease or both stable
        return (self.prerelease or '') < (other.prerelease or '')


@dataclass
class VersionConstraint:
    """Represents a version constraint with semantic versioning support."""
    operator: str  # >=, <=, >, <, ~, *, ==
    version: str

    @staticmethod
    def parse(constraint_str: str) -> 'VersionConstraint':
        """Parse version constraint string."""
        constraint_str = constraint_str.strip()

        if '*' in constraint_str:
            return VersionConstraint('*', constraint_str.replace('*', ''))

        if constraint_str.startswith('~'):
            return VersionConstraint('~', constraint_str[1:])

        operators = ['>=', '<=', '>', '<', '==']
        for op in operators:
            if constraint_str.startswith(op):
                return VersionConstraint(op, constraint_str[len(op):].strip())

        return VersionConstraint('==', constraint_str)

    def matches(self, version: str) -> bool:
        """Check if version matches constraint."""
        try:
            return self._compare_versions(version)
        except Exception:
            return False

    def _compare_versions(self, version: str) -> bool:
        """Compare versions according to operator."""
        v1_parts = self._parse_version_parts(version)
        v2_parts = self._parse_version_parts(self.version)

        if self.operator == '==':
            return v1_parts == v2_parts
        elif self.operator == '>=':
            return v1_parts >= v2_parts
        elif self.operator == '<=':
            return v1_parts <= v2_parts
        elif self.operator == '>':
            return v1_parts > v2_parts
        elif self.operator == '<':
            return v1_parts < v2_parts
        elif self.operator == '~':
            return (v1_parts[:2] == v2_parts[:2] and v1_parts >= v2_parts)
        elif self.operator == '*':
            prefix_parts = v2_parts
            return v1_parts[:len(prefix_parts)] == prefix_parts

        return False

    @staticmethod
    def _parse_version_parts(version: str) -> Tuple[int, ...]:
        """Parse version string into comparable tuple."""
        parts = []
        for part in version.split('.'):
            match = re.match(r'^(\d+)', part)
            if match:
                parts.append(int(match.group(1)))
        return tuple(parts)


# ============================================================================
# Maven Central Integration
# ============================================================================

@dataclass
class MavenArtifact:
    """Represents a Maven artifact."""
    group: str
    artifact: str
    version: str
    update_policy: str = "last-stable"

    def coordinate(self) -> str:
        """Get Maven coordinate string."""
        return f"{self.group}:{self.artifact}:{self.version}"


class MavenCentralClient:
    """Client for Maven Central REST API."""

    @staticmethod
    def search_versions(group: str, artifact: str, limit: int = 50) -> List[str]:
        """Search for all versions of an artifact."""
        try:
            query = f"g:{group} AND a:{artifact}"
            url = f"{MAVEN_CENTRAL_API}?q={query}&core=gav&rows={limit}&wt=json"

            with request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read())
                docs = data.get('response', {}).get('docs', [])
                versions = [doc['v'] for doc in docs if 'v' in doc]
                return versions
        except Exception as e:
            print_warning(f"Failed to search Maven Central: {e}")
            return []

    @staticmethod
    def get_latest_versions(group: str, artifact: str,
                            stable_only: bool = True) -> List[VersionInfo]:
        """Get latest versions sorted by semver."""
        versions_str = MavenCentralClient.search_versions(group, artifact)

        versions = []
        for v_str in versions_str:
            v_info = VersionInfo.parse(v_str)
            if v_info:
                if not stable_only or v_info.is_stable():
                    versions.append(v_info)

        # Sort descending
        versions.sort(reverse=True)
        return versions

    @staticmethod
    def check_for_updates(artifact: MavenArtifact) -> Dict[str, Any]:
        """Check for updates based on update policy."""
        current_version = VersionInfo.parse(artifact.version)
        if not current_version:
            return {"error": "Invalid current version"}

        all_versions = MavenCentralClient.get_latest_versions(
            artifact.group,
            artifact.artifact,
            stable_only=True
        )

        if not all_versions:
            return {"error": "No versions found"}

        latest_stable = all_versions[0]

        result = {
            "current": str(current_version),
            "latest_stable": str(latest_stable),
            "has_update": latest_stable > current_version,
            "breaking_change": False
        }

        # Check for breaking changes (major version bump)
        if latest_stable.major > current_version.major:
            result["breaking_change"] = True
            result["breaking_change_type"] = "major"

        # Apply update policy
        if artifact.update_policy == "pinned":
            result["recommended"] = str(current_version)
        elif artifact.update_policy == "last-stable":
            result["recommended"] = str(latest_stable)
        elif artifact.update_policy == "latest":
            # Include pre-releases
            all_with_pre = MavenCentralClient.get_latest_versions(
                artifact.group, artifact.artifact, stable_only=False
            )
            result["recommended"] = str(all_with_pre[0]) if all_with_pre else str(latest_stable)
        elif artifact.update_policy == "major-only":
            # Find latest with same or higher major
            candidates = [v for v in all_versions if v.major >= current_version.major]
            result["recommended"] = str(candidates[0]) if candidates else str(current_version)
        elif artifact.update_policy == "minor-only":
            # Find latest with same major
            candidates = [v for v in all_versions if v.major == current_version.major]
            result["recommended"] = str(candidates[0]) if candidates else str(current_version)

        return result


# ============================================================================
# Spring Boot BOM Integration
# ============================================================================

class SpringBootBOM:
    """Handle Spring Boot BOM integration."""

    @staticmethod
    def download_bom(version: str) -> Optional[str]:
        """Download Spring Boot BOM POM file."""
        url = SPRING_BOOT_BOM_URL.format(version=version)

        try:
            with request.urlopen(url, timeout=30) as response:
                return response.read().decode('utf-8')
        except Exception as e:
            print_warning(f"Failed to download Spring Boot BOM: {e}")
            return None

    @staticmethod
    def parse_bom(pom_content: str) -> Dict[str, str]:
        """Parse BOM and extract dependency versions."""
        try:
            root = ET.fromstring(pom_content)

            # Handle XML namespaces
            ns = {'mvn': 'http://maven.apache.org/POM/4.0.0'}

            # Extract properties
            properties = {}
            props_elem = root.find('mvn:properties', ns)
            if props_elem is not None:
                for prop in props_elem:
                    tag = prop.tag.replace('{http://maven.apache.org/POM/4.0.0}', '')
                    properties[tag] = prop.text

            # Extract dependency management
            dep_mgmt = root.find('.//mvn:dependencyManagement/mvn:dependencies', ns)
            dependencies = {}

            if dep_mgmt is not None:
                for dep in dep_mgmt.findall('mvn:dependency', ns):
                    group = dep.find('mvn:groupId', ns)
                    artifact = dep.find('mvn:artifactId', ns)
                    version = dep.find('mvn:version', ns)

                    if group is not None and artifact is not None and version is not None:
                        key = f"{group.text}:{artifact.text}"
                        version_text = version.text

                        # Resolve properties
                        if version_text and version_text.startswith('${') and version_text.endswith('}'):
                            prop_name = version_text[2:-1]
                            version_text = properties.get(prop_name, version_text)

                        dependencies[key] = version_text

            return dependencies
        except Exception as e:
            print_warning(f"Failed to parse Spring Boot BOM: {e}")
            return {}

    @staticmethod
    def sync_to_catalog(bom_version: str, catalog_path: Path) -> bool:
        """Sync Spring Boot BOM versions to libs.versions.toml."""
        pom_content = SpringBootBOM.download_bom(bom_version)
        if not pom_content:
            return False

        dependencies = SpringBootBOM.parse_bom(pom_content)
        if not dependencies:
            return False

        print_info(f"Found {len(dependencies)} managed dependencies in Spring Boot {bom_version}")

        # Read existing catalog
        if catalog_path.exists():
            catalog = toml.load(catalog_path)
        else:
            catalog = {"versions": {}, "libraries": {}}

        # Add Spring Boot version
        if "versions" not in catalog:
            catalog["versions"] = {}
        catalog["versions"]["spring-boot"] = bom_version

        # Add managed dependencies
        updated_count = 0
        for coord, version in dependencies.items():
            parts = coord.split(':')
            if len(parts) == 2:
                group, artifact = parts

                # Create library entry
                lib_name = artifact.replace('-', '_')
                if "libraries" not in catalog:
                    catalog["libraries"] = {}

                catalog["libraries"][lib_name] = {
                    "group": group,
                    "name": artifact,
                    "version": version
                }
                updated_count += 1

        # Write catalog
        try:
            with open(catalog_path, 'w') as f:
                toml.dump(catalog, f)
            print_success(f"Synced {updated_count} dependencies to {catalog_path}")
            return True
        except Exception as e:
            print_error(f"Failed to write catalog: {e}")
            return False


# ============================================================================
# Configuration Management
# ============================================================================

@dataclass
class SharedCatalogConfig:
    """Configuration for shared version catalog."""
    enabled: bool = False
    source: Optional[str] = None  # URL or file path
    sync_on_update: bool = True
    override_local: bool = False


@dataclass
class MavenCentralLibrary:
    """Configuration for a Maven Central tracked library."""
    group: str
    artifact: str
    version: str
    update_policy: str = "last-stable"


@dataclass
class GradleInitConfig:
    """Configuration for gradleInit with all features."""

    # Template settings
    template_url: Optional[str] = None
    template_version: Optional[str] = None

    # Project defaults
    default_group: Optional[str] = None
    default_version: str = "0.1.0"

    # Build tool versions
    gradle_version: Optional[str] = None
    kotlin_version: Optional[str] = None
    jdk_version: Optional[str] = None

    # Version constraints
    version_constraints: Dict[str, str] = field(default_factory=dict)

    # Shared catalog
    shared_catalog: SharedCatalogConfig = field(default_factory=SharedCatalogConfig)

    # Maven Central tracking
    maven_central_libraries: List[MavenCentralLibrary] = field(default_factory=list)

    # Spring Boot
    spring_boot_enabled: bool = False
    spring_boot_version: Optional[str] = None
    spring_boot_compatibility: str = "last-stable"  # pinned, last-stable, latest

    # Update settings
    auto_check_updates: bool = False
    auto_check_interval: str = "weekly"  # daily, weekly, monthly
    last_update_check: Optional[str] = None

    # Custom values
    custom_values: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def load_from_file(config_path: Path) -> Optional['GradleInitConfig']:
        """Load configuration from .gradleInit file."""
        if not config_path.exists():
            return None

        try:
            data = toml.load(config_path)

            # Parse shared catalog
            shared_cat_data = data.get('dependencies', {}).get('shared_catalog', {})
            shared_catalog = SharedCatalogConfig(
                enabled=shared_cat_data.get('enabled', False),
                source=shared_cat_data.get('source'),
                sync_on_update=shared_cat_data.get('sync_on_update', True),
                override_local=shared_cat_data.get('override_local', False)
            )

            # Parse Maven Central libraries
            maven_libs = []
            for lib_data in data.get('dependencies', {}).get('maven_central', {}).get('libraries', []):
                maven_libs.append(MavenCentralLibrary(
                    group=lib_data['group'],
                    artifact=lib_data['artifact'],
                    version=lib_data['version'],
                    update_policy=lib_data.get('update_policy', 'last-stable')
                ))

            # Parse Spring Boot
            spring_data = data.get('dependencies', {}).get('spring_boot', {})

            return GradleInitConfig(
                template_url=data.get('template', {}).get('url'),
                template_version=data.get('template', {}).get('version'),
                default_group=data.get('defaults', {}).get('group'),
                default_version=data.get('defaults', {}).get('version', '0.1.0'),
                gradle_version=data.get('versions', {}).get('gradle'),
                kotlin_version=data.get('versions', {}).get('kotlin'),
                jdk_version=data.get('versions', {}).get('jdk'),
                version_constraints=data.get('constraints', {}),
                shared_catalog=shared_catalog,
                maven_central_libraries=maven_libs,
                spring_boot_enabled=spring_data.get('enabled', False),
                spring_boot_version=spring_data.get('version'),
                spring_boot_compatibility=spring_data.get('compatibility_mode', 'last-stable'),
                auto_check_updates=data.get('updates', {}).get('auto_check', False),
                auto_check_interval=data.get('updates', {}).get('check_interval', 'weekly'),
                last_update_check=data.get('updates', {}).get('last_check'),
                custom_values=data.get('custom', {})
            )
        except Exception as e:
            print_warning(f"Failed to load config from {config_path}: {e}")
            return None

    def save_to_file(self, config_path: Path):
        """Save configuration to .gradleInit file."""
        data = {
            'template': {
                'url': self.template_url,
                'version': self.template_version
            },
            'defaults': {
                'group': self.default_group,
                'version': self.default_version
            },
            'versions': {
                'gradle': self.gradle_version,
                'kotlin': self.kotlin_version,
                'jdk': self.jdk_version
            },
            'constraints': self.version_constraints,
            'dependencies': {
                'shared_catalog': {
                    'enabled': self.shared_catalog.enabled,
                    'source': self.shared_catalog.source,
                    'sync_on_update': self.shared_catalog.sync_on_update,
                    'override_local': self.shared_catalog.override_local
                },
                'maven_central': {
                    'libraries': [
                        {
                            'group': lib.group,
                            'artifact': lib.artifact,
                            'version': lib.version,
                            'update_policy': lib.update_policy
                        }
                        for lib in self.maven_central_libraries
                    ]
                },
                'spring_boot': {
                    'enabled': self.spring_boot_enabled,
                    'version': self.spring_boot_version,
                    'compatibility_mode': self.spring_boot_compatibility
                }
            },
            'updates': {
                'auto_check': self.auto_check_updates,
                'check_interval': self.auto_check_interval,
                'last_check': self.last_update_check
            },
            'custom': self.custom_values
        }

        # Remove None values
        data = self._remove_none_recursive(data)

        try:
            with open(config_path, 'w') as f:
                toml.dump(data, f)
            print_success(f"Configuration saved to {config_path}")
        except Exception as e:
            print_error(f"Failed to save config: {e}")

    @staticmethod
    def _remove_none_recursive(data: Any) -> Any:
        """Recursively remove None values from dict."""
        if isinstance(data, dict):
            return {k: GradleInitConfig._remove_none_recursive(v)
                    for k, v in data.items() if v is not None}
        elif isinstance(data, list):
            return [GradleInitConfig._remove_none_recursive(item) for item in data]
        return data

    def check_version_constraint(self, name: str, version: str) -> bool:
        """Check if version satisfies constraint."""
        if name not in self.version_constraints:
            return True

        constraint = VersionConstraint.parse(self.version_constraints[name])
        return constraint.matches(version)

    def merge_with_env_and_args(self, env_vars: Dict[str, str],
                                cli_args: Dict[str, Any]) -> 'GradleInitConfig':
        """Merge config with ENV and CLI args (priority: CLI > ENV > config)."""
        merged = GradleInitConfig(
            template_url=cli_args.get('template_url') or
                         env_vars.get('GRADLE_INIT_TEMPLATE') or
                         self.template_url,
            template_version=cli_args.get('template_version') or
                             env_vars.get('GRADLE_INIT_TEMPLATE_VERSION') or
                             self.template_version,
            default_group=cli_args.get('group') or
                          env_vars.get('GRADLE_INIT_GROUP') or
                          self.default_group,
            default_version=cli_args.get('version') or
                            env_vars.get('GRADLE_INIT_VERSION') or
                            self.default_version,
            gradle_version=cli_args.get('gradle_version') or
                           env_vars.get('GRADLE_VERSION') or
                           self.gradle_version,
            kotlin_version=cli_args.get('kotlin_version') or
                           env_vars.get('KOTLIN_VERSION') or
                           self.kotlin_version,
            jdk_version=cli_args.get('jdk_version') or
                        env_vars.get('JDK_VERSION') or
                        self.jdk_version,
            version_constraints=self.version_constraints.copy(),
            shared_catalog=self.shared_catalog,
            maven_central_libraries=self.maven_central_libraries.copy(),
            spring_boot_enabled=self.spring_boot_enabled,
            spring_boot_version=self.spring_boot_version,
            spring_boot_compatibility=self.spring_boot_compatibility,
            auto_check_updates=self.auto_check_updates,
            auto_check_interval=self.auto_check_interval,
            last_update_check=self.last_update_check,
            custom_values=self.custom_values.copy()
        )

        return merged


# ============================================================================
# Shared Catalog Manager
# ============================================================================

class SharedCatalogManager:
    """Manage shared version catalogs from URL or file."""

    @staticmethod
    def fetch_catalog(source: str) -> Optional[Dict[str, Any]]:
        """Fetch catalog from URL or file."""
        parsed = urlparse(source)

        try:
            if parsed.scheme in ('http', 'https'):
                # Download from URL
                with request.urlopen(source, timeout=10) as response:
                    content = response.read().decode('utf-8')
                    return toml.loads(content)
            elif parsed.scheme == 'file' or parsed.scheme == '':
                # Load from file
                path = Path(parsed.path if parsed.scheme == 'file' else source)
                if path.exists():
                    return toml.load(path)
                else:
                    print_error(f"Catalog file not found: {path}")
                    return None
            else:
                print_error(f"Unsupported catalog source scheme: {parsed.scheme}")
                return None
        except Exception as e:
            print_error(f"Failed to fetch catalog from {source}: {e}")
            return None

    @staticmethod
    def merge_catalogs(local: Dict[str, Any], shared: Dict[str, Any],
                       override_local: bool = False) -> Dict[str, Any]:
        """Merge shared catalog into local catalog."""
        if override_local:
            # Shared wins
            merged = {**local, **shared}
        else:
            # Local wins
            merged = {**shared, **local}

        return merged

    @staticmethod
    def sync_catalog(config: GradleInitConfig, catalog_path: Path) -> bool:
        """Sync shared catalog to local project."""
        if not config.shared_catalog.enabled or not config.shared_catalog.source:
            return True

        print_info(f"Syncing shared catalog from {config.shared_catalog.source}")

        shared = SharedCatalogManager.fetch_catalog(config.shared_catalog.source)
        if not shared:
            return False

        # Load local catalog
        local = {}
        if catalog_path.exists():
            local = toml.load(catalog_path)

        # Merge
        merged = SharedCatalogManager.merge_catalogs(
            local, shared, config.shared_catalog.override_local
        )

        # Save
        try:
            with open(catalog_path, 'w') as f:
                toml.dump(merged, f)
            print_success(f"Shared catalog synced to {catalog_path}")
            return True
        except Exception as e:
            print_error(f"Failed to sync catalog: {e}")
            return False


# ============================================================================
# Update Manager
# ============================================================================

class UpdateManager:
    """Coordinate updates from all sources."""

    @staticmethod
    def should_check_updates(config: GradleInitConfig) -> bool:
        """Check if it's time to check for updates."""
        if not config.auto_check_updates:
            return False

        if not config.last_update_check:
            return True

        try:
            last_check = datetime.fromisoformat(config.last_update_check)
            now = datetime.now()

            if config.auto_check_interval == "daily":
                return (now - last_check) > timedelta(days=1)
            elif config.auto_check_interval == "weekly":
                return (now - last_check) > timedelta(weeks=1)
            elif config.auto_check_interval == "monthly":
                return (now - last_check) > timedelta(days=30)
        except Exception:
            return True

        return False

    @staticmethod
    def check_all_updates(config: GradleInitConfig) -> Dict[str, Any]:
        """Check for updates from all sources."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'shared_catalog': None,
            'maven_central': [],
            'spring_boot': None
        }

        # Check shared catalog
        if config.shared_catalog.enabled and config.shared_catalog.source:
            catalog = SharedCatalogManager.fetch_catalog(config.shared_catalog.source)
            if catalog:
                report['shared_catalog'] = {
                    'available': True,
                    'source': config.shared_catalog.source
                }

        # Check Maven Central libraries
        for lib in config.maven_central_libraries:
            artifact = MavenArtifact(
                group=lib.group,
                artifact=lib.artifact,
                version=lib.version,
                update_policy=lib.update_policy
            )

            update_info = MavenCentralClient.check_for_updates(artifact)
            if 'error' not in update_info:
                report['maven_central'].append({
                    'artifact': artifact.coordinate(),
                    'update_info': update_info
                })

        # Check Spring Boot
        if config.spring_boot_enabled:
            # Could check for newer Spring Boot versions here
            report['spring_boot'] = {
                'current': config.spring_boot_version,
                'mode': config.spring_boot_compatibility
            }

        return report

    @staticmethod
    def print_update_report(report: Dict[str, Any]):
        """Print formatted update report."""
        print_header("Update Report")

        print_info(f"Generated: {report['timestamp']}")

        # Shared catalog
        if report['shared_catalog']:
            print_info("\nShared Catalog:")
            print_success(f"  Available from: {report['shared_catalog']['source']}")

        # Maven Central
        if report['maven_central']:
            print_info("\nMaven Central Updates:")
            for item in report['maven_central']:
                artifact = item['artifact']
                info = item['update_info']

                if info.get('has_update'):
                    current = info['current']
                    recommended = info.get('recommended', info['latest_stable'])

                    msg = f"  {artifact}: {current} → {recommended}"
                    if info.get('breaking_change'):
                        print_warning(msg + " [BREAKING]")
                    else:
                        print_success(msg)
                else:
                    print_info(f"  {artifact}: Up to date")

        # Spring Boot
        if report['spring_boot']:
            print_info("\nSpring Boot:")
            print_info(f"  Version: {report['spring_boot']['current']}")
            print_info(f"  Mode: {report['spring_boot']['mode']}")


# ============================================================================
# Template Engine
# ============================================================================

class TemplateEngine:
    """Jinja2-based template engine with custom filters."""

    def __init__(self, template_dir: Path, config: GradleInitConfig,
                 context: Dict[str, Any]):
        """Initialize template engine."""
        self.template_dir = template_dir
        self.config = config
        self.context = context

        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(template_dir)),
            autoescape=jinja2.select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )

        # Add custom filters
        self.env.filters['camelCase'] = self._camel_case
        self.env.filters['pascalCase'] = self._pascal_case
        self.env.filters['snakeCase'] = self._snake_case
        self.env.filters['kebabCase'] = self._kebab_case

        # Add custom globals
        self.env.globals['env'] = self._get_env_var
        self.env.globals['config'] = self._get_config_value

    @staticmethod
    def _camel_case(text: str) -> str:
        """Convert to camelCase."""
        parts = re.split(r'[-_\s]+', text)
        return parts[0].lower() + ''.join(p.capitalize() for p in parts[1:])

    @staticmethod
    def _pascal_case(text: str) -> str:
        """Convert to PascalCase."""
        parts = re.split(r'[-_\s]+', text)
        return ''.join(p.capitalize() for p in parts)

    @staticmethod
    def _snake_case(text: str) -> str:
        """Convert to snake_case."""
        return re.sub(r'[-\s]+', '_', text.lower())

    @staticmethod
    def _kebab_case(text: str) -> str:
        """Convert to kebab-case."""
        return re.sub(r'[_\s]+', '-', text.lower())

    def _get_env_var(self, var_name: str, default: str = '') -> str:
        """Get environment variable with default."""
        return os.environ.get(var_name, default)

    def _get_config_value(self, key: str, default: Any = None) -> Any:
        """Get value from config."""
        keys = key.split('.')
        value = self.config.custom_values

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default

        return value if value is not None else default

    def render_template(self, template_path: Path) -> str:
        """Render a template file."""
        try:
            relative_path = template_path.relative_to(self.template_dir)
            template = self.env.get_template(str(relative_path))
            return template.render(**self.context)
        except jinja2.TemplateError as e:
            print_error(f"Template error in {template_path}: {e}")
            raise

    def process_directory(self, source_dir: Path, target_dir: Path):
        """Process all templates in directory."""
        for item in source_dir.rglob('*'):
            if item.is_file():
                if '.git' in item.parts:
                    continue

                relative = item.relative_to(source_dir)
                target_path = target_dir / relative

                is_template = item.suffix == '.j2'

                if not is_template:
                    try:
                        content = item.read_text(encoding='utf-8')
                        is_template = '{{' in content or '{%' in content
                    except Exception:
                        is_template = False

                target_path.parent.mkdir(parents=True, exist_ok=True)

                if is_template:
                    if item.suffix == '.j2':
                        target_path = target_path.with_suffix('')

                    rendered = self.render_template(item)
                    target_path.write_text(rendered, encoding='utf-8')
                    print_info(f"  Template: {relative}")
                else:
                    shutil.copy2(item, target_path)
                    print_info(f"  Copy: {relative}")


# ============================================================================
# Template Source Handler
# ============================================================================

class TemplateSource:
    """Handle different template sources."""

    @staticmethod
    def fetch_template(template_url: str, version: Optional[str] = None) -> Path:
        """Fetch template from URL."""
        parsed = urlparse(template_url)

        if parsed.scheme in ('http', 'https'):
            if template_url.endswith('.git') or 'github.com' in template_url:
                return TemplateSource._fetch_git_repo(template_url, version)
            else:
                return TemplateSource._fetch_https_archive(template_url)
        elif parsed.scheme == 'file':
            return Path(parsed.path)
        elif parsed.scheme == '':
            path = Path(template_url)
            if not path.exists():
                raise ValueError(f"Template path does not exist: {template_url}")
            return path
        else:
            raise ValueError(f"Unsupported URL scheme: {parsed.scheme}")

    @staticmethod
    def _fetch_git_repo(repo_url: str, version: Optional[str] = None) -> Path:
        """Clone git repository."""
        print_info(f"Cloning template from {repo_url}")

        temp_dir = Path(tempfile.mkdtemp(prefix='gradleinit_'))

        try:
            cmd = ['git', 'clone', '--depth', '1']
            if version:
                cmd.extend(['--branch', version])
            cmd.extend([repo_url, str(temp_dir)])

            subprocess.run(cmd, check=True, capture_output=True)
            print_success("Template cloned successfully")

            git_dir = temp_dir / '.git'
            if git_dir.exists():
                shutil.rmtree(git_dir)

            return temp_dir
        except subprocess.CalledProcessError as e:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise RuntimeError(f"Failed to clone repository: {e.stderr.decode()}")

    @staticmethod
    def _fetch_https_archive(archive_url: str) -> Path:
        """Download and extract archive."""
        print_info(f"Downloading template from {archive_url}")

        temp_dir = Path(tempfile.mkdtemp(prefix='gradleinit_'))
        archive_path = temp_dir / 'template.zip'

        try:
            with request.urlopen(archive_url) as response:
                archive_path.write_bytes(response.read())

            print_success("Template downloaded")

            extract_dir = temp_dir / 'extracted'
            shutil.unpack_archive(archive_path, extract_dir)

            contents = list(extract_dir.iterdir())
            if len(contents) == 1 and contents[0].is_dir():
                template_root = contents[0]
            else:
                template_root = extract_dir

            return template_root

        except Exception as e:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise RuntimeError(f"Failed to download template: {e}")


# ============================================================================
# Self-Updater
# ============================================================================

class SelfUpdater:
    """Handle script self-updates."""

    @staticmethod
    def check_for_update() -> Optional[str]:
        """Check if newer version is available."""
        try:
            with request.urlopen(GITHUB_RAW_URL, timeout=5) as response:
                content = response.read().decode('utf-8')

                # Extract version from script
                match = re.search(r'SCRIPT_VERSION\s*=\s*"([^"]+)"', content)
                if match:
                    remote_version = match.group(1)
                    if remote_version != SCRIPT_VERSION:
                        return remote_version
        except Exception:
            pass

        return None

    @staticmethod
    def perform_update(script_path: Path) -> bool:
        """Download and replace script."""
        try:
            print_info("Downloading latest version...")

            with request.urlopen(GITHUB_RAW_URL, timeout=10) as response:
                new_content = response.read()

            # Backup current version
            backup_path = script_path.with_suffix('.py.bak')
            shutil.copy2(script_path, backup_path)

            # Write new version
            script_path.write_bytes(new_content)
            script_path.chmod(0o755)

            print_success("Update successful!")
            print_info(f"Backup saved to: {backup_path}")
            return True

        except Exception as e:
            print_error(f"Update failed: {e}")
            return False


# ============================================================================
# Project Initializer
# ============================================================================

class GradleInitializer:
    """Main class for initializing Gradle projects."""

    def __init__(self, config: GradleInitConfig):
        """Initialize with configuration."""
        self.config = config

    def init_project(self, project_name: str, target_dir: Path,
                     template_url: Optional[str] = None,
                     additional_context: Optional[Dict[str, Any]] = None):
        """Initialize a new Gradle project."""

        print_header(f"Initializing Project: {project_name}")

        template_url = template_url or self.config.template_url or DEFAULT_TEMPLATE_URL

        try:
            template_dir = TemplateSource.fetch_template(
                template_url,
                self.config.template_version
            )
        except Exception as e:
            print_error(f"Failed to fetch template: {e}")
            return False

        context = self._prepare_context(project_name, additional_context)

        if not self._validate_version_constraints(context):
            return False

        target_dir.mkdir(parents=True, exist_ok=True)

        try:
            engine = TemplateEngine(template_dir, self.config, context)
            print_info("Processing templates...")
            engine.process_directory(template_dir, target_dir)
            print_success(f"Project created in {target_dir}")

            # Sync shared catalog if enabled
            if self.config.shared_catalog.enabled:
                catalog_path = target_dir / 'gradle' / 'libs.versions.toml'
                SharedCatalogManager.sync_catalog(self.config, catalog_path)

            # Sync Spring Boot BOM if enabled
            if self.config.spring_boot_enabled and self.config.spring_boot_version:
                catalog_path = target_dir / 'gradle' / 'libs.versions.toml'
                SpringBootBOM.sync_to_catalog(self.config.spring_boot_version, catalog_path)

            self._init_git_repo(target_dir)

            print_header("Project initialization complete!")
            print_success(f"Project: {project_name}")
            print_success(f"Location: {target_dir}")

            print_info("\nNext steps:")
            print_info("  cd " + str(target_dir))
            print_info("  ./gradlew build")

            return True

        except Exception as e:
            print_error(f"Failed to process templates: {e}")
            return False
        finally:
            if template_url.startswith(('http://', 'https://')):
                shutil.rmtree(template_dir, ignore_errors=True)

    def _prepare_context(self, project_name: str,
                         additional: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare template context."""
        context = {
            'project_name': project_name,
            'project_group': self.config.default_group or f'com.example.{project_name}',
            'project_version': self.config.default_version,
            'gradle_version': self.config.gradle_version or '9.0',
            'kotlin_version': self.config.kotlin_version or '2.2.0',
            'jdk_version': self.config.jdk_version or '21',
            'timestamp': datetime.now().isoformat(),
        }

        context.update(self.config.custom_values)

        if additional:
            context.update(additional)

        return context

    def _validate_version_constraints(self, context: Dict[str, Any]) -> bool:
        """Validate versions meet constraints."""
        checks = [
            ('gradle_version', context.get('gradle_version')),
            ('kotlin_version', context.get('kotlin_version')),
            ('jdk_version', context.get('jdk_version'))
        ]

        all_valid = True
        for name, version in checks:
            if version and not self.config.check_version_constraint(name, version):
                constraint = self.config.version_constraints[name]
                print_error(f"{name} {version} does not satisfy constraint {constraint}")
                all_valid = False

        return all_valid

    @staticmethod
    def _init_git_repo(project_dir: Path):
        """Initialize git repository."""
        try:
            subprocess.run(['git', 'init'], cwd=project_dir,
                           check=True, capture_output=True)
            subprocess.run(['git', 'add', '.'], cwd=project_dir,
                           check=True, capture_output=True)
            subprocess.run(['git', 'commit', '-m', 'Initial commit'],
                           cwd=project_dir, check=True, capture_output=True)
            print_success("Git repository initialized")
        except subprocess.CalledProcessError:
            print_warning("Failed to initialize git repository")


# ============================================================================
# CLI Interface
# ============================================================================

def parse_env_with_defaults(env_vars: Dict[str, str]) -> Dict[str, str]:
    """Parse environment variables with default values."""
    result = {}

    for key, value in env_vars.items():
        matches = re.findall(r'\$\{([^}:]+)(?::-([^}]*))?\}', value)

        if matches:
            for var_name, default in matches:
                env_value = os.environ.get(var_name, default)
                value = value.replace(f'${{{var_name}:-{default}}}', env_value)
                value = value.replace(f'${{{var_name}}}', env_value)

        result[key] = value

    return result


def create_cli() -> argparse.ArgumentParser:
    """Create CLI argument parser."""
    parser = argparse.ArgumentParser(
        description='Gradle Project Initializer v' + SCRIPT_VERSION,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--version', action='version',
                        version=f'gradleInit {SCRIPT_VERSION}')

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize new project')
    init_parser.add_argument('project_name', help='Project name')
    init_parser.add_argument('--dir', type=Path, help='Target directory')
    init_parser.add_argument('--template', dest='template_url',
                             help='Template URL')
    init_parser.add_argument('--template-version', dest='template_version',
                             help='Template version')
    init_parser.add_argument('--group', help='Project group ID')
    init_parser.add_argument('--version', dest='project_version',
                             help='Project version')
    init_parser.add_argument('--gradle-version', dest='gradle_version',
                             help='Gradle version')
    init_parser.add_argument('--kotlin-version', dest='kotlin_version',
                             help='Kotlin version')
    init_parser.add_argument('--jdk-version', dest='jdk_version',
                             help='JDK version')

    # Config command
    config_parser = subparsers.add_parser('config', help='Manage configuration')
    config_parser.add_argument('--show', action='store_true',
                               help='Show configuration')
    config_parser.add_argument('--template', dest='template_url',
                               help='Set template URL')
    config_parser.add_argument('--group', help='Set default group')
    config_parser.add_argument('--constraint', action='append', nargs=2,
                               metavar=('NAME', 'VERSION'),
                               help='Add version constraint')

    # Update command
    update_parser = subparsers.add_parser('update', help='Check for updates')
    update_parser.add_argument('--check', action='store_true',
                               help='Check for updates')
    update_parser.add_argument('--sync-shared', action='store_true',
                               help='Sync shared catalog')
    update_parser.add_argument('--sync-spring-boot', metavar='VERSION',
                               help='Sync Spring Boot BOM')
    update_parser.add_argument('--self-update', action='store_true',
                               help='Update gradleInit script')

    return parser


def main():
    """Main entry point."""
    parser = create_cli()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Load config
    config_path = Path.home() / CONFIG_FILE_NAME
    if not config_path.exists():
        config_path = Path.cwd() / CONFIG_FILE_NAME

    base_config = GradleInitConfig.load_from_file(config_path) or GradleInitConfig()

    # Merge with ENV and args
    env_vars = parse_env_with_defaults(dict(os.environ))
    cli_args = {k: v for k, v in vars(args).items() if v is not None}
    merged_config = base_config.merge_with_env_and_args(env_vars, cli_args)

    # Execute command
    if args.command == 'init':
        target_dir = args.dir or Path.cwd() / args.project_name

        additional_context = {}
        if args.group:
            additional_context['project_group'] = args.group
        if args.project_version:
            additional_context['project_version'] = args.project_version

        initializer = GradleInitializer(merged_config)
        success = initializer.init_project(
            args.project_name,
            target_dir,
            args.template_url,
            additional_context
        )

        # Check for updates if auto-check enabled
        if UpdateManager.should_check_updates(merged_config):
            print_info("\nChecking for updates...")
            report = UpdateManager.check_all_updates(merged_config)
            UpdateManager.print_update_report(report)

            # Update last check time
            merged_config.last_update_check = datetime.now().isoformat()
            merged_config.save_to_file(config_path)

        return 0 if success else 1

    elif args.command == 'config':
        if args.show:
            print_header("Current Configuration")

            if merged_config.template_url:
                print_info(f"Template URL: {merged_config.template_url}")
            if merged_config.default_group:
                print_info(f"Default Group: {merged_config.default_group}")

            if merged_config.shared_catalog.enabled:
                print_info("\nShared Catalog:")
                print_info(f"  Source: {merged_config.shared_catalog.source}")

            if merged_config.maven_central_libraries:
                print_info("\nMaven Central Libraries:")
                for lib in merged_config.maven_central_libraries:
                    print_info(f"  {lib.group}:{lib.artifact}:{lib.version} ({lib.update_policy})")

            if merged_config.spring_boot_enabled:
                print_info("\nSpring Boot:")
                print_info(f"  Version: {merged_config.spring_boot_version}")
                print_info(f"  Mode: {merged_config.spring_boot_compatibility}")
        else:
            if args.template_url:
                merged_config.template_url = args.template_url
            if args.group:
                merged_config.default_group = args.group
            if args.constraint:
                for name, constraint in args.constraint:
                    merged_config.version_constraints[name] = constraint

            config_path = Path.home() / CONFIG_FILE_NAME
            merged_config.save_to_file(config_path)

        return 0

    elif args.command == 'update':
        if args.self_update:
            new_version = SelfUpdater.check_for_update()
            if new_version:
                print_info(f"New version available: {new_version}")
                script_path = Path(__file__).resolve()
                return 0 if SelfUpdater.perform_update(script_path) else 1
            else:
                print_success("Already at latest version")
                return 0

        if args.check:
            report = UpdateManager.check_all_updates(merged_config)
            UpdateManager.print_update_report(report)

            merged_config.last_update_check = datetime.now().isoformat()
            merged_config.save_to_file(config_path)
            return 0

        if args.sync_shared:
            catalog_path = Path.cwd() / 'gradle' / 'libs.versions.toml'
            success = SharedCatalogManager.sync_catalog(merged_config, catalog_path)
            return 0 if success else 1

        if args.sync_spring_boot:
            catalog_path = Path.cwd() / 'gradle' / 'libs.versions.toml'
            success = SpringBootBOM.sync_to_catalog(args.sync_spring_boot, catalog_path)
            return 0 if success else 1

    return 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print_warning("\nOperation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)