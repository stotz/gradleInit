# Jinja2 Template Features in gradleInit

This document describes all available Jinja2 features, filters, functions, and variables available in gradleInit templates.

## Table of Contents

1. [Context Variables](#context-variables)
2. [Global Functions](#global-functions)
3. [Custom Filters](#custom-filters)
4. [Custom Tests](#custom-tests)
5. [Usage Examples](#usage-examples)

---

## Context Variables

These variables are automatically available in all templates:

### Project Variables
- `project_name` - The name of the project (e.g., "myApp")
- `group` - Maven group ID (e.g., "com.example")
- `version` - Project version (e.g., "1.0.0")
- `gradle_version` - Gradle version (e.g., "8.14")
- `kotlin_version` - Kotlin version (e.g., "2.1.0")
- `jdk_version` - JDK version (e.g., "21")

### Date/Time Variables
- `timestamp` - Current timestamp in ISO format (e.g., "2024-11-17T23:45:30.123456")
- `year` - Current year (e.g., 2024)
- `date` - Current date in YYYY-MM-DD format (e.g., "2024-11-17")

### Config Variables
All values from `~/.gradleInit/config` are available:
- From `[defaults]` section directly as variables
- From `[custom]` section directly as variables
- Use `config()` function for nested access

---

## Global Functions

### DateTime Functions

#### `now()`
Returns the current datetime object.

```jinja2
{# Get current datetime #}
{{ now() }}

{# Format current datetime #}
{{ now().strftime('%Y-%m-%d %H:%M:%S') }}

{# Get specific parts #}
Year: {{ now().year }}
Month: {{ now().month }}
Day: {{ now().day }}
```

#### `datetime`
Access to Python's datetime module.

```jinja2
{# Create specific datetime #}
{{ datetime(2024, 12, 25, 10, 30) }}

{# Parse from string #}
{{ datetime.fromisoformat('2024-11-17T23:45:30') }}
```

### Environment Functions

#### `env(key, default=None)`
Get environment variable value.

```jinja2
{# Get environment variable with default #}
{{ env('USER', 'unknown') }}
{{ env('HOME') }}
{{ env('PATH') }}

{# Conditional based on environment #}
{% if env('CI') %}
  Running in CI environment
{% endif %}
```

#### `getenv(key, default=None)`
Alias for `env()`.

```jinja2
{{ getenv('JAVA_HOME', '/usr/lib/jvm/default') }}
```

### Config Function

#### `config(key, default=None)`
Get configuration value using dot-notation.

```jinja2
{# Get nested config values #}
Company: {{ config('custom.company', 'Unknown') }}
Email: {{ config('custom.email', 'no-reply@example.com') }}
Database: {{ config('custom.database.type', 'h2') }}

{# Direct access to defaults #}
{{ config('group', 'com.example') }}
```

---

## Custom Filters

### Naming Convention Filters

#### `camelCase`
Convert to camelCase.

```jinja2
{{ "my_project_name" | camelCase }}
{# Output: myProjectName #}
```

#### `PascalCase`
Convert to PascalCase.

```jinja2
{{ "my_project_name" | PascalCase }}
{# Output: MyProjectName #}
```

#### `snake_case`
Convert to snake_case.

```jinja2
{{ "MyProjectName" | snake_case }}
{# Output: my_project_name #}
```

#### `kebab_case`
Convert to kebab-case.

```jinja2
{{ "MyProjectName" | kebab_case }}
{# Output: my-project-name #}
```

#### `package_path`
Convert package name to path.

```jinja2
{{ "com.example.myapp" | package_path }}
{# Output: com/example/myapp #}
```

### Text Manipulation Filters

#### `capitalize_first`
Capitalize only the first letter.

```jinja2
{{ "hello world" | capitalize_first }}
{# Output: Hello world #}
```

#### `lower_first`
Lowercase only the first letter.

```jinja2
{{ "Hello World" | lower_first }}
{# Output: hello World #}
```

### DateTime Filters

#### `datetime(format='%Y-%m-%d %H:%M:%S')`
Format a datetime string or object.

```jinja2
{# Format timestamp #}
{{ timestamp | datetime }}
{# Output: 2024-11-17 23:45:30 #}

{# Custom format #}
{{ timestamp | datetime('%d/%m/%Y %H:%M') }}
{# Output: 17/11/2024 23:45 #}
```

#### `date(format='%Y-%m-%d')`
Format as date only.

```jinja2
{{ timestamp | date }}
{# Output: 2024-11-17 #}

{{ timestamp | date('%d.%m.%Y') }}
{# Output: 17.11.2024 #}
```

#### `time(format='%H:%M:%S')`
Format as time only.

```jinja2
{{ timestamp | time }}
{# Output: 23:45:30 #}

{{ timestamp | time('%H:%M') }}
{# Output: 23:45 #}
```

---

## Custom Tests

### `springboot`
Test if value contains "springboot".

```jinja2
{% if project_name is springboot %}
  This is a Spring Boot project
{% endif %}
```

### `ktor`
Test if value contains "ktor".

```jinja2
{% if template_name is ktor %}
  This is a Ktor project
{% endif %}
```

---

## Usage Examples

### Complete File Header

```kotlin
/**
 * {{ project_name | PascalCase }}
 * 
 * @author {{ config('custom.author', 'Unknown') }}
 * @version {{ version }}
 * @created {{ date }}
 * @updated {{ now().strftime('%Y-%m-%d %H:%M:%S') }}
 * 
 * Copyright (c) {{ year }} {{ config('custom.company', 'Your Company') }}
 */
```

### Conditional Configuration

```kotlin
object Config {
    const val DEBUG = {% if env('DEBUG') == 'true' %}true{% else %}false{% endif %}
    const val DATABASE = "{{ config('custom.database', 'h2') }}"
    
    {% if env('CI') %}
    // CI-specific configuration
    const val CI_MODE = true
    {% endif %}
}
```

### Package Declarations

```kotlin
package {{ group }}.{{ project_name | snake_case }}

import {{ group }}.{{ project_name | snake_case }}.model.*
```

### Dynamic Imports Based on Project Type

```kotlin
{% if project_name is springboot %}
import org.springframework.boot.SpringApplication
import org.springframework.boot.autoconfigure.SpringBootApplication
{% elif project_name is ktor %}
import io.ktor.server.engine.*
import io.ktor.server.netty.*
{% endif %}
```

### README Generation

```markdown
# {{ project_name }}

**Version:** {{ version }}  
**Created:** {{ date }}  
**Kotlin:** {{ kotlin_version }}  
**Gradle:** {{ gradle_version }}

## Build

```bash
./gradlew build
```

## Run

```bash
./gradlew run
```

---

*Generated by gradleInit on {{ now().strftime('%Y-%m-%d at %H:%M:%S') }}*
```

### Environment-Specific Properties

```properties
# Application Properties
app.name={{ project_name }}
app.version={{ version }}
app.build.time={{ timestamp }}

# Environment
app.env={{ env('APP_ENV', 'development') }}
app.debug={{ env('DEBUG', 'false') }}

# User Info
app.build.user={{ env('USER', 'unknown') }}
app.build.host={{ env('HOSTNAME', 'unknown') }}
```

### Conditional Features

```kotlin
class {{ project_name | PascalCase }}Application {
    
    init {
        println("Starting {{ project_name }}...")
        println("Version: {{ version }}")
        println("Built: {{ date }}")
        
        {% if config('custom.features.database') %}
        // Database configuration
        setupDatabase()
        {% endif %}
        
        {% if config('custom.features.cache') %}
        // Cache configuration
        setupCache()
        {% endif %}
    }
}
```

### Complex Date Formatting

```kotlin
object BuildInfo {
    const val VERSION = "{{ version }}"
    const val BUILD_DATE = "{{ now().strftime('%Y-%m-%d') }}"
    const val BUILD_TIME = "{{ now().strftime('%H:%M:%S') }}"
    const val BUILD_TIMESTAMP = "{{ timestamp }}"
    const val BUILD_YEAR = {{ year }}
    const val BUILD_MONTH = {{ now().month }}
    const val BUILD_DAY = {{ now().day }}
}
```

---

## Common Patterns

### Safe Defaults

Always provide defaults for optional values:

```jinja2
{{ config('custom.company', 'Unknown Company') }}
{{ env('DATABASE_URL', 'jdbc:h2:mem:test') }}
```

### Type Conversion

```jinja2
{# Boolean from environment #}
const val ENABLED = {{ env('FEATURE_ENABLED', 'false') }}

{# Number from config #}
const val PORT = {{ config('server.port', 8080) }}
```

### String Safety

```jinja2
{# Ensure string values are quoted #}
const val NAME = "{{ project_name }}"
const val AUTHOR = "{{ config('custom.author', 'Unknown') }}"
```

---

## Troubleshooting

### Undefined Variable Error

If you get `'env' is undefined`, make sure you're using the latest version of gradleInit (>= v1.6.0).

### Date Formatting

Use Python's `strftime` format codes:
- `%Y` - 4-digit year (2024)
- `%m` - Month (01-12)
- `%d` - Day (01-31)
- `%H` - Hour 24h (00-23)
- `%M` - Minute (00-59)
- `%S` - Second (00-59)

Full reference: https://strftime.org/

### Environment Variables

Environment variables are read-only. To set defaults, use the `env()` function's second parameter.

---

## Best Practices

1. **Always provide defaults** for optional configuration
2. **Use semantic naming** - choose the right filter for the context
3. **Document template variables** in TEMPLATE.md
4. **Test templates** with different configurations
5. **Escape strings** properly in generated code
6. **Use datetime filters** instead of raw timestamp strings
7. **Leverage conditional blocks** for optional features
8. **Keep templates simple** - complex logic belongs in code

---

**Version:** 1.6.0  
**Updated:** 2024-11-17
