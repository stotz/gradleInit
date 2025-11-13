#!/usr/bin/env python3
"""
gradleInit - Modern Kotlin/Gradle Project Initializer

A comprehensive tool for creating and managing Kotlin/Gradle multiproject builds
with convention plugins, version catalogs, and intelligent dependency management.

Features:
- Project initialization with templates
- Convention plugins (common, library, application, spring)
- Version catalog management
- Spring Boot BOM integration
- Maven Central package updates
- Shared version catalog (URL or file)
- .gradleInit configuration persistence
- Self-update capability

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
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from urllib import request
from urllib.error import URLError

try:
    import toml
except ImportError:
    print("Error: 'toml' package required. Install with: pip install toml")
    sys.exit(1)


# ============================================================================
# Constants
# ============================================================================

SCRIPT_VERSION = "1.1.0"
GITHUB_RAW_URL = "https://raw.githubusercontent.com/stotz/gradleInit/main/gradleInit.py"
GITHUB_TEMPLATE_URL = "https://github.com/stotz/gradleInit.git"

MAVEN_CENTRAL_API = "https://search.maven.org/solrsearch/select"
MAVEN_CENTRAL_VERSIONS = "https://search.maven.org/solrsearch/select?q=g:{group}+AND+a:{artifact}&core=gav&rows=50&wt=json"
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
    """Print header."""
    print_color(f"\n{'=' * 70}", Color.BOLD)
    print_color(f"  {message}", Color.HEADER + Color.BOLD)
    print_color(f"{'=' * 70}\n", Color.BOLD)


def print_success(message: str):
    """Print success message."""
    print_color(f"? {message}", Color.GREEN)


def print_info(message: str):
    """Print info message."""
    print_color(f"? {message}", Color.CYAN)


def print_warning(message: str):
    """Print warning message."""
    print_color(f"? {message}", Color.YELLOW)


def print_error(message: str):
    """Print error message."""
    print_color(f"? {message}", Color.RED)


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class VersionInfo:
    """Semantic version information."""
    major: int
    minor: int
    patch: int
    qualifier: Optional[str] = None
    
    @classmethod
    def parse(cls, version: str) -> Optional['VersionInfo']:
        """Parse version string to VersionInfo."""
        pattern = r'^(\d+)\.(\d+)\.(\d+)(?:[-.](.+))?$'
        match = re.match(pattern, version)
        
        if not match:
            return None
        
        major, minor, patch, qualifier = match.groups()
        return cls(int(major), int(minor), int(patch), qualifier)
    
    def __str__(self) -> str:
        """Convert to version string."""
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.qualifier:
            version += f"-{self.qualifier}"
        return version
    
    def is_stable(self) -> bool:
        """Check if version is stable."""
        if not self.qualifier:
            return True
        unstable = ['alpha', 'beta', 'rc', 'snapshot', 'preview', 'm']
        return not any(m in self.qualifier.lower() for m in unstable)
    
    def compare(self, other: 'VersionInfo') -> int:
        """Compare versions. Returns -1, 0, or 1."""
        for s, o in [(self.major, other.major), (self.minor, other.minor), (self.patch, other.patch)]:
            if s < o:
                return -1
            elif s > o:
                return 1
        
        if self.qualifier is None and other.qualifier is None:
            return 0
        elif self.qualifier is None:
            return 1
        elif other.qualifier is None:
            return -1
        else:
            return -1 if self.qualifier < other.qualifier else (1 if self.qualifier > other.qualifier else 0)


@dataclass
class MavenArtifact:
    """Maven artifact representation."""
    group: str
    artifact: str
    version: str
    timestamp: Optional[int] = None
    
    @property
    def coordinate(self) -> str:
        """Return Maven coordinate."""
        return f"{self.group}:{self.artifact}:{self.version}"


@dataclass
class SharedCatalogConfig:
    """Shared version catalog configuration."""
    enabled: bool = False
    source: Optional[str] = None  # URL or file path
    sync_on_update: bool = True
    override_local: bool = False  # If true, shared catalog overrides local versions


@dataclass
class MavenCentralLibrary:
    """Maven Central library tracking."""
    group: str
    artifact: str
    version: str
    update_policy: str = "last-stable"
    reason: Optional[str] = None
    last_updated: Optional[str] = None


@dataclass
class SpringBootConfig:
    """Spring Boot configuration."""
    enabled: bool = False
    version: str = "3.5.7"
    compatibility_mode: str = "last-stable"
    starters: List[str] = field(default_factory=list)
    libraries: List[str] = field(default_factory=list)


@dataclass
class DependenciesConfig:
    """Dependencies configuration."""
    strategy: str = "manual"
    shared_catalog: SharedCatalogConfig = field(default_factory=SharedCatalogConfig)
    spring_boot: SpringBootConfig = field(default_factory=SpringBootConfig)
    maven_central_enabled: bool = True
    maven_central_libraries: List[MavenCentralLibrary] = field(default_factory=list)


@dataclass
class UpdateConfig:
    """Update configuration."""
    auto_check: bool = True
    check_interval: str = "weekly"
    last_check: Optional[str] = None
    notify_breaking_changes: bool = True


@dataclass
class GradleInitConfig:
    """Complete .gradleInit configuration."""
    project_name: str
    project_version: str = "0.1.0-SNAPSHOT"
    project_group: str = "com.example"
    gradle_version: str = "9.0"
    kotlin_version: str = "2.2.0"
    jvm_target: str = "21"
    template_source: str = GITHUB_TEMPLATE_URL
    created: str = field(default_factory=lambda: datetime.now().isoformat())
    gradleInit_version: str = SCRIPT_VERSION
    modules: Dict[str, Dict[str, str]] = field(default_factory=dict)
    dependencies: DependenciesConfig = field(default_factory=DependenciesConfig)
    update: UpdateConfig = field(default_factory=UpdateConfig)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Utility Functions
# ============================================================================

class FileUtils:
    """File operation utilities."""
    
    @staticmethod
    def calculate_hash(file_path: Path) -> str:
        """Calculate SHA256 hash of file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for block in iter(lambda: f.read(4096), b""):
                sha256.update(block)
        return sha256.hexdigest()
    
    @staticmethod
    def backup_file(file_path: Path) -> Optional[Path]:
        """Create timestamped backup of file."""
        if not file_path.exists():
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.parent / f"{file_path.name}.backup.{timestamp}"
        shutil.copy2(file_path, backup_path)
        print_success(f"Backup created: {backup_path.name}")
        return backup_path
    
    @staticmethod
    def download_file(url: str, destination: Path, timeout: int = 30) -> bool:
        """Download file from URL."""
        try:
            print_info(f"Downloading from {url}")
            with request.urlopen(url, timeout=timeout) as response:
                destination.write_bytes(response.read())
            return True
        except URLError as e:
            print_error(f"Download failed: {e}")
            return False
        except Exception as e:
            print_error(f"Unexpected error: {e}")
            return False


class CommandRunner:
    """Command execution utilities."""
    
    @staticmethod
    def run(command: List[str], cwd: Optional[Path] = None) -> Tuple[int, str, str]:
        """Run command and return exit code, stdout, stderr."""
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=False
            )
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return 1, "", str(e)


# ============================================================================
# Version Catalog Manager
# ============================================================================

class VersionCatalogManager:
    """Manages version catalogs including shared catalogs."""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.catalog_path = project_dir / "gradle" / "libs.versions.toml"
    
    def load_catalog(self, path: Optional[Path] = None) -> Optional[Dict]:
        """Load version catalog from file."""
        catalog_path = path or self.catalog_path
        
        if not catalog_path.exists():
            return None
        
        try:
            return toml.load(catalog_path)
        except Exception as e:
            print_error(f"Failed to load catalog: {e}")
            return None
    
    def save_catalog(self, catalog: Dict, path: Optional[Path] = None) -> bool:
        """Save version catalog to file."""
        catalog_path = path or self.catalog_path
        
        try:
            catalog_path.parent.mkdir(parents=True, exist_ok=True)
            with open(catalog_path, 'w') as f:
                toml.dump(catalog, f)
            return True
        except Exception as e:
            print_error(f"Failed to save catalog: {e}")
            return False
    
    def load_shared_catalog(self, source: str) -> Optional[Dict]:
        """Load shared version catalog from URL or file."""
        print_info(f"Loading shared catalog from: {source}")
        
        # Check if URL
        if source.startswith(('http://', 'https://')):
            temp_file = self.project_dir / ".shared-catalog.toml.tmp"
            
            if FileUtils.download_file(source, temp_file):
                catalog = self.load_catalog(temp_file)
                temp_file.unlink()
                return catalog
            return None
        
        # Local file path
        source_path = Path(source).expanduser().resolve()
        
        if not source_path.exists():
            print_error(f"Shared catalog not found: {source_path}")
            return None
        
        return self.load_catalog(source_path)
    
    def merge_catalogs(
        self,
        local: Dict,
        shared: Dict,
        override_local: bool = False
    ) -> Dict:
        """Merge shared catalog into local catalog."""
        merged = local.copy()
        
        for section in ['versions', 'libraries', 'plugins', 'bundles']:
            if section not in shared:
                continue
            
            if section not in merged:
                merged[section] = {}
            
            for key, value in shared[section].items():
                # If override_local or key doesn't exist locally
                if override_local or key not in merged[section]:
                    merged[section][key] = value
        
        return merged
    
    def sync_with_shared(
        self,
        shared_source: str,
        override_local: bool = False,
        dry_run: bool = False
    ) -> Tuple[bool, List[str]]:
        """Sync local catalog with shared catalog."""
        print_header("Sync with Shared Catalog")
        
        # Load catalogs
        local = self.load_catalog()
        if not local:
            print_error("Failed to load local catalog")
            return False, []
        
        shared = self.load_shared_catalog(shared_source)
        if not shared:
            return False, []
        
        # Merge
        merged = self.merge_catalogs(local, shared, override_local)
        
        # Detect changes
        changes = self._detect_changes(local, merged)
        
        if not changes:
            print_success("No changes needed")
            return True, []
        
        # Display changes
        print_info(f"\nFound {len(changes)} changes:")
        for change in changes:
            print(f"  {change}")
        
        # Apply if not dry run
        if not dry_run:
            FileUtils.backup_file(self.catalog_path)
            self.save_catalog(merged)
            print_success("Catalog synchronized")
        else:
            print_info("Dry run - no changes applied")
        
        return True, changes
    
    def _detect_changes(self, old: Dict, new: Dict) -> List[str]:
        """Detect changes between catalogs."""
        changes = []
        
        for section in ['versions', 'libraries', 'plugins']:
            if section not in new:
                continue
            
            old_section = old.get(section, {})
            new_section = new[section]
            
            for key, new_value in new_section.items():
                old_value = old_section.get(key)
                
                if old_value != new_value:
                    if old_value is None:
                        changes.append(f"[{section}] + {key}: {new_value}")
                    else:
                        changes.append(f"[{section}] {key}: {old_value} -> {new_value}")
        
        return changes


# ============================================================================
# Maven Central Integration
# ============================================================================

class MavenCentralClient:
    """Client for Maven Central API."""
    
    @staticmethod
    def search_versions(group: str, artifact: str) -> Optional[List[Dict]]:
        """Search Maven Central for artifact versions."""
        url = MAVEN_CENTRAL_VERSIONS.format(group=group, artifact=artifact)
        
        try:
            with request.urlopen(url, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                if 'response' in data and 'docs' in data['response']:
                    return data['response']['docs']
                return None
        except Exception as e:
            print_error(f"Maven Central search failed: {e}")
            return None
    
    @staticmethod
    def get_latest_versions(
        group: str,
        artifact: str,
        stable_only: bool = True,
        limit: int = 10
    ) -> List[MavenArtifact]:
        """Get latest versions of artifact."""
        docs = MavenCentralClient.search_versions(group, artifact)
        
        if not docs:
            return []
        
        artifacts = []
        
        for doc in docs:
            version = doc.get('v')
            if not version:
                continue
            
            version_info = VersionInfo.parse(version)
            if not version_info:
                continue
            
            if stable_only and not version_info.is_stable():
                continue
            
            artifacts.append(MavenArtifact(
                group=group,
                artifact=artifact,
                version=version,
                timestamp=doc.get('timestamp')
            ))
        
        # Sort by version (newest first)
        artifacts.sort(
            key=lambda a: VersionInfo.parse(a.version),
            reverse=True
        )
        
        return artifacts[:limit]
    
    @staticmethod
    def check_for_updates(
        current_version: str,
        group: str,
        artifact: str,
        update_policy: str = "last-stable"
    ) -> Tuple[bool, Optional[str], List[str]]:
        """Check if updates available."""
        current = VersionInfo.parse(current_version)
        if not current:
            return False, None, []
        
        if update_policy == "pinned":
            return False, None, []
        
        stable_only = update_policy in ["last-stable", "major-only", "minor-only"]
        artifacts = MavenCentralClient.get_latest_versions(group, artifact, stable_only)
        
        if not artifacts:
            return False, None, []
        
        newer_versions = []
        recommended = None
        
        for artifact_item in artifacts:
            version = VersionInfo.parse(artifact_item.version)
            if not version or version.compare(current) <= 0:
                continue
            
            # Apply policy filters
            if update_policy == "major-only" and version.major == current.major:
                continue
            elif update_policy == "minor-only" and version.major != current.major:
                continue
            
            newer_versions.append(artifact_item.version)
            if not recommended:
                recommended = artifact_item.version
        
        return len(newer_versions) > 0, recommended, newer_versions
    
    @staticmethod
    def check_breaking_changes(current: str, new: str) -> Tuple[bool, str]:
        """Check if update contains breaking changes."""
        curr_ver = VersionInfo.parse(current)
        new_ver = VersionInfo.parse(new)
        
        if not curr_ver or not new_ver:
            return False, "Unable to parse versions"
        
        if new_ver.major > curr_ver.major:
            return True, f"Major version change: {curr_ver.major}.x -> {new_ver.major}.x"
        
        if curr_ver.is_stable() and not new_ver.is_stable():
            return True, f"Downgrade to pre-release: {new_ver.qualifier}"
        
        return False, "No breaking changes detected"


# ============================================================================
# Spring Boot BOM Integration
# ============================================================================

class SpringBootBOM:
    """Spring Boot BOM integration."""
    
    @staticmethod
    def download_bom(version: str) -> Optional[str]:
        """Download Spring Boot BOM POM."""
        url = SPRING_BOOT_BOM_URL.format(version=version)
        
        try:
            with request.urlopen(url, timeout=30) as response:
                return response.read().decode('utf-8')
        except Exception as e:
            print_error(f"Failed to download BOM: {e}")
            return None
    
    @staticmethod
    def parse_bom(pom_content: str) -> Dict[str, str]:
        """Parse BOM POM and extract versions."""
        versions = {}
        
        try:
            root = ET.fromstring(pom_content)
            ns = {'maven': 'http://maven.apache.org/POM/4.0.0'}
            
            # Extract properties
            properties = root.find('maven:properties', ns)
            if properties is not None:
                for prop in properties:
                    tag = prop.tag.split('}')[-1] if '}' in prop.tag else prop.tag
                    if tag.endswith('.version'):
                        lib_name = tag.replace('.version', '')
                        versions[lib_name] = prop.text
            
            return versions
        except Exception as e:
            print_error(f"Failed to parse BOM: {e}")
            return {}
    
    @staticmethod
    def sync_with_bom(
        catalog_manager: VersionCatalogManager,
        spring_boot_version: str,
        libraries: Optional[List[str]] = None,
        dry_run: bool = False
    ) -> Tuple[bool, List[str]]:
        """Sync version catalog with Spring Boot BOM."""
        print_header(f"Sync with Spring Boot {spring_boot_version} BOM")
        
        # Download and parse BOM
        pom = SpringBootBOM.download_bom(spring_boot_version)
        if not pom:
            return False, []
        
        bom_versions = SpringBootBOM.parse_bom(pom)
        if not bom_versions:
            return False, []
        
        # Map to common library names
        mapped = SpringBootBOM._map_versions(bom_versions)
        
        # Filter if specific libraries requested
        if libraries:
            mapped = {k: v for k, v in mapped.items() if k in libraries}
        
        # Update catalog
        catalog = catalog_manager.load_catalog()
        if not catalog:
            return False, []
        
        changes = []
        if 'versions' not in catalog:
            catalog['versions'] = {}
        
        for key, new_version in mapped.items():
            old_version = catalog['versions'].get(key)
            
            if old_version != new_version:
                catalog['versions'][key] = new_version
                change_msg = f"{key}: {old_version} -> {new_version}" if old_version else f"{key}: + {new_version}"
                changes.append(change_msg)
        
        if not changes:
            print_success("No updates needed")
            return True, []
        
        print_info(f"\nFound {len(changes)} updates:")
        for change in changes:
            print(f"  {change}")
        
        if not dry_run:
            FileUtils.backup_file(catalog_manager.catalog_path)
            catalog_manager.save_catalog(catalog)
            print_success("Catalog updated")
        else:
            print_info("Dry run - no changes applied")
        
        return True, changes
    
    @staticmethod
    def _map_versions(bom_versions: Dict[str, str]) -> Dict[str, str]:
        """Map BOM versions to catalog format."""
        mappings = {
            'jackson': 'jackson',
            'hibernate': 'hibernate',
            'netty': 'netty',
            'reactor': 'reactor',
            'slf4j': 'slf4j',
            'logback': 'logback',
            'junit-jupiter': 'junit-jupiter',
            'mockito': 'mockito',
            'assertj': 'assertj',
        }
        
        result = {}
        for catalog_key, bom_key in mappings.items():
            if bom_key in bom_versions:
                result[catalog_key] = bom_versions[bom_key]
        
        return result


# ============================================================================
# Configuration Manager
# ============================================================================

class ConfigManager:
    """Manages .gradleInit configuration."""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.config_path = project_dir / ".gradleInit"
    
    def load(self) -> Optional[GradleInitConfig]:
        """Load configuration from file."""
        if not self.config_path.exists():
            return None
        
        try:
            data = toml.load(self.config_path)
            
            # Parse dependencies
            deps_data = data.get('dependencies', {})
            
            # Shared catalog
            shared_catalog_data = deps_data.get('shared_catalog', {})
            shared_catalog = SharedCatalogConfig(**shared_catalog_data) if shared_catalog_data else SharedCatalogConfig()
            
            # Spring Boot
            spring_boot_data = deps_data.get('spring_boot', {})
            spring_boot = SpringBootConfig(**spring_boot_data) if spring_boot_data else SpringBootConfig()
            
            # Maven Central libraries
            maven_libs = [
                MavenCentralLibrary(**lib)
                for lib in deps_data.get('maven_central_libraries', [])
            ]
            
            dependencies = DependenciesConfig(
                strategy=deps_data.get('strategy', 'manual'),
                shared_catalog=shared_catalog,
                spring_boot=spring_boot,
                maven_central_enabled=deps_data.get('maven_central_enabled', True),
                maven_central_libraries=maven_libs
            )
            
            # Update config
            update_data = data.get('update', {})
            update = UpdateConfig(**update_data) if update_data else UpdateConfig()
            
            return GradleInitConfig(
                project_name=data.get('project_name', ''),
                project_version=data.get('project_version', '0.1.0-SNAPSHOT'),
                project_group=data.get('project_group', 'com.example'),
                gradle_version=data.get('gradle_version', '9.0'),
                kotlin_version=data.get('kotlin_version', '2.2.0'),
                jvm_target=data.get('jvm_target', '21'),
                template_source=data.get('template_source', GITHUB_TEMPLATE_URL),
                created=data.get('created', datetime.now().isoformat()),
                gradleInit_version=data.get('gradleInit_version', SCRIPT_VERSION),
                modules=data.get('modules', {}),
                dependencies=dependencies,
                update=update,
                metadata=data.get('metadata', {})
            )
        except Exception as e:
            print_error(f"Failed to load config: {e}")
            return None
    
    def save(self, config: GradleInitConfig) -> bool:
        """Save configuration to file."""
        try:
            # Convert to dict
            data = {
                'project_name': config.project_name,
                'project_version': config.project_version,
                'project_group': config.project_group,
                'gradle_version': config.gradle_version,
                'kotlin_version': config.kotlin_version,
                'jvm_target': config.jvm_target,
                'template_source': config.template_source,
                'created': config.created,
                'gradleInit_version': config.gradleInit_version,
                'modules': config.modules,
                'dependencies': {
                    'strategy': config.dependencies.strategy,
                    'shared_catalog': asdict(config.dependencies.shared_catalog),
                    'spring_boot': asdict(config.dependencies.spring_boot),
                    'maven_central_enabled': config.dependencies.maven_central_enabled,
                    'maven_central_libraries': [
                        asdict(lib) for lib in config.dependencies.maven_central_libraries
                    ]
                },
                'update': asdict(config.update),
                'metadata': config.metadata
            }
            
            # Write header
            with open(self.config_path, 'w') as f:
                f.write(f"# .gradleInit configuration\n")
                f.write(f"# Generated by gradleInit v{SCRIPT_VERSION}\n")
                f.write(f"# Created: {config.created}\n\n")
                toml.dump(data, f)
            
            print_success(f"Configuration saved: {self.config_path}")
            return True
        except Exception as e:
            print_error(f"Failed to save config: {e}")
            return False
    
    def generate_from_project(self) -> Optional[GradleInitConfig]:
        """Generate config from existing project."""
        print_info("Analyzing project...")
        
        # Read settings.gradle.kts
        settings_file = self.project_dir / "settings.gradle.kts"
        project_name = self.project_dir.name
        
        if settings_file.exists():
            content = settings_file.read_text()
            match = re.search(r'rootProject\.name\s*=\s*"([^"]+)"', content)
            if match:
                project_name = match.group(1)
        
        # Read gradle.properties
        props_file = self.project_dir / "gradle.properties"
        version = "0.1.0-SNAPSHOT"
        group = "com.example"
        
        if props_file.exists():
            for line in props_file.read_text().splitlines():
                if line.startswith('version='):
                    version = line.split('=', 1)[1].strip()
                elif line.startswith('group='):
                    group = line.split('=', 1)[1].strip()
        
        # Detect modules
        modules = {}
        for item in self.project_dir.iterdir():
            if item.is_dir() and (item / "build.gradle.kts").exists():
                build_file = item / "build.gradle.kts"
                content = build_file.read_text()
                
                is_app = 'application' in content or 'mainClass' in content
                module_type = "application" if is_app else "library"
                
                modules[item.name] = {
                    'type': module_type,
                    'convention_plugin': f"kotlin-{module_type}-conventions"
                }
        
        config = GradleInitConfig(
            project_name=project_name,
            project_version=version,
            project_group=group,
            modules=modules
        )
        
        print_success(f"Generated config for project: {project_name}")
        return config


# ============================================================================
# Update Manager
# ============================================================================

class UpdateManager:
    """Manages dependency updates."""
    
    def __init__(self, project_dir: Path, config: GradleInitConfig):
        self.project_dir = project_dir
        self.config = config
        self.catalog_manager = VersionCatalogManager(project_dir)
    
    def check_all_updates(self, dry_run: bool = False) -> Dict[str, Any]:
        """Check all configured updates."""
        print_header("Checking for Updates")
        
        results = {
            'spring_boot': None,
            'maven_central': [],
            'shared_catalog': None
        }
        
        # Check Spring Boot
        if self.config.dependencies.spring_boot.enabled:
            results['spring_boot'] = self._check_spring_boot_updates()
        
        # Check Maven Central libraries
        for lib in self.config.dependencies.maven_central_libraries:
            result = self._check_library_updates(lib)
            if result:
                results['maven_central'].append(result)
        
        # Check shared catalog
        if self.config.dependencies.shared_catalog.enabled:
            results['shared_catalog'] = self._check_shared_catalog_updates(dry_run)
        
        # Generate report
        self._generate_report(results)
        
        return results
    
    def _check_spring_boot_updates(self) -> Optional[Dict]:
        """Check Spring Boot updates."""
        current = self.config.dependencies.spring_boot.version
        mode = self.config.dependencies.spring_boot.compatibility_mode
        
        if mode == "pinned":
            return None
        
        print_info(f"Checking Spring Boot updates (current: {current})...")
        
        # For now, return placeholder
        # In real implementation, would check Maven Central
        return {
            'current': current,
            'recommended': current,
            'available': []
        }
    
    def _check_library_updates(self, lib: MavenCentralLibrary) -> Optional[Dict]:
        """Check library updates."""
        has_update, recommended, newer = MavenCentralClient.check_for_updates(
            lib.version,
            lib.group,
            lib.artifact,
            lib.update_policy
        )
        
        if not has_update:
            return None
        
        is_breaking, reason = MavenCentralClient.check_breaking_changes(
            lib.version,
            recommended
        )
        
        return {
            'library': f"{lib.group}:{lib.artifact}",
            'current': lib.version,
            'recommended': recommended,
            'policy': lib.update_policy,
            'breaking': is_breaking,
            'breaking_reason': reason if is_breaking else None,
            'newer_versions': newer[:3]
        }
    
    def _check_shared_catalog_updates(self, dry_run: bool) -> Optional[Dict]:
        """Check shared catalog updates."""
        source = self.config.dependencies.shared_catalog.source
        
        if not source:
            return None
        
        success, changes = self.catalog_manager.sync_with_shared(
            source,
            self.config.dependencies.shared_catalog.override_local,
            dry_run=True  # Always dry run for check
        )
        
        return {
            'source': source,
            'changes': changes,
            'success': success
        }
    
    def _generate_report(self, results: Dict[str, Any]):
        """Generate and print update report."""
        print_header("Update Report")
        
        total_updates = 0
        breaking_changes = 0
        
        # Maven Central updates
        if results['maven_central']:
            print_info("\nMaven Central Libraries:")
            for update in results['maven_central']:
                total_updates += 1
                if update['breaking']:
                    breaking_changes += 1
                
                print(f"\n  {update['library']}")
                print(f"    Current:     {update['current']}")
                print(f"    Recommended: {update['recommended']}")
                print(f"    Policy:      {update['policy']}")
                
                if update['breaking']:
                    print_warning(f"    Breaking:    {update['breaking_reason']}")
        
        # Shared catalog
        if results['shared_catalog'] and results['shared_catalog']['changes']:
            print_info(f"\nShared Catalog ({results['shared_catalog']['source']}):")
            for change in results['shared_catalog']['changes'][:5]:
                print(f"    {change}")
        
        # Summary
        print_header("Summary")
        print(f"  Total updates available: {total_updates}")
        if breaking_changes > 0:
            print_warning(f"  Breaking changes: {breaking_changes}")
        
        if total_updates == 0:
            print_success("  All dependencies are up to date!")


# ============================================================================
# Self-Update
# ============================================================================

class SelfUpdater:
    """Handles script self-updates."""
    
    @staticmethod
    def update(dry_run: bool = False, force: bool = False) -> bool:
        """Update script from GitHub."""
        print_header("Self Update")
        
        script_path = Path(__file__).resolve()
        temp_script = script_path.parent / f".{script_path.name}.tmp"
        
        try:
            if not FileUtils.download_file(GITHUB_RAW_URL, temp_script):
                return False
            
            # Extract version
            content = temp_script.read_text()
            version_match = re.search(r'SCRIPT_VERSION\s*=\s*["\']([^"\']+)["\']', content)
            remote_version = version_match.group(1) if version_match else "unknown"
            
            print_info(f"Current version: {SCRIPT_VERSION}")
            print_info(f"Remote version: {remote_version}")
            
            if not force and remote_version == SCRIPT_VERSION:
                print_success("Already up to date!")
                temp_script.unlink()
                return True
            
            if dry_run:
                print_info(f"Would update from {SCRIPT_VERSION} to {remote_version}")
                temp_script.unlink()
                return True
            
            # Validate Python syntax
            try:
                compile(content, str(temp_script), 'exec')
            except SyntaxError as e:
                print_error(f"Downloaded script has syntax errors: {e}")
                temp_script.unlink()
                return False
            
            # Backup and replace
            backup = FileUtils.backup_file(script_path)
            shutil.copy2(temp_script, script_path)
            temp_script.unlink()
            
            if os.name != 'nt':
                os.chmod(script_path, 0o755)
            
            print_success(f"Updated from {SCRIPT_VERSION} to {remote_version}")
            if backup:
                print_info(f"Backup: {backup}")
            print_info("Restart script to use new version")
            
            return True
        except Exception as e:
            print_error(f"Self-update failed: {e}")
            if temp_script.exists():
                temp_script.unlink()
            return False


# ============================================================================
# Project Creator (Simplified for now)
# ============================================================================

class ProjectCreator:
    """Creates new Gradle projects."""
    
    @staticmethod
    def create_simple_project(
        project_name: str,
        group: str,
        version: str,
        save_config: bool = False
    ) -> bool:
        """Create a simple project structure."""
        print_header(f"Creating Project: {project_name}")
        
        project_dir = Path.cwd() / project_name
        
        if project_dir.exists():
            print_error(f"Directory already exists: {project_name}")
            return False
        
        try:
            project_dir.mkdir()
            
            # Create basic structure
            (project_dir / "gradle").mkdir()
            
            # Create settings.gradle.kts
            settings_content = f'rootProject.name = "{project_name}"\n'
            (project_dir / "settings.gradle.kts").write_text(settings_content)
            
            # Create gradle.properties
            props_content = f"""version={version}
group={group}

org.gradle.jvmargs=-Xmx2048m
org.gradle.parallel=true
org.gradle.caching=true
"""
            (project_dir / "gradle.properties").write_text(props_content)
            
            print_success(f"Project created: {project_name}")
            
            # Save config if requested
            if save_config:
                config = GradleInitConfig(
                    project_name=project_name,
                    project_version=version,
                    project_group=group
                )
                ConfigManager(project_dir).save(config)
            
            return True
        except Exception as e:
            print_error(f"Failed to create project: {e}")
            return False


# ============================================================================
# CLI Interface
# ============================================================================

def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        description="gradleInit - Modern Kotlin/Gradle Project Initializer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create project
  %(prog)s my-project --group com.example
  
  # With config
  %(prog)s my-project --save-config
  
  # Self-update
  %(prog)s --self-update
  
  # Check updates
  %(prog)s --check-updates
  
  # Sync with shared catalog
  %(prog)s --sync-shared-catalog https://example.com/catalog.toml
  
  # Generate config from existing project
  %(prog)s --generate-config
        """
    )
    
    # Project creation
    parser.add_argument('project_name', nargs='?', help="Project name")
    parser.add_argument('--group', default='com.example', help="Group ID")
    parser.add_argument('--version', default='0.1.0-SNAPSHOT', help="Project version")
    parser.add_argument('--save-config', action='store_true', help="Save .gradleInit config")
    
    # Update commands
    parser.add_argument('--self-update', action='store_true', help="Update script from GitHub")
    parser.add_argument('--check-updates', action='store_true', help="Check for dependency updates")
    parser.add_argument('--dry-run', action='store_true', help="Show changes without applying")
    parser.add_argument('--force', action='store_true', help="Force operation")
    
    # Config commands
    parser.add_argument('--show-config', action='store_true', help="Show current config")
    parser.add_argument('--generate-config', action='store_true', help="Generate config from project")
    
    # Shared catalog
    parser.add_argument('--sync-shared-catalog', metavar='SOURCE', help="Sync with shared catalog (URL or file)")
    
    # Spring Boot
    parser.add_argument('--sync-spring-boot', metavar='VERSION', help="Sync with Spring Boot BOM")
    
    # Version
    parser.add_argument('--version-info', action='version', version=f'%(prog)s {SCRIPT_VERSION}')
    
    return parser


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Self-update
    if args.self_update:
        sys.exit(0 if SelfUpdater.update(args.dry_run, args.force) else 1)
    
    # Show config
    if args.show_config:
        config_manager = ConfigManager(Path.cwd())
        config = config_manager.load()
        
        if config:
            print_header("Current Configuration")
            print(f"Project: {config.project_name} v{config.project_version}")
            print(f"Group: {config.project_group}")
            print(f"Kotlin: {config.kotlin_version}")
            print(f"Created: {config.created}")
            
            if config.dependencies.shared_catalog.enabled:
                print(f"\nShared Catalog: {config.dependencies.shared_catalog.source}")
            
            if config.dependencies.spring_boot.enabled:
                print(f"\nSpring Boot: {config.dependencies.spring_boot.version}")
        else:
            print_warning("No .gradleInit config found")
        
        sys.exit(0)
    
    # Generate config
    if args.generate_config:
        config_manager = ConfigManager(Path.cwd())
        config = config_manager.generate_from_project()
        
        if config:
            config_manager.save(config)
        
        sys.exit(0 if config else 1)
    
    # Check updates
    if args.check_updates:
        config_manager = ConfigManager(Path.cwd())
        config = config_manager.load()
        
        if not config:
            print_warning("No .gradleInit config found. Run with --generate-config first.")
            sys.exit(1)
        
        update_manager = UpdateManager(Path.cwd(), config)
        update_manager.check_all_updates(args.dry_run)
        sys.exit(0)
    
    # Sync shared catalog
    if args.sync_shared_catalog:
        catalog_manager = VersionCatalogManager(Path.cwd())
        success, changes = catalog_manager.sync_with_shared(
            args.sync_shared_catalog,
            override_local=False,
            dry_run=args.dry_run
        )
        sys.exit(0 if success else 1)
    
    # Sync Spring Boot
    if args.sync_spring_boot:
        catalog_manager = VersionCatalogManager(Path.cwd())
        success, changes = SpringBootBOM.sync_with_bom(
            catalog_manager,
            args.sync_spring_boot,
            dry_run=args.dry_run
        )
        sys.exit(0 if success else 1)
    
    # Create project
    if args.project_name:
        success = ProjectCreator.create_simple_project(
            args.project_name,
            args.group,
            args.version,
            args.save_config
        )
        sys.exit(0 if success else 1)
    
    # No command - show help
    parser.print_help()
    sys.exit(0)


if __name__ == "__main__":
    main()
