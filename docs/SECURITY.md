# Security

[README.md](../README.md)  
[AI_Instruktion.md](AI_Instruktion.md)

---

[![Security](https://img.shields.io/badge/Security-RSA--4096-green.svg)](SECURITY.md)

## Overview

gradleInit uses RSA-4096 signatures with SHA-256 checksums to verify repository integrity.

## Trust Levels

| Level | Description | Verification |
|-------|-------------|--------------|
| `official` | Signed with embedded key | Automatic |
| `verified` | Signed with user-imported key | Key must be imported first |
| `unverified` | No signature | Warning on every use |

## Key Management

### Generate Keypair

```bash
gradleInit keys --generate <name>
```

Creates:
- `~/.gradleInit/keys/<name>.private.pem` - Keep secure!
- `~/.gradleInit/keys/<name>.public.pem` - Share with users

### Import Public Key

```bash
gradleInit keys --import <name> <path-or-url>
```

### List Keys

```bash
gradleInit keys --list
```

### Export Public Key

```bash
gradleInit keys --export <name>
```

## Repository Signing

### Sign Repository

```bash
gradleInit sign --repo <path> --key <keyname>
```

Creates:
- `CHECKSUMS.sha256` - SHA-256 hashes of all files
- `CHECKSUMS.sig` - RSA signature of checksums

### Verify Repository

```bash
gradleInit verify --repo <path> --key <keyname>
```

## File Format

### CHECKSUMS.sha256

```
<sha256-hash>  <relative-path>
<sha256-hash>  <relative-path>
...
```

### CHECKSUMS.sig

Binary RSA-4096 signature of CHECKSUMS.sha256 content.

## Security Guarantees

1. **Integrity** - Any file modification is detected
2. **Authenticity** - Only holder of private key can sign
3. **Non-repudiation** - Signature proves origin

## Attack Prevention

| Attack | Prevention |
|--------|------------|
| File tampering | SHA-256 checksum mismatch |
| Signature forgery | RSA-4096 cryptographic strength |
| Key substitution | Embedded official key in gradleInit.py |
| Man-in-the-middle | Signature verification after download |

## CI Usage

Auto-install dependencies without prompts:

```bash
gradleInit --install-deps keys --list
```

---

[README.md](../README.md)
