# Windows Setup Guide

Complete guide for using gradleInit on Windows.

## Installation

### 1. Install Python

Download from https://www.python.org/downloads/ (Python 3.7+)

**Important:** Check "Add Python to PATH" during installation!

Verify:
```powershell
python --version
```

### 2. Install Dependencies

```powershell
pip install jinja2 toml
```

### 3. Download gradleInit.py

```powershell
# Download to your preferred location
cd C:\Users\YourUsername\tools
# Download gradleInit.py here
```

## Configuration

### Option 1: .gradleInit File (Recommended)

Create `%USERPROFILE%\.gradleInit`:

**Location:** `C:\Users\YourUsername\.gradleInit`

**Content:**
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

[custom]
author = "Hans Muster"
email = "hans.muster@company.com"
company = "Company AG"
license = "MIT"
```

**Create file:**

```powershell
# Using PowerShell
notepad $env:USERPROFILE\.gradleInit
# or
code $env:USERPROFILE\.gradleInit
```

### Option 2: Environment Variables

#### PowerShell Profile

Edit your PowerShell profile:

```powershell
notepad $PROFILE
```

Add configuration:
```powershell
# gradleInit Configuration
$env:GRADLE_INIT_TEMPLATE = "https://github.com/stotz/gradleInit.git"
$env:GRADLE_INIT_GROUP = "com.mycompany"

# Personal Info
$env:GRADLE_INIT_AUTHOR = "Hans Muster"
$env:GRADLE_INIT_EMAIL = "hans.muster@company.com"
$env:GRADLE_INIT_COMPANY = "Company AG"
$env:GRADLE_INIT_LICENSE = "MIT"

# Tool Versions
$env:GRADLE_VERSION = "9.0"
$env:KOTLIN_VERSION = "2.2.0"
$env:JDK_VERSION = "21"
```

**Reload profile:**
```powershell
. $PROFILE
```

#### System Environment Variables (Persistent)

**Via GUI:**
1. Press `Win + X`, select "System"
2. Click "Advanced system settings"
3. Click "Environment Variables"
4. Under "User variables", click "New"
5. Add variables:
   - `GRADLE_INIT_AUTHOR` = `Hans Muster`
   - `GRADLE_INIT_EMAIL` = `hans.muster@company.com`
   - `GRADLE_INIT_COMPANY` = `Company AG`

**Via PowerShell (Admin):**
```powershell
[System.Environment]::SetEnvironmentVariable('GRADLE_INIT_AUTHOR', 'Hans Muster', 'User')
[System.Environment]::SetEnvironmentVariable('GRADLE_INIT_EMAIL', 'hans.muster@company.com', 'User')
[System.Environment]::SetEnvironmentVariable('GRADLE_INIT_COMPANY', 'Company AG', 'User')
```

## Usage

### PowerShell

```powershell
# Navigate to gradleInit location
cd C:\Users\YourUsername\tools

# Create project
python gradleInit.py init my-project

# With options
python gradleInit.py init my-project --group com.mycompany --version 1.0.0

# Show config
python gradleInit.py config --show
```

### Command Prompt

```cmd
cd C:\Users\YourUsername\tools
python gradleInit.py init my-project
```

### Create Batch Script

Create `gradleInit.bat`:

```batch
@echo off
python C:\Users\YourUsername\tools\gradleInit.py %*
```

Place in a directory that's in your PATH (e.g., `C:\Windows\System32` or `C:\Users\YourUsername\bin`)

**Then use anywhere:**
```powershell
gradleInit init my-project
gradleInit config --show
```

### PowerShell Function

Add to your PowerShell profile:

```powershell
function gradleInit {
    python C:\Users\$env:USERNAME\tools\gradleInit.py $args
}
```

**Then use anywhere:**
```powershell
gradleInit init my-project
gradleInit config --show
```

## Complete Setup Example

### For Entris Banking

**1. Create .gradleInit file:**

```powershell
$configContent = @"
[template]
url = "https://github.com/myorg/gradle-template.git"
version = "main"

[defaults]
group = "com.mycompany"
version = "0.1.0"

[versions]
gradle = "9.0"
kotlin = "2.2.0"
jdk = "21"

[custom]
author = "Hans Muster"
email = "hans.muster@company.com"
company = "Company AG"
license = "Proprietary"
maven_url = "https://maven.myorg.ch"
docker_registry = "registry.myorg.ch"
"@

$configContent | Out-File -FilePath "$env:USERPROFILE\.gradleInit" -Encoding utf8
```

**2. Verify:**

```powershell
python gradleInit.py config --show
```

**3. Create project:**

```powershell
python gradleInit.py init customer-service
```

## Paths on Windows

### Config File Locations

gradleInit checks these locations (in order):

1. Current directory: `.\.gradleInit`
2. User home: `%USERPROFILE%\.gradleInit` (e.g., `C:\Users\Username\.gradleInit`)

### Template Locations

**Local templates:**

```powershell
# Absolute path
python gradleInit.py init my-project --template C:\templates\kotlin-gradle

# Relative path
python gradleInit.py init my-project --template .\templates\kotlin-gradle

# UNC path (network share)
python gradleInit.py init my-project --template \\fileserver\templates\gradle

# File URL
python gradleInit.py init my-project --template file:///C:/templates/kotlin-gradle
```

## Working with Git on Windows

### Install Git for Windows

Download from https://git-scm.com/download/win

### Configure Git

```powershell
git config --global user.name "Hans Muster"
git config --global user.email "hans.muster@company.com"
```

### Line Endings

```powershell
# Recommended for Windows
git config --global core.autocrlf true
```

## IDE Integration

### IntelliJ IDEA

1. Open project folder
2. IDEA automatically detects Gradle
3. Trust the project
4. Wait for indexing to complete

### VS Code

1. Install extensions:
   - Kotlin
   - Gradle for Java
2. Open project folder
3. Trust workspace
4. Use Command Palette (`Ctrl+Shift+P`) for Gradle tasks

## Troubleshooting

### Python not found

```powershell
# Verify installation
where python

# If not found, add to PATH:
# System Properties → Environment Variables → Path → Add Python path
# e.g., C:\Users\Username\AppData\Local\Programs\Python\Python311
```

### Script execution policy

If you get execution policy errors:

```powershell
# Check current policy
Get-ExecutionPolicy

# Allow scripts (run as Admin)
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Long path issues

Enable long paths in Windows:

```powershell
# Run as Admin
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```

### Line ending issues

If you see `^M` characters:

```powershell
# Configure Git
git config --global core.autocrlf true

# Convert existing files
dos2unix filename  # Install via Chocolatey: choco install dos2unix
```

### Permission errors

Run PowerShell as Administrator:
- Press `Win + X`
- Select "Windows PowerShell (Admin)"

## Tips for Windows Users

### 1. Use PowerShell (Not Command Prompt)

PowerShell is more powerful and modern.

### 2. Consider WSL2

For a Linux-like experience:

```powershell
# Install WSL2
wsl --install

# Then use gradleInit in Linux environment
```

### 3. Use Git Bash

Comes with Git for Windows, provides Unix-like shell:

```bash
# In Git Bash
export GRADLE_INIT_AUTHOR="Hans Muster"
./gradleInit.py init my-project
```

### 4. Path Separators

Python handles both:
- Windows: `C:\Users\Username\templates`
- Unix-style: `C:/Users/Username/templates`

Both work!

### 5. Environment Variables Persistence

**PowerShell profile:** `$PROFILE`
- Only for PowerShell
- Per-user

**System Environment Variables:**
- All applications
- Requires restart of applications

## Advanced: Automation

### PowerShell Script for Team Setup

**setup-gradle-env.ps1:**
```powershell
# gradleInit Setup Script for Entris Banking

Write-Host "Setting up gradleInit for Entris Banking..." -ForegroundColor Green

# Create config file
$configPath = "$env:USERPROFILE\.gradleInit"
$configContent = @"
[template]
url = "https://github.com/myorg/gradle-template.git"

[defaults]
group = "com.mycompany"

[versions]
gradle = "9.0"
kotlin = "2.2.0"
jdk = "21"

[custom]
company = "Company AG"
license = "Proprietary"
maven_url = "https://maven.myorg.ch"
"@

$configContent | Out-File -FilePath $configPath -Encoding utf8

# Set user-specific environment variables
$env:GRADLE_INIT_AUTHOR = Read-Host "Enter your name"
$env:GRADLE_INIT_EMAIL = Read-Host "Enter your email"

# Add to PowerShell profile
$profileContent = @"

# gradleInit Configuration
`$env:GRADLE_INIT_AUTHOR = '$env:GRADLE_INIT_AUTHOR'
`$env:GRADLE_INIT_EMAIL = '$env:GRADLE_INIT_EMAIL'

function gradleInit {
    python $PSScriptRoot\gradleInit.py `$args
}
"@

Add-Content -Path $PROFILE -Value $profileContent

Write-Host "✓ Setup complete!" -ForegroundColor Green
Write-Host "Please restart PowerShell or run: . `$PROFILE" -ForegroundColor Yellow
```

**Usage:**
```powershell
.\setup-gradle-env.ps1
```

## Network Shares (UNC Paths)

```powershell
# Template on network share
python gradleInit.py init my-project --template \\fileserver\templates\gradle-template

# Config file on network share (not recommended, use local)
# But templates can be shared:
[template]
url = "file://fileserver/templates/gradle-template"
```

## Summary

**Quick Setup:**

1. Install Python 3.7+
2. Install dependencies: `pip install jinja2 toml`
3. Create `%USERPROFILE%\.gradleInit` with your settings
4. Use: `python gradleInit.py init my-project`

**For Entris Banking:**

```toml
# %USERPROFILE%\.gradleInit
[defaults]
group = "com.mycompany"

[custom]
author = "Hans Muster"
email = "hans.muster@company.com"
company = "Company AG"
```

Then:
```powershell
python gradleInit.py init customer-service
```

All settings automatically applied! 🚀