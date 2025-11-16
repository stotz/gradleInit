# Enhanced Template Hint System

## Overview

The enhanced hint system allows template authors to embed metadata directly in template files using a special syntax. This provides validation, default values, and automatic documentation generation.

## Syntax

```
{{ @@[sort]|(regex)|[help_text]=[default]@@variable_name }}
```

### Components

| Component | Required | Description | Example |
|-----------|----------|-------------|---------|
| `@@` | Yes | Hint delimiter | `@@...@@` |
| `sort` | No | Sort order for menu (01-99) | `01` |
| `\|` | No | Separator between components | `\|` |
| `(regex)` | No | Validation regex pattern | `(11\|17\|21)` |
| `help_text` | Yes | Help text shown to users | `JDK version` |
| `=default` | No | Default value | `=21` |
| `variable_name` | Yes | Jinja2 variable name | `jdk_version` |

## Examples

### 1. Full Syntax (sort + regex + help + default)

```kotlin
kotlin {
    jvmToolchain({{ @@03|(11|17|21)|JDK version=21@@jdk_version }})
}
```

**Features:**
- Sort order: 3 (shown third in interactive menu)
- Regex validation: Only accepts `11`, `17`, or `21`
- Help text: "JDK version"
- Default value: `21`
- Variable: `jdk_version`

### 2. Regex + Help + Default (no sort)

```kotlin
database = "{{ @@(h2|postgres|mysql)|Database type=h2@@db_type }}"
```

**Features:**
- Sort order: 999 (default, shown last)
- Regex validation: Only accepts `h2`, `postgres`, or `mysql`
- Help text: "Database type"
- Default value: `h2`

### 3. Help + Default Only

```kotlin
group = "{{ @@01|Maven group ID=com.example@@group }}"
```

**Features:**
- Sort order: 1
- No regex validation
- Help text: "Maven group ID"
- Default value: `com.example`

### 4. Windows Paths with Regex

```kotlin
installDir = "{{ @@04|(c:\\\\user|c:\\\\home)|Install Dir=c:\\\\home@@install_dir }}"
```

**Features:**
- Works correctly with Windows paths containing `:`
- Regex validates path options
- Default: `c:\home`

### 5. URLs with Regex

```kotlin
repo = "{{ @@(http://.*|https://.*)|Repository URL=https://github.com@@repo_url }}"
```

**Features:**
- Validates http:// or https:// URLs
- Default: `https://github.com`

### 6. Help Text Only

```kotlin
version = "{{ @@02|Application version@@version }}"
```

**Features:**
- Sort order: 2
- No regex validation
- No default value (user must provide)

### 7. Plain Variable (backward compatible)

```kotlin
author = "{{ author }}"
```

**Features:**
- No metadata
- Works as before
- Sort order: 999 (shown last)

## Validation Behavior

### Interactive Mode

When a user enters a value in interactive mode:

1. If the variable has a regex pattern, the value is validated
2. If validation fails, the error message shows the pattern
3. The user is prompted to enter a valid value
4. This repeats until a valid value is provided

### Command-Line Mode

When a value is provided via CLI argument:

1. If the variable has a regex pattern, the value is validated
2. If validation fails, an error message is displayed with:
   - The invalid value
   - The regex pattern
   - The template variable name
   - The help text
3. The program exits with an error code

## Default Value Behavior

Default values are applied with the following priority:

1. **CLI arguments** (highest priority)
2. **Environment variables** (`GRADLE_INIT_*`)
3. **Config file** (`.gradleInit`)
4. **Template defaults** (from hints)
5. **System defaults** (lowest priority)

### Example Priority

Given this template variable:

```kotlin
group = "{{ @@01|Maven group ID=com.example@@group }}"
```

Values are resolved in this order:

```bash
# 1. CLI argument (highest)
gradleInit.py init my-app --template kotlin-single --group com.mycompany
# Result: group = "com.mycompany"

# 2. Environment variable
export GRADLE_INIT_GROUP=com.envcompany
gradleInit.py init my-app --template kotlin-single
# Result: group = "com.envcompany"

# 3. Config file ~/.gradleInit
defaults:
  group: com.configcompany
# Result: group = "com.configcompany"

# 4. Template default (from hint)
# No CLI, ENV, or config value
# Result: group = "com.example"
```

## Template Compilation

During project generation, hints are automatically removed:

**Template source:**
```kotlin
group = "{{ @@01|Maven group ID=com.example@@group }}"
version = "{{ @@02|Application version=1.0.0@@version }}"
kotlin {
    jvmToolchain({{ @@03|(11|17|21)|JDK version=21@@jdk_version }})
}
```

**Compiled output (with values):**
```kotlin
group = "com.mycompany"
version = "1.0.0"
kotlin {
    jvmToolchain(21)
}
```

## Benefits

### For Template Authors

- **Self-documenting templates**: Metadata lives with the template
- **Single source of truth**: No separate documentation needed
- **Input validation**: Regex ensures valid values
- **Better UX**: Users see helpful prompts and defaults

### For Users

- **Clear prompts**: Sorted, meaningful questions
- **Sensible defaults**: Most values pre-filled
- **Validation**: Immediate feedback on invalid input
- **Better errors**: Clear error messages with patterns

### For Tools

- **Automatic --help**: Generated from hints
- **Interactive menus**: Sorted, validated prompts
- **IDE support**: Future autocomplete/validation
- **Documentation**: Auto-generated from hints

## Migration Guide

### For Existing Templates

Old syntax still works:

```kotlin
// Old (still works)
group = "{{ group }}"
```

New syntax is optional:

```kotlin
// New (recommended)
group = "{{ @@01|Maven group ID=com.example@@group }}"
```

Mix and match:

```kotlin
// Enhanced
group = "{{ @@01|Maven group ID=com.example@@group }}"

// Plain
description = "{{ description }}"
```

### Adding Hints to Existing Templates

1. Identify variables that benefit from hints
2. Add sort order for important variables (01-10)
3. Add regex for constrained values
4. Add defaults for common values
5. Keep help text short and clear

### Testing

After adding hints, test:

1. **Parsing**: `python test_hint_parsing.py`
2. **Interactive**: `gradleInit.py init test --template x --interactive`
3. **CLI**: `gradleInit.py init test --template x --group com.test`
4. **Validation**: Try invalid regex values
5. **Defaults**: Omit values and check defaults

## Advanced Examples

### Boolean with Regex

```kotlin
useCache = {{ @@(true|false)|Enable caching=true@@use_cache }}
```

### Version with Regex

```kotlin
kotlinVersion = "{{ @@(\d+\.\d+\.\d+)|Kotlin version=2.0.0@@kotlin_version }}"
```

### Multiple Choice with Sort

```kotlin
// Database (shown first)
database = "{{ @@01|(h2|postgres|mysql)|Database=h2@@database }}"

// Cache (shown second)
cache = "{{ @@02|(redis|memcached|none)|Cache=redis@@cache }}"
```

### Complex Path with Default

```kotlin
dataDir = "{{ @@(\.\/data|\/opt\/app\/data|C:\\\\AppData)|Data directory=./data@@data_dir }}"
```

## Why `|` as Separator?

The `|` character was chosen over `:` because:

1. **Regex compatibility**: Regex patterns are wrapped in `(...)`, so `|` inside is regex-OR
2. **Windows paths**: Paths like `c:\user` contain `:`, which would conflict
3. **URLs**: URLs like `https://example.com` contain `:`, which would conflict
4. **Clear separation**: `|` clearly separates components outside of `(...)`

Example problem with `:` separator:

```kotlin
// BAD: Ambiguous parsing with ':'
{{ @@04:(c:\user|c:\home):Install Dir=c:\home@@install_dir }}
//         ^                ^            ^
//         |                |            |
//      separator?      separator?  separator?

// GOOD: Clear parsing with '|'
{{ @@04|(c:\user|c:\home)|Install Dir=c:\home@@install_dir }}
//      (     regex     ) |   help   |
```

## Future Enhancements

### Planned Features

- **Type system**: `{{ @@int|Port number=8080@@port }}`
- **Required flag**: `{{ @@required|Database URL@@db_url }}`
- **Choices list**: `{{ @@choices:red,green,blue|Color=red@@color }}`
- **Min/max validation**: `{{ @@min:1|max:100|Thread count=10@@threads }}`
- **IDE integration**: Autocomplete and validation in IDEs
- **Interactive builder**: GUI for creating hint syntax

### Example Future Syntax

```kotlin
// Type-aware with range
port = {{ @@int|min:1024|max:65535|Port number=8080@@port }}

// Required field
apiKey = "{{ @@required|string|API key@@api_key }}"

// Enum-like choices
logLevel = "{{ @@choices:DEBUG,INFO,WARN,ERROR|Log level=INFO@@log_level }}"
```
