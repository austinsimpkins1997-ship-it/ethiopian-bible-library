"""Keep portable text-layer checksums aligned with their generated local readers."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def sync_layer_checksum(example_path: Path, package_path: Path) -> None:
    """Update only the checksum field after a trusted source builder rewrites a reader."""
    record = json.loads(example_path.read_text(encoding="utf-8"))
    package = record.get("content_package")
    if not isinstance(package, dict) or not package.get("uri"):
        raise ValueError(f"{example_path.name} has no content package URI.")
    record_uri = Path(package["uri"])
    expected_path = (example_path.parent / record_uri).resolve()
    if expected_path != package_path.resolve() or not package_path.is_file():
        raise ValueError(f"{example_path.name} does not point to {package_path.name}.")
    package["sha256"] = hashlib.sha256(package_path.read_bytes()).hexdigest()
    example_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sync_all_layer_checksums_for_package(package_path: Path, examples_dir: Path) -> list[Path]:
    """Update every layer record whose package URI points to a rewritten local reader.

    Composite reader files can contain more than one independently catalogued layer.
    Rewriting the shared file changes the full-file digest recorded by each layer,
    including records that select a nested JSON pointer.
    """
    target = package_path.resolve()
    updated: list[Path] = []
    for example_path in sorted(examples_dir.glob("*-layer.json")):
        record = json.loads(example_path.read_text(encoding="utf-8"))
        package = record.get("content_package")
        if not isinstance(package, dict) or not isinstance(package.get("uri"), str):
            continue
        referenced = (example_path.parent / package["uri"]).resolve()
        if referenced == target:
            sync_layer_checksum(example_path, package_path)
            updated.append(example_path)
    if not updated:
        raise ValueError(f"No text-layer records reference rebuilt package {package_path}.")
    return updated
