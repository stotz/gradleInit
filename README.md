# gradleInit.py - Modern Gradle Project Initializer

Ein umfassendes Tool zum Erstellen und Verwalten von Kotlin/Gradle Multiproject Builds mit Template-Unterstützung, Jinja2 Template Engine und intelligenter Konfigurationsverwaltung.

## Features

✨ **Template Support**
- Templates von GitHub, HTTPS URLs oder lokalem Filesystem
- Git-Repositories mit Branch/Tag Unterstützung
- Archive (ZIP, TAR.GZ) von HTTPS URLs
- Lokale Templates mit `file://` URLs

🎨 **Jinja2 Template Engine**
- Vollständige Jinja2 Syntax Unterstützung
- Custom Filters: `camelCase`, `pascalCase`, `snakeCase`, `kebabCase`
- Zugriff auf Umgebungsvariablen: `{{ env('MY_VAR', 'default') }}`
- Zugriff auf Config-Werte: `{{ config('custom.key', 'default') }}`

⚙️ **Konfigurationsmanagement**
- `.gradleInit` Konfigurationsdatei (TOML-Format)
- Umgebungsvariablen mit Default-Werten: `${VAR:-default}`
- Prioritäten: CLI Args > ENV > `.gradleInit`
- Version Pinning mit semantischer Versionierung

📦 **Version Constraints**
- Semantic Versioning Support: `>=1.2.0`, `<=2.0.0`, `~1.3.0`
- Wildcard Patterns: `1.4.*`
- Validierung bei Projekt-Initialisierung

🔄 **Shared Version Catalog**
- Zentrale Versionsverwaltung für Teams
- Von GitHub, HTTPS oder lokalem File
- Sync zwischen mehreren Projekten
- Override-Mechanismus für lokale Anpassungen

🌐 **Maven Central Integration**
- Automatische Package-Updates
- Breaking-Change Detection
- Update Policies: `pinned`, `last-stable`, `latest`, `major-only`, `minor-only`
- Smart Dependency Management

🍃 **Spring Boot BOM Support**
- Integration von 600+ getesteten Spring Boot Dependencies
- Automatischer BOM Sync
- Kompatibilitätsmodi: `pinned`, `last-stable`, `latest`
- Hybrid-Ansatz mit eigenem Catalog

🔧 **Intelligent Update Manager**
- Koordinierte Updates aus allen Quellen
- Auto-Check Intervalle (daily, weekly, monthly)
- Update-Reports mit Breaking-Change Warnings
- Self-Update Capability für das Script selbst

## Installation

### Voraussetzungen

- Python 3.7 oder höher
- Git (für Git-basierte Templates)

### Abhängigkeiten installieren

```bash
pip install jinja2 toml
```

**Oder mit pipx (empfohlen für isolierte Installation):**

```bash
pipx install --include-deps jinja2
pipx inject gradleInit toml
```

### Script ausführbar machen

```bash
chmod +x gradleInit.py
```

Optional: In PATH verfügbar machen

```bash
# Linux/macOS
sudo ln -s $(pwd)/gradleInit.py /usr/local/bin/gradleInit

# Oder zum User-Bin-Verzeichnis
mkdir -p ~/.local/bin
ln -s $(pwd)/gradleInit.py ~/.local/bin/gradleInit
# Stelle sicher, dass ~/.local/bin in deinem PATH ist
```

## Schnellstart

### Projekt mit Default-Template initialisieren

```bash
./gradleInit.py init my-awesome-project
```

### Projekt mit Custom Template

```bash
# GitHub Repository
./gradleInit.py init my-project --template https://github.com/username/gradle-template.git

# Spezifischer Branch/Tag
./gradleInit.py init my-project --template https://github.com/username/gradle-template.git --template-version v1.2.0

# HTTPS Archive
./gradleInit.py init my-project --template https://example.com/templates/kotlin-gradle.zip

# Lokales Template
./gradleInit.py init my-project --template file:///home/user/templates/gradle-kotlin
```

### Mit zusätzlichen Parametern

```bash
./gradleInit.py init my-project \
  --group com.mycompany \
  --version 1.0.0 \
  --gradle-version 9.0 \
  --kotlin-version 2.2.0 \
  --jdk-version 21
```

### Updates verwalten

```bash
# Alle Updates prüfen
./gradleInit.py update --check

# Shared Catalog synchronisieren
./gradleInit.py update --sync-shared

# Spring Boot BOM synchronisieren
./gradleInit.py update --sync-spring-boot 3.5.7

# Script selbst aktualisieren
./gradleInit.py update --self-update
```

## Konfiguration

### .gradleInit Datei

Erstelle eine `.gradleInit` Datei in deinem Home-Verzeichnis oder Projekt-Root:

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

[dependencies.shared_catalog]
enabled = true
source = "https://github.com/myorg/shared-catalog/raw/main/gradle/libs.versions.toml"
sync_on_update = true
override_local = false

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

[dependencies.spring_boot]
enabled = true
version = "3.5.7"
compatibility_mode = "last-stable"

[updates]
auto_check = true
check_interval = "weekly"
last_check = "2025-01-15T10:30:00"

[custom]
author = "Your Name"
license = "MIT"
# Beliebige Custom-Werte für Templates
```

### Konfiguration verwalten

```bash
# Konfiguration anzeigen
./gradleInit.py config --show

# Template URL setzen
./gradleInit.py config --template https://github.com/myorg/gradle-template.git

# Default Group setzen
./gradleInit.py config --group com.mycompany

# Version Constraint hinzufügen
./gradleInit.py config --constraint gradle_version ">=9.0"
./gradleInit.py config --constraint kotlin_version "~2.2.0"
```

### Umgebungsvariablen

```bash
# Template URL
export GRADLE_INIT_TEMPLATE="https://github.com/stotz/gradleInit.git"
export GRADLE_INIT_TEMPLATE_VERSION="v1.0.0"

# Default Werte
export GRADLE_INIT_GROUP="com.mycompany"
export GRADLE_INIT_VERSION="0.1.0"

# Versionen
export GRADLE_VERSION="9.0"
export KOTLIN_VERSION="2.2.0"
export JDK_VERSION="21"
```

**Mit Default-Werten:**

```bash
export GRADLE_VERSION="${GRADLE_VERSION:-9.0}"
export MY_CUSTOM_VAR="${MY_CUSTOM_VAR:-defaultValue}"
```

### Prioritäten

Die Werte werden in folgender Reihenfolge überschrieben:

1. **CLI Arguments** (höchste Priorität)
2. **Umgebungsvariablen**
3. **`.gradleInit` Config-Datei** (niedrigste Priorität)

```bash
# Example: CLI Args überschreiben alles
GRADLE_VERSION=8.0 ./gradleInit.py init my-project --gradle-version 9.0
# Verwendet 9.0 (CLI gewinnt)
```

## Templates erstellen

### Verzeichnisstruktur

```
my-template/
├── .gitignore.j2
├── settings.gradle.kts.j2
├── build.gradle.kts.j2
├── gradle.properties.j2
├── src/
│   └── main/
│       └── kotlin/
│           └── {{ project_group|replace('.', '/') }}/
│               └── Main.kt.j2
└── README.md.j2
```

### Template Syntax

Templates verwenden Jinja2 Syntax. Dateien mit `.j2` Extension werden automatisch gerendert und die Extension wird entfernt.

**Variablen:**

```kotlin
// build.gradle.kts.j2
group = "{{ project_group }}"
version = "{{ project_version }}"

kotlin {
    jvmToolchain({{ jdk_version }})
}
```

**Filters:**

```kotlin
// Main.kt.j2
package {{ project_group }}

class {{ project_name|pascalCase }} {
    fun greet() {
        println("Hello from {{ project_name|kebabCase }}!")
    }
}
```

Verfügbare Filter:
- `camelCase`: `my-project` → `myProject`
- `pascalCase`: `my-project` → `MyProject`
- `snakeCase`: `my-project` → `my_project`
- `kebabCase`: `my_project` → `my-project`

**Umgebungsvariablen:**

```yaml
# .github/workflows/ci.yml.j2
name: CI
env:
  DOCKER_REGISTRY: {{ env('DOCKER_REGISTRY', 'docker.io') }}
  BUILD_NUMBER: {{ env('BUILD_NUMBER', '0') }}
```

**Config-Werte:**

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

**Konditionelle Inhalte:**

```kotlin
// build.gradle.kts.j2
plugins {
    kotlin("jvm") version "{{ kotlin_version }}"
    {% if config('spring.enabled', false) %}
    id("org.springframework.boot") version "{{ config('spring.version', '3.2.0') }}"
    {% endif %}
}
```

**Schleifen:**

```kotlin
// settings.gradle.kts.j2
rootProject.name = "{{ project_name }}"

{% for module in config('modules', []) %}
include("{{ module }}")
{% endfor %}
```

### Template Context

Folgende Variablen sind standardmäßig verfügbar:

```python
{
    'project_name': 'my-project',           # Projekt Name
    'project_group': 'com.example',         # Group ID
    'project_version': '0.1.0',             # Version
    'gradle_version': '9.0',                # Gradle Version
    'kotlin_version': '2.2.0',              # Kotlin Version
    'jdk_version': '21',                    # JDK Version
    'timestamp': '2025-01-15T10:30:00',    # ISO Timestamp
    # Plus alle Werte aus [custom] Sektion der .gradleInit
}
```

### Verzeichnisse und Dateien erstellen

**Verzeichnisse werden automatisch erstellt:**

```
src/main/kotlin/{{ project_group|replace('.', '/') }}/
```

Für `project_group = "com.example.myapp"`:

```
src/main/kotlin/com/example/myapp/
```

**Binärdateien kopieren:**

Dateien ohne Template-Syntax (keine `{{ }}` oder `{% %}`) werden direkt kopiert:

```
my-template/
├── gradle/
│   └── wrapper/
│       ├── gradle-wrapper.jar      # Wird kopiert
│       └── gradle-wrapper.properties.j2  # Wird gerendert
```

## Version Constraints

### Unterstützte Operatoren

```toml
[constraints]
# Exact match
gradle_version = "9.0"
gradle_version = "==9.0"

# Greater than / Less than
kotlin_version = ">=2.2.0"
kotlin_version = "<=3.0.0"
kotlin_version = ">2.1.0"
kotlin_version = "<3.0.0"

# Tilde (patch-level updates erlaubt)
kotlin_version = "~2.2.0"  # Erlaubt 2.2.x

# Wildcard
jdk_version = "21.*"       # Erlaubt 21.0, 21.1, etc.
```

### Validierung

Bei der Projekt-Initialisierung werden alle Version Constraints geprüft:

```bash
$ ./gradleInit.py init my-project --kotlin-version 2.1.0

# Mit constraint kotlin_version = ">=2.2.0":
✗ kotlin_version 2.1.0 does not satisfy constraint >=2.2.0
```

## Advanced Usage

### Custom Template mit allen Features

```bash
./gradleInit.py init enterprise-app \
  --template https://github.com/myorg/enterprise-template.git \
  --template-version v2.5.0 \
  --group com.mycompany.enterprise \
  --version 1.0.0-SNAPSHOT \
  --gradle-version 9.0 \
  --kotlin-version 2.2.0 \
  --jdk-version 21 \
  --dir ~/projects/enterprise-app
```

### Template-Entwicklung Workflow

1. **Template Repository erstellen:**

```bash
mkdir gradle-template && cd gradle-template
git init
```

2. **Template-Dateien erstellen:**

```bash
# Basis-Struktur
touch settings.gradle.kts.j2
touch build.gradle.kts.j2
mkdir -p src/main/kotlin
```

3. **Lokal testen:**

```bash
./gradleInit.py init test-project --template file://$(pwd)
```

4. **Auf GitHub pushen:**

```bash
git remote add origin https://github.com/username/gradle-template.git
git push -u origin main
git tag v1.0.0
git push --tags
```

5. **Von GitHub verwenden:**

```bash
./gradleInit.py init prod-project \
  --template https://github.com/username/gradle-template.git \
  --template-version v1.0.0
```

### Shared Template mit Team

1. **Template in .gradleInit konfigurieren:**

```toml
[template]
url = "https://github.com/myorg/company-gradle-template.git"
version = "v2.0.0"

[defaults]
group = "com.myorg"

[custom]
company = "MyOrg Inc."
license = "Proprietary"
```

2. **Template global verfügbar machen:**

```bash
# In ~/.gradleInit oder /etc/gradleInit
cp .gradleInit ~/.gradleInit
```

3. **Team-Mitglieder initialisieren Projekte:**

```bash
# Verwendet automatisch das Company Template
./gradleInit.py init new-service
```

## Best Practices

### 1. Template Versionierung

Verwende Git Tags für stabile Template-Versionen:

```bash
git tag -a v1.0.0 -m "Stable template version 1.0.0"
git push --tags
```

Pinne Template-Version in `.gradleInit`:

```toml
[template]
url = "https://github.com/myorg/template.git"
version = "v1.0.0"  # Stabil, reproduzierbar
```

### 2. Separation of Concerns

Erstelle spezialisierte Templates:

```
templates/
├── kotlin-library/       # Für Libraries
├── kotlin-app/          # Für Applications
├── spring-boot/         # Für Spring Boot Apps
└── android/             # Für Android Apps
```

### 3. Template Dokumentation

Füge `TEMPLATE.md` zu jedem Template hinzu:

```markdown
# Template: Kotlin Library

## Required Variables
- project_name
- project_group
- project_version

## Custom Configuration
- custom.publish (boolean): Enable publishing to Maven Central
- custom.license: Project license (default: MIT)
```

### 4. CI/CD Integration

```yaml
# .github/workflows/new-project.yml
name: Create New Project
on:
  workflow_dispatch:
    inputs:
      project_name:
        required: true
      project_group:
        required: true

jobs:
  create:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install jinja2 toml
      
      - name: Create project
        run: |
          python gradleInit.py init ${{ inputs.project_name }} \
            --group ${{ inputs.project_group }} \
            --template ${{ secrets.TEMPLATE_URL }}
```

## Troubleshooting

### Package nicht gefunden

```
Missing required packages: jinja2, toml
Install with: pip install jinja2 toml
```

**Lösung:**

```bash
pip install jinja2 toml
# Oder mit pipx
pipx install --include-deps jinja2
pipx inject gradleInit toml
```

### Template Download fehlgeschlagen

```
✗ Failed to fetch template: ...
```

**Lösungen:**

1. **Prüfe URL:** Stelle sicher, dass die URL korrekt ist
2. **Prüfe Berechtigungen:** Bei privaten Repos, nutze Git Credentials
3. **Prüfe Netzwerk:** Teste mit `curl` oder `wget`
4. **Nutze lokales Template:** `--template file:///path/to/template`

### Template-Rendering Fehler

```
✗ Template error in settings.gradle.kts.j2: ...
```

**Debug-Strategie:**

1. **Syntax prüfen:** Validiere Jinja2 Syntax online
2. **Variablen prüfen:** `{{ variableName }}` statt `{{ variable_name }}`?
3. **Filter prüfen:** Nutze nur verfügbare Filter
4. **Escaping:** Nutze `{% raw %}...{% endraw %}` für literale `{{ }}`

### Version Constraint fehlgeschlagen

```
✗ gradle_version 8.5 does not satisfy constraint >=9.0
```

**Lösungen:**

1. **Version anpassen:** `--gradle-version 9.0`
2. **Constraint ändern:** `.gradleInit` bearbeiten
3. **Constraint entfernen:** Zeile aus `[constraints]` löschen

### Git Repository Fehler

```
⚠ Failed to initialize git repository
```

**Ursachen:**

1. Git nicht installiert: `sudo apt install git` (Linux)
2. Keine Git-Config: `git config --global user.name "..."`

## Beispiele

### Minimales Template

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

tasks.test {
    useJUnitPlatform()
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

include("core")
include("app")
```

### Spring Boot Template

Mit `.gradleInit`:

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

## Lizenz

MIT License - siehe LICENSE Datei für Details.

## Contributing

Contributions sind willkommen! Bitte erstelle einen Pull Request oder Issue auf GitHub.

## Support

- GitHub Issues: https://github.com/stotz/gradleInit/issues
- Dokumentation: https://github.com/stotz/gradleInit/wiki
