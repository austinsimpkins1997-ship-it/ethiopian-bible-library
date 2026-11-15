"""Rebuild the public archive from retained inputs, offline and in dependency order."""

from pathlib import Path
import runpy
import sys

from archive_manifest import enable_atomic_path_writes

ROOT = Path(__file__).resolve().parent
BUILDERS = (
    "build_genesis_english.py", "build_genesis_geez.py", "build_exodus_geez.py",
    "build_brenton_exodus.py", "build_octateuch_readers.py", "build_eritrea_canon_evidence.py",
    "build_psalms_geez.py", "integrate_psalms.py", "audit_crosswire_module.py",
    "build_octateuch_inventory.py", "build_canon_registry.py", "build_brenton_octateuch.py",
    "build_brenton_research_readers.py", "build_brenton_job.py", "build_brenton_tobit.py",
    "build_brenton_sirach.py", "build_brenton_ruth.py", "build_gamo_research_readers.py",
    "build_maale_research_readers.py", "build_oyda_research_readers.py",
    "build_yemsa_research_readers.py", "build_dawro_research_readers.py",
    "build_baiso_research_readers.py", "build_alaba_kabeena_research_readers.py",
    "build_standalone.py",
)


def main():
    # Same bytes on Windows and Linux; generated-file hashes depend on this.
    enable_atomic_path_writes()
    for builder in BUILDERS:
        print(f"\n=== {builder} ===", flush=True)
        runpy.run_path(str(ROOT / builder), run_name="__main__")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
