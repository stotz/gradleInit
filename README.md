# gradleInit v1.1.0 - Complete Documentation

## Overview

**gradleInit v1.1.0** is a complete rewrite in modern, modular Python with all features in a single file. It combines professional software engineering with practical usability.

## Architecture

### Design Principles

1. **Single File** - Everything in one `gradleInit.py`
2. **Modular** - Clear class separation and responsibilities
3. **Object-Oriented** - Classes for major components
4. **Testable** - Methods designed for easy unit testing
5. **Type-Safe** - Dataclasses with type hints
6. **Modern Python** - Python 3.7+ features

### Class Structure

```
gradleInit.py (1600+ lines)
├── Utilities
│   ├── Color                     # Terminal colors
│   ├── FileUtils                 # File operations
│   └── CommandRunner             # Command execution
│
├── Data Classes
│   ├── VersionInfo               # Semantic versioning
│   ├── MavenArtifact            # Maven artifacts
│   ├── SharedCatalogConfig      # Shared catalog config
│   ├── MavenCentralLibrary      # Library tracking
│   ├── SpringBootConfig         # Spring Boot settings
│   ├── DependenciesConfig       # Dependencies config
│   ├── UpdateConfig             # Update preferences
│   └── GradleInitConfig         # Complete config
│
├── Managers
│   ├── VersionCatalogManager    # Version catalog operations
│   ├── ConfigManager            # .gradleInit config
│   ├── UpdateManager            # Update coordination
│   └── SelfUpdater              # Script self-update
│
├── Integrations
│   ├── MavenCentralClient       # Maven Central API
│   ├── SpringBootBOM            # Spring Boot BOM
│   └── ProjectCreator           # Project creation
│
└── CLI
    ├── create_parser()          # Argument parser
    └── main()                   # Entry point
```

## Features

### 1. Shared Version Catalog

Use a shared `libs.versions.toml` from URL or file for all projects:

```bash
# From URL
gradleInit --sync-shared-catalog https://company.com/shared-catalog.toml

# From local file
gradleInit --sync-shared-catalog ~/company/shared-catalog.toml

# From network drive
gradleInit --sync-shared-catalog //fileserver/shared/catalog.toml
```

**Configuration in .gradleInit:**

```toml
[dependencies.shared_catalog]
enabled = true
source = "https://company.com/shared-catalog.toml"
sync_on_update = true
override_local = false  # Keep local overrides
```

**Use Cases:**

1. **Company-wide Standards**
   ```toml
   # Company shared-catalog.toml
   [versions]
   kotlin = "2.2.0"
   jackson = "2.18.2"
   
   # All company projects use same versions
   ```

2. **Team Conventions**
   ```bash
   # Team lead maintains catalog on GitHub
   # Team members sync: gradleInit --sync-shared-catalog <url>
   ```

3. **Multi-Project Coordination**
   ```bash
   # Microservices share versions from central file
   # Update once, sync everywhere
   ```

### 2. Maven Central Integration

Automatic updates from Maven Central with intelligent policies:

```python
# Check single library
maven_client = MavenCentralClient()
has_update, recommended, newer = maven_client.check_for_updates(
    current_version="3.0.1",
    group="io.ktor",
    artifact="ktor-server-core",
    update_policy="last-stable"
)
```

**Update Policies:**

- **pinned**: Never update
- **last-stable**: Latest stable (no RC/SNAPSHOT)
- **latest**: Including pre-releases
- **major-only**: Only major versions
- **minor-only**: Only minor/patch

**Breaking Change Detection:**

```python
is_breaking, reason = MavenCentralClient.check_breaking_changes(
    "2.3.0",  # Current
    "3.0.0"   # New
)
# (True, "Major version change: 2.x -> 3.x")
```

### 3. Spring Boot BOM Sync

Sync with Spring Boot's tested dependency versions:

```bash
# Sync all compatible versions
gradleInit --sync-spring-boot 3.5.7

# Dry run first
gradleInit --sync-spring-boot 3.5.7 --dry-run
```

**What it syncs:**

- Jackson (2.18.2)
- Hibernate (6.6.4.Final)
- Netty (4.1.115.Final)
- Reactor
- SLF4J, Logback
- JUnit, Mockito
- And 600+ more

### 4. .gradleInit Configuration

Persistent project configuration:

```toml
# .gradleInit
project_name = "my-api"
project_version = "1.0.0"
project_group = "com.company"

[dependencies.shared_catalog]
enabled = true
source = "https://company.com/catalog.toml"
override_local = false

[dependencies.spring_boot]
enabled = true
version = "3.5.7"
compatibility_mode = "last-stable"

[[dependencies.maven_central_libraries]]
group = "io.ktor"
artifact = "ktor-server-core"
version = "3.0.1"
update_policy = "last-stable"

[update]
auto_check = true
check_interval = "weekly"
notify_breaking_changes = true
```

### 5. Intelligent Update Management

Coordinated updates across all sources:

```bash
# Check all configured updates
gradleInit --check-updates

# Output:
# === Checking for Updates ===
#
# Maven Central Libraries:
#
#   io.ktor:ktor-server-core
#     Current:     3.0.1
#     Recommended: 3.0.2
#     Policy:      last-stable
#
# Shared Catalog (https://company.com/catalog.toml):
#     [versions] kotlin: 2.1.0 -> 2.2.0
#     [versions] jackson: 2.17.0 -> 2.18.2
#
# === Summary ===
#   Total updates available: 3
#   Breaking changes: 0
```

## Usage Examples

### Example 1: Create Project with Shared Catalog

```bash
# Create project
gradleInit my-api --group com.company --save-config

cd my-api

# Configure shared catalog in .gradleInit
cat >> .gradleInit << EOF
[dependencies.shared_catalog]
enabled = true
source = "https://company.com/shared-catalog.toml"
sync_on_update = true
EOF

# Initial sync
gradleInit --sync-shared-catalog https://company.com/shared-catalog.toml

# Weekly updates
gradleInit --check-updates
```

### Example 2: Multi-Project Setup

```bash
# Setup 3 microservices with shared catalog

# Shared catalog on fileserver
SHARED_CATALOG="//fileserver/shared/microservices-catalog.toml"

# Service 1
gradleInit user-service --save-config
cd user-service
gradleInit --sync-shared-catalog "$SHARED_CATALOG"
cd ..

# Service 2
gradleInit order-service --save-config
cd order-service
gradleInit --sync-shared-catalog "$SHARED_CATALOG"
cd ..

# Service 3
gradleInit payment-service --save-config
cd payment-service
gradleInit --sync-shared-catalog "$SHARED_CATALOG"
cd ..

# Update shared catalog once
# All services sync: gradleInit --sync-shared-catalog "$SHARED_CATALOG"
```

### Example 3: Existing Project Migration

```bash
cd my-existing-project

# Generate .gradleInit from project
gradleInit --generate-config

# Configure Maven Central tracking
cat >> .gradleInit << EOF
[[dependencies.maven_central_libraries]]
group = "io.ktor"
artifact = "ktor-server-core"
version = "3.0.1"
update_policy = "last-stable"

[[dependencies.maven_central_libraries]]
group = "io.insert-koin"
artifact = "koin-core"
version = "4.0.0"
update_policy = "minor-only"
EOF

# Check for updates
gradleInit --check-updates
```

### Example 4: Spring Boot Project

```bash
# Create project
gradleInit spring-api --group com.company --save-config

cd spring-api

# Configure Spring Boot in .gradleInit
cat >> .gradleInit << EOF
[dependencies.spring_boot]
enabled = true
version = "3.5.7"
compatibility_mode = "last-stable"
starters = ["web", "data-jpa", "security"]
EOF

# Sync with Spring Boot BOM
gradleInit --sync-spring-boot 3.5.7

# Check for Spring Boot updates
gradleInit --check-updates
```

### Example 5: Conservative Production Setup

```bash
gradleInit production-service --save-config

# Conservative config
cat > .gradleInit << EOF
project_name = "production-service"
project_version = "2.5.0"
project_group = "com.company"

[dependencies]
strategy = "manual"

[dependencies.shared_catalog]
enabled = false

[dependencies.spring_boot]
enabled = true
version = "3.4.5"  # Not latest, but stable
compatibility_mode = "pinned"  # Don't auto-update

[[dependencies.maven_central_libraries]]
group = "io.ktor"
artifact = "ktor-server-core"
version = "2.3.5"
update_policy = "minor-only"  # Only patches

[update]
auto_check = false
notify_breaking_changes = true
EOF
```

## Code Quality

### Object-Oriented Design

**Clear Responsibilities:**

```python
# Version Catalog - manages TOML files
catalog_manager = VersionCatalogManager(project_dir)
catalog_manager.sync_with_shared(source, override_local)

# Maven Central - API client
maven_client = MavenCentralClient()
maven_client.get_latest_versions(group, artifact)

# Config - persistence
config_manager = ConfigManager(project_dir)
config_manager.save(config)

# Updates - coordination
update_manager = UpdateManager(project_dir, config)
update_manager.check_all_updates()
```

### Dataclasses

Type-safe configuration:

```python
@dataclass
class GradleInitConfig:
    """Complete configuration with type hints."""
    project_name: str
    project_version: str = "0.1.0-SNAPSHOT"
    dependencies: DependenciesConfig = field(default_factory=DependenciesConfig)
    
# Usage
config = GradleInitConfig(
    project_name="my-api",
    project_group="com.company"
)
```

### Error Handling

Graceful failures:

```python
def load_catalog(self) -> Optional[Dict]:
    """Load catalog, return None on failure."""
    try:
        return toml.load(self.catalog_path)
    except Exception as e:
        print_error(f"Failed to load catalog: {e}")
        return None
```

### Modularity

Easy to test:

```python
# Test version parsing
version = VersionInfo.parse("3.5.7-RC2")
assert version.major == 3
assert not version.is_stable()

# Test version comparison
v1 = VersionInfo.parse("3.0.1")
v2 = VersionInfo.parse("3.1.0")
assert v1.compare(v2) == -1

# Test Maven Central client
artifacts = MavenCentralClient.get_latest_versions(
    "io.ktor",
    "ktor-server-core",
    stable_only=True
)
assert len(artifacts) > 0
```

## CLI Reference

### Project Creation

```bash
# Basic project
gradleInit my-project

# With config
gradleInit my-project --group com.company --save-config

# Specify version
gradleInit my-project --version 1.0.0
```

### Configuration

```bash
# Show current config
gradleInit --show-config

# Generate from existing project
gradleInit --generate-config
```

### Updates

```bash
# Check all updates
gradleInit --check-updates

# Dry run
gradleInit --check-updates --dry-run
```

### Shared Catalog

```bash
# Sync from URL
gradleInit --sync-shared-catalog https://example.com/catalog.toml

# Sync from file
gradleInit --sync-shared-catalog ~/shared/catalog.toml

# Dry run
gradleInit --sync-shared-catalog <source> --dry-run
```

### Spring Boot

```bash
# Sync with Spring Boot BOM
gradleInit --sync-spring-boot 3.5.7

# Dry run
gradleInit --sync-spring-boot 3.5.7 --dry-run
```

### Self-Update

```bash
# Check for script updates
gradleInit --self-update --dry-run

# Update script
gradleInit --self-update

# Force update
gradleInit --self-update --force
```

## Integration Examples

### GitHub Actions

```yaml
name: Dependency Updates

on:
  schedule:
    - cron: '0 0 * * 1'  # Weekly
  workflow_dispatch:

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install toml
      
      - name: Check updates
        run: |
          python gradleInit.py --check-updates > updates.txt
      
      - name: Create PR
        if: ${{ hashFiles('updates.txt') != '' }}
        uses: peter-evans/create-pull-request@v5
        with:
          title: 'chore: dependency updates available'
          body-path: updates.txt
```

### Pre-Commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Check for updates weekly
LAST_CHECK=$(cat .last-update-check 2>/dev/null || echo 0)
NOW=$(date +%s)
WEEK=604800

if [ $((NOW - LAST_CHECK)) -gt $WEEK ]; then
    echo "Checking for updates..."
    python gradleInit.py --check-updates --dry-run
    echo $NOW > .last-update-check
fi
```

## Best Practices

### 1. Shared Catalog Workflow

```bash
# Central team maintains catalog
# shared-catalog.toml on GitHub/fileserver

# Projects reference it
[dependencies.shared_catalog]
enabled = true
source = "https://company.com/shared-catalog.toml"
override_local = false  # Company versions take precedence

# Weekly sync
gradleInit --check-updates  # Includes shared catalog check
```

### 2. Update Policy Guidelines

**Production:**
```toml
update_policy = "minor-only"  # Conservative
compatibility_mode = "pinned"  # No auto-updates
```

**Development:**
```toml
update_policy = "last-stable"  # Latest stable
compatibility_mode = "last-stable"  # Auto-update
```

### 3. Breaking Change Management

```bash
# Always check updates in dry-run first
gradleInit --check-updates --dry-run

# Review breaking changes
# If breaking: test in feature branch

git checkout -b update/dependencies
gradleInit --check-updates  # Apply
./gradlew clean build test
# If success: create PR
```

## Troubleshooting

### Shared Catalog Not Loading

```bash
# Check URL is accessible
curl -I https://company.com/catalog.toml

# Check file exists
ls -la ~/shared/catalog.toml

# Check TOML syntax
python -c "import toml; toml.load(open('catalog.toml'))"
```

### Maven Central API Errors

```bash
# Check network
curl -I https://search.maven.org

# Increase timeout in code if needed
# Or use corporate Maven mirror
```

### Config Validation

```bash
# Show current config
gradleInit --show-config

# Regenerate if corrupt
mv .gradleInit .gradleInit.backup
gradleInit --generate-config
```

## Summary

gradleInit v1.1.0 provides:

- ✅ **Single File** - Easy deployment
- ✅ **Modular** - Clean class structure
- ✅ **Shared Catalogs** - URL or file based
- ✅ **Smart Updates** - Maven Central + Spring Boot
- ✅ **Persistent Config** - .gradleInit file
- ✅ **Breaking Detection** - Semantic versioning
- ✅ **Professional Code** - OO, testable, modern

**All in 1600 lines of well-organized Python!**
