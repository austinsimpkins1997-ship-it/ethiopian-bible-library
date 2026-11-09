"""Verify all files listed in the local archive-manifest.json."""

from pathlib import Path

from archive_manifest import verify_manifest


if __name__ == "__main__":
    try:
        count = verify_manifest(Path(__file__).resolve().parent)
    except (OSError, ValueError, KeyError) as error:
        raise SystemExit(f"Archive package verification failed: {error}") from error
    print(f"Archive package verified: {count} files match the manifest.")
