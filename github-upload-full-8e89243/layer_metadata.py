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
