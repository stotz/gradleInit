# Git Files in gradleInit Projects

## What Gets Committed to Git?

When you create a project with gradleInit, these files are automatically committed:

### ✅ Build Configuration
```
✓ build.gradle.kts              # Build configuration
✓ settings.gradle.kts            # Project settings
✓ gradle.properties              # Gradle properties
✓ gradle/libs.versions.toml     # Version catalog
```

### ✅ Gradle Wrapper (IMPORTANT!)
```
✓ gradlew                        # Unix wrapper script
✓ gradlew.bat                    # Windows wrapper script
✓ gradle/wrapper/gradle-wrapper.jar         # Wrapper JAR
✓ gradle/wrapper/gradle-wrapper.properties  # Wrapper config
```

**Why commit the wrapper?**
- Ensures everyone uses same Gradle version
- No global Gradle installation needed
- Reproducible builds
- CI/CD works out of the box

### ✅ Source Code
```
✓ src/main/kotlin/**/*.kt       # Application code
✓ src/test/kotlin/**/*.kt       # Tests
✓ src/main/resources/**/*       # Resources
```

### ✅ Configuration Files
```
✓ .gitignore                    # Git ignore rules
✓ .editorconfig                 # Code style
✓ README.md                     # Documentation (if present)
```

## What Gets Ignored?

The `.gitignore` file prevents these from being committed:

### ❌ Build Outputs
```
✗ build/                        # Compiled code
✗ .gradle/                      # Gradle cache
✗ *.class                       # Compiled classes
```

### ❌ IDE Files
```
✗ .idea/                        # IntelliJ IDEA
✗ *.iml                         # IntelliJ modules
✗ .vscode/                      # VS Code
✗ .project, .classpath          # Eclipse
```

### ❌ OS Files
```
✗ .DS_Store                     # macOS
✗ Thumbs.db                     # Windows
```

### ❌ Temporary Files
```
✗ *.log                         # Log files
✗ *.swp, *~                     # Editor temp files
```

## Verify Your Git Repository

After creating a project, verify what's committed:

```bash
cd my-project

# Check status (should be clean)
git status

# Show commit history
git log --oneline

# List all tracked files
git ls-files

# Count files in git
git ls-files | wc -l
```

**Expected output:**
```bash
$ git status
On branch master
nothing to commit, working tree clean

$ git log --oneline
abc1234 (HEAD -> master) Initial commit from gradleInit

$ git ls-files | wc -l
11  # Typical kotlin-single project
```

## Standard .gitignore Content

gradleInit templates include this `.gitignore`:

```gitignore
# Gradle
.gradle/
build/
!gradle/wrapper/gradle-wrapper.jar

# Compiled
*.class

# IDE
.idea/
*.iml
*.iws
*.ipr
.vscode/
.project
.classpath
.settings/

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Temp
*.swp
*~
```

**Note:** The `!gradle/wrapper/gradle-wrapper.jar` line ensures the wrapper JAR IS committed despite `*.jar` being ignored elsewhere.

## Pushing to GitHub

### Verify Before Push

```bash
# Check what will be pushed
git log --oneline
git ls-files

# Verify nothing sensitive is committed
git diff --cached  # Should be empty if already committed
```

### Push Methods

**Option 1: New Repository (Recommended)**

```bash
# 1. Create repo on GitHub: https://github.com/new
#    DO NOT initialize with README/gitignore/license

# 2. Connect and push
cd my-project
git remote add origin https://github.com/USERNAME/my-project.git
git branch -M main
git push -u origin main
```

**Option 2: GitHub CLI (Easiest)**

```bash
cd my-project
gh repo create my-project --public --source=. --push

# Or private
gh repo create my-project --private --source=. --push
```

**Option 3: Existing Repository**

```bash
cd my-project
git remote add origin https://github.com/USERNAME/existing-repo.git
git branch -M main
git push -u origin main
```

### Change Remote URL

If you need to change the repository URL:

```bash
# Show current remote
git remote -v

# Change remote URL
git remote set-url origin https://github.com/USERNAME/new-repo.git

# Verify
git remote -v

# Push
git push -u origin main
```

## Common Issues

### Issue: Too Many Files in Git

If you accidentally committed build files:

```bash
# Remove from git but keep locally
git rm -r --cached build/
git rm -r --cached .gradle/
git rm -r --cached .idea/

# Commit the removal
git commit -m "Remove build artifacts from git"

# Push
git push
```

### Issue: Wrapper JAR Not in Git

The wrapper JAR **should** be committed! If missing:

```bash
# Check if .gitignore blocks it
grep wrapper .gitignore

# Should have: !gradle/wrapper/gradle-wrapper.jar

# Add wrapper JAR
git add -f gradle/wrapper/gradle-wrapper.jar
git commit -m "Add Gradle wrapper JAR"
git push
```

### Issue: Large Files Committed

If you accidentally committed large files:

```bash
# Remove from history (careful!)
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch path/to/large/file' \
  --prune-empty --tag-name-filter cat -- --all

# Or use BFG Repo-Cleaner (easier)
bfg --delete-files large-file.zip
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

## Best Practices

✅ **DO Commit:**
- All source code
- Build configuration
- Gradle wrapper
- Documentation
- Configuration templates

❌ **DON'T Commit:**
- Build outputs (`build/`, `.gradle/`)
- IDE-specific files (`.idea/`, `*.iml`)
- OS-specific files (`.DS_Store`)
- Secrets (API keys, passwords)
- Large binary files
- Temporary files

## GitHub Repository Settings

After pushing, configure your repository:

1. **Add Description**
   - Settings → General → Description

2. **Add Topics**
   - Settings → General → Topics
   - Examples: `kotlin`, `gradle`, `gradle-kotlin-dsl`

3. **Configure Branch Protection**
   - Settings → Branches → Add rule
   - Protect `main` branch

4. **Enable Actions**
   - Actions → Set up workflow
   - Add CI/CD pipeline

5. **Add License**
   - Add file → Create new file → `LICENSE`
   - Or: Settings → Add license

## Verify on GitHub

After pushing, check:

```
Repository
├── 📁 gradle/
│   ├── 📁 wrapper/
│   │   ├── gradle-wrapper.jar     ✓
│   │   └── gradle-wrapper.properties ✓
│   └── libs.versions.toml         ✓
├── 📁 src/
│   ├── 📁 main/kotlin/
│   └── 📁 test/kotlin/
├── 📄 build.gradle.kts            ✓
├── 📄 settings.gradle.kts         ✓
├── 📄 gradle.properties           ✓
├── 📄 gradlew                     ✓
├── 📄 gradlew.bat                 ✓
├── 📄 .gitignore                  ✓
├── 📄 .editorconfig               ✓
└── 📄 README.md (optional)        ✓

❌ Should NOT see:
├── 📁 build/
├── 📁 .gradle/
├── 📁 .idea/
└── 📄 *.class
```

## Collaborating

For team projects:

```bash
# Clone repository
git clone https://github.com/USERNAME/project.git
cd project

# Build immediately (wrapper included!)
./gradlew build

# No need to install Gradle globally!
```

**This is why the wrapper is so important!**

---

**Summary:** gradleInit creates a clean, professional Git repository with only the necessary files committed. The Gradle wrapper ensures reproducible builds, and the `.gitignore` keeps build artifacts out of version control.
