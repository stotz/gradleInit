#!/usr/bin/env python3
"""
version_sync - maintenance tool for the gradleInit version SSoT.

The single source of truth for all versions lives in:
    gradleInit/versions/gradle/libs.versions.toml      (libraries + Kotlin)
    gradleInit/versions/gradle/wrapper/gradle-wrapper.properties  (Gradle)

This tool keeps the following derived locations in sync with that SSoT:
    - template version catalogs   gradleInitTemplates/<t>/gradle/libs.versions.toml
    - tool defaults               gradleInit/gradleInit.py
                                  (kotlin_version, DEFAULT_GRADLE_VERSION)
    - READMEs                     gradleInit/README.md
                                  gradleInitTemplates/kotlin-javaFX/README.md

It is a maintenance tool and is intentionally NOT part of the gradleInit.py CLI.
It expects gradleInit and gradleInitTemplates checked out as siblings.

Modes:
    --check    Read-only. Report every divergence between the SSoT and the
               derived locations. Exit code 0 if consistent, 1 otherwise.
    --update   Raise SSoT versions via the resolvers (Maven Central + Gradle),
               within each entry's maintenance constraint. Writes only the SSoT;
               run --apply afterwards to propagate. Honors the recent-hours guard
               (--include-recent to override); --yes skips the prompt.
    --apply    Write SSoT values into the derived locations.

README annotation:
    <!-- versions:begin --> ... <!-- versions:end -->   fully generated block
    <!-- vregion:begin --> ... <!-- vregion:end -->      managed prose region;
        every version number inside must sit in a span marker
    <!--v:KEY-->value<!--/v-->                           single managed value

Usage:
    python version_sync.py --check
    python version_sync.py --check --root /path/containing/both/repos
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import toml
except ImportError:
    print("[ERROR] Missing required dependency: toml")
    print("Install with: pip install toml")
    sys.exit(2)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Aliases in a template catalog that carry no resolvable numeric version and
# are therefore not compared against the SSoT.
SKIP_ALIASES = {"jdk", "kotlin"}

TEMPLATES = [
    "kotlin-single",
    "kotlin-multi",
    "ktor",
    "springboot",
    "kotlin-javaFX",
    "multiproject-root",
]

# Label -> SSoT alias mapping for the generated "Current Versions" block.
BLOCK_LABELS = {
    "Kotlin": "kotlin",
    "JUnit": "junit",
    "AssertJ": "assertj",
    "MockK": "mockk",
    "Shadow": "shadow",
    "Ktor": "ktor",
    "Spring Boot": "spring-boot",
    "JavaFX": "javafx",
    "Logback": "logback",
    "Clikt": "clikt",
}

SPAN_RE = re.compile(r"<!--v:([A-Za-z0-9_\-]+)-->(.*?)<!--/v-->", re.S)
VREGION_RE = re.compile(r"<!--\s*vregion:begin\s*-->(.*?)<!--\s*vregion:end\s*-->", re.S)
BLOCK_RE = re.compile(r"<!--\s*versions:begin\s*-->(.*?)<!--\s*versions:end\s*-->", re.S)
VERSION_TOKEN_RE = re.compile(r"\d+\.\d+(?:\.\d+)?")
WRAPPER_VERSION_RE = re.compile(r"gradle-(\d+\.\d+(?:\.\d+)?)-")


# ---------------------------------------------------------------------------
# SSoT parsing
# ---------------------------------------------------------------------------

def _write_lf(path: Path, text: str) -> None:
    """Write text with Unix (LF) line endings on every platform.

    Path.write_text translates '\\n' to the platform newline (CRLF on Windows).
    Because the signature hashes files as raw bytes and git normalises committed
    files to LF, a CRLF working copy would make the released signature fail to
    verify on a clean clone or in CI. Normalise to LF and write the exact bytes.
    """
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    path.write_bytes(normalized.encode("utf-8"))


def parse_ssot(versions_dir: Path) -> Tuple[Dict[str, str], List[dict]]:
    """Parse the SSoT into a flat alias->version dict plus the override list.

    The Gradle version is read from the wrapper properties and exposed under
    the synthetic alias 'gradle'.
    """
    toml_path = versions_dir / "gradle" / "libs.versions.toml"
    wrapper_path = versions_dir / "gradle" / "wrapper" / "gradle-wrapper.properties"

    data = toml.load(toml_path)
    ssot: Dict[str, str] = dict(data.get("versions", {}))

    wrapper_text = wrapper_path.read_text(encoding="utf-8")
    match = WRAPPER_VERSION_RE.search(wrapper_text)
    if not match:
        raise ValueError(f"No Gradle version found in {wrapper_path}")
    ssot["gradle"] = match.group(1)

    overrides = data.get("gradleInit", {}).get("override", [])
    return ssot, overrides


def _override_for(overrides: List[dict], template: str, alias: str):
    """Return the override version for a template/library pair, or None."""
    for entry in overrides:
        if entry.get("template") == template and entry.get("library") == alias:
            return entry.get("version")
    return None


# ---------------------------------------------------------------------------
# Pure check functions (each returns a list of error strings)
# ---------------------------------------------------------------------------

def check_toml_versions(toml_path: Path, ssot: Dict[str, str],
                        overrides: List[dict], template: str) -> List[str]:
    """Verify a template catalog's versions against the SSoT."""
    errors: List[str] = []
    data = toml.load(toml_path)
    for alias, value in data.get("versions", {}).items():
        if alias in SKIP_ALIASES:
            continue
        if isinstance(value, str) and "{{" in value:
            # Unrendered Jinja placeholder (for example kotlin); not comparable.
            continue
        expected = _override_for(overrides, template, alias)
        if expected is None:
            expected = ssot.get(alias)
        if expected is None:
            errors.append(
                f"[{template}] library '{alias}' is not present in the SSoT"
            )
            continue
        if value != expected:
            errors.append(
                f"[{template}] '{alias}' is {value}, SSoT says {expected}"
            )
    return errors


def check_tool_defaults(gradleinit_text: str, ssot: Dict[str, str]) -> List[str]:
    """Verify kotlin_version and DEFAULT_GRADLE_VERSION against the SSoT."""
    errors: List[str] = []

    kotlin_match = re.search(r"'kotlin_version'\s*:\s*'([^']+)'", gradleinit_text)
    if not kotlin_match:
        errors.append("tool default kotlin_version not found in gradleInit.py")
    elif kotlin_match.group(1) != ssot.get("kotlin"):
        errors.append(
            f"tool default kotlin_version is {kotlin_match.group(1)}, "
            f"SSoT says {ssot.get('kotlin')}"
        )

    gradle_match = re.search(r'DEFAULT_GRADLE_VERSION\s*=\s*"([^"]+)"', gradleinit_text)
    if not gradle_match:
        errors.append("DEFAULT_GRADLE_VERSION not found in gradleInit.py")
    elif gradle_match.group(1) != ssot.get("gradle"):
        errors.append(
            f"DEFAULT_GRADLE_VERSION is {gradle_match.group(1)}, "
            f"SSoT says {ssot.get('gradle')}"
        )

    return errors


def check_readme_spans(text: str, ssot: Dict[str, str], name: str) -> List[str]:
    """Verify every <!--v:KEY-->value<!--/v--> span against the SSoT."""
    errors: List[str] = []
    for match in SPAN_RE.finditer(text):
        key, value = match.group(1), match.group(2)
        if key not in ssot:
            errors.append(f"[{name}] unknown version key '{key}' in span marker")
            continue
        if value != ssot[key]:
            errors.append(
                f"[{name}] span '{key}' is {value}, SSoT says {ssot[key]}"
            )
    return errors


def check_vregion_strict(text: str, name: str) -> List[str]:
    """Inside every vregion, all version numbers must sit in a span marker."""
    errors: List[str] = []
    for match in VREGION_RE.finditer(text):
        region = match.group(1)
        stripped = SPAN_RE.sub("", region)
        for token in VERSION_TOKEN_RE.finditer(stripped):
            errors.append(
                f"[{name}] unmarked version '{token.group(0)}' inside vregion "
                f"(wrap it in <!--v:KEY-->...<!--/v-->)"
            )
    return errors


def check_readme_block(text: str, ssot: Dict[str, str], name: str) -> List[str]:
    """Verify the generated 'Current Versions' block against the SSoT."""
    errors: List[str] = []
    match = BLOCK_RE.search(text)
    if not match:
        return errors
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        label, rest = line.split(":", 1)
        label = label.strip()
        alias = BLOCK_LABELS.get(label)
        if alias is None:
            continue
        token = VERSION_TOKEN_RE.search(rest)
        if not token:
            errors.append(f"[{name}] block line '{label}' has no version")
            continue
        if token.group(0) != ssot.get(alias):
            errors.append(
                f"[{name}] block '{label}' is {token.group(0)}, "
                f"SSoT says {ssot.get(alias)}"
            )
    return errors


# ---------------------------------------------------------------------------
# Apply functions (write SSoT values into derived locations)
# ---------------------------------------------------------------------------

_TOML_VALUE_RE = re.compile(r'^(\s*)([A-Za-z0-9_\-]+)(\s*=\s*")([^"]*)(".*)$')


def apply_toml_versions(text: str, ssot: Dict[str, str],
                        overrides: List[dict], template: str) -> Tuple[str, List[str]]:
    """Return (new_text, changes) with [versions] values set to the SSoT.

    Only value lines inside the [versions] section are touched. Jinja
    placeholders (for example kotlin) and skip aliases (jdk) are left intact.
    """
    out_lines: List[str] = []
    changes: List[str] = []
    in_versions = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_versions = stripped == "[versions]"
            out_lines.append(line)
            continue
        if in_versions:
            match = _TOML_VALUE_RE.match(line)
            if match:
                alias, value = match.group(2), match.group(4)
                if alias not in SKIP_ALIASES and "{{" not in value:
                    expected = _override_for(overrides, template, alias)
                    if expected is None:
                        expected = ssot.get(alias)
                    if expected is not None and value != expected:
                        line = match.group(1) + match.group(2) + match.group(3) + expected + match.group(5)
                        changes.append(f"[{template}] {alias}: {value} -> {expected}")
        out_lines.append(line)
    trailing = "\n" if text.endswith("\n") else ""
    return "\n".join(out_lines) + trailing, changes


def apply_tool_defaults(text: str, ssot: Dict[str, str]) -> Tuple[str, List[str]]:
    """Return (new_text, changes) with kotlin_version and DEFAULT_GRADLE_VERSION set."""
    changes: List[str] = []

    def replace_kotlin(match):
        current = match.group(2)
        target = ssot.get("kotlin")
        if target and current != target:
            changes.append(f"kotlin_version: {current} -> {target}")
            return match.group(1) + target + match.group(3)
        return match.group(0)

    def replace_gradle(match):
        current = match.group(2)
        target = ssot.get("gradle")
        if target and current != target:
            changes.append(f"DEFAULT_GRADLE_VERSION: {current} -> {target}")
            return match.group(1) + target + match.group(3)
        return match.group(0)

    text = re.sub(r"('kotlin_version'\s*:\s*')([^']+)(')", replace_kotlin, text)
    text = re.sub(r'(DEFAULT_GRADLE_VERSION\s*=\s*")([^"]+)(")', replace_gradle, text)
    return text, changes


def apply_readme_spans(text: str, ssot: Dict[str, str]) -> Tuple[str, List[str]]:
    """Return (new_text, changes) with every known span set to the SSoT value."""
    changes: List[str] = []

    def replace(match):
        key, value = match.group(1), match.group(2)
        target = ssot.get(key)
        if target is None or value == target:
            return match.group(0)
        changes.append(f"span {key}: {value} -> {target}")
        return f"<!--v:{key}-->{target}<!--/v-->"

    return SPAN_RE.sub(replace, text), changes


def apply_readme_block(text: str, ssot: Dict[str, str]) -> Tuple[str, List[str]]:
    """Return (new_text, changes) with the generated block's versions updated.

    Only the version token of each known label line is replaced, so labels and
    any trailing notes are preserved.
    """
    changes: List[str] = []

    def replace_block(block_match):
        body = block_match.group(1)
        new_lines: List[str] = []
        for line in body.splitlines():
            if ":" in line:
                label, rest = line.split(":", 1)
                alias = BLOCK_LABELS.get(label.strip())
                if alias and ssot.get(alias):
                    token = VERSION_TOKEN_RE.search(rest)
                    if token and token.group(0) != ssot[alias]:
                        changes.append(
                            f"block {label.strip()}: {token.group(0)} -> {ssot[alias]}"
                        )
                        rest = rest[:token.start()] + ssot[alias] + rest[token.end():]
                line = label + ":" + rest
            new_lines.append(line)
        return (block_match.group(0)[:block_match.group(0).index(body)]
                + "\n".join(new_lines)
                + block_match.group(0)[block_match.group(0).index(body) + len(body):])

    return BLOCK_RE.sub(replace_block, text), changes


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run_check(root: Path) -> List[str]:
    """Run all checks against the repositories under root. Returns errors."""
    gradleinit = root / "gradleInit"
    templates = root / "gradleInitTemplates"
    versions_dir = gradleinit / "versions"

    ssot, overrides = parse_ssot(versions_dir)
    errors: List[str] = []

    for template in TEMPLATES:
        toml_path = templates / template / "gradle" / "libs.versions.toml"
        if toml_path.exists():
            errors += check_toml_versions(toml_path, ssot, overrides, template)

    gradleinit_py = gradleinit / "gradleInit.py"
    if gradleinit_py.exists():
        errors += check_tool_defaults(
            gradleinit_py.read_text(encoding="utf-8"), ssot
        )

    main_readme = gradleinit / "README.md"
    if main_readme.exists():
        text = main_readme.read_text(encoding="utf-8")
        errors += check_readme_spans(text, ssot, "gradleInit/README.md")
        errors += check_vregion_strict(text, "gradleInit/README.md")
        errors += check_readme_block(text, ssot, "gradleInit/README.md")

    javafx_readme = templates / "kotlin-javaFX" / "README.md"
    if javafx_readme.exists():
        text = javafx_readme.read_text(encoding="utf-8")
        errors += check_readme_spans(text, ssot, "kotlin-javaFX/README.md")
        errors += check_vregion_strict(text, "kotlin-javaFX/README.md")

    return errors


def run_apply(root: Path) -> List[str]:
    """Write SSoT values into all derived locations. Returns the change log."""
    gradleinit = root / "gradleInit"
    templates = root / "gradleInitTemplates"
    versions_dir = gradleinit / "versions"

    ssot, overrides = parse_ssot(versions_dir)
    changes: List[str] = []

    for template in TEMPLATES:
        toml_path = templates / template / "gradle" / "libs.versions.toml"
        if toml_path.exists():
            new_text, toml_changes = apply_toml_versions(
                toml_path.read_text(encoding="utf-8"), ssot, overrides, template
            )
            if toml_changes:
                _write_lf(toml_path, new_text)
                changes += toml_changes

    gradleinit_py = gradleinit / "gradleInit.py"
    if gradleinit_py.exists():
        new_text, tool_changes = apply_tool_defaults(
            gradleinit_py.read_text(encoding="utf-8"), ssot
        )
        if tool_changes:
            _write_lf(gradleinit_py, new_text)
            changes += tool_changes

    readmes = [
        gradleinit / "README.md",
        templates / "kotlin-javaFX" / "README.md",
    ]
    for readme in readmes:
        if not readme.exists():
            continue
        text = readme.read_text(encoding="utf-8")
        text, span_changes = apply_readme_spans(text, ssot)
        text, block_changes = apply_readme_block(text, ssot)
        if span_changes or block_changes:
            _write_lf(readme, text)
            changes += span_changes + block_changes

    return changes


# ---------------------------------------------------------------------------
# Update mode (raise SSoT versions via the resolvers, write only the SSoT)
# ---------------------------------------------------------------------------

def _load_gradleinit():
    """Import the sibling gradleInit.py as a library (resolvers + helpers)."""
    import importlib.util
    gi_path = Path(__file__).resolve().parents[1] / "gradleInit.py"
    if not gi_path.exists():
        print(f"[ERROR] gradleInit.py not found at {gi_path}")
        return None
    spec = importlib.util.spec_from_file_location("gradleInit", str(gi_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_maven_central(gi):
    """Load the Maven Central resolver from the installed modules, or None."""
    try:
        paths = gi.GradleInitPaths()
        modules_dir = getattr(paths, "modules_dir", None)
        if modules_dir and modules_dir.exists():
            sys.path.insert(0, str(modules_dir))
            from resolvers.maven_central import MavenCentral  # type: ignore
            return MavenCentral()
    except Exception:
        pass
    return None


def _load_plugin_portal(gi):
    """Load the Gradle Plugin Portal resolver from the installed modules, or None."""
    try:
        paths = gi.GradleInitPaths()
        modules_dir = getattr(paths, "modules_dir", None)
        if modules_dir and modules_dir.exists():
            sys.path.insert(0, str(modules_dir))
            from resolvers.gradle_plugin_portal import GradlePluginPortal  # type: ignore
            return GradlePluginPortal()
    except Exception:
        pass
    return None


def gradle_ssot_plan(gi, toml_text: str, wrapper_text: str,
                     available: List[str]) -> Tuple:
    """Return (current, target, policy) for the SSoT Gradle wrapper.

    target is None when the policy is absent/pin or already at the newest within
    policy. Pure: takes texts and the available version list (no network, no IO).
    """
    policy = gi._parse_gradle_policy(toml_text)
    if policy is None:
        return (None, None, None)
    current = gi._extract_gradle_version(wrapper_text)
    if not current or policy in ("pin", ""):
        return (current, None, policy)
    target = gi._select_gradle_target(current, available, policy) if available else None
    return (current, target, policy)


def run_audit(root: Path) -> int:
    """Cross-check every SSoT entry against both registries (Maven Central and
    the Gradle Plugin Portal) to detect stale mirrors and wrong source URLs."""
    toml_path = root / "gradleInit" / "versions" / "gradle" / "libs.versions.toml"
    if not toml_path.exists():
        print(f"[ERROR] SSoT catalog not found: {toml_path}")
        return 2
    gi = _load_gradleinit()
    if gi is None:
        return 2
    maven_central = _load_maven_central(gi)
    plugin_portal = _load_plugin_portal(gi)
    if maven_central is None and plugin_portal is None:
        print("[ERROR] no resolvers available - run: gradleInit modules --update")
        return 2
    print(f"-> Auditing version sources in {toml_path}")
    print()
    manager = gi.VersionManager(toml_path)
    findings = gi.print_source_audit(
        gi.audit_version_sources(manager, maven_central, plugin_portal))
    return 1 if findings else 0


def run_update(root: Path, include_recent: bool = False, assume_yes: bool = False,
               gi=None, maven_central="auto") -> int:
    """Raise the SSoT versions via the resolvers. Writes only the SSoT files.

    Propagation into templates/tool/READMEs is a separate step (--apply).
    """
    versions_dir = root / "gradleInit" / "versions"
    toml_path = versions_dir / "gradle" / "libs.versions.toml"
    wrapper_path = versions_dir / "gradle" / "wrapper" / "gradle-wrapper.properties"
    if not toml_path.exists():
        print(f"[ERROR] SSoT catalog not found: {toml_path}")
        return 2

    if gi is None:
        gi = _load_gradleinit()
        if gi is None:
            return 2
    if maven_central == "auto":
        maven_central = _load_maven_central(gi)

    # Libraries via Maven Central (reuse the end-user resolver/constraint engine)
    manager = gi.VersionManager(toml_path)
    try:
        recent_hours = gi.load_config(gi.GradleInitPaths().config_file).get(
            "versions", {}).get("maven_recent_hours", 48)
    except Exception:
        recent_hours = 48
    if maven_central is None:
        print("[WARN] Maven Central resolver not available; only Gradle will be checked.")
        results = []
    else:
        results = manager.check_updates(maven_central, include_recent=include_recent,
                                        recent_hours=recent_hours,
                                        plugin_portal=_load_plugin_portal(gi))
    lib_updates = [r for r in results if r.get("status") == "UPDATE"]
    too_recent = [r for r in results if r.get("status") == "TOO_RECENT"]

    # Gradle via services.gradle.org (reuse the version helpers)
    try:
        available = gi.fetch_gradle_versions()
    except Exception:
        available = []
    wrapper_text = wrapper_path.read_text(encoding="utf-8") if wrapper_path.exists() else ""
    gradle_current, gradle_target, gradle_policy = gradle_ssot_plan(
        gi, toml_path.read_text(encoding="utf-8"), wrapper_text, available)

    print(f"-> Raising SSoT versions in {versions_dir}")
    name_width = max([len(r["name"]) for r in results] + [len("gradle")]) if results else len("gradle")
    for r in results:
        name = r["name"].ljust(name_width)
        status = r.get("status")
        if status == "UPDATE":
            print(f"  [UPDATE]  {name}: {r['current']} -> {r['latest']} ({r['message']})")
        elif status == "TOO_RECENT":
            print(f"  [RECENT]  {name}: {r['current']} -> {r.get('latest')} ({r['message']})")
        elif status == "CURRENT":
            print(f"  [CURRENT] {name}: {r['current']} (up to date)")
        elif status == "PINNED":
            print(f"  [PINNED]  {name}: {r['current']} ({r['message']})")
        elif status == "STALE_SOURCE":
            print(f"  [STALE!]  {name}: {r['current']} ({r['message']})")
        elif status in ("SKIP", "NOT_FOUND"):
            print(f"  [SKIP]    {name}: {r['current']} ({r['message']})")
        elif status == "VIOLATE":
            print(f"  [VIOLATE] {name}: {r['message']}")
        else:
            print(f"  [{status:7}] {name}: {r.get('message', '')}")
    if gradle_target:
        print(f"  [UPDATE]  {'gradle'.ljust(name_width)}: {gradle_current} -> {gradle_target} (@{gradle_policy})")
    elif gradle_current:
        label = "PINNED" if gradle_policy in ("pin", "", None) else "CURRENT"
        print(f"  [{label:7}] {'gradle'.ljust(name_width)}: {gradle_current}")

    print()
    summary = []
    if lib_updates:
        summary.append(f"{len(lib_updates)} lib update(s)")
    if gradle_target:
        summary.append("1 gradle update")
    if too_recent:
        summary.append(f"{len(too_recent)} too recent")
    print(", ".join(summary) if summary else "no updates within policy")

    if not lib_updates and not gradle_target:
        print("[OK] SSoT already at the latest versions within policy.")
        return 0

    if not assume_yes:
        try:
            response = input("Raise these SSoT versions? [y/N] ").strip().lower()
        except EOFError:
            response = "n"
        if response != "y":
            print("Aborted.")
            return 0

    for r in lib_updates:
        if manager.update_version(r["name"], r["latest"]):
            print(f"[OK] {r['name']}: {r['current']} -> {r['latest']}")
        else:
            print(f"[ERROR] failed to raise {r['name']}")
    if lib_updates:
        # VersionManager.update_version uses write_text, which emits CRLF on
        # Windows. Re-normalise the SSoT catalog to LF so the signed gradleInit
        # repo stays byte-consistent with git's LF-normalised commit.
        _write_lf(toml_path, toml_path.read_text(encoding="utf-8"))
    if gradle_target:
        _write_lf(wrapper_path,
                  gi._rewrite_distribution_url(wrapper_path.read_text(encoding="utf-8"), gradle_target))
        print(f"[OK] gradle: {gradle_current} -> {gradle_target}")

    print()
    print("[OK] SSoT raised. Run 'version_sync.py --apply' to propagate the new")
    print("     versions into the templates, tool defaults and READMEs.")
    return 0


def default_root() -> Path:
    """Directory that contains both gradleInit and gradleInitTemplates."""
    return Path(__file__).resolve().parents[2]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="gradleInit version SSoT sync tool")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true",
                      help="Read-only consistency check (exit 1 on drift)")
    mode.add_argument("--update", action="store_true",
                      help="Raise SSoT versions via resolvers (Maven Central + Gradle)")
    mode.add_argument("--audit", action="store_true",
                      help="Cross-check every SSoT entry against both registries "
                           "(stale-mirror / wrong-URL detection)")
    mode.add_argument("--apply", action="store_true",
                      help="Write SSoT values into derived locations")
    parser.add_argument("--root", type=Path, default=None,
                        help="Directory containing gradleInit and gradleInitTemplates")
    parser.add_argument("--include-recent", action="store_true",
                        help="With --update: also raise versions released within the recent-hours window")
    parser.add_argument("--yes", action="store_true",
                        help="With --update: apply without the confirmation prompt")
    args = parser.parse_args(argv)

    root = args.root if args.root is not None else default_root()

    if args.update:
        return run_update(root, include_recent=args.include_recent, assume_yes=args.yes)

    if args.audit:
        return run_audit(root)

    if args.apply:
        changes = run_apply(root)
        if not changes:
            print("[OK] nothing to apply; derived locations already match the SSoT.")
        else:
            print(f"[OK] applied {len(changes)} change(s):")
            for change in changes:
                print(f"  - {change}")
        remaining = run_check(root)
        if remaining:
            print(f"[WARN] {len(remaining)} issue(s) remain after apply:")
            for issue in remaining:
                print(f"  - {issue}")
            return 1
        return 0

    errors = run_check(root)
    if errors:
        print(f"[FAIL] version SSoT check found {len(errors)} issue(s):")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("[OK] all derived versions are consistent with the SSoT.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
