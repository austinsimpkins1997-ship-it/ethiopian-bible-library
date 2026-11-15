"""Recover newline-damaged captures only when their existing pinned SHA-256 matches.

Dry run by default. This never changes source manifests or invents new digests.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def recover_bytes(raw: bytes, digest: str) -> bytes | None:
    if hashlib.sha256(raw).hexdigest() == digest:
        return raw
    lf = raw.replace(b"\r\n", b"\n")
    for candidate in (lf, lf.replace(b"\n", b"\r\n")):
        if hashlib.sha256(candidate).hexdigest() == digest:
            return candidate
    return None


def pinned_files(root: Path):
    def walk(value):
        if isinstance(value, dict):
            yield value
            for child in value.values():
                yield from walk(child)
        elif isinstance(value, list):
            for child in value:
                yield from walk(child)

    seen = set()
    archive_path = root / "archive.json"
    if archive_path.is_file():
        for source in json.loads(archive_path.read_text(encoding="utf-8")).get("sources", []):
            name, digest = source.get("local_snapshot_path"), source.get("local_snapshot_sha256")
            if isinstance(name, str) and isinstance(digest, str) and len(digest) == 64:
                candidate = (root / name).resolve()
                if candidate.is_relative_to(root.resolve()) and candidate.is_file():
                    seen.add((candidate, digest))
                    yield candidate, digest
    for manifest in sorted((root / "readers/source").rglob("*.json")):
        try:
            records = json.loads(manifest.read_text(encoding="utf-8"))
        except (ValueError, UnicodeError):
            continue
        for record in walk(records):
            digest = record.get("sha256") or record.get("response_sha256")
            name = record.get("capture_file") or record.get("path") or record.get("local_raw_response_path")
            if not (isinstance(digest, str) and len(digest) == 64 and isinstance(name, str)):
                continue
            for candidate in (manifest.parent / name, root / name):
                candidate = candidate.resolve()
                if candidate.is_relative_to(root.resolve()) and candidate.is_file():
                    key = (candidate, digest)
                    if key not in seen:
                        seen.add(key)
                        yield candidate, digest
                    break


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Restore only digest-proven newline variants")
    args = parser.parse_args()
    checked = repaired = damaged = 0
    for path, digest in pinned_files(ROOT):
        checked += 1
        raw = path.read_bytes()
        recovered = recover_bytes(raw, digest)
        if recovered == raw:
            continue
        if recovered is None:
            damaged += 1
            print(f"UNRESOLVED: {path.relative_to(ROOT).as_posix()}")
        else:
            repaired += 1
            print(f"{'RESTORED' if args.apply else 'RECOVERABLE'}: {path.relative_to(ROOT).as_posix()}")
            if args.apply:
                path.write_bytes(recovered)
    print(f"Checked {checked} pinned records; {repaired} newline recoveries; {damaged} unresolved.")
    if damaged or (repaired and not args.apply):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
