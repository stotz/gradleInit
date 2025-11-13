# gradleInit

A Python-based project initializer for modern Kotlin/Gradle multiproject builds with convention plugins, version catalogs, and integrated tooling.

## Features

- **Modern Gradle Setup**: Gradle 9.0 with Kotlin DSL, JDK 21 target
- **Convention Plugins**: Reusable build logic in composite build pattern
- **Version Catalog**: Centralized dependency management with type-safe accessors
- **Git Metadata Integration**: Automatic version information from git (commit, branch, author, timestamp)
- **Testing Framework**: JUnit 5, Kotest, MockK, Coroutines Test
- **Code Quality**: detekt for static analysis, Kover for coverage, Dokka for documentation
- **Self-Update**: Update script and version catalogs from GitHub
- **CI/CD Ready**: GitHub Actions workflow included
- **Backend Stack**: Pre-configured for Ktor, Koin, Exposed, Clikt, kotlinx-serialization

## Requirements

- Python 3.7+
- Git
- JDK 21+ (for created projects)

## Installation

```bash
git clone https://github.com/stotz/gradleInit.git
cd gradleInit
chmod +x gradleInit.py
```

## Usage

### Create New Project

```bash
# Basic project
python gradleInit.py my-project

# With custom package
python gradleInit.py my-project --package com.company.myproject

# With modules
python gradleInit.py my-project --modules app:application:Main,core,domain,data

# With git initialization
python gradleInit.py my-project --modules app:application:Main --git-init
```

### Module Types

**Library Module** (default):
```bash
--modules core
```
Creates a library with `kotlin-library-conventions` plugin and standard test dependencies.

**Application Module**:
```bash
--modules app:application:MainClass
```
Creates an application with `kotlin-application-conventions` plugin, logging, git properties, and main class.

### Self-Update

```bash
# Check for updates
python gradleInit.py --self-update --dry-run

# Apply update
python gradleInit.py --self-update

# Show version
python gradleInit.py --version
```

### Update Version Catalog

```bash
# Preview changes
python gradleInit.py --update-versions /path/to/project --dry-run

# Apply update
python gradleInit.py --update-versions /path/to/project

# Refresh dependencies
cd /path/to/project
./gradlew --refresh-dependencies
```

## Project Structure

```
my-project/
├── .editorconfig                       # Editor configuration
├── .gitignore                          # Git ignore rules
├── gradle.properties                   # Gradle settings
├── settings.gradle.kts                 # Project settings
├── build-logic/                        # Convention plugins
│   ├── settings.gradle.kts
│   ├── build.gradle.kts
│   ├── gradle/libs.versions.toml
│   └── src/main/kotlin/
│       ├── kotlin-common-conventions.gradle.kts
│       ├── kotlin-library-conventions.gradle.kts
│       └── kotlin-application-conventions.gradle.kts
├── config/detekt/
│   ├── detekt.yml                      # detekt configuration
│   └── baseline.xml
├── gradle/
│   ├── libs.versions.toml              # Version catalog
│   └── wrapper/
├── .github/workflows/
│   └── ci.yml                          # GitHub Actions
└── [modules]/
    ├── app/                            # Application module
    │   ├── src/main/kotlin/
    │   ├── src/main/resources/
    │   │   ├── version.properties
    │   │   ├── logback.xml
    │   │   └── git.properties          # Generated at build
    │   └── build.gradle.kts
    └── core/                           # Library module
        ├── src/main/kotlin/
        ├── src/test/kotlin/
        └── build.gradle.kts
```

## Convention Plugins

### kotlin-common-conventions

Shared configuration for all Kotlin modules:
- Kotlin JVM with toolchain 21
- Compiler options: strict JSR305, opt-in support
- JUnit Platform test configuration
- detekt static analysis
- Kover coverage reporting
- Dokka documentation generation

### kotlin-library-conventions

For library modules:
- Extends `kotlin-common-conventions`
- Java Library plugin
- Standard test dependencies
- JAR manifest configuration

### kotlin-application-conventions

For application modules:
- Extends `kotlin-common-conventions`
- Application plugin
- Git properties plugin (commit ID, branch, author, timestamp)
- Logging dependencies (kotlin-logging, Logback)
- Version properties in resources
- Custom `printVersion` task

## Version Catalog

Pre-configured dependencies in `gradle/libs.versions.toml`:

**Core:**
- kotlin = 2.2.0
- jvm-target = 21

**Testing:**
- junit-jupiter = 5.11.3
- kotest = 5.9.1
- mockk = 1.13.13
- kotlinx-coroutines-test = 1.9.0

**Backend (Optional):**
- ktor = 3.0.1
- koin = 4.0.0
- exposed = 0.56.0
- clikt = 5.0.1

**Code Quality:**
- detekt = 1.23.7
- kover = 0.9.0
- dokka = 2.0.0

**Bundles:**
- `testing`: JUnit, Kotest, MockK, Coroutines Test
- `logging`: kotlin-logging, SLF4J, Logback
- `ktor-server`: Server core, Netty, Content negotiation, Serialization
- `ktor-client`: Client core, CIO, Content negotiation
- `koin`: Core, Ktor integration
- `exposed`: Core, DAO, JDBC

## Gradle Tasks

### Building
```bash
./gradlew build                # Build all modules
./gradlew :module:build       # Build specific module
./gradlew clean               # Clean build outputs
```

### Testing
```bash
./gradlew test                # Run tests
./gradlew koverHtmlReport     # Generate coverage report
./gradlew koverVerify         # Verify coverage thresholds
```

### Code Quality
```bash
./gradlew detekt              # Run static analysis
./gradlew detektBaseline      # Create/update baseline
```

### Documentation
```bash
./gradlew dokkaHtml           # Generate KDoc HTML
```

### Running
```bash
./gradlew :app:run            # Run application
./gradlew printVersion        # Show version with git metadata
```

## Git Metadata

Application modules automatically include git information accessible at runtime:

```kotlin
val gitProps = Properties().apply {
    load(this::class.java.getResourceAsStream("/git.properties"))
}

println("Branch: ${gitProps["git.branch"]}")
println("Commit: ${gitProps["git.commit.id.abbrev"]}")
println("Author: ${gitProps["git.commit.user.name"]}")
println("Time: ${gitProps["git.commit.time"]}")
```

Or via Gradle:
```bash
./gradlew printVersion
```

## Configuration

### gradle.properties

```properties
# Gradle settings
org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
org.gradle.parallel=true
org.gradle.caching=true
org.gradle.configuration-cache=true

# Kotlin settings
kotlin.code.style=official
kotlin.incremental=true
kotlin.caching.enabled=true

# Project
version=0.1.0-SNAPSHOT
group=com.example
```

### detekt

Comprehensive rule configuration in `config/detekt/detekt.yml`:
- Complexity checks
- Code smells
- Coroutine best practices
- Exception handling
- Naming conventions
- Performance optimizations
- Potential bugs
- Style rules

## CI/CD

GitHub Actions workflow (`.github/workflows/ci.yml`) runs on push and pull requests:
- Checkout with full git history
- JDK 21 setup with Gradle cache
- Build all modules
- Run tests
- Generate coverage report
- Run detekt analysis
- Archive artifacts
- Publish test results

## Command Reference

### Project Creation

| Option | Description | Example |
|--------|-------------|---------|
| `project_name` | Project name (required) | `my-project` |
| `--package PKG` | Base package name | `--package com.company.project` |
| `--group GRP` | Group ID | `--group com.company` |
| `--modules MODS` | Comma-separated modules | `--modules app:application:Main,core` |
| `--git-init` | Initialize git repository | `--git-init` |
| `--no-verify` | Skip Gradle verification | `--no-verify` |
| `--template-url URL` | Custom template repository | `--template-url https://...` |
| `--template-dir DIR` | Local template directory | `--template-dir ~/templates` |

### Update Commands

| Option | Description | Example |
|--------|-------------|---------|
| `--self-update` | Update script from GitHub | `--self-update` |
| `--update-versions DIR` | Update version catalog | `--update-versions ./project` |
| `--dry-run` | Preview changes only | `--dry-run` |
| `--force` | Force update | `--force` |
| `--version` | Show script version | `--version` |

## Examples

### Backend API Project

```bash
python gradleInit.py backend-api \
  --package com.company.api \
  --group com.company \
  --modules app:application:Application,core,domain,data,web \
  --git-init

cd backend-api
./gradlew build
```

### CLI Application

```bash
python gradleInit.py my-cli \
  --package com.company.cli \
  --modules app:application:CliApp \
  --git-init

# Add Clikt dependency to app/build.gradle.kts
cd my-cli
./gradlew :app:run
```

### Microservices Structure

```bash
python gradleInit.py my-services \
  --package com.company.services \
  --modules \
    user-service:application:UserService,\
    order-service:application:OrderService,\
    shared-domain,\
    shared-core \
  --git-init
```

## Customization

### Using a Fork

```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/yourcompany/gradleInit.git

# Customize template files in template/
# Modify convention plugins in template/build-logic/src/main/kotlin/

# Use your fork
python gradleInit.py my-project \
  --template-url https://github.com/yourcompany/gradleInit.git
```

### Adding Dependencies

Edit `gradle/libs.versions.toml`:

```toml
[versions]
custom-lib = "1.0.0"

[libraries]
custom-lib = { module = "com.example:custom-lib", version.ref = "custom-lib" }
```

Use in modules:

```kotlin
dependencies {
    implementation(libs.custom.lib)
}
```

## Best Practices

1. **Use Convention Plugins**: Apply appropriate plugin to each module
2. **Leverage Version Catalog**: Define all dependencies in `libs.versions.toml`
3. **Maintain Test Coverage**: Use `koverVerify` to enforce thresholds
4. **Run detekt**: Check code quality before committing
5. **Document Public APIs**: Write KDoc for public interfaces
6. **Update Regularly**: Use `--update-versions` for dependency updates
7. **Test After Updates**: Always run full build and tests after version updates

## Security Considerations

### Self-Update

**Implemented:**
- HTTPS for all downloads
- Python syntax validation before installation
- Automatic backups with timestamp
- Rollback on failure

**Recommended for Production:**
- Use `--dry-run` before applying updates
- Pin to specific versions in CI/CD
- Review changes on GitHub before updating
- Consider using own fork for critical systems

### Version Catalog Updates

**Workflow:**
1. Use `--dry-run` to preview changes
2. Review release notes for breaking changes
3. Create feature branch
4. Apply update
5. Run full test suite
6. Create pull request for review

## Troubleshooting

### Permission Denied

```bash
chmod +x gradlew
chmod +x gradleInit.py
```

### Configuration Cache Warnings

```bash
./gradlew build --no-configuration-cache
```

### Clean Everything

```bash
./gradlew clean
rm -rf .gradle build-logic/.gradle
./gradlew build
```

### Update Fails

```bash
# Restore from backup
cp gradleInit.py.backup.* gradleInit.py
cp gradle/libs.versions.toml.backup.* gradle/libs.versions.toml
```

## Development

### Running Tests

```bash
chmod +x test-update-features.sh
./test-update-features.sh
```

### Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Update documentation
6. Submit pull request

## Version History

### 1.0.0 (Current)
- Initial release
- Convention plugins support
- Version catalog integration
- Git metadata integration
- Self-update functionality
- Version catalog update functionality
- Comprehensive documentation

## Resources

- [Gradle Best Practices](https://docs.gradle.org/current/userguide/best_practices_index.html)
- [Kotlin Documentation](https://kotlinlang.org/docs/home.html)
- [detekt](https://detekt.dev/)
- [Ktor](https://ktor.io/)
- [Koin](https://insert-koin.io/)

## License

MIT License - see LICENSE file for details

## Support

- Issues: [GitHub Issues](https://github.com/stotz/gradleInit/issues)
- Discussions: [GitHub Discussions](https://github.com/stotz/gradleInit/discussions)

## Acknowledgments

- Gradle team for best practices documentation
- Kotlin community for ecosystem tools
- Contributors to detekt, Kover, Dokka, and other tools
