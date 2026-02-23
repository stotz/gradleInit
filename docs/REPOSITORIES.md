# Repositories

[README.md](../README.md)  
[AI_Instruktion.md](AI_Instruktion.md)

---

[![Repositories](https://img.shields.io/badge/Repos-3-blue.svg)](REPOSITORIES.md)

## Structure

```
gradleInit (Main)
    |
    +-- gradleInitTemplates (Templates)
    |
    +-- gradleInitModules (Modules)
```

## gradleInit

**Repository:** https://github.com/stotz/gradleInit.git

Main project containing:
- `gradleInit.py` - Main script
- `docs/` - Documentation
- `test_*.py` - Test files

## gradleInitTemplates

**Repository:** https://github.com/stotz/gradleInitTemplates.git

Project templates:
- `kotlin-single/` - Single-module Kotlin project
- `kotlin-multi/` - Multi-module Kotlin project
- `ktor/` - Ktor server project
- `springboot/` - Spring Boot project
- `kotlin-javaFX/` - JavaFX desktop application
- `multiproject-root/` - Root for multi-module projects

Each template contains:
- `TEMPLATE.md` - Metadata and hints
- `build.gradle.kts` - Gradle build file
- `gradle/libs.versions.toml` - Version catalog
- Source files with Jinja2 placeholders

Signed files:
- `CHECKSUMS.sha256`
- `CHECKSUMS.sig`

## gradleInitModules

**Repository:** https://github.com/stotz/gradleInitModules.git

Optional modules for extended functionality:

```
gradleInitModules/
    MODULES.toml           # Module manifest
    CHECKSUMS.sha256       # Checksums
    CHECKSUMS.sig          # Signature
    resolvers/
        maven_central.py   # Maven Central version resolver
    integrations/
        (future)
```

### MODULES.toml Format

```toml
[repository]
name = "official"
description = "Official gradleInit modules"
version = "1.0.0"
min_gradleinit_version = "1.9.0"

[resolvers]
maven_central = { file = "resolvers/maven_central.py", class = "MavenCentral", default = true }
```

## Signing Workflow

### Initial Setup (once)

```bash
cd /path/to/gradleInit
python gradleInit.py keys --generate official
```

### Sign Templates

```bash
python gradleInit.py sign --repo /path/to/gradleInitTemplates --key official
```

### Sign Modules

```bash
python gradleInit.py sign --repo /path/to/gradleInitModules --key official
```

### Embed Public Key

Copy output of `gradleInit.py keys --export official` into `OFFICIAL_PUBLIC_KEY` constant in `gradleInit.py`.

## Version Synchronization

When releasing:

1. Update `SCRIPT_VERSION` in gradleInit.py
2. Sign templates repository
3. Sign modules repository
4. Commit and push all three repositories
5. Create matching Git tags

---

[README.md](../README.md)
