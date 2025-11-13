# gradleInit.py

> Modern Kotlin/Gradle Project Initializer with intelligent dependency management

A comprehensive tool for creating and managing Kotlin/Gradle multiproject builds with Jinja2 templating, Maven Central integration, Spring Boot BOM support, and team-wide version catalogs.

[![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)](https://github.com/stotz/gradleInit)
[![Python](https://img.shields.io/badge/python-3.7+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

## Features

- 🎨 **Jinja2 Templates** - Full template engine with custom filters
- 📦 **Custom URLs** - GitHub, HTTPS, or local file templates
- 🔄 **Shared Catalogs** - Team-wide version management
- 🌐 **Maven Central** - Auto-updates with breaking-change detection
- 🍃 **Spring Boot BOM** - 600+ tested dependencies
- ⚙️ **Smart Config** - Priority: CLI > ENV > .gradleInit
- 📊 **Update Manager** - Coordinated updates from all sources
- 🔧 **Self-Update** - Script updates itself

## Quick Start

### Install

```bash
# Install dependencies
pip install jinja2 toml

# Make executable
chmod +x gradleInit.py
```

### Create Your First Project

```bash
# Simple project
./gradleInit.py init my-project

# With custom settings
./gradleInit.py init my-project \
  --group com.mycompany \
  --version 1.0.0 \
  --gradle-version 9.0 \
  --kotlin-version 2.2.0
```

### Use Custom Templates

```bash
# GitHub template
./gradleInit.py init my-project \
  --template https://github.com/user/gradle-template.git \
  --template-version v1.2.0

# Local template
./gradleInit.py init my-project \
  --template file:///path/to/template
```

## Configuration

### Create .gradleInit

Create `~/.gradleInit` for persistent settings:

```toml
[template]
url = "https://github.com/stotz/gradleInit.git"
version = "main"

[defaults]
group = "com.mycompany"
version = "0.1.0"

[versions]
gradle = "9.0"
kotlin = "2.2.0"
jdk = "21"

[constraints]
gradle_version = ">=9.0"
kotlin_version = "~2.2.0"
jdk_version = ">=21"

# Shared version catalog for teams
[dependencies.shared_catalog]
enabled = true
source = "https://github.com/myorg/shared-catalog/raw/main/libs.versions.toml"
sync_on_update = true
override_local = false

# Track Maven Central libraries
[[dependencies.maven_central.libraries]]
group = "io.ktor"
artifact = "ktor-server-core"
version = "3.0.1"
update_policy = "last-stable"

# Spring Boot BOM integration
[dependencies.spring_boot]
enabled = true
version = "3.5.7"
compatibility_mode = "last-stable"

# Auto-update settings
[updates]
auto_check = true
check_interval = "weekly"

[custom]
author = "Your Name"
license = "MIT"
```

### Environment Variables

```bash
export GRADLE_INIT_TEMPLATE="https://github.com/myorg/template.git"
export GRADLE_INIT_GROUP="com.mycompany"
export GRADLE_VERSION="9.0"
export KOTLIN_VERSION="2.2.0"
```

With defaults:
```bash
export GRADLE_VERSION="${GRADLE_VERSION:-9.0}"
export MY_VAR="${MY_VAR:-default}"
```

## Advanced Features

### Shared Version Catalog

Perfect for teams to share dependency versions across projects:

```toml
[dependencies.shared_catalog]
enabled = true
source = "https://github.com/company/catalog/raw/main/libs.versions.toml"
# or local: source = "file:///mnt/share/gradle-catalog.toml"
```

**Benefits:**
- ✅ Centralized version management
- ✅ Consistent dependencies across projects
- ✅ Easy updates for entire team
- ✅ Local overrides when needed

### Maven Central Integration

Automatic dependency updates with intelligent policies:

```toml
[[dependencies.maven_central.libraries]]
group = "io.ktor"
artifact = "ktor-server-core"
version = "3.0.1"
update_policy = "last-stable"
```

**Update Policies:**
- `pinned` - Never update
- `last-stable` - Latest stable version
- `latest` - Including pre-releases
- `major-only` - Major versions only
- `minor-only` - Minor/patch versions only

**Check for updates:**
```bash
./gradleInit.py update --check
```

**Output:**
```
Update Report
Generated: 2025-01-15T15:30:00

Maven Central Updates:
  ✓ io.ktor:ktor-server-core: 3.0.1 → 3.0.2
  ⚠ com.example:lib: 2.5.0 → 3.0.0 [BREAKING]
  → other-lib:module: Up to date
```

### Spring Boot BOM

Use Spring Boot's 600+ tested dependencies:

```toml
[dependencies.spring_boot]
enabled = true
version = "3.5.7"
compatibility_mode = "last-stable"
```

**Sync to project:**
```bash
./gradleInit.py update --sync-spring-boot 3.5.7
```

**Compatibility Modes:**
- `pinned` - Fixed version
- `last-stable` - Latest stable
- `latest` - Including pre-releases

### Version Constraints

Enforce version requirements with semantic versioning:

```toml
[constraints]
gradle_version = ">=9.0"      # Minimum 9.0
kotlin_version = "~2.2.0"     # 2.2.x only
jdk_version = "21.*"          # 21.0, 21.1, etc.
```

**Supported operators:**
- `>=`, `<=`, `>`, `<` - Comparison
- `~` - Tilde range (patch-level updates)
- `*` - Wildcard
- `==` - Exact match

## Template Development

### Template Structure

```
my-template/
├── settings.gradle.kts.j2
├── build.gradle.kts.j2
├── gradle.properties.j2
├── .gitignore.j2
├── README.md.j2
└── src/
    ├── main/kotlin/
    │   └── Main.kt.j2
    └── test/kotlin/
        └── MainTest.kt.j2
```

### Jinja2 Syntax

**Variables:**
```kotlin
// build.gradle.kts.j2
group = "{{ project_group }}"
version = "{{ project_version }}"

kotlin {
    jvmToolchain({{ jdk_version }})
}
```

**Custom Filters:**
```kotlin
// Main.kt.j2
package {{ project_group }}

class {{ project_name|pascalCase }} {
    fun greet() {
        println("Hello from {{ project_name|kebabCase }}!")
    }
}
```

Available filters: `camelCase`, `pascalCase`, `snakeCase`, `kebabCase`

**Environment Variables:**
```yaml
# .github/workflows/ci.yml.j2
env:
  DOCKER_REGISTRY: {{ env('DOCKER_REGISTRY', 'docker.io') }}
  BUILD_NUMBER: {{ env('BUILD_NUMBER', '0') }}
```

**Config Values:**
```kotlin
// build.gradle.kts.j2
description = "{{ config('custom.description', 'A Kotlin project') }}"

tasks.jar {
    manifest {
        attributes(
            "Implementation-Vendor" to "{{ config('custom.author', 'Unknown') }}"
        )
    }
}
```

**Conditionals:**
```kotlin
plugins {
    kotlin("jvm") version "{{ kotlin_version }}"
    {% if config('spring.enabled', false) %}
    id("org.springframework.boot") version "{{ config('spring.version', '3.2.0') }}"
    {% endif %}
}
```

**Loops:**
```kotlin
// settings.gradle.kts.j2
rootProject.name = "{{ project_name }}"

{% for module in config('modules', []) %}
include("{{ module }}")
{% endfor %}
```

### Template Context

Available variables:
```python
{
    'project_name': 'my-project',
    'project_group': 'com.example',
    'project_version': '0.1.0',
    'gradle_version': '9.0',
    'kotlin_version': '2.2.0',
    'jdk_version': '21',
    'timestamp': '2025-01-15T10:30:00',
    # Plus all values from [custom] section
}
```

## CLI Reference

### Commands

**Initialize Project:**
```bash
gradleInit.py init <name> [options]
  --template <url>           # Template source
  --template-version <ver>   # Branch/tag/commit
  --group <group>            # Maven group ID
  --version <version>        # Project version
  --gradle-version <ver>     # Gradle version
  --kotlin-version <ver>     # Kotlin version
  --jdk-version <ver>        # JDK version
  --dir <path>               # Target directory
```

**Manage Configuration:**
```bash
gradleInit.py config [options]
  --show                     # Show current config
  --template <url>           # Set template URL
  --group <group>            # Set default group
  --constraint <n> <ver>     # Add version constraint
```

**Update Management:**
```bash
gradleInit.py update [options]
  --check                    # Check all updates
  --sync-shared              # Sync shared catalog
  --sync-spring-boot <ver>   # Sync Spring Boot BOM
  --self-update              # Update gradleInit itself
```

## Use Cases

### 1. Solo Developer

```bash
# One-time setup
./gradleInit.py config \
  --template https://github.com/me/template.git \
  --group com.myname

# Create projects
./gradleInit.py init my-app
./gradleInit.py init my-lib
```

### 2. Team with Shared Catalog

**Admin creates shared catalog:**
```bash
# Create shared-catalog.toml
cat > shared-catalog.toml << EOF
[versions]
kotlin = "2.2.0"
ktor = "3.0.2"

[libraries]
ktor-server = { group = "io.ktor", name = "ktor-server-core", version.ref = "ktor" }
EOF

# Commit to company repo
git add shared-catalog.toml
git commit -m "Add shared Gradle catalog"
git push
```

**Developers use it:**
```bash
# Configure
./gradleInit.py config \
  --template https://github.com/company/template.git

# Add to ~/.gradleInit:
[dependencies.shared_catalog]
enabled = true
source = "https://github.com/company/shared-catalog/raw/main/shared-catalog.toml"

# Projects automatically use shared catalog
./gradleInit.py init customer-service
./gradleInit.py init payment-service
```

### 3. Maven Central Tracking

```bash
# Configure tracked libraries
cat >> ~/.gradleInit << EOF
[[dependencies.maven_central.libraries]]
group = "io.ktor"
artifact = "ktor-server-core"
version = "3.0.1"
update_policy = "last-stable"

[[dependencies.maven_central.libraries]]
group = "com.fasterxml.jackson.core"
artifact = "jackson-databind"
version = "2.17.0"
update_policy = "minor-only"
EOF

# Weekly auto-checks
[updates]
auto_check = true
check_interval = "weekly"

# Manual check
./gradleInit.py update --check
```

### 4. Spring Boot Projects

```bash
# Configure Spring Boot
[dependencies.spring_boot]
enabled = true
version = "3.5.7"
compatibility_mode = "last-stable"

# Create Spring Boot project
./gradleInit.py init my-spring-app

# Sync BOM manually
./gradleInit.py update --sync-spring-boot 3.5.7
```

## Architecture

### Class Overview

**Version Handling:**
- `VersionInfo` - Semantic version parser
- `VersionConstraint` - Constraint validator

**Maven Integration:**
- `MavenArtifact` - Artifact model
- `MavenCentralClient` - REST API client

**Spring Boot:**
- `SpringBootBOM` - BOM download & parse

**Configuration:**
- `SharedCatalogConfig` - Shared catalog settings
- `MavenCentralLibrary` - Library tracking model
- `GradleInitConfig` - Master configuration

**Managers:**
- `SharedCatalogManager` - Catalog operations
- `UpdateManager` - Update coordination
- `SelfUpdater` - Script updates

**Template Engine:**
- `TemplateEngine` - Jinja2 integration
- `TemplateSource` - URL/file handler

**Project Creation:**
- `GradleInitializer` - Main orchestrator

### Code Quality

✅ **Modern Python** - Type hints, dataclasses, Python 3.7+  
✅ **OOP Design** - Clear responsibilities, testable  
✅ **Single File** - 1476 lines, well-organized  
✅ **Error Handling** - Graceful degradation  
✅ **Documentation** - Docstrings everywhere  

## Examples

### Minimal Template

```
minimal-template/
├── settings.gradle.kts.j2
└── build.gradle.kts.j2
```

**settings.gradle.kts.j2:**
```kotlin
rootProject.name = "{{ project_name }}"
```

**build.gradle.kts.j2:**
```kotlin
plugins {
    kotlin("jvm") version "{{ kotlin_version }}"
}

group = "{{ project_group }}"
version = "{{ project_version }}"

repositories {
    mavenCentral()
}

dependencies {
    testImplementation(kotlin("test"))
}
```

### Multimodule Template

```
multimodule-template/
├── settings.gradle.kts.j2
├── build.gradle.kts.j2
├── core/
│   └── build.gradle.kts.j2
└── app/
    └── build.gradle.kts.j2
```

**settings.gradle.kts.j2:**
```kotlin
rootProject.name = "{{ project_name }}"

{% for module in config('modules', ['core', 'app']) %}
include("{{ module }}")
{% endfor %}
```

### Spring Boot Template

With config:
```toml
[custom]
spring_version = "3.2.0"
spring_modules = ["web", "data-jpa", "security"]
```

**build.gradle.kts.j2:**
```kotlin
plugins {
    kotlin("jvm") version "{{ kotlin_version }}"
    kotlin("plugin.spring") version "{{ kotlin_version }}"
    id("org.springframework.boot") version "{{ config('custom.spring_version', '3.2.0') }}"
}

dependencies {
    implementation("org.springframework.boot:spring-boot-starter")
    {% for module in config('custom.spring_modules', []) %}
    implementation("org.springframework.boot:spring-boot-starter-{{ module }}")
    {% endfor %}
}
```

## Troubleshooting

### Missing packages

```
Error: Missing required packages: jinja2, toml
```

**Solution:**
```bash
pip install jinja2 toml
```

### Template not found

```
Error: Failed to fetch template
```

**Solutions:**
1. Check URL: `curl <template-url>`
2. Use local template: `--template file:///path`
3. Check git credentials for private repos

### Version constraint failed

```
Error: gradle_version 8.5 does not satisfy constraint >=9.0
```

**Solutions:**
1. Update version: `--gradle-version 9.0`
2. Change constraint in `.gradleInit`
3. Remove constraint

### Git initialization failed

**Cause:** Git not installed or not configured

**Solution:**
```bash
# Install git
sudo apt install git  # Linux
brew install git      # macOS

# Configure
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

## Best Practices

### 1. Version Control Templates

```bash
# Tag stable versions
git tag -a v1.0.0 -m "Stable template v1.0.0"
git push --tags

# Pin in config
[template]
version = "v1.0.0"  # Stable, reproducible
```

### 2. Separate Templates by Type

```
templates/
├── kotlin-library/       # For libraries
├── kotlin-app/          # For applications
├── spring-boot/         # For Spring Boot
└── android/             # For Android
```

### 3. Document Templates

Add `TEMPLATE.md` to each template:

```markdown
# Kotlin Library Template

## Required Variables
- project_name
- project_group
- project_version

## Custom Configuration
- custom.publish (boolean): Enable Maven Central publishing
- custom.license: Project license (default: MIT)

## Example
```toml
[custom]
publish = true
license = "Apache-2.0"
```

### 4. CI/CD Integration

**GitHub Actions:**
```yaml
name: Create Project
on: workflow_dispatch

jobs:
  create:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install jinja2 toml
      - run: |
          python gradleInit.py init ${{ github.event.inputs.name }} \
            --template ${{ secrets.TEMPLATE_URL }}
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- **Issues**: https://github.com/stotz/gradleInit/issues
- **Discussions**: https://github.com/stotz/gradleInit/discussions
- **Documentation**: https://github.com/stotz/gradleInit/wiki

## Changelog

### v1.1.0 (Current)
- ✨ Added shared version catalog support
- ✨ Added Maven Central integration
- ✨ Added Spring Boot BOM support
- ✨ Added intelligent update manager
- ✨ Added self-update capability
- ✨ Added breaking-change detection
- ✨ Added auto-check scheduling
- 🐛 Various bug fixes and improvements

### v2.0.0
- ✨ Initial release with Jinja2 templating
- ✨ Custom URL support
- ✨ Version constraints
- ✨ Configuration management

---

**Made with ❤️ for the Kotlin/Gradle community**
