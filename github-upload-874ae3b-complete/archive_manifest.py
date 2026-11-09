"""Create and verify deterministic checksums for the local archive package."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


MANIFEST_NAME = "archive-manifest.json"
EXCLUDED_PARTS = {".git", "__pycache__"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(root: Path) -> dict:
    root = root.resolve()
    files = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if relative.as_posix() == MANIFEST_NAME or not path.is_file():
            continue
        if EXCLUDED_PARTS.intersection(relative.parts) or path.suffix == ".pyc":
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
        "scope": "Every regular package file except this manifest, Git metadata, Python bytecode, and __pycache__ directories.",
        "files": files,
    }


def write_manifest(root: Path) -> dict:
    manifest = build_manifest(root)
    (root / MANIFEST_NAME).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def verify_manifest(root: Path) -> int:
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
