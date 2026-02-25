# gradleInit

> Modern Kotlin/Gradle Project Initializer with Template Management, Version Updates & Security

A comprehensive single-file Python tool for creating professional Kotlin/Gradle projects. Features intelligent template management, dependency version updates with npm-style constraints, repository signing, and cross-platform compatibility.

[![Version](https://img.shields.io/badge/version-1.9.0-blue.svg)](https://github.com/stotz/gradleInit)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

---

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Three Repository Architecture](#three-repository-architecture)
- [Commands](#commands)
  - [Project Creation](#project-creation)
  - [Template Management](#template-management)
  - [Module Management](#module-management)
  - [Version Management](#version-management)
  - [Security](#security)
- [Version Constraints](#version-constraints)
- [Custom Repositories](#custom-repositories)
- [Configuration](#configuration)
- [Documents](#documents)

---

## Features

### Core Capabilities

- **Single-File Tool** - Everything in one Python script
- **Template Management** - Official and custom templates from GitHub
- **Version Updates** - npm-style constraints with Maven Central integration
- **Repository Signing** - RSA-4096 signatures with SHA-256 checksums
- **Multi-Module Projects** - Root + subprojects with shared version catalogs
- **Cross-Platform** - Linux, macOS, Windows (Git Bash, PowerShell, CMD)

### Project Types

| Template | Description | Key Dependencies |
|----------|-------------|------------------|
| `kotlin-single` | Single-module CLI application | Clikt 5.1.0, Shadow 9.3.1 |
| `kotlin-multi` | Multi-module with buildSrc | Shadow 9.3.1 |
| `ktor` | Ktor HTTP server | Ktor 3.4.0, Logback 1.5.29 |
| `springboot` | Spring Boot REST API | Spring Boot 4.0.2 |
| `kotlin-javaFX` | JavaFX desktop application | JavaFX 25.0.1, Ikonli 12.4.0 |
| `multiproject-root` | Root for multi-module projects | All above available |

### Current Versions (from Templates)

```
Kotlin:      2.1.0+ (via kotlin_version variable)
JUnit:       5.13.4
AssertJ:     3.27.3
MockK:       1.14.9
Shadow:      9.3.1
Ktor:        3.4.0
Spring Boot: 4.0.2
JavaFX:      25.0.1
Logback:     1.5.29
Clikt:       5.1.0
```

---

## Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/stotz/gradleInit.git
cd gradleInit
pip install toml jinja2 pyyaml

# 2. Download templates and modules
./gradleInit.py templates --update
./gradleInit.py modules --download

# 3. Create project
./gradleInit.py init my-app --template kotlin-single --group com.example

# 4. Build and run
cd my-app
./gradlew build
./gradlew run
```

---

## Installation

### Prerequisites

- Python 3.8+
- Git
- Java/JDK 21+ (for Gradle)

### Install

```bash
git clone https://github.com/stotz/gradleInit.git
cd gradleInit
pip install toml jinja2 pyyaml

# Optional: Install cryptography for signing features
pip install cryptography

# Make executable (Linux/macOS)
chmod +x gradleInit.py

# Verify
./gradleInit.py --version
```

### First Run

```bash
# Download official templates
./gradleInit.py templates --update

# Download optional modules (Maven Central resolver)
./gradleInit.py modules --download

# Verify setup
./gradleInit.py templates --list
```

---

## Three Repository Architecture

gradleInit uses three coordinated repositories:

```
gradleInit (Main Tool)
    |
    +-- gradleInitTemplates (Project Templates)
    |       - kotlin-single, kotlin-multi, ktor, springboot, kotlin-javaFX
    |       - multiproject-root for multi-module projects
    |       - Signed with CHECKSUMS.sha256 + CHECKSUMS.sig
    |
    +-- gradleInitModules (Optional Extensions)
            - Maven Central version resolver
            - Future: Spring Boot BOM, other integrations
            - Signed with CHECKSUMS.sha256 + CHECKSUMS.sig
```

### Repository URLs

| Repository | URL | Purpose |
|------------|-----|---------|
| gradleInit | https://github.com/stotz/gradleInit | Main tool, documentation |
| gradleInitTemplates | https://github.com/stotz/gradleInitTemplates | Project templates |
| gradleInitModules | https://github.com/stotz/gradleInitModules | Optional modules |

### Local Storage

```
~/.gradleInit/
    config              # User configuration
    templates/          # Cloned templates
        official/       # Official templates
        custom/         # Custom template repositories
    modules/            # Cloned modules
    cache/
        maven/          # Maven Central version cache (1h TTL)
    keys/               # RSA keypairs for signing
```

---

## Commands

### Project Creation

#### Create Single Project

```bash
# Basic
./gradleInit.py init my-app --template kotlin-single --group com.example

# With version and config
./gradleInit.py init my-app \
    --template kotlin-single \
    --group com.example \
    --version 1.0.0 \
    --config kotlin_version=2.1.0 \
    --config jdk_version=21

# Interactive mode
./gradleInit.py init --interactive
```

#### Create Multi-Module Project

```bash
# 1. Create root project
./gradleInit.py init enterprise-app --template multiproject-root --group com.enterprise

# 2. Add subprojects
cd enterprise-app
gradleInit subproject core --template kotlin-single
gradleInit subproject api --template ktor
gradleInit subproject web --template springboot

# 3. Build all
./gradlew build
```

### Template Management

```bash
# List available templates
./gradleInit.py templates --list

# Update templates from GitHub
./gradleInit.py templates --update

# Show template details
./gradleInit.py templates --info kotlin-single

# Add custom template repository
./gradleInit.py templates --add-repo myteam https://github.com/myteam/templates.git
```

### Module Management

Modules provide optional features like Maven Central version resolution.

#### Download Modules

```bash
./gradleInit.py modules --download
```

Downloads modules from https://github.com/stotz/gradleInitModules to `~/.gradleInit/modules/`.

**Output:**
```
-> Downloading modules from https://github.com/stotz/gradleInitModules.git...
[OK] Modules downloaded successfully
[OK] Advanced features enabled: Maven Central
```

**If directory exists but is invalid:**
```
[ERROR] Directory already exists and is not empty:
[ERROR]   C:\Users\User\.gradleInit\modules
-> To fix this, remove the directory and try again:
->   rm -rf "C:\Users\User\.gradleInit\modules"
->   gradleInit modules --download
```

#### Update Modules

```bash
./gradleInit.py modules --update
```

Performs `git pull` on the modules repository and **clears the Maven cache** (ensures new resolver logic is used immediately).

**Output:**
```
-> Updating modules...
-> Maven cache cleared
[OK] Modules updated
```

### Version Management

The `versions` command checks and updates dependency versions in `gradle/libs.versions.toml`.

#### Check for Updates

```bash
./gradleInit.py versions --check
```

**Output:**
```
-> Checking versions in /path/to/project/gradle/libs.versions.toml

  [SKIP]    jdk    : 25 (no source URL)
  [UPDATE]  kotlin : 2.0.0 -> 2.1.0 (@*)
  [CURRENT] shadow : 9.3.1 (up to date)
  [UPDATE]  junit  : 5.10.0 -> 5.13.4 (@*)
  [CURRENT] assertj: 3.27.1 (up to date)
  [PINNED]  mockk  : 1.14.9 (@pin)

2 updates available, 1 pinned, 1 skipped, 2 current
```

#### Apply Updates

```bash
# Interactive
./gradleInit.py versions --update

# Auto-confirm (for CI)
./gradleInit.py versions --update --yes

# Update specific dependency
./gradleInit.py versions --update junit
```

#### Status Meanings

| Status | Description |
|--------|-------------|
| `[UPDATE]` | Newer version available within constraint |
| `[CURRENT]` | Already at latest version within constraint |
| `[PINNED]` | Version is pinned (`@pin` or no constraint) |
| `[SKIP]` | No source URL in comment |
| `[VIOLATE]` | No version satisfies constraint |
| `[NO_API]` | Maven Central resolver not available |

### Security

#### Generate Keypair

```bash
./gradleInit.py keys --generate mykey
```

Creates RSA-4096 keypair:
- `~/.gradleInit/keys/mykey.private.pem` - Keep secure!
- `~/.gradleInit/keys/mykey.public.pem` - Share with users

#### Sign Repository

```bash
./gradleInit.py sign --repo /path/to/repo --key mykey
```

Creates:
- `CHECKSUMS.sha256` - SHA-256 hashes of all files
- `CHECKSUMS.sig` - RSA signature of checksums

#### Verify Repository

```bash
./gradleInit.py verify --repo /path/to/repo --key mykey
```

#### Import Public Key

```bash
./gradleInit.py keys --import teamkey https://example.com/team.public.pem
```

---

## Version Constraints

gradleInit uses npm-style version constraints in `libs.versions.toml` comments.

### Syntax

```toml
[versions]
# https://mvnrepository.com/artifact/org.junit.jupiter/junit-jupiter @*
junit = "5.10.0"
```

Format: `# <url> @<constraint>`

### Available Constraints

| Constraint | Description | Example |
|------------|-------------|---------|
| `@pin` | Never update (default if no constraint) | `@pin` |
| `@*` | Always update to latest stable | `@*` |
| `@^1.2.3` | Minor updates (>=1.2.3 <2.0.0) | `@^5.10.0` -> 5.13.4 |
| `@~1.2.3` | Patch updates (>=1.2.3 <1.3.0) | `@~5.10.0` -> 5.10.2 |
| `@>=1.0.0` | Minimum version | `@>=5.0.0` |
| `@<2.0.0` | Maximum version | `@<6.0.0` |
| `@>=1.0 <2.0` | Version range | `@>=5.0 <6.0` |
| `@1.x` | Any 1.x version | `@5.x` |

### Pre-release Versions

By default, `@*` returns only **stable versions** (excludes alpha, beta, RC, SNAPSHOT, M1, etc.).

Examples of filtered pre-release versions:
- `2.3.20-RC` - filtered
- `6.1.0-M1` - filtered
- `1.0.0-alpha` - filtered
- `1.0.0-SNAPSHOT` - filtered

**Note:** There is currently no constraint to explicitly include pre-release versions. If you need a pre-release, pin the exact version:

```toml
# https://mvnrepository.com/artifact/org.example/lib @pin
lib = "2.0.0-beta1"
```

### Examples

```toml
[versions]
# Always latest stable
# https://mvnrepository.com/artifact/org.junit.jupiter/junit-jupiter @*
junit = "5.13.4"

# Same major version only (Kotlin 2.x)
# https://mvnrepository.com/artifact/org.jetbrains.kotlin/kotlin-stdlib @^2.0.0
kotlin = "2.1.0"

# Same minor version only (patches only)
# https://mvnrepository.com/artifact/ch.qos.logback/logback-classic @~1.5.0
logback = "1.5.29"

# Maximum version (stay below 4.0)
# https://mvnrepository.com/artifact/org.assertj/assertj-core @<4.0.0
assertj = "3.27.3"

# Pinned - never update automatically
# https://mvnrepository.com/artifact/io.mockk/mockk @pin
mockk = "1.14.9"

# Implicit pin (no @constraint)
# https://mvnrepository.com/artifact/com.example/legacy
legacy = "1.0.0"
```

---

## Custom Repositories

### Custom Template Repository

#### 1. Create Repository Structure

```
my-templates/
    kotlin-custom/
        TEMPLATE.md           # Required: metadata
        build.gradle.kts      # Jinja2 template
        settings.gradle.kts
        gradle/
            libs.versions.toml
        src/
            main/kotlin/...
    another-template/
        ...
    CHECKSUMS.sha256          # Optional: for verification
    CHECKSUMS.sig
```

#### 2. TEMPLATE.md Format

```markdown
# Template Name

Description of the template.

## Variables

| Variable | Default | Description |
|----------|---------|-------------|
| project_name | - | Project name |
| project_group | com.example | Group ID |
```

#### 3. Add to gradleInit

```bash
./gradleInit.py templates --add-repo myteam https://github.com/myteam/templates.git
```

#### 4. Use Template

```bash
./gradleInit.py init my-project --template myteam:kotlin-custom --group com.myteam
```

### Custom Module Repository

#### 1. Create Repository Structure

```
my-modules/
    MODULES.toml              # Required: manifest
    CHECKSUMS.sha256
    CHECKSUMS.sig
    resolvers/
        __init__.py
        my_resolver.py
```

#### 2. MODULES.toml Format

```toml
[repository]
name = "myteam"
description = "Custom modules for MyTeam"
version = "1.0.0"
min_gradleinit_version = "1.9.0"

[resolvers]
my_resolver = { file = "resolvers/my_resolver.py", class = "MyResolver" }
```

#### 3. Configure in ~/.gradleInit/config

```toml
[modules]
repo = "https://github.com/myteam/gradleInitModules.git"
```

### Security with Signing

#### Sign Your Repository

```bash
# Generate keypair (once)
./gradleInit.py keys --generate myteam

# Sign templates
./gradleInit.py sign --repo /path/to/my-templates --key myteam

# Sign modules
./gradleInit.py sign --repo /path/to/my-modules --key myteam
```

#### Distribute Public Key

Share `~/.gradleInit/keys/myteam.public.pem` with users.

#### Users Import and Verify

```bash
# Import public key
./gradleInit.py keys --import myteam https://myteam.com/myteam.public.pem

# Verify repository
./gradleInit.py verify --repo ~/.gradleInit/templates/myteam --key myteam
```

### Trust Levels

| Level | Description | Verification |
|-------|-------------|--------------|
| `official` | Signed with embedded key | Automatic |
| `verified` | Signed with imported key | After key import |
| `unverified` | No signature | Warning on use |

---

## Configuration

### Configuration File

Location: `~/.gradleInit/config`

```toml
[templates]
official_repo = "https://github.com/stotz/gradleInitTemplates.git"
auto_update = false

[modules]
repo = "https://github.com/stotz/gradleInitModules.git"
auto_load = true

[defaults]
group = "com.example"
version = "0.1.0"
gradle_version = "8.14"
kotlin_version = "2.1.0"
jdk_version = "21"

[custom]
author = ""
email = ""
company = ""
license = "MIT"
```

### Priority Order

1. **CLI Arguments** (highest)
2. **Environment Variables** (`GRADLE_INIT_*`)
3. **Config File** (`~/.gradleInit/config`)
4. **Defaults** (lowest)

### Environment Variables

```bash
export GRADLE_INIT_GROUP="com.mycompany"
export GRADLE_INIT_AUTHOR="John Doe"
export GRADLE_VERSION="8.14"
export KOTLIN_VERSION="2.1.0"
export JDK_VERSION="21"
```

---

## Documents

- [Enhanced Template Hint System](docs/ENHANCED_HINTS_GUIDE.md) - Inline `@@` syntax for self-documenting templates
- [Jinja2 Template Features](docs/JINJA2_FEATURES.md) - Filters, functions, variables
- [Environment Variables](docs/ENV_VARIABLES.md) - `GRADLE_INIT_*` configuration
- [Security](docs/SECURITY.md) - RSA-4096 signing and verification
- [Repositories](docs/REPOSITORIES.md) - Three-repository architecture

---

## CLI Reference

```
gradleInit.py [OPTIONS] COMMAND [ARGS]

Commands:
  init              Create new project
  subproject        Add subproject to existing project
  templates         Manage templates
  versions          Check and update dependency versions
  keys              Manage signing keys
  sign              Sign repository
  verify            Verify repository signature
  config            Manage configuration

Global Options:
  --version         Show version
  --help            Show help
  --verbose         Verbose output
  --install-deps    Auto-install dependencies (for CI)
```

---

## License

MIT License - see [LICENSE](LICENSE) file.

---

**Made with care for the Kotlin/Gradle community**
