# gradleInit

> Modern Kotlin/Gradle Project Initializer with Template Management & Interactive CLI

A comprehensive single-file Python tool for creating professional Kotlin/Gradle projects in seconds. Features intelligent template management, interactive project setup, automatic Gradle wrapper generation, and built-in Git initialization.

[![Version](https://img.shields.io/badge/version-1.4.0-blue.svg)](https://github.com/stotz/gradleInit)
[![Python](https://img.shields.io/badge/python-3.7+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

---

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage](#usage)
  - [Interactive Mode](#interactive-mode)
  - [Command Line](#command-line)
  - [Template Management](#template-management)
- [Configuration](#configuration)
- [Templates](#templates)
- [Advanced Features](#advanced-features)
- [CLI Reference](#cli-reference)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

---

## Features

### 🎯 Core Capabilities

✅ **Single-File Tool** - Everything in one Python script, easy to install and distribute  
✅ **Interactive Mode** - User-friendly prompts for project creation  
✅ **Template Management** - GitHub templates with automatic cloning and updates  
✅ **Gradle Wrapper** - Automatic wrapper generation with version selection  
✅ **Git Integration** - Initialize repository and create initial commit  
✅ **Version Catalogs** - Modern libs.versions.toml for dependency management  
✅ **Cross-Platform** - Works on Linux, macOS, and Windows  
✅ **Verbose Output** - See exactly what commands are being executed  

### 📦 Project Types

Out-of-the-box templates for:
- **kotlin-single** - Simple single-module Kotlin project
- **kotlin-multi** - Multi-module project with buildSrc conventions
- **springboot** - Spring Boot REST API with Kotlin
- **ktor** - Ktor server application

### ⚙️ Smart Features

- **Gradle Version Selection** - Interactive picker or specify version
- **Template Repository** - Official templates from GitHub
- **Custom Templates** - Support for GitHub URLs and subdirectories
- **Configuration Persistence** - Save defaults in `~/.gradleInit/config`
- **Command Output** - Verbose mode shows all executed commands

---

## Quick Start

### 5-Second Project Creation

```bash
# Interactive mode - easiest way!
./gradleInit.py init --interactive
```

**You'll be prompted for:**
1. Project name
2. Template selection (kotlin-single, kotlin-multi, springboot, ktor)
3. Group ID (e.g., com.mycompany)
4. Version
5. Gradle version

**Then:**
```bash
cd my-project
./gradlew build
./gradlew run
```

### With Command Line

```bash
# Create simple Kotlin project
./gradleInit.py init my-app --template kotlin-single --group ch.typedef

# Create Spring Boot service
./gradleInit.py init customer-api --template springboot --group com.company

# With specific versions
./gradleInit.py init my-project \
  --template kotlin-single \
  --group com.mycompany \
  --version 1.0.0 \
  --config gradle_version=8.14 \
  --config kotlin_version=2.1.0
```

### What You Get

```
my-app/
├── build.gradle.kts           # Kotlin DSL build configuration
├── settings.gradle.kts        # Project settings
├── gradle.properties          # Gradle properties
├── gradle/
│   ├── wrapper/               # Gradle wrapper (generated)
│   │   ├── gradle-wrapper.jar
│   │   └── gradle-wrapper.properties
│   └── libs.versions.toml     # Version catalog
├── gradlew                    # Unix wrapper script
├── gradlew.bat                # Windows wrapper script
├── src/
│   ├── main/kotlin/          # Your source code
│   └── test/kotlin/          # Your tests
├── .git/                      # Git repository (initialized)
├── .gitignore                 # Pre-configured
└── .editorconfig              # Code style configuration

✓ Ready to build and run!
```

---

## Installation

### Prerequisites

- **Python 3.7+**
- **Git** (for template cloning)
- **Java/JDK** (to run Gradle)

### Install Dependencies

```bash
pip install toml
```

That's it! gradleInit has minimal dependencies.

### Download gradleInit

```bash
# Clone repository
git clone https://github.com/stotz/gradleInit.git
cd gradleInit

# Make executable
chmod +x gradleInit.py

# Test installation
./gradleInit.py --version
```

### Optional: Add to PATH

**Linux/macOS:**
```bash
# Add to your PATH
sudo ln -s $(pwd)/gradleInit.py /usr/local/bin/gradleInit

# Or user-only
mkdir -p ~/.local/bin
ln -s $(pwd)/gradleInit.py ~/.local/bin/gradleInit
```

**Windows:**
```powershell
# Add current directory to PATH
$env:PATH += ";$(pwd)"

# Make permanent (PowerShell as Admin)
[Environment]::SetEnvironmentVariable(
    "Path",
    $env:Path + ";C:\path\to\gradleInit",
    [EnvironmentVariableTarget]::User
)
```

### First Run - Download Templates

```bash
# Download official templates from GitHub
./gradleInit.py templates --update

# Verify templates are available
./gradleInit.py templates --list
```

**Output:**
```
======================================================================
  Available Templates
======================================================================

official:
  kotlin-single    - Simple single-module Kotlin project
  kotlin-multi     - Multi-module Kotlin project  
  springboot       - Spring Boot REST API
  ktor             - Ktor server application
```

---

## Usage

### Interactive Mode

**Easiest way to create a project:**

```bash
./gradleInit.py init --interactive
```

**Example Session:**
```
Project name: my-awesome-app

→ Available templates:
  1. kotlin-single  - Simple single-module Kotlin project
  2. kotlin-multi   - Multi-module Kotlin project
  3. springboot     - Spring Boot REST API
  4. ktor           - Ktor server application

Select template (1-4): 1

Group ID [com.example]: ch.typedef
Version [0.1.0]: 1.0.0

→ Gradle version selection:
  1. Use default (8.14)
  2. Select from list
  3. Enter version manually

Choice [1]: 2

======================================================================
  Select Gradle Version
======================================================================

Available versions:
   1. 9.2.1 (latest)
   2. 9.2.0
   3. 9.1.0
   4. 9.0.0
   5. 8.14.3
   6. 8.14.2
   7. 8.14.1
   8. 8.14 (recommended)
   ...

Enter number or version: 8

→ Creating project...
✓ Project created successfully!
```

### Command Line

**Quick creation with defaults:**
```bash
./gradleInit.py init my-project --template kotlin-single --group ch.typedef
```

**Full customization:**
```bash
./gradleInit.py init my-service \
  --template springboot \
  --group com.mycompany.services \
  --version 1.0.0 \
  --config gradle_version=8.14 \
  --config kotlin_version=2.1.0 \
  --config jdk_version=21
```

**With GitHub template URL:**
```bash
./gradleInit.py init my-project \
  --template https://github.com/myorg/custom-template.git \
  --group com.mycompany
```

**With GitHub subdirectory:**
```bash
./gradleInit.py init my-project \
  --template https://github.com/myorg/templates/tree/main/kotlin-base \
  --group com.mycompany
```

### Template Management

**List available templates:**
```bash
./gradleInit.py templates --list
```

**Update templates from GitHub:**
```bash
./gradleInit.py templates --update
```

**Show template details:**
```bash
./gradleInit.py templates --info kotlin-single
```

**Add custom template repository:**
```bash
./gradleInit.py templates --add-repo myteam https://github.com/myteam/templates.git
```

---

## Configuration

### Configuration File

gradleInit uses `~/.gradleInit/config` for persistent settings:

**Linux/macOS:**
```
/home/username/.gradleInit/config
```

**Windows:**
```
C:\Users\Username\.gradleInit\config
```

### Default Configuration

Created automatically on first run:

```toml
[templates]
official_repo = "https://github.com/stotz/gradleInitTemplates.git"
auto_update = false
update_interval = "weekly"

[modules]
repo = "https://github.com/stotz/gradleInitModules.git"
auto_load = true
version = "v1.3.0"

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

### Managing Configuration

**Show current config:**
```bash
./gradleInit.py config --show
```

**Initialize config file:**
```bash
./gradleInit.py config --init
```

### Customize Defaults

Edit `~/.gradleInit/config`:

```toml
[defaults]
group = "ch.typedef"          # Your default group
version = "1.0.0"              # Default version
gradle_version = "8.14"        # Preferred Gradle version
kotlin_version = "2.1.0"       # Preferred Kotlin version
jdk_version = "21"             # Target JDK

[custom]
author = "Hans Muster"         # Your name
email = "hans@example.com"     # Your email
company = "My Company AG"      # Company name
license = "Apache-2.0"         # Preferred license
```

**Now projects use these defaults:**
```bash
./gradleInit.py init my-project --template kotlin-single
# Uses: group=ch.typedef, version=1.0.0, author="Hans Muster"
```

### Priority Order

```
CLI Arguments > Config File > Built-in Defaults
```

**Example:**
```bash
# Config has: group = "ch.typedef"
# CLI specifies: --group com.mycompany

./gradleInit.py init my-app --template kotlin-single --group com.mycompany
# Result: group=com.mycompany (CLI wins)
```

---

## Templates

### Official Templates

Maintained at: https://github.com/stotz/gradleInitTemplates

#### kotlin-single
Simple single-module Kotlin application.

**Features:**
- Clean Kotlin project structure
- Gradle Kotlin DSL
- Version catalog (libs.versions.toml)
- JUnit 5 test setup
- .editorconfig for consistent formatting

**Generated Structure:**
```
my-app/
├── build.gradle.kts
├── settings.gradle.kts
├── gradle/libs.versions.toml
├── src/
│   ├── main/kotlin/Main.kt
│   └── test/kotlin/MainTest.kt
└── gradlew, gradlew.bat
```

**Usage:**
```bash
./gradleInit.py init my-app --template kotlin-single --group ch.typedef
cd my-app
./gradlew run
```

#### kotlin-multi
Multi-module project with buildSrc.

**Features:**
- buildSrc for shared build logic
- Convention plugins
- Module structure (app, lib)
- Version catalog
- Multi-module dependency management

**Generated Structure:**
```
my-project/
├── buildSrc/
│   └── src/main/kotlin/
│       ├── kotlin-common-conventions.gradle.kts
│       └── kotlin-application-conventions.gradle.kts
├── app/
│   ├── build.gradle.kts
│   └── src/main/kotlin/
├── lib/
│   ├── build.gradle.kts
│   └── src/main/kotlin/
└── settings.gradle.kts
```

**Usage:**
```bash
./gradleInit.py init my-project --template kotlin-multi --group ch.typedef
cd my-project
gradle build  # Note: Uses system Gradle, not wrapper
```

#### springboot
Spring Boot REST API with Kotlin.

**Features:**
- Spring Boot 3.x setup
- Spring Web MVC
- Kotlin configuration
- Application properties
- Health endpoint
- Test setup with Spring Test

**Generated Structure:**
```
my-api/
├── build.gradle.kts
├── src/
│   ├── main/
│   │   ├── kotlin/Application.kt
│   │   ├── kotlin/HelloController.kt
│   │   └── resources/application.properties
│   └── test/kotlin/
└── gradlew
```

**Usage:**
```bash
./gradleInit.py init customer-api --template springboot --group com.company
cd customer-api
./gradlew bootRun
```

#### ktor
Ktor server application.

**Features:**
- Ktor 3.x setup
- Netty engine
- Content negotiation
- Kotlin serialization
- Routing setup

**Generated Structure:**
```
my-service/
├── build.gradle.kts
├── src/main/kotlin/Application.kt
└── gradlew
```

**Usage:**
```bash
./gradleInit.py init my-service --template ktor --group ch.typedef
cd my-service
./gradlew run
```

### Custom Templates

#### From GitHub Repository

```bash
./gradleInit.py init my-project \
  --template https://github.com/myorg/kotlin-template.git \
  --group com.mycompany
```

#### From GitHub Subdirectory

```bash
./gradleInit.py init my-project \
  --template https://github.com/myorg/templates/tree/main/kotlin-base
```

**gradleInit automatically:**
- Parses the GitHub URL
- Clones the repository
- Extracts the specified subdirectory
- Uses it as the template

#### Template Structure

A template is any directory with these files:

```
my-template/
├── build.gradle.kts              # Or .j2 for Jinja2 template
├── settings.gradle.kts           # Required
├── gradle.properties             # Recommended
├── gradle/
│   └── libs.versions.toml        # Recommended
├── src/
│   └── main/kotlin/Main.kt
└── TEMPLATE.md                   # Optional: Template variables
```

**Jinja2 Templating:**

If your template has `.j2` files, they'll be rendered with these variables:

```jinja2
// build.gradle.kts.j2
group = "{{ group }}"
version = "{{ version }}"

kotlin {
    jvmToolchain({{ jdk_version }})
}
```

**Available Variables:**
- `project_name` - Project name
- `group` - Maven group ID
- `version` - Project version
- `kotlin_version` - Kotlin version
- `gradle_version` - Gradle version
- `jdk_version` - JDK version
- `date` - Current date (YYYY-MM-DD)

---

## Advanced Features

### Gradle Version Selection

**Interactive Selection:**
```bash
./gradleInit.py init my-app --template kotlin-single --interactive
# Then choose option 2 when prompted for Gradle version
```

Shows latest 15 Gradle versions from services.gradle.org.

**Direct Specification:**
```bash
./gradleInit.py init my-app \
  --template kotlin-single \
  --config gradle_version=8.14
```

**In Config File:**
```toml
[defaults]
gradle_version = "8.14"  # Your preferred version
```

### Gradle Wrapper Generation

gradleInit automatically generates Gradle wrapper for single-module projects:

**What happens:**
1. Project structure created
2. Temporary build files generated
3. `gradle wrapper --gradle-version X.Y` executed
4. Wrapper files created:
   - `gradlew` (Unix)
   - `gradlew.bat` (Windows)
   - `gradle/wrapper/` directory

**Console Output:**
```
→ Executing: gradle wrapper --gradle-version 8.14
→ Working directory: /path/to/my-app
→ Process exit code: 0
→ Standard output:
  BUILD SUCCESSFUL in 5s
  1 actionable task: 1 executed
✓ Gradle Wrapper 8.14 generated
```

**Note:** kotlin-multi template uses buildSrc and doesn't generate wrapper. Use system Gradle instead.

### Git Integration

Every project is automatically initialized as a Git repository:

**What happens:**
1. `git init` - Initialize repository
2. `git add .` - Stage all files
3. `git commit -m "Initial commit from gradleInit"` - Create first commit

**Console Output:**
```
→ Executing: git init
→ Working directory: /path/to/my-app
  Initialized empty Git repository
→ Executing: git add .
→ Executing: git commit -m 'Initial commit from gradleInit'
  [master (root-commit) abc1234] Initial commit from gradleInit
   11 files changed, 842 insertions(+)
✓ Git repository initialized
```

**Push to GitHub:**
```bash
cd my-app

# Using HTTPS (easier, requires username/password or token)
git remote add origin https://github.com/username/my-app.git
git branch -M main
git push -u origin main

# OR using SSH (recommended, requires SSH key setup)
git remote add origin git@github.com:username/my-app.git
git branch -M main
git push -u origin main
```

**SSH Setup:** https://docs.github.com/en/authentication/connecting-to-github-with-ssh

**Or with GitHub CLI:**
```bash
cd my-app
gh repo create my-app --public --source=. --push
```

### Verbose Command Output

gradleInit shows exactly what it's doing:

```
→ Executing: git clone --depth 1 https://github.com/stotz/gradleInitTemplates.git
→ Cloning to: C:\Users\User\.gradleInit\templates\official
✓ Cloned official templates

→ Executing: gradle wrapper --gradle-version 8.14
→ Working directory: C:\devl\my-app
→ Process exit code: 0
✓ Gradle Wrapper 8.14 generated

→ Executing: git init
→ Working directory: C:\devl\my-app
✓ Git repository initialized
```

**Benefits:**
- Transparency - see what's happening
- Debugging - identify where failures occur  
- Learning - understand the workflow
- Trust - verify commands before execution

---

## CLI Reference

### Global Options

```bash
./gradleInit.py --version              # Show version
./gradleInit.py --help                 # Show help
```

### init Command

Create a new project from template.

```bash
./gradleInit.py init PROJECT_NAME [OPTIONS]
```

**Options:**
```
--template TEMPLATE          Template name or GitHub URL (required)
--group GROUP                Maven group ID (e.g., com.example)
--version VERSION            Project version (e.g., 1.0.0)
--interactive, -i            Enable interactive prompts
--config KEY=VALUE           Set configuration value
--help, -h                   Show help
```

**Examples:**
```bash
# Interactive mode
./gradleInit.py init --interactive

# Simple project
./gradleInit.py init my-app --template kotlin-single --group ch.typedef

# With all options
./gradleInit.py init my-service \
  --template springboot \
  --group com.company.services \
  --version 1.0.0 \
  --config gradle_version=8.14 \
  --config kotlin_version=2.1.0

# Custom template
./gradleInit.py init my-project \
  --template https://github.com/myorg/template.git

# Template subdirectory
./gradleInit.py init my-app \
  --template https://github.com/myorg/templates/tree/main/kotlin-base
```

### templates Command

Manage template repositories.

```bash
./gradleInit.py templates [OPTIONS]
```

**Options:**
```
--list                       List available templates
--info NAME                  Show template details
--update                     Update template repositories
--add-repo NAME URL          Add custom repository
--help                       Show help
```

**Examples:**
```bash
# List templates
./gradleInit.py templates --list

# Update from GitHub
./gradleInit.py templates --update

# Show template info
./gradleInit.py templates --info kotlin-single

# Add custom repository
./gradleInit.py templates --add-repo myteam https://github.com/myteam/templates.git
```

### config Command

Manage configuration.

```bash
./gradleInit.py config [OPTIONS]
```

**Options:**
```
--show                       Display current configuration
--init                       Initialize configuration file
--help                       Show help
```

**Examples:**
```bash
# Show configuration
./gradleInit.py config --show

# Initialize config
./gradleInit.py config --init
```

---

## Troubleshooting

### Installation Issues

**Problem: `toml` module not found**

```
ModuleNotFoundError: No module named 'toml'
```

**Solution:**
```bash
pip install toml

# Or with user installation
pip install --user toml

# Windows
py -m pip install toml
```

**Problem: Permission denied**

```bash
./gradleInit.py: Permission denied
```

**Solution:**
```bash
chmod +x gradleInit.py
```

### Template Issues

**Problem: No templates found**

```
No templates found.
Run: gradleInit.py templates --update
```

**Solution:**
```bash
./gradleInit.py templates --update
```

**Problem: Template clone failed**

```
✗ Failed to clone: [WinError 5] Access is denied
```

**Solutions:**

1. **Close any programs** that might lock files (antivirus, file explorer)
2. **Run as administrator** (Windows)
3. **Delete cached templates:**
   ```bash
   rm -rf ~/.gradleInit/templates/official
   ./gradleInit.py templates --update
   ```

**Problem: GitHub URL not recognized**

```
✗ Template not found: https://github.com/...
```

**Solution:** Verify URL format:
```bash
# Correct formats:
https://github.com/user/repo.git
https://github.com/user/repo
https://github.com/user/repo/tree/main/subdir
github.com/user/repo  # Auto-adds https://
```

### Build Issues

**Problem: Gradle version incompatible with Kotlin**

```
Kotlin 2.2.20 isn't supported by Gradle 9.2
```

**Solution:** Use Gradle 8.14 (or 8.11+):
```bash
./gradleInit.py init my-app \
  --template kotlin-single \
  --config gradle_version=8.14
```

**Or change default:**
```toml
# ~/.gradleInit/config
[defaults]
gradle_version = "8.14"
```

**Problem: settings.gradle.kts error**

```
'void Settings_gradle.<init>(...)'
```

**Solution:** This is usually a Gradle version issue. Use 8.14:
```bash
cd my-app
./gradlew wrapper --gradle-version 8.14
./gradlew build
```

### Git Issues

**Problem: Git not configured**

```
Author identity unknown
```

**Solution:**
```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

**Problem: Git not found**

```
Warning: Failed to initialize git repository
```

**Solution:** Install Git:

```bash
# macOS
brew install git

# Ubuntu/Debian
sudo apt install git

# Fedora/RHEL
sudo dnf install git

# Windows
# Download from: https://git-scm.com/download/win
```

### Common Mistakes

❌ **Using uppercase in project names**
```bash
./gradleInit.py init MyProject  # Avoid
```
✅ **Use lowercase with hyphens**
```bash
./gradleInit.py init my-project
```

❌ **Forgetting --template**
```bash
./gradleInit.py init my-app
# Error: Template required
```
✅ **Always specify template**
```bash
./gradleInit.py init my-app --template kotlin-single
```

❌ **Wrong config syntax**
```bash
--config gradle_version 8.14  # Missing =
```
✅ **Use KEY=VALUE**
```bash
--config gradle_version=8.14
```

---

## Contributing

Contributions are welcome! Here's how you can help:

### Reporting Issues

1. Check [existing issues](https://github.com/stotz/gradleInit/issues)
2. Include version info:
   ```bash
   ./gradleInit.py --version
   python --version
   ```
3. Provide steps to reproduce
4. Include error messages

### Pull Requests

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Test thoroughly
4. Commit: `git commit -m "Add amazing feature"`
5. Push: `git push origin feature/amazing-feature`
6. Create Pull Request

### Areas for Contribution

- 📝 Documentation improvements
- 🎨 New templates
- 🐛 Bug fixes
- ✨ New features
- 🧪 Testing
- 🌐 Internationalization

---

## Roadmap

### Planned Features

- [ ] **Template marketplace** - Discover community templates
- [ ] **Template validation** - Verify template structure
- [ ] **Custom post-init scripts** - Run setup after creation
- [ ] **Docker support** - Generate Dockerfiles
- [ ] **CI/CD templates** - GitHub Actions, GitLab CI
- [ ] **Multi-platform templates** - Kotlin Multiplatform
- [ ] **Maven support** - Alternative to Gradle
- [ ] **Template wizard** - Create templates interactively

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **Kotlin Team** - Amazing programming language
- **Gradle** - Powerful build system
- **Python** - Versatile scripting language
- **Jinja2** - Template engine inspiration
- **Community** - Templates and feedback

---

## Support

- **Issues**: https://github.com/stotz/gradleInit/issues
- **Discussions**: https://github.com/stotz/gradleInit/discussions
- **Templates**: https://github.com/stotz/gradleInitTemplates
- **Kotlin Slack**: #gradle channel

---

## Changelog

### v1.4.0 (2025-11-15) - Current

**Major Features:**
- ✨ Interactive mode with prompts (`--interactive`)
- ✨ Template management commands
- ✨ Gradle version selection from services.gradle.org
- ✨ Automatic Gradle wrapper generation
- ✨ Built-in Git initialization with first commit
- ✨ Verbose command output
- ✨ GitHub subdirectory template support

**Templates:**
- ✨ kotlin-single - Simple Kotlin application
- ✨ kotlin-multi - Multi-module with buildSrc
- ✨ springboot - Spring Boot REST API
- ✨ ktor - Ktor server application

**Improvements:**
- 📚 Comprehensive documentation
- 🎨 Better error messages
- 🔧 Windows compatibility fixes
- ⚡ Faster template cloning
- 🛡️ Gradle 9.x compatibility handling

**Bug Fixes:**
- 🐛 Fixed template directory empty check
- 🐛 Fixed argparse prefix matching
- 🐛 Fixed Windows git clone locking
- 🐛 Fixed settings.gradle.kts for Gradle 9.2+

### v1.3.0 (2025-01-10)

**Initial modern release:**
- ✨ Jinja2 template engine
- ✨ GitHub template support
- ✨ Configuration management
- ✨ Version catalog support

---

**Made with ❤️ for the Kotlin/Gradle community**

*Start building amazing Kotlin projects today! 🚀*