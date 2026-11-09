"""Verify packaged files after copying into a GitHub clone with existing files."""

from pathlib import Path

from archive_manifest import verify_manifest


if __name__ == "__main__":
    try:
        count = verify_manifest(Path(__file__).resolve().parent, allow_extra_files=True)
    except (OSError, ValueError, KeyError) as error:
        raise SystemExit(f"Copied package verification failed: {error}") from error
    print(
        f"Copied package verified: {count} manifest-listed files match their recorded sizes and SHA-256 hashes. "
        "Destination-only files were left outside this check."
    )
