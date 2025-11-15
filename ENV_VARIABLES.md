# Environment Variables Guide

Complete guide for using environment variables with gradleInit.

## Quick Reference

### Standard Variables

```bash
# Template
export GRADLE_INIT_TEMPLATE="https://github.com/myorg/template.git"
export GRADLE_INIT_TEMPLATE_VERSION="v1.0.0"

# Project defaults
export GRADLE_INIT_GROUP="com.mycompany"
export GRADLE_INIT_VERSION="0.1.0"

# Tool versions
export GRADLE_VERSION="9.0"
export KOTLIN_VERSION="2.2.0"
export JDK_VERSION="21"
```

### Custom Variables (for Templates)

**Any variable with `GRADLE_INIT_*` prefix:**

```bash
export GRADLE_INIT_AUTHOR="Hans Muster"
export GRADLE_INIT_EMAIL="hans.muster@company.com"
export GRADLE_INIT_COMPANY="Company AG"
export GRADLE_INIT_LICENSE="MIT"
export GRADLE_INIT_DESCRIPTION="My awesome project"
```

**Becomes in templates:**

```jinja2
Author: {{ config('custom.author') }}
Email: {{ config('custom.email') }}
Company: {{ config('custom.company') }}
License: {{ config('custom.license') }}
Description: {{ config('custom.description') }}
```

## Complete Setup Examples

### Example 1: Personal Projects

**~/.bashrc or ~/.zshrc:**

```bash
# gradleInit Configuration
export GRADLE_INIT_TEMPLATE="https://github.com/yourusername/kotlin-template.git"
export GRADLE_INIT_GROUP="com.yourname"

# Personal Info
export GRADLE_INIT_AUTHOR="Your Name"
export GRADLE_INIT_EMAIL="you@example.com"
export GRADLE_INIT_LICENSE="MIT"

# Tool Versions
export GRADLE_VERSION="9.0"
export KOTLIN_VERSION="2.2.0"
export JDK_VERSION="21"
```

**Usage:**

```bash
./gradleInit.py init my-project
# All ENV variables automatically applied!
```

### Example 2: Company Projects (Entris Banking)

**~/.bashrc or ~/.zshrc:**

```bash
# Company Template
export GRADLE_INIT_TEMPLATE="https://github.com/myorg/gradle-template.git"
export GRADLE_INIT_TEMPLATE_VERSION="v2.0.0"

# Company Defaults
export GRADLE_INIT_GROUP="com.mycompany"
export GRADLE_INIT_COMPANY="Company AG"
export GRADLE_INIT_AUTHOR="Hans Muster"
export GRADLE_INIT_EMAIL="hans.muster@company.com"
export GRADLE_INIT_LICENSE="Proprietary"

# Company Standards
export GRADLE_VERSION="9.0"
export KOTLIN_VERSION="2.2.0"
export JDK_VERSION="21"

# Company Specific
export GRADLE_INIT_MAVEN_URL="https://maven.myorg.ch"
export GRADLE_INIT_DOCKER_REGISTRY="registry.myorg.ch"
```

**Usage:**

```bash
./gradleInit.py init customer-service
# Creates project with all company settings
```

### Example 3: Multi-Environment

**~/.bashrc:**

```bash
# Function to switch environments
function gradle-env-work() {
    export GRADLE_INIT_TEMPLATE="https://github.com/company/template.git"
    export GRADLE_INIT_GROUP="com.company"
    export GRADLE_INIT_AUTHOR="Hans Muster"
    export GRADLE_INIT_EMAIL="urs.stotz@company.com"
    export GRADLE_INIT_COMPANY="My Company Inc."
    export GRADLE_INIT_LICENSE="Proprietary"
    echo "✓ Switched to work environment"
}

function gradle-env-personal() {
    export GRADLE_INIT_TEMPLATE="https://github.com/yourusername/template.git"
    export GRADLE_INIT_GROUP="com.yourname"
    export GRADLE_INIT_AUTHOR="Your Name"
    export GRADLE_INIT_EMAIL="you@personal.com"
    export GRADLE_INIT_COMPANY=""
    export GRADLE_INIT_LICENSE="MIT"
    echo "✓ Switched to personal environment"
}

# Set default
gradle-env-personal
```

**Usage:**

```bash
# Work project
gradle-env-work
./gradleInit.py init work-project

# Personal project
gradle-env-personal
./gradleInit.py init hobby-project
```

## Priority System

**Priority Order (highest to lowest):**

1. **CLI Arguments** (highest)
2. **Environment Variables**
3. **~/.gradleInit file**
4. **Defaults** (lowest)

**Example:**

```bash
# ~/.gradleInit
[custom]
author = "Config File Author"

# ENV
export GRADLE_INIT_AUTHOR="ENV Author"

# CLI (not directly supported for custom values, use config)
./gradleInit.py init my-project

# Result: Uses "ENV Author" (ENV > Config File)
```

## ENV Variable Mapping

### Standard Mappings

| ENV Variable | Maps To | Example |
|--------------|---------|---------|
| `GRADLE_INIT_TEMPLATE` | `template.url` | Repository URL |
| `GRADLE_INIT_TEMPLATE_VERSION` | `template.version` | v1.0.0, main |
| `GRADLE_INIT_GROUP` | `defaults.group` | com.mycompany |
| `GRADLE_INIT_VERSION` | `defaults.version` | 0.1.0 |
| `GRADLE_VERSION` | `versions.gradle` | 9.0 |
| `KOTLIN_VERSION` | `versions.kotlin` | 2.2.0 |
| `JDK_VERSION` | `versions.jdk` | 21 |

### Custom Mappings

**Pattern:** `GRADLE_INIT_*` → `custom.*`

| ENV Variable | Template Access | Example Value |
|--------------|-----------------|---------------|
| `GRADLE_INIT_AUTHOR` | `{{ config('custom.author') }}` | John Doe |
| `GRADLE_INIT_EMAIL` | `{{ config('custom.email') }}` | john@example.com |
| `GRADLE_INIT_COMPANY` | `{{ config('custom.company') }}` | ACME Corp |
| `GRADLE_INIT_LICENSE` | `{{ config('custom.license') }}` | MIT |
| `GRADLE_INIT_WEBSITE` | `{{ config('custom.website') }}` | https://example.com |
| `GRADLE_INIT_DESCRIPTION` | `{{ config('custom.description') }}` | My project |

**Any custom variable:**

```bash
export GRADLE_INIT_DOCKER_REGISTRY="registry.company.com"
export GRADLE_INIT_MAVEN_URL="https://maven.company.com"
export GRADLE_INIT_TEAM="Backend Team"
```

Accessible as:
```jinja2
{{ config('custom.docker_registry') }}
{{ config('custom.maven_url') }}
{{ config('custom.team') }}
```

## Using with ~/.gradleInit

**Combine ENV and Config File:**

**~/.gradleInit:**
```toml
[custom]
author = "Default Author"
license = "MIT"
```

**ENV (overrides config):**
```bash
export GRADLE_INIT_AUTHOR="Hans Muster"
# license stays "MIT" from config
```

**Result:**
- `author` = "Hans Muster" (from ENV)
- `license` = "MIT" (from config)

## Default Values

Use shell parameter expansion for defaults:

```bash
export GRADLE_VERSION="${GRADLE_VERSION:-9.0}"
export KOTLIN_VERSION="${KOTLIN_VERSION:-2.2.0}"
export GRADLE_INIT_AUTHOR="${GRADLE_INIT_AUTHOR:-Unknown}"
export GRADLE_INIT_LICENSE="${GRADLE_INIT_LICENSE:-MIT}"
```

**How it works:**
- If `GRADLE_VERSION` already set → use existing value
- If not set → use default value `9.0`

## Template Examples

### Example 1: Using Author Info

**build.gradle.kts.j2:**
```kotlin
tasks.jar {
    manifest {
        attributes(
            "Implementation-Vendor" to "{{ config('custom.author', 'Unknown') }}",
            "Implementation-Vendor-Email" to "{{ config('custom.email', '') }}"
        )
    }
}
```

**With ENV:**
```bash
export GRADLE_INIT_AUTHOR="Hans Muster"
export GRADLE_INIT_EMAIL="hans.muster@company.com"
```

**Result:**
```kotlin
"Implementation-Vendor" to "Hans Muster",
"Implementation-Vendor-Email" to "hans.muster@company.com"
```

### Example 2: Company Info in README

**README.md.j2:**
```markdown
# {{ project_name }}

{{ config('custom.description', 'A Kotlin project') }}

## Author

{{ config('custom.author', 'Unknown') }}
{% if config('custom.company') %}
{{ config('custom.company') }}
{% endif %}
{% if config('custom.email') %}
Contact: {{ config('custom.email') }}
{% endif %}

## License

{{ config('custom.license', 'MIT') }}
```

**With ENV:**
```bash
export GRADLE_INIT_AUTHOR="Hans Muster"
export GRADLE_INIT_EMAIL="hans.muster@company.com"
export GRADLE_INIT_COMPANY="Company AG"
export GRADLE_INIT_LICENSE="Proprietary"
export GRADLE_INIT_DESCRIPTION="Customer Service Microservice"
```

### Example 3: Docker Registry

**build.gradle.kts.j2:**
```kotlin
tasks.register("dockerBuild") {
    doLast {
        val registry = "{{ config('custom.docker_registry', 'docker.io') }}"
        val image = "$registry/{{ project_group }}/{{ project_name }}:{{ project_version }}"
        println("Building: $image")
    }
}
```

**With ENV:**
```bash
export GRADLE_INIT_DOCKER_REGISTRY="registry.myorg.ch"
```

## Verification

Check which values are being used:

```bash
# Show current config
./gradleInit.py config --show

# Create test project and check generated files
./gradleInit.py init test-project --dir /tmp/test-project
cat /tmp/test-project/README.md
cat /tmp/test-project/build.gradle.kts
```

## Tips

### 1. Use a Setup Script

**setup-gradle-env.sh:**
```bash
#!/bin/bash

export GRADLE_INIT_TEMPLATE="https://github.com/myorg/gradle-template.git"
export GRADLE_INIT_GROUP="com.mycompany"
export GRADLE_INIT_AUTHOR="Hans Muster"
export GRADLE_INIT_EMAIL="hans.muster@company.com"
export GRADLE_INIT_COMPANY="Company AG"
export GRADLE_VERSION="9.0"
export KOTLIN_VERSION="2.2.0"
export JDK_VERSION="21"

echo "✓ Gradle environment configured"
echo "  Author: $GRADLE_INIT_AUTHOR"
echo "  Company: $GRADLE_INIT_COMPANY"
echo "  Template: $GRADLE_INIT_TEMPLATE"
```

**Usage:**
```bash
source setup-gradle-env.sh
./gradleInit.py init my-project
```

### 2. Per-Project Override

```bash
# Company defaults loaded from ~/.bashrc
# Override for specific project
GRADLE_INIT_LICENSE="Apache-2.0" \
GRADLE_INIT_DESCRIPTION="Open source library" \
./gradleInit.py init open-source-lib
```

### 3. CI/CD Integration

**GitHub Actions:**
```yaml
env:
  GRADLE_INIT_AUTHOR: ${{ secrets.COMPANY_NAME }}
  GRADLE_INIT_EMAIL: ${{ secrets.CONTACT_EMAIL }}
  GRADLE_INIT_COMPANY: ${{ secrets.COMPANY_NAME }}
  GRADLE_VERSION: "9.0"

jobs:
  create:
    steps:
      - run: |
          python gradleInit.py init ${{ inputs.project_name }}
```

## Common Patterns

### Pattern 1: Team Settings

```bash
# ~/.bashrc - shared by team via dotfiles repo
export GRADLE_INIT_COMPANY="Company AG"
export GRADLE_INIT_MAVEN_URL="https://maven.myorg.ch"
export GRADLE_INIT_DOCKER_REGISTRY="registry.myorg.ch"
export GRADLE_VERSION="9.0"
export KOTLIN_VERSION="2.2.0"
```

### Pattern 2: Personal Override

```bash
# Personal settings override team defaults
export GRADLE_INIT_AUTHOR="Hans Muster"
export GRADLE_INIT_EMAIL="hans.muster@company.com"
```

### Pattern 3: Project-Specific

```bash
# One-time override for special project
GRADLE_INIT_DESCRIPTION="Legacy system migration" \
GRADLE_INIT_JDK_VERSION="17" \
./gradleInit.py init legacy-migration
```

## Troubleshooting

### Values Not Applied

**Check priority:**
```bash
# 1. Check ENV
echo $GRADLE_INIT_AUTHOR

# 2. Check config
cat ~/.gradleInit

# 3. Verify in generated project
./gradleInit.py init test --dir /tmp/test
grep -r "author" /tmp/test/
```

### Wrong Values Used

**Debug:**
```bash
# Create project with verbose output
./gradleInit.py init debug-project 2>&1 | tee debug.log

# Check what was actually used
cat debug-project/README.md
cat debug-project/build.gradle.kts
```

---

**Complete example for Entris Banking:**

```bash
# ~/.bashrc
export GRADLE_INIT_TEMPLATE="https://github.com/myorg/gradle-template.git"
export GRADLE_INIT_GROUP="com.mycompany"
export GRADLE_INIT_AUTHOR="Hans Muster"
export GRADLE_INIT_EMAIL="hans.muster@company.com"
export GRADLE_INIT_COMPANY="Company AG"
export GRADLE_INIT_LICENSE="Proprietary"
export GRADLE_INIT_MAVEN_URL="https://maven.myorg.ch"
export GRADLE_INIT_DOCKER_REGISTRY="registry.myorg.ch"
export GRADLE_VERSION="9.0"
export KOTLIN_VERSION="2.2.0"
export JDK_VERSION="21"
```

Then just:
```bash
./gradleInit.py init customer-service
# All company settings automatically applied!
```