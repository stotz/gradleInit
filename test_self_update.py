#!/usr/bin/env python3
"""
Tests for the self-update logic (gradleInit --update).

Specification:
- detect_install_type returns 'git' inside a git working tree, else 'single-file'.
- _select_latest_tag returns the highest vX.Y.Z tag and ignores non-semver names.
- _verify_single_file accepts a download only when the signature validates over the
  CHECKSUMS bytes AND the script hash matches its CHECKSUMS entry; otherwise it
  rejects (no --force escape hatch exists).

The network download, git pull and self-replace are thin wrappers verified by CI.

Usage:
    python test_self_update.py
    python -m pytest test_self_update.py -v
"""

import hashlib
import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE))
_SPEC = importlib.util.spec_from_file_location("gradleInit", str(_HERE / "gradleInit.py"))
gradleInit = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(gradleInit)

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding


def _make_keypair():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return private_key, public_pem


def _sign(private_key, data: bytes) -> bytes:
    return private_key.sign(data, padding.PKCS1v15(), hashes.SHA256())


class TestSelectLatestTag(unittest.TestCase):
    def test_picks_highest_semver(self):
        tags = ["v1.2.0", "v1.10.3", "v1.10.1", "main", "v0.9.9", "v1.9.20"]
        self.assertEqual(gradleInit._select_latest_tag(tags), "v1.10.3")

    def test_ignores_non_semver(self):
        self.assertIsNone(gradleInit._select_latest_tag(["main", "latest", "v1.2"]))


class TestDetectInstallType(unittest.TestCase):
    def test_git_working_tree(self):
        if shutil.which("git") is None:
            self.skipTest("git not available")
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            script = repo / "gradleInit.py"
            script.write_text("# dummy\n", encoding="utf-8")
            self.assertEqual(gradleInit.detect_install_type(script), "git")

    def test_single_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "gradleInit.py"
            script.write_text("# dummy\n", encoding="utf-8")
            self.assertEqual(gradleInit.detect_install_type(script), "single-file")


class TestVerifySingleFile(unittest.TestCase):
    def setUp(self):
        self.private_key, self.public_pem = _make_keypair()
        self.script = b"print('hello gradleInit')\n"
        digest = hashlib.sha256(self.script).hexdigest()
        self.checksums = (f"{digest}  gradleInit.py\n"
                          f"{'0' * 64}  README.md\n").encode("utf-8")
        self.signature = _sign(self.private_key, self.checksums)

    def test_valid(self):
        ok, message = gradleInit._verify_single_file(
            self.script, self.checksums, self.signature, self.public_pem
        )
        self.assertTrue(ok, message)

    def test_bad_signature(self):
        ok, _ = gradleInit._verify_single_file(
            self.script, self.checksums, b"tampered" + self.signature, self.public_pem
        )
        self.assertFalse(ok)

    def test_tampered_script(self):
        ok, _ = gradleInit._verify_single_file(
            self.script + b"# evil\n", self.checksums, self.signature, self.public_pem
        )
        self.assertFalse(ok)

    def test_checksums_without_script_entry(self):
        checksums = (f"{'0' * 64}  README.md\n").encode("utf-8")
        signature = _sign(self.private_key, checksums)
        ok, message = gradleInit._verify_single_file(
            self.script, checksums, signature, self.public_pem
        )
        self.assertFalse(ok)
        self.assertIn("No checksum entry", message)

    def test_crlf_script_still_verifies(self):
        # Signed over LF; a CRLF download must still verify after normalization.
        crlf_script = self.script.replace(b"\n", b"\r\n")
        ok, message = gradleInit._verify_single_file(
            crlf_script, self.checksums, self.signature, self.public_pem
        )
        self.assertTrue(ok, message)

    def test_crlf_checksums_still_verifies(self):
        # Signature is over the LF checksums; a CRLF copy must reconcile.
        crlf_checksums = self.checksums.replace(b"\n", b"\r\n")
        ok, message = gradleInit._verify_single_file(
            self.script, crlf_checksums, self.signature, self.public_pem
        )
        self.assertTrue(ok, message)


class TestLineEndingNormalization(unittest.TestCase):
    """Line endings must never affect a hash or signature (text only; binary as-is)."""

    def test_normalize_crlf_and_cr_to_lf(self):
        self.assertEqual(gradleInit._normalize_text_bytes(b"a\r\nb\rc\n"), b"a\nb\nc\n")

    def test_binary_with_nul_is_unchanged(self):
        data = b"PK\x03\x04\r\n\x00payload\r\n"
        self.assertEqual(gradleInit._normalize_text_bytes(data), data)

    def test_get_file_hash_crlf_equals_lf(self):
        sec = gradleInit.RepositorySecurity()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "lf.txt").write_bytes(b"line1\nline2\n")
            (root / "crlf.txt").write_bytes(b"line1\r\nline2\r\n")
            self.assertEqual(
                sec._get_file_hash(root, "lf.txt"),
                sec._get_file_hash(root, "crlf.txt"),
            )

    def test_sign_verify_survives_crlf_working_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            keys = root / "keys"
            keys.mkdir()
            repo = root / "repo"
            (repo / "sub").mkdir(parents=True)
            (repo / "a.txt").write_bytes(b"alpha\nbeta\n")
            (repo / "sub" / "b.toml").write_bytes(b'x = "1"\n')

            sec = gradleInit.RepositorySecurity(keys_dir=keys)
            sec.generate_keypair("test")
            sec.sign_repository(repo, "test")

            # Simulate a Windows checkout: working copy and CHECKSUMS turn CRLF.
            (repo / "a.txt").write_bytes(b"alpha\r\nbeta\r\n")
            cks = repo / sec.CHECKSUMS_FILE
            cks.write_bytes(cks.read_bytes().replace(b"\n", b"\r\n"))

            ok, message = sec.verify_repository(repo, "test")
            self.assertTrue(ok, message)


class TestSelfUpdateTarget(unittest.TestCase):
    """The global --update must resolve to self/all/None correctly and never
    hijack subcommand --update flags."""

    def test_no_command_is_self(self):
        self.assertEqual(gradleInit._self_update_target(True, None), "self")

    def test_all_token(self):
        self.assertEqual(gradleInit._self_update_target(True, "all"), "all")
        self.assertEqual(gradleInit._self_update_target(True, "ALL"), "all")

    def test_subcommands_not_hijacked(self):
        for command in ("templates", "modules", "versions", "init"):
            self.assertIsNone(
                gradleInit._self_update_target(True, command),
                f"--update with '{command}' must not be a self/all update",
            )

    def test_no_update_flag(self):
        self.assertIsNone(gradleInit._self_update_target(False, None))
        self.assertIsNone(gradleInit._self_update_target(False, "all"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
