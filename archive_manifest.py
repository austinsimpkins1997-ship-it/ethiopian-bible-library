"""Create and verify deterministic checksums for the local archive package."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time


MANIFEST_NAME = "archive-manifest.json"
EXCLUDED_PARTS = {".git", "__pycache__", "tmp", ".venv", "venv", "node_modules"}


def is_package_path(relative: Path) -> bool:
    """One public inventory rule for manifests, source ZIPs and site exports."""
    if EXCLUDED_PARTS.intersection(relative.parts) or relative.suffix == ".pyc":
        return False
    top = relative.parts[0]
    if top in {"dist", "source-captures", "site"} or top.startswith(("github-upload", "github-docs-upload", "github-runtime-repair-", ".maale-gpg-")):
        return False
    return not (len(relative.parts) == 1 and relative.suffix == ".zip")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_text_atomically(path: Path, text: str, encoding: str = "utf-8", newline: str | None = None) -> None:
    """Replace a generated archive file only after its complete new contents are written."""
    path = Path(path)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding=encoding, newline="\n" if newline is None else newline, dir=path.parent,
            prefix=f".{path.name}.", suffix=".tmp", delete=False,
        ) as stream:
            temporary_path = Path(stream.name)
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        for attempt in range(8):
            try:
                os.replace(temporary_path, path)
                break
            except PermissionError:
                if attempt == 7:
                    raise
                time.sleep(0.15)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def enable_atomic_path_writes() -> None:
    """Use complete-file replacement for writes made by the standalone build's modules."""
    if getattr(Path.write_text, "_archive_atomic_writer", False):
        return
    original_write_text = Path.write_text

    def write_text(path, text, encoding=None, errors=None, newline=None):
        if errors not in (None, "strict"):
            return original_write_text(path, text, encoding=encoding, errors=errors, newline=newline)
        return write_text_atomically(
            path, text, encoding=encoding or "utf-8", newline=newline,
        )

    write_text._archive_atomic_writer = True
    Path.write_text = write_text


def check_git_text_bytes(root: Path) -> None:
    """Reject working text that Git will change before a Linux checkout hashes it.

    Source captures marked -text retain their exact bytes. Unversioned downloaded
    packages need no Git installation; this guard applies to an owning checkout.
    """
    root = root.resolve()
    if not (root / ".git").exists():
        return
    if shutil.which("git") is None:
        raise ValueError("Git is required to check text bytes in this repository checkout.")
    names = subprocess.check_output([
        "git", "-C", str(root), "ls-files", "--cached", "--others", "--exclude-standard", "-z",
    ]).split(b"\0")
    names = [name for name in names if name and is_package_path(Path(os.fsdecode(name)))]
    if not names:
        return
    attributes = subprocess.check_output(
        ["git", "-C", str(root), "check-attr", "-z", "--stdin", "text", "eol"],
        input=b"\0".join(names) + b"\0",
    ).split(b"\0")
    by_path = {}
    for index in range(0, len(attributes) - 1, 3):
        name, attribute, value = attributes[index:index + 3]
        by_path.setdefault(name, {})[attribute] = value
    mismatches = []
    for name in names:
        attributes_for_path = by_path.get(name, {})
        if (attributes_for_path.get(b"eol") != b"lf"
                or attributes_for_path.get(b"text") == b"unset"):
            continue
        path = root / os.fsdecode(name)
        if not path.is_file() or path.is_symlink():
            continue
        data = path.read_bytes()
        # Git's text=auto leaves binary input alone, even when eol=lf is set.
        if attributes_for_path.get(b"text") == b"auto" and b"\0" in data[:8000]:
            continue
        if b"\r\n" in data:
            mismatches.append(os.fsdecode(name))
    if mismatches:
        raise ValueError(
            "Git-normalized text contains CRLF working bytes: " + ", ".join(mismatches)
            + ". Save these text files with LF endings, then rebuild. "
            "Do not normalize retained readers/source captures marked -text."
        )


def build_manifest(root: Path) -> dict:
    root = root.resolve()
    files = []
    # Path ordering is case-insensitive on Windows and case-sensitive on Linux.
    # Sort the portable spelling explicitly so both builds checksum identical JSON.
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root)
        if relative.as_posix() == MANIFEST_NAME or not path.is_file():
            continue
        if not is_package_path(relative):
            continue
        if path.is_symlink():
            raise ValueError(f"Cannot checksum a package symlink reproducibly: {relative.as_posix()}.")
        files.append({
            "path": relative.as_posix(),
            "size_bytes": path.stat().st_size,
            "sha256": _sha256(path),
        })
    return {
        "manifest_version": 1,
        "hash_algorithm": "SHA-256",
        "scope": "Canonical public project files; excludes this manifest, Git metadata, caches, temporary files, private source-captures, legacy upload copies and generated release ZIPs/dist.",
        "files": files,
    }


def write_manifest(root: Path) -> dict:
    check_git_text_bytes(root)
    manifest = build_manifest(root)
    write_text_atomically(
        root / MANIFEST_NAME,
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
    )
    return manifest


def verify_manifest(root: Path, *, allow_extra_files: bool = False) -> int:
    root = root.resolve()
    manifest_path = root / MANIFEST_NAME
    if not manifest_path.is_file():
        raise ValueError(f"Missing {MANIFEST_NAME}; rebuild the archive first.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (manifest.get("manifest_version") != 1 or manifest.get("hash_algorithm") != "SHA-256"
            or not isinstance(manifest.get("files"), list)):
        raise ValueError(f"{MANIFEST_NAME} has an unsupported structure.")
    recorded = {}
    for item in manifest["files"]:
        if (not isinstance(item, dict) or not isinstance(item.get("path"), str)
                or not isinstance(item.get("size_bytes"), int) or isinstance(item.get("size_bytes"), bool)
                or not isinstance(item.get("sha256"), str)):
            raise ValueError(f"{MANIFEST_NAME} contains a malformed file record.")
        relative = Path(item["path"])
        if relative.is_absolute() or ".." in relative.parts or item["path"] in recorded:
            raise ValueError(f"{MANIFEST_NAME} contains an unsafe or duplicate path: {item['path']}.")
        target = (root / relative).resolve()
        if not target.is_relative_to(root) or not target.is_file():
            raise ValueError(f"Manifest file is missing or outside the package: {item['path']}.")
        if target.stat().st_size != item["size_bytes"] or _sha256(target) != item["sha256"]:
            raise ValueError(f"Checksum or size mismatch: {item['path']}.")
        recorded[item["path"]] = item
    if not allow_extra_files:
        expected = build_manifest(root)
        expected_paths = {item["path"] for item in expected["files"]}
        if set(recorded) != expected_paths:
            missing = sorted(expected_paths - set(recorded))
            extra = sorted(set(recorded) - expected_paths)
            raise ValueError(f"Manifest file inventory differs; missing={missing}, extra={extra}.")
    return len(recorded)


if __name__ == "__main__":
    count = verify_manifest(Path(__file__).resolve().parent)
    print(f"Verified SHA-256 and byte lengths for {count} archive package files.")
