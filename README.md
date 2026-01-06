# gradleInit

A single-file Python tool for creating Kotlin/Gradle projects. Supports templates, multi-project builds, automatic Gradle wrapper generation, and Git initialization.

[![Version](https://img.shields.io/badge/version-1.7.0-blue.svg)](https://github.com/stotz/gradleInit)
[![Python](https://img.shields.io/badge/python-3.7+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

---

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage](#usage)
  - [Interactive Mode](#interactive-mode)
  - [Command Line Mode](#command-line-mode)
  - [Multi-Project Builds](#multi-project-builds)
- [Templates](#templates)
- [Configuration](#configuration)
- [Project Setup](#project-setup)
  - [Generated Files](#generated-files)
  - [Git Integration](#git-integration)
  - [Push to Remote Repository](#push-to-remote-repository)
- [CLI Reference](#cli-reference)
- [Troubleshooting](#troubleshooting)

---

## Features

- Single-file tool - one Python script, minimal dependencies
- Template-based project generation with Jinja2
- Multi-project support with `multiproject-root` and `subproject` command
- Automatic Gradle wrapper generation
- Git repository initialization with `.gitignore`, `.gitattributes`, `.editorconfig`
- Version catalog support (`libs.versions.toml`)
- Cross-platform (Linux, macOS, Windows)

### Available Templates

| Template | Description |
|----------|-------------|
| `kotlin-single` | Single-module Kotlin project |
| `kotlin-multi` | Multi-module project with buildSrc conventions |
| `kotlin-javaFX` | JavaFX application with Kotlin |
| `springboot` | Spring Boot REST API |
| `ktor` | Ktor server application |
| `multiproject-root` | Root project for incremental multi-module builds |

---

## Quick Start

```bash
# Download and setup
git clone https://github.com/stotz/gradleInit.git
cd gradleInit
pip install jinja2 toml

# Download templates
./gradleInit.py templates --update

# Create a project
./gradleInit.py init my-app --template kotlin-single --group com.example

# Build and run
cd my-app
./gradlew build
./gradlew run
```

---

## Installation

### Prerequisites

- Python 3.7+
- Git
- Java/JDK (for Gradle)
- Gradle (optional, for wrapper generation)

### Install Dependencies

```bash
pip install jinja2 toml
```

### Download

```bash
git clone https://github.com/stotz/gradleInit.git
cd gradleInit
chmod +x gradleInit.py
```

### Add to PATH (optional)

```bash
# Linux/macOS
sudo ln -s $(pwd)/gradleInit.py /usr/local/bin/gradleInit

# Windows (PowerShell as Admin)
$env:PATH += ";$(pwd)"
```

### First Run

```bash
./gradleInit.py templates --update
./gradleInit.py templates --list
```

---

## Usage

### Interactive Mode

```bash
./gradleInit.py init --interactive
```

Prompts for project name, template, group ID, version, and Gradle version.

### Command Line Mode

```bash
# Basic usage
./gradleInit.py init my-app --template kotlin-single --group com.example

# With version and Gradle version
./gradleInit.py init my-app \
  --template kotlin-single \
  --group com.example \
  --version 1.0.0 \
  --config gradle_version=8.14

# Skip interactive prompts
./gradleInit.py init my-app --template kotlin-single --group com.example --no-interactive
```

### Multi-Project Builds

For projects that grow incrementally, use `multiproject-root` to create a root project, then add subprojects as needed.

#### Create Root Project

```bash
./gradleInit.py init my-platform --template multiproject-root --group com.example
cd my-platform
```

This creates a root project with shared configuration and an empty `gradle/libs.versions.toml`.

#### Add Subprojects

```bash
# Add a library module
./gradleInit.py subproject core-lib --template kotlin-single

# Add a service module
./gradleInit.py subproject user-service --template springboot

# Add another service
./gradleInit.py subproject api-gateway --template ktor
```

Each subproject:
- Is added to `settings.gradle.kts` automatically
- Merges its dependencies into the shared `libs.versions.toml`
- Uses the root project's Gradle wrapper

#### Resulting Structure

```
my-platform/
├── build.gradle.kts
├── settings.gradle.kts
├── gradle/
│   └── libs.versions.toml      # Merged from all subprojects
├── core-lib/
│   ├── build.gradle.kts
│   └── src/main/kotlin/
├── user-service/
│   ├── build.gradle.kts
│   └── src/main/kotlin/
└── api-gateway/
    ├── build.gradle.kts
    └── src/main/kotlin/
```

#### Build

```bash
./gradlew build                    # Build all
./gradlew :core-lib:build          # Build specific module
./gradlew :user-service:bootRun    # Run Spring Boot service
```

---

## Templates

### Official Templates

Located at: https://github.com/stotz/gradleInitTemplates

#### kotlin-single

Single-module Kotlin application with JUnit 5 tests.

```bash
./gradleInit.py init my-app --template kotlin-single --group com.example
```

#### kotlin-multi

Multi-module project with buildSrc convention plugins. Contains `app` and `lib` modules.

```bash
./gradleInit.py init my-project --template kotlin-multi --group com.example
```

Note: Uses system Gradle instead of wrapper due to buildSrc compilation requirements.

#### kotlin-javaFX

JavaFX desktop application with Ikonli icons, ControlsFX, FormsFX, and ValidatorFX.

```bash
./gradleInit.py init my-gui --template kotlin-javaFX --group com.example
```

#### springboot

Spring Boot 3.x REST API with Kotlin.

```bash
./gradleInit.py init my-api --template springboot --group com.example
cd my-api
./gradlew bootRun
```

#### ktor

Ktor server with Netty, content negotiation, and Kotlin serialization.

```bash
./gradleInit.py init my-service --template ktor --group com.example
cd my-service
./gradlew run
```

#### multiproject-root

Root project structure for incremental multi-module builds. Use with `subproject` command.

```bash
./gradleInit.py init my-platform --template multiproject-root --group com.example
```

### Custom Templates

#### From GitHub

```bash
./gradleInit.py init my-project \
  --template https://github.com/myorg/my-template.git \
  --group com.example
```

#### From GitHub Subdirectory

```bash
./gradleInit.py init my-project \
  --template https://github.com/myorg/templates/tree/main/kotlin-base \
  --group com.example
```

### Template Management

```bash
# List available templates
./gradleInit.py templates --list

# Update templates from GitHub
./gradleInit.py templates --update

# Show template details
./gradleInit.py templates --info kotlin-single

# Clear compiled template cache
./gradleInit.py templates --clear-cache

# Add custom repository
./gradleInit.py templates --add-repo myteam https://github.com/myteam/templates.git
```

---

## Configuration

### Configuration File

Location: `~/.gradleInit/config`

```toml
[defaults]
group = "com.example"
version = "0.1.0"
gradle_version = "8.14"
kotlin_version = "2.1.0"
jdk_version = "21"

[custom]
author = "Your Name"
email = "you@example.com"
company = "Company Name"
```

### Manage Configuration

```bash
# Show current config
./gradleInit.py config --show

# Initialize config file
./gradleInit.py config --init
```

### Priority Order

```
CLI Arguments > Environment Variables > Config File > Built-in Defaults
```

---

## Project Setup

### Generated Files

Every generated project includes:

| File | Purpose |
|------|---------|
| `.editorconfig` | Editor settings for consistent formatting |
| `.gitattributes` | Git line ending and diff settings |
| `.gitignore` | Ignore patterns for build outputs, IDE files |
| `gradle/libs.versions.toml` | Centralized dependency versions |
| `gradle.properties` | Gradle settings |

#### .editorconfig

Defines coding style for editors that support EditorConfig:

```ini
root = true

[*]
charset = utf-8
end_of_line = lf
indent_style = space
indent_size = 4
insert_final_newline = true
trim_trailing_whitespace = true

[*.{kt,kts}]
indent_size = 4

[*.{xml,json,yaml,yml}]
indent_size = 2
```

#### .gitattributes

Ensures consistent line endings and proper diff handling:

```gitattributes
* text=auto eol=lf
*.bat text eol=crlf
*.jar binary
*.png binary
gradlew text eol=lf
```

#### .gitignore

Excludes build outputs and IDE-specific files:

```gitignore
# Gradle
build/
.gradle/

# IDE
.idea/
*.iml
.vscode/

# OS
.DS_Store
Thumbs.db
```

### Git Integration

Every project is initialized as a Git repository:

1. `git init` - Initialize repository
2. `git add -f gradle/wrapper/gradle-wrapper.jar` - Force-add wrapper JAR
3. `git add .` - Stage all files
4. `git add --renormalize .` - Normalize line endings per `.gitattributes`
5. `git commit -m 'Initial commit from gradleInit'` - Create first commit

The `--renormalize` step ensures all files have correct line endings according to `.gitattributes`, regardless of the OS used during creation.

### Push to Remote Repository

After project creation, push to your preferred Git hosting service.

#### GitHub

```bash
cd my-app

# Create repository on GitHub first, then:

# HTTPS
git remote add origin https://github.com/USERNAME/my-app.git
git branch -M main
git push -u origin main

# SSH (requires SSH key setup)
git remote add origin git@github.com:USERNAME/my-app.git
git branch -M main
git push -u origin main

# GitHub CLI
gh repo create my-app --public --source=. --push
```

#### GitLab

```bash
cd my-app

# HTTPS
git remote add origin https://gitlab.com/USERNAME/my-app.git
git branch -M main
git push -u origin main

# SSH
git remote add origin git@gitlab.com:USERNAME/my-app.git
git branch -M main
git push -u origin main
```

#### Bitbucket

```bash
cd my-app

# HTTPS
git remote add origin https://bitbucket.org/USERNAME/my-app.git
git branch -M main
git push -u origin main

# SSH
git remote add origin git@bitbucket.org:USERNAME/my-app.git
git branch -M main
git push -u origin main
```

#### Self-Hosted Git Server

```bash
cd my-app
git remote add origin git@git.mycompany.com:group/my-app.git
git branch -M main
git push -u origin main
```

---

## CLI Reference

### Global Options

```bash
./gradleInit.py --version    # Show version
./gradleInit.py --help       # Show help
```

### init Command

Create a new project.

```bash
./gradleInit.py init PROJECT_NAME [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--template TEMPLATE` | Template name or GitHub URL (required) |
| `--group GROUP` | Maven group ID |
| `--version VERSION` | Project version |
| `--interactive, -i` | Enable interactive prompts |
| `--no-interactive` | Disable all prompts |
| `--config KEY=VALUE` | Set configuration value |

Examples:

```bash
./gradleInit.py init my-app --template kotlin-single --group com.example
./gradleInit.py init my-app --template kotlin-single --config gradle_version=8.14
./gradleInit.py init --interactive
```

### subproject Command

Add a subproject to an existing multi-project build.

```bash
./gradleInit.py subproject NAME --template TEMPLATE [OPTIONS]
```

Must be run from within a project created with `multiproject-root`.

| Option | Description |
|--------|-------------|
| `--template TEMPLATE` | Template for the subproject (required) |

Examples:

```bash
./gradleInit.py subproject core --template kotlin-single
./gradleInit.py subproject api --template springboot
```

### templates Command

Manage templates.

```bash
./gradleInit.py templates [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--list` | List available templates |
| `--info NAME` | Show template details |
| `--update` | Update from GitHub |
| `--clear-cache` | Clear compiled template cache |
| `--add-repo NAME URL` | Add custom repository |

### config Command

Manage configuration.

```bash
./gradleInit.py config [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--show` | Display current configuration |
| `--init` | Initialize configuration file |

---

## Troubleshooting

### Module not found: jinja2 or toml

```bash
pip install jinja2 toml
```

### No templates found

```bash
./gradleInit.py templates --update
```

### Git: Author identity unknown

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

### Gradle version incompatible with Kotlin

Use Gradle 8.14 or compatible version:

```bash
./gradleInit.py init my-app --template kotlin-single --config gradle_version=8.14
```

### kotlin-multi: Plugin not found

The `kotlin-multi` template uses buildSrc which requires system Gradle. Do not use the Gradle wrapper.

```bash
gradle build    # Use system Gradle
```

### Template clone failed (Windows)

Close programs that might lock files, then:

```bash
rm -rf ~/.gradleInit/templates/official
./gradleInit.py templates --update
```

### Line ending issues

If files have wrong line endings after checkout:

```bash
git add --renormalize .
git commit -m "Normalize line endings"
```

---

## License

MIT License - see [LICENSE](LICENSE) file.

---

## Links

- Repository: https://github.com/stotz/gradleInit
- Templates: https://github.com/stotz/gradleInitTemplates
- Issues: https://github.com/stotz/gradleInit/issues
