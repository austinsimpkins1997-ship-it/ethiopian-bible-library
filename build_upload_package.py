"""Export the verified repository root as a source ZIP and a separate public site.

Rebuild first with build_release.py. Outputs stay in ignored dist/, never in
their own input inventory. No uploads, network calls or permissions changes.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import shutil
import zipfile

from archive_manifest import MANIFEST_NAME, is_package_path, verify_manifest, write_manifest
from build_standalone import DEFERRED_EMBEDDED_READER_FIELDS

ROOT = Path(__file__).resolve().parent


def site_path(relative: Path) -> bool:
    return (is_package_path(relative) and relative.parts[0] not in {".github", "tests"}
            and relative.name not in {".gitignore", ".gitattributes"}
            and relative.suffix.lower() not in {".py", ".ps1", ".bat"})


def validate_embedded(root: Path) -> None:
    """Compare the intentionally lean page with full data, not whole-object equality."""
    html = (root / "index.html").read_text(encoding="utf-8")
    match = re.search(r'<script id="archive-data" type="application/json">(.*?)</script>', html, re.S)
    if match is None:
        raise ValueError("Packaged index has no embedded archive metadata.")
    page = json.loads(match.group(1))
    expected = deepcopy(json.loads((root / "archive.json").read_text(encoding="utf-8")))
    for reader, embedded in zip(expected["readers"], page["readers"]):
        package = embedded.get("reader_data_url", "")
        relative = Path(package)
        if (not package or relative.is_absolute() or ".." in relative.parts
                or relative.parent != Path("readers") or relative.suffix != ".json"):
            raise ValueError(f"Unsafe or missing reader package: {package!r}")
        if json.loads((root / relative).read_text(encoding="utf-8")) != reader:
            raise ValueError(f"Reader package differs from full archive: {package}")
        reader["reader_data_url"] = package
        reader.pop("chapters", None)
        for field in DEFERRED_EMBEDDED_READER_FIELDS:
            reader.pop(field, None)
        if reader.get("parallel_translation"):
            reader["parallel_translation"].pop("chapters", None)
    if page != expected:
        raise ValueError("Packaged index metadata differs from the archive.")


def write_zip(root: Path, paths: list[str], output: Path) -> dict:
    temporary = output.with_suffix(".zip.tmp")
    try:
        with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for name in sorted(paths):
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, (root / name).read_bytes())
        with zipfile.ZipFile(temporary) as archive:
            bad = archive.testzip()
            if bad or set(archive.namelist()) != set(paths):
                raise ValueError(f"ZIP inventory/CRC failed: {bad}")
            for name in paths:
                if hashlib.sha256(archive.read(name)).digest() != hashlib.sha256((root / name).read_bytes()).digest():
                    raise ValueError(f"ZIP byte comparison failed: {name}")
        temporary.replace(output)
    finally:
        if temporary.exists():
            temporary.unlink()
    return {"file": output.name, "files": len(paths), "bytes": output.stat().st_size,
            "sha256": hashlib.sha256(output.read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-only", action="store_true", help="Stage site for GitHub Pages without ZIPs")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist", help="Fresh directory within dist/")
    args = parser.parse_args()
    verify_manifest(ROOT)
    validate_embedded(ROOT)
    manifest = json.loads((ROOT / MANIFEST_NAME).read_text(encoding="utf-8"))
    paths = [row["path"] for row in manifest["files"]]
    if any(not is_package_path(Path(name)) for name in paths):
        raise ValueError("Manifest includes a non-public delivery path.")
    paths.append(MANIFEST_NAME)
    dist = args.output_dir.resolve()
    if not dist.is_relative_to((ROOT / "dist").resolve()):
        raise ValueError("Release output must stay within this project's dist/ directory.")
    dist.mkdir(parents=True, exist_ok=True)
    site = dist / "site"
    if site.exists():
        raise ValueError("dist/site already exists; retain the prior output and use a fresh export directory.")
    site.mkdir()
    for name in paths:
        if name == MANIFEST_NAME or not site_path(Path(name)):
            continue
        target = site / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    site_manifest = write_manifest(site)
    verify_manifest(site)
    validate_embedded(site)
    print(f"Staged dist/site: {len(site_manifest['files'])} public files; metadata, readers and hashes verified.")
    if args.site_only:
        return
    records = [write_zip(ROOT, paths, dist / "EthiopianBibleLibrary_GitHub_Source.zip"),
               write_zip(site, [r["path"] for r in site_manifest["files"]] + [MANIFEST_NAME],
                         dist / "EthiopianBibleLibrary_Website.zip")]
    (dist / "release-checksums.json").write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8", newline="\n")
    for record in records:
        print(json.dumps(record))


if __name__ == "__main__":
    main()
