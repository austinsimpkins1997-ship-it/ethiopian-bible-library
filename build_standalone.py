"""Embed archive.json into index.html so the catalogue works without data fetches."""

from __future__ import annotations

import json
import hashlib
import re
from pathlib import Path
from urllib.parse import unquote, urlparse
from archive_manifest import verify_manifest, write_manifest
from coverage_summary import build_coverage_statement, validate_unit_count, validate_unit_coverage
from availability_survey import validate_availability_survey
from rights_metadata import validate_rights_classification
from review_metadata import validate_review_record
from reader_validation import validate_observed_unit_count
from package_pointer import resolve_json_pointer
from build_brenton_exodus import parse_chapter as parse_brenton_exodus_chapter
from build_brenton_octateuch import validate as validate_brenton_octateuch_companions
from audit_crosswire_module import build_audit as build_crosswire_module_audit
from audit_mark_tei import build_audit as build_mark_tei_audit


ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "archive.json"
HTML_PATH = ROOT / "index.html"
EMBED_RE = re.compile(
    r'(<script id="archive-data" type="application/json">).*?(</script>)',
    re.DOTALL,
)


def validate_offline_shell() -> int:
    """Fail the build if the service worker precaches missing or unsafe shell paths."""
    service_worker = (ROOT / "sw.js").read_text(encoding="utf-8")
    match = re.search(r"const APP_FILES\s*=\s*\[(.*?)\]\.map", service_worker, re.DOTALL)
    if not match:
        raise ValueError("Service worker has no recognizable local APP_FILES cache list.")
    paths = re.findall(r"['\"]([^'\"]+)['\"]", match.group(1))
    required = {"index.html", "styles.css", "app.js", "reader-package.js", "reader-alignment.js", "manifest.webmanifest", "archive-manifest.json", "schemas/reader-package.schema.json"}
    missing = required - set(paths)
    if missing:
        raise ValueError(f"Offline shell does not precache required app files: {', '.join(sorted(missing))}.")
    for relative_path in paths:
        local_path = Path(relative_path)
        if local_path.is_absolute() or ".." in local_path.parts or not (ROOT / local_path).is_file():
            raise ValueError(f"Offline shell path is not a present, local file: {relative_path}.")
    if "new URL(request.url).origin !== SITE_BASE.origin" not in service_worker:
        raise ValueError("Service worker must limit intercepted requests to the site's own origin.")
    if "request.mode === 'navigate'" not in service_worker or "new URL('index.html', SITE_BASE)" not in service_worker:
        raise ValueError("Service worker navigation handler must provide its local offline index fallback.")
    app_script = (ROOT / "app.js").read_text(encoding="utf-8")
    if re.search(r"\bfetch\s*\(|\bXMLHttpRequest\b|\bWebSocket\b", app_script):
        raise ValueError("Application code must not fetch reader or catalogue data at runtime.")
    html = HTML_PATH.read_text(encoding="utf-8")
    if not re.search(r'<a\s+id="archive-export"\s+href="archive\.json"\s+download\b', html):
        raise ValueError("The archive export must retain its local JSON fallback link.")
    if not re.search(r'<a\s+href="archive-manifest\.json"\s+download\b', html):
        raise ValueError("The archive checksum manifest must be downloadable from the page.")
    if not re.search(r'<button[^>]+id="reader-download"', html) or "window.ReaderPackage.createReaderPackage" not in app_script:
        raise ValueError("The reader must offer its locally generated, provenance-bearing JSON export.")
    package_schema = json.loads((ROOT / "schemas" / "reader-package.schema.json").read_text(encoding="utf-8"))
    if package_schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema" or package_schema.get("$id") != "https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/schemas/reader-package.schema.json":
        raise ValueError("Reader package schema must use the published JSON Schema 2020-12 identifier.")
    for required in (
        "state.archiveData = data;",
        "JSON.stringify(state.archiveData, null, 2)",
        "new Blob([",
        "URL.createObjectURL(file)",
        "link.download = 'ethiopian-bible-library-archive.json'",
    ):
        if required not in app_script:
            raise ValueError(f"Offline archive export is missing required behavior: {required}")
    return len(paths)


def require_unique(items: list[dict], field: str, label: str) -> set[str]:
    values = [item.get(field) for item in items]
    if any(not value for value in values):
        raise ValueError(f"Every {label} needs a {field}.")
    if len(values) != len(set(values)):
        raise ValueError(f"Duplicate {field} in {label}.")
    return set(values)


def validate_source_urls(sources: list[dict]) -> None:
    site_root = ROOT.resolve()
    for source in sources:
        value = source.get("url")
        if not isinstance(value, str) or not value:
            raise ValueError(f"{source.get('source_id')} needs a source URL.")
        parsed = urlparse(value)
        if parsed.scheme in {"http", "https"}:
            if parsed.scheme != "https":
                raise ValueError(f"{source['source_id']} uses an insecure external URL; source links must use HTTPS: {value}")
            if not parsed.netloc:
                raise ValueError(f"{source['source_id']} has an incomplete external URL: {value}")
            continue
        if parsed.scheme or parsed.netloc:
            raise ValueError(f"{source['source_id']} uses an unsupported URL scheme: {value}")
        if not parsed.path:
            if parsed.fragment:
                continue  # In-page references may target IDs generated by app.js.
            raise ValueError(f"{source['source_id']} has an empty relative URL.")
        local_path = (ROOT / unquote(parsed.path)).resolve()
        if not local_path.is_relative_to(site_root) or not local_path.is_file():
            raise ValueError(f"{source['source_id']} points to a missing or out-of-site file: {value}")


def validate_brenton_exodus_capture() -> None:
    """Check local capture inventory integrity, not scripture accuracy."""
    capture_dir = ROOT / "readers" / "source" / "brenton-exodus"
    manifest_path = capture_dir / "capture-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    chapters = manifest.get("chapters", [])
    expected = list(range(1, 41))
    if manifest.get("chapter_count") != len(expected) or [row.get("chapter") for row in chapters] != expected:
        raise ValueError("Brenton Exodus capture manifest must list all 40 expected chapter pages in order.")
    extracted_chapters = []
    for row in chapters:
        number = row["chapter"]
        filename = f"Exodus_{number:02d}.txt"
        if row.get("capture_file") != filename or row.get("source_url") != f"https://ebible.org/eng-Brenton/EXO{number:02d}.htm":
            raise ValueError(f"Brenton Exodus capture metadata mismatch for chapter {number}.")
        path = (capture_dir / filename).resolve()
        if not path.is_relative_to(capture_dir.resolve()) or not path.is_file():
            raise ValueError(f"Brenton Exodus capture file is missing or outside its directory: {filename}.")
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != row.get("sha256"):
            raise ValueError(f"Brenton Exodus capture checksum mismatch: {filename}.")
        text = content.decode("utf-8")
        if (f"Brenton Septuagint Translation, Exodus {number}" not in text
                or f"https://ebible.org/eng-Brenton/EXO{number:02d}.htm" not in text
                or "raw HTML not retained" not in text):
            raise ValueError(f"Brenton Exodus capture header/limitation mismatch: {filename}.")
        extracted_chapters.append(parse_brenton_exodus_chapter(row))
    reader = json.loads((ROOT / "readers" / "exodus-geez.json").read_text(encoding="utf-8"))
    companion = reader.get("parallel_translation", {})
    if companion.get("translation_id") != "exodus-english-brenton-lxx-1851":
        raise ValueError("The Exodus reader must preserve the separately identified Brenton English companion.")
    if companion.get("chapters") != extracted_chapters:
        raise ValueError("The bundled Exodus companion does not exactly reproduce the captured-page extraction.")
    extracted_label_count = sum(len(chapter["verses"]) for chapter in extracted_chapters)
    if (manifest.get("extracted_label_count") != extracted_label_count
            or companion.get("verse_label_count") != extracted_label_count
            or companion.get("verification_status", "").find("not labeled verified scripture") < 0):
        raise ValueError("Brenton Exodus extraction count or unreviewed status is missing or stale.")
    notice = (capture_dir / "CAPTURE-NOTICE.txt").read_text(encoding="utf-8")
    if "not labeled verified scripture" not in notice:
        raise ValueError("Brenton Exodus capture notice must preserve the unreviewed research-only status.")


def validate_crosswire_module_audit() -> None:
    """Require the stored structural report to match the local SWORD package."""
    audit_path = ROOT / "readers" / "source" / "crosswire" / "module-structure-audit.json"
    if not audit_path.is_file():
        raise ValueError("Run audit_crosswire_module.py; the local module structure report is missing.")
    stored = json.loads(audit_path.read_text(encoding="utf-8"))
    if stored != build_crosswire_module_audit():
        raise ValueError("The stored CrossWire module structure report is stale or does not match its source package.")


def validate_mark_tei_audit() -> None:
    """Require the Mark TEI report to match the retained source without adding it as reader text."""
    audit_path = ROOT / "readers" / "source" / "mark" / "structure-audit.json"
    if not audit_path.is_file():
        raise ValueError("Run audit_mark_tei.py; the local Mark TEI structure report is missing.")
    stored = json.loads(audit_path.read_text(encoding="utf-8"))
    if stored != build_mark_tei_audit():
        raise ValueError("The stored Mark TEI structure report is stale or does not match the retained source file.")


def require_object_fields(value: object, required: set[str], label: str) -> dict:
    """Require a JSON object and its schema-required keys without external dependencies."""
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object.")
    missing = required - set(value)
    if missing:
        raise ValueError(f"{label} is missing required fields: {sorted(missing)}")
    return value


def validate_closed_schema_objects(value: object, node: dict, root_schema: dict, label: str) -> None:
    """Enforce closed objects and array constraints, including siblings of $ref."""
    if "$ref" in node:
        if not node["$ref"].startswith("#/"):
            raise ValueError(f"{label} uses an unsupported external schema reference.")
        target = root_schema
        for part in node["$ref"][2:].split("/"):
            target = target[part.replace("~1", "/").replace("~0", "~")]
        validate_closed_schema_objects(value, target, root_schema, label)
        node = {key: constraint for key, constraint in node.items() if key != "$ref"}
    if "oneOf" in node:
        def matches_type(candidate: dict) -> bool:
            allowed = candidate.get("type")
            if allowed is None:
                return True
            if not isinstance(allowed, list):
                allowed = [allowed]
            return any(
                (kind == "null" and value is None)
                or (kind == "object" and isinstance(value, dict))
                or (kind == "array" and isinstance(value, list))
                or (kind == "string" and isinstance(value, str))
                or (kind == "integer" and isinstance(value, int) and not isinstance(value, bool))
                or (kind == "boolean" and isinstance(value, bool))
                for kind in allowed
            )
        branches = [candidate for candidate in node["oneOf"] if matches_type(candidate)]
        if len(branches) != 1:
            raise ValueError(f"{label} must match exactly one schema branch; matched {len(branches)}.")
        validate_closed_schema_objects(value, branches[0], root_schema, label)
        return
    if isinstance(value, dict):
        properties = node.get("properties", {})
        missing = set(node.get("required", [])) - set(value)
        if missing:
            raise ValueError(f"{label} is missing required schema properties: {sorted(missing)}.")
        if node.get("additionalProperties") is False:
            extra = set(value) - set(properties)
            if extra:
                raise ValueError(f"{label} has unexpected schema properties: {sorted(extra)}.")
        for key, child in value.items():
            if key in properties:
                validate_closed_schema_objects(child, properties[key], root_schema, f"{label}.{key}")
    elif isinstance(value, list):
        if len(value) < node.get("minItems", 0):
            raise ValueError(f"{label} has fewer than {node['minItems']} required items.")
        if node.get("uniqueItems"):
            fingerprints = [json.dumps(child, ensure_ascii=False, sort_keys=True, separators=(",", ":")) for child in value]
            if len(fingerprints) != len(set(fingerprints)):
                raise ValueError(f"{label} must not contain duplicate items.")
        if "items" in node:
            for index, child in enumerate(value):
                validate_closed_schema_objects(child, node["items"], root_schema, f"{label}[{index}]")


def validate_global_layer_example(source_ids: set[str]) -> list[dict]:
    schema_path = ROOT / "schemas" / "text-layer.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    identifier_audit = json.loads((ROOT / "language-script-code-audit.json").read_text(encoding="utf-8"))
    audited_language_tags = set(identifier_audit.get("language_subtags", {}).get("codes", []))
    script_audit = identifier_audit.get("script_codes", {})
    audited_script_codes = set(script_audit.get("iso_15924_codes", [])) | set(script_audit.get("iana_special_codes", []))
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise ValueError("Global text-layer schema must declare JSON Schema 2020-12.")
    properties = schema.get("properties", {})
    language_pattern = re.compile(r"^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*$")
    valid_layer_types = set(properties["layer_type"].get("enum", []))
    valid_text_origins = set(properties["text_origin"].get("enum", []))
    valid_publication_states = set(properties["publication_state"].get("enum", []))
    example_paths = sorted((ROOT / "examples").glob("*-layer.json"))
    if not example_paths:
        raise ValueError("At least one global text-layer example is required.")
    records: list[dict] = []
    for example_path in example_paths:
        record = json.loads(example_path.read_text(encoding="utf-8"))
        validate_closed_schema_objects(record, schema, schema, example_path.name)
        missing = set(schema.get("required", [])) - set(record)
        if missing:
            raise ValueError(f"{example_path.name} is missing required fields: {sorted(missing)}")
        witness = require_object_fields(
            record.get("witness"), {"witness_id", "witness_type", "title", "source_ids"},
            f"{example_path.name} witness",
        )
        if witness.get("witness_type") not in {"manuscript", "printed_edition", "digital_edition", "transcription", "composite", "unknown"}:
            raise ValueError(f"{example_path.name} has an invalid witness type.")
        if (not isinstance(witness.get("title"), str) or not witness["title"].strip()
                or not isinstance(witness.get("source_ids"), list) or not witness["source_ids"]
                or any(not isinstance(source_id, str) or not source_id for source_id in witness["source_ids"])):
            raise ValueError(f"{example_path.name} witness needs a title and one or more source IDs.")
        assertions = record.get("tradition_assertions")
        if not isinstance(assertions, list):
            raise ValueError(f"{example_path.name} tradition_assertions must be a list.")
        for index, assertion in enumerate(assertions):
            assertion = require_object_fields(
                assertion, {"tradition_id", "canon_id", "mapping_state", "evidence_source_ids"},
                f"{example_path.name} tradition assertion {index + 1}",
            )
            if assertion.get("mapping_state") not in {"asserted_by_source", "reviewed_match", "related_work", "uncertain", "not_mapped"}:
                raise ValueError(f"{example_path.name} tradition assertion {index + 1} has an invalid mapping state.")
            evidence_ids = assertion.get("evidence_source_ids")
            if (not isinstance(evidence_ids, list) or not evidence_ids
                    or any(not isinstance(source_id, str) or not source_id for source_id in evidence_ids)):
                raise ValueError(f"{example_path.name} tradition assertion {index + 1} needs cited source IDs.")
        package = require_object_fields(
            record.get("content_package"), {"uri", "media_type", "sha256"},
            f"{example_path.name} content_package",
        )
        if (not isinstance(package.get("uri"), str) or not package["uri"].strip()
                or not isinstance(package.get("media_type"), str)
                or not re.fullmatch(r"^[A-Za-z0-9!#$&^_.+-]+/[A-Za-z0-9!#$&^_.+-]+$", package["media_type"])):
            raise ValueError(f"{example_path.name} content_package needs a local URI and valid media type.")
        coverage = require_object_fields(
            record.get("coverage"), {"extent_state", "extent_basis", "unit_count"},
            f"{example_path.name} coverage",
        )
        if coverage.get("extent_state") not in {"complete_for_declared_edition", "partial", "unknown"}:
            raise ValueError(f"{example_path.name} has an invalid coverage extent_state.")
        if coverage.get("extent_basis") not in {"edition_contents_statement", "source_inventory", "independent_collation", "unknown"}:
            raise ValueError(f"{example_path.name} has an invalid coverage extent_basis.")
        validate_unit_count(coverage.get("unit_count"), f"{example_path.name} coverage.unit_count")
        validate_unit_coverage(coverage, f"{example_path.name} coverage")
        lacunae = coverage.get("missing_or_lacunose_ranges", [])
        if not isinstance(lacunae, list) or any(not isinstance(value, str) for value in lacunae):
            raise ValueError(f"{example_path.name} coverage.missing_or_lacunose_ranges must be a list of strings.")
        rights = require_object_fields(
            record.get("rights"), {"status", "statement"}, f"{example_path.name} rights",
        )
        if rights.get("status") not in {"public_domain_claimed", "open_license", "permission_limited", "all_rights_reserved", "unknown", "mixed"}:
            raise ValueError(f"{example_path.name} has an invalid rights status.")
        if (not isinstance(rights.get("statement"), str) or not rights["statement"].strip()
                or not isinstance(rights.get("attribution_required", False), bool)):
            raise ValueError(f"{example_path.name} rights needs a statement and a boolean attribution_required value.")
        if rights.get("status") == "open_license" and (
                not isinstance(rights.get("license_id"), str) or not rights["license_id"].strip()):
            raise ValueError(f"{example_path.name} needs a nonempty license identifier for its open-license claim.")
        review_dimensions = record.get("review_dimensions")
        if not isinstance(review_dimensions, list):
            raise ValueError(f"{example_path.name} review_dimensions must be a list.")
        valid_dimensions = {"identity", "transcription_accuracy", "translation_accuracy", "chapter_or_section_sequence", "unit_boundaries", "completeness", "alignment", "rights", "language_identification", "community_review", "other"}
        valid_review_states = {"not_checked", "in_progress", "checked_with_limits", "reviewed", "disputed", "unknown"}
        for index, review in enumerate(review_dimensions):
            review = require_object_fields(
                review, {"dimension", "state", "scope", "evidence_source_ids"},
                f"{example_path.name} review dimension {index + 1}",
            )
            if review.get("dimension") not in valid_dimensions or review.get("state") not in valid_review_states:
                raise ValueError(f"{example_path.name} review dimension {index + 1} has an invalid dimension or state.")
            validate_review_record(review, f"{example_path.name} review dimension {index + 1}")
            if not isinstance(review.get("scope"), str) or not review["scope"].strip():
                raise ValueError(f"{example_path.name} review dimension {index + 1} needs a nonempty scope.")
            evidence_ids = review.get("evidence_source_ids")
            if not isinstance(evidence_ids, list) or any(not isinstance(source_id, str) or not source_id for source_id in evidence_ids):
                raise ValueError(f"{example_path.name} review dimension {index + 1} evidence_source_ids must be a list of source IDs.")
        labels = record.get("labels", [])
        if not isinstance(labels, list):
            raise ValueError(f"{example_path.name} labels must be a list.")
        for index, label in enumerate(labels):
            label = require_object_fields(
                label, {"value", "language_tag", "label_type"},
                f"{example_path.name} label {index + 1}",
            )
            if (not isinstance(label.get("value"), str) or not label["value"].strip()
                    or not language_pattern.fullmatch(str(label.get("language_tag", "")))
                    or label.get("label_type") not in {"preferred", "alternate", "transliterated", "original_form", "community_name"}):
                raise ValueError(f"{example_path.name} label {index + 1} needs text, a language tag, and a valid label type.")
        if record.get("schema_version") != properties.get("schema_version", {}).get("const"):
            raise ValueError(f"{example_path.name} version does not match its schema.")
        agent_roles = {"author", "translator", "editor", "transcriber", "digitizer", "reviewer", "publisher", "community_steward", "software"}
        agents = record.get("agents")
        if not isinstance(agents, list):
            raise ValueError(f"{example_path.name} agents must be a list; use an empty list when no layer-specific attribution is supported.")
        for agent in agents:
            agent_sources = agent.get("source_ids") if isinstance(agent, dict) else None
            if (not isinstance(agent, dict) or not isinstance(agent.get("role"), str)
                    or agent.get("role") not in agent_roles
                    or not isinstance(agent.get("name"), str) or not agent["name"].strip()
                    or not isinstance(agent_sources, list) or not agent_sources
                    or any(not isinstance(source_id, str) for source_id in agent_sources)
                    or set(agent_sources) - source_ids):
                raise ValueError(f"{example_path.name} has an agent attribution without a name, valid role, or cited source; do not infer contributor identities.")
        if (record.get("layer_type") not in valid_layer_types
                or record.get("text_origin") not in valid_text_origins
                or record.get("publication_state") not in valid_publication_states):
            raise ValueError(f"{example_path.name} has an invalid layer type, text origin, or publication state.")
        if (record.get("publication_state") == "bundled"
                and record.get("text_origin") in {"machine_generated_draft", "unknown"}):
            raise ValueError(f"{example_path.name} cannot bundle generated draft wording or text with unknown origin.")
        if (record.get("layer_type") in {"source_text_transcription", "diplomatic_transcription"}
                and record.get("text_origin") != "source_transcription"):
            raise ValueError(f"{example_path.name} transcription layer must identify its origin as a source transcription.")
        if (record.get("layer_type") == "translation"
                and record.get("text_origin") not in {"published_translation", "machine_generated_draft"}):
            raise ValueError(f"{example_path.name} translation layer needs a published-translation or generated-draft origin.")
        identifiers = [record.get("record_id"), record.get("work_id"), record.get("witness", {}).get("witness_id")]
        for assertion in record.get("tradition_assertions", []):
            identifiers.extend((assertion.get("tradition_id"), assertion.get("canon_id")))
        for identifier in identifiers:
            parsed = urlparse(str(identifier or ""))
            if parsed.scheme not in {"https", "urn"} or (parsed.scheme == "https" and not parsed.netloc):
                raise ValueError(f"{example_path.name} has an identifier that is not a persistent HTTPS IRI or URN.")
        if (not language_pattern.fullmatch(str(record.get("language_tag", "")))
                or not re.fullmatch(r"^[A-Z][a-z]{3}$", str(record.get("script_code", "")))):
            raise ValueError(f"{example_path.name} needs a BCP 47 language tag and ISO 15924 script code.")
        path = record.get("basis_path")
        if path is not None and (
                not isinstance(path, list) or not path
                or any(not language_pattern.fullmatch(str(tag)) for tag in path)):
            raise ValueError(f"{example_path.name} needs a language-tagged basis path or explicit null.")
        if (record["layer_type"] == "translation" and path is not None
                and (len(path) < 2 or path[-1] != record["language_tag"])):
            raise ValueError(f"{example_path.name} translation path must end at its output language.")
        if (record["layer_type"] in {"source_text_transcription", "diplomatic_transcription"}
                and path is not None and path != [record["language_tag"]]):
            raise ValueError(f"{example_path.name} transcription basis path must identify its text language.")
        path_requires_language = (
            record["layer_type"] == "translation"
            or (record["layer_type"] in {"source_text_transcription", "diplomatic_transcription"}
                and record.get("language_tag") != "und")
        )
        if (path is None and record.get("publication_state") == "bundled" and path_requires_language):
            raise ValueError(f"{example_path.name} cannot publish a translation or transcription with an unknown language basis.")
        referenced_sources: set[str] = set()

        def gather_sources(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    if key in {"source_ids", "evidence_source_ids"} and isinstance(child, list):
                        referenced_sources.update(child)
                    else:
                        gather_sources(child)
            elif isinstance(value, list):
                for child in value:
                    gather_sources(child)

        gather_sources(record)
        if not referenced_sources or referenced_sources - source_ids:
            raise ValueError(f"{example_path.name} has missing source records: {sorted(referenced_sources - source_ids)}")
        rights_evidence = set(rights.get("evidence_source_ids", []))
        if record.get("publication_state") == "bundled":
            if rights.get("status") not in {"public_domain_claimed", "open_license", "permission_limited"}:
                raise ValueError(f"{example_path.name} cannot bundle text with unresolved or mixed rights.")
            if not rights_evidence or rights_evidence - source_ids:
                raise ValueError(f"{example_path.name} needs valid rights evidence before bundling.")
        relative_path = unquote(str(package.get("uri", "")))
        package_path = (example_path.parent / relative_path).resolve()
        if not package_path.is_relative_to(ROOT.resolve()) or not package_path.is_file():
            raise ValueError(f"{example_path.name} must reference an existing local package inside the site.")
        digest = hashlib.sha256(package_path.read_bytes()).hexdigest()
        if package.get("sha256", "").lower() != digest:
            raise ValueError(f"{example_path.name} package SHA-256 does not match its local reader.")
        package_document = json.loads(package_path.read_text(encoding="utf-8"))
        selector = package.get("json_pointer", "")
        packaged_reader = resolve_json_pointer(package_document, selector, f"{example_path.name} content package")
        if not isinstance(packaged_reader, dict):
            raise ValueError(f"{example_path.name} content package selector must resolve to a JSON object.")
        if packaged_reader.get("text_origin") != record["text_origin"]:
            raise ValueError(f"{example_path.name} text origin disagrees with its packaged reader.")
        packaged_unit_count = sum(
            len(chapter.get("verses", chapter.get("units", [])))
            for chapter in packaged_reader.get("chapters", [])
        )
        if (record.get("language_tag") != packaged_reader.get("language_tag")
                or record.get("script_code") != packaged_reader.get("script_code")
                or record.get("text_origin") != packaged_reader.get("text_origin")
                or record.get("language_tag") not in audited_language_tags
                or record.get("script_code") not in audited_script_codes
                or record.get("coverage", {}).get("unit_count") != packaged_unit_count):
            raise ValueError(f"{example_path.name} language, script, origin, or unit count disagrees with its content package.")
        records.append(record)
    manifest = {
        "manifest_version": 1,
        "schema_uri": "../schemas/text-layer.schema.json",
        "coverage_statement": f"This manifest includes portable metadata for {len(records)} selected text layers across the bundled readers. It does not represent complete canon or language coverage.",
        "records": records,
    }
    return manifest["records"]


def main() -> None:
    offline_shell_files = validate_offline_shell()
    archive = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    # Source-backed reader JSON files are merged offline; companion-only files are nested by their builder.
    reader_files = sorted((ROOT / "readers").glob("*-geez.json")) + [
        ROOT / "readers" / "jubilees-geez-hacohen.json",
        ROOT / "readers" / "enoch-geez-eotc.json",
        ROOT / "readers" / "psalms-geez-ludolf.json",
        ROOT / "readers" / "mark-research-tei.json",
        ROOT / "readers" / "job-brenton-lxx-1851.json",
        ROOT / "readers" / "tobit-brenton-lxx-1851.json",
        ROOT / "readers" / "sirach-brenton-lxx-1851.json",
    ] + sorted((ROOT / "readers").glob("brenton-lxx-*-research.json"))
    current_readers = [json.loads(path.read_text(encoding="utf-8")) for path in reader_files if path.exists()]
    current_readers.sort(key=lambda reader: (
        0 if reader.get("canon_id") else 1,
        reader.get("canon_id") or reader.get("research_corpus_id", ""),
    ))
    current_ids = {reader.get("reader_id") for reader in current_readers}
    archive["readers"] = [reader for reader in archive.get("readers", []) if reader.get("reader_id") not in current_ids] + current_readers
    canon_path = ROOT / "canon-registry.json"
    if canon_path.exists():
        registry = json.loads(canon_path.read_text(encoding="utf-8"))
        archive["canon_registry"] = registry
    language_registry_path = ROOT / "translation-registry.json"
    if language_registry_path.exists():
        archive["translation_registry"] = json.loads(language_registry_path.read_text(encoding="utf-8"))
    reader_names = ", ".join(reader.get("title", reader.get("reader_id", "unnamed reader")) for reader in current_readers)
    canon_reader_count = sum(bool(reader.get("canon_id")) for reader in current_readers)
    research_reader_count = sum(bool(reader.get("research_corpus_id")) for reader in current_readers)
    research_reader_noun = "reader" if research_reader_count == 1 else "readers"
    archive["reader_policy"] = (
        f"This embedded archive bundles {canon_reader_count} canon-linked reader records and "
        f"{research_reader_count} separately scoped research {research_reader_noun}: {reader_names}. "
        "Language and edition scope, source limits, and rights are recorded per reader. Companion translations are "
        "distinct witnesses and are not presumed to translate the accompanying source text. Source snapshots, notices, "
        "and boundaries are stored locally. No runtime fetch or generated scripture is used."
    )
    catalogue = archive.get("catalogue", [])
    sources = archive.get("sources", [])
    related = archive.get("related_texts", [])
    readers = archive.get("readers", [])
    canon_registry = archive.get("canon_registry", {})
    translation_registry = archive.get("translation_registry", {})
    translation_schema = json.loads((ROOT / "translation-registry.schema.json").read_text(encoding="utf-8"))
    if translation_schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise ValueError("Translation registry schema must declare JSON Schema 2020-12.")
    validate_closed_schema_objects(translation_registry, translation_schema, translation_schema, "translation-registry.json")
    if not all(isinstance(items, list) for items in (catalogue, sources, related, readers)):
        raise ValueError("catalogue, sources, related_texts, and readers must be arrays.")

    require_unique(catalogue, "catalogue_id", "catalogue record")
    source_ids = require_unique(sources, "source_id", "source record")
    validate_source_urls(sources)
    validate_brenton_exodus_capture()
    validate_brenton_octateuch_companions()
    validate_crosswire_module_audit()
    validate_mark_tei_audit()
    require_unique(related, "related_id", "related-text record")
    require_unique(readers, "reader_id", "reader record")
    portable_layer_records = validate_global_layer_example(source_ids)

    canon_books = canon_registry.get("books", [])
    if canon_registry.get("book_count") != 81 or len(canon_books) != 81:
        raise ValueError("The canon coverage registry must contain the Church-listed 81 entries.")
    if sum(book.get("section") == "Old Testament" for book in canon_books) != 46 or sum(book.get("section") == "New Testament" for book in canon_books) != 35:
        raise ValueError("The canon coverage registry must preserve the stated 46/35 section counts.")
    canon_ids = require_unique(canon_books, "canon_id", "canon registry entry")
    readers_by_id = {reader["reader_id"]: reader for reader in readers}
    catalogue_ids = {item["catalogue_id"] for item in catalogue}
    if any(not book.get("catalogue_ids") for book in canon_books):
        raise ValueError("Every Church-list entry needs a catalogue navigation record, even when its identity crosswalk remains unresolved.")
    if any(set(book.get("catalogue_ids", [])) - catalogue_ids for book in canon_books):
        raise ValueError("A canon registry entry refers to an unknown catalogue row.")
    mapped_catalogue_ids = {catalogue_id for book in canon_books for catalogue_id in book.get("catalogue_ids", [])}
    if catalogue_ids - mapped_catalogue_ids:
        raise ValueError(f"Catalogue rows are missing from the canon navigation crosswalk: {sorted(catalogue_ids - mapped_catalogue_ids)}")
    canon_by_id = {book["canon_id"]: book for book in canon_books}
    catalogue_by_id = {item["catalogue_id"]: item for item in catalogue}
    # The Church list orders James after III John, but this catalogue places
    # James first. Guard these evidence-reviewed title links against regressions.
    expected_nt_catalogue = {
        "eotc-nt-20": ("eotc-075", "1 Peter"),
        "eotc-nt-21": ("eotc-076", "2 Peter"),
        "eotc-nt-22": ("eotc-077", "1 John"),
        "eotc-nt-23": ("eotc-078", "2 John"),
        "eotc-nt-24": ("eotc-079", "3 John"),
        "eotc-nt-25": ("eotc-074", "James"),
    }
    for canon_id, (catalogue_id, display_name) in expected_nt_catalogue.items():
        entry = canon_by_id[canon_id]
        if entry.get("catalogue_ids") != [catalogue_id] or catalogue_by_id[catalogue_id].get("display_name") != display_name:
            raise ValueError(f"Incorrect catalogue crosswalk for {entry.get('source_label')!r}.")
    ezra_group = canon_by_id["eotc-ot-16"]
    if ezra_group.get("catalogue_ids") != ["eotc-090", "eotc-019"]:
        raise ValueError("Church-list entry 16 must keep both Ezra title-level discovery rows.")
    if "unresolved" not in ezra_group.get("mapping_note", "").lower():
        raise ValueError("Ezra entry 16 must retain its unresolved identity and crosswalk warning.")
    wisdom_entry = canon_by_id["eotc-ot-26"]
    if catalogue_by_id["eotc-031"].get("display_name") != wisdom_entry.get("source_label"):
        raise ValueError("The wisdom catalogue row must preserve the Church list's source label.")
    if "not established" not in wisdom_entry.get("mapping_note", "").lower():
        raise ValueError("The wisdom entry must retain its unresolved work-identity warning.")
    for canon_id in ("eotc-ot-20", "eotc-ot-21", "eotc-ot-24", "eotc-ot-25", "eotc-ot-45"):
        if "SRC-101" not in canon_by_id[canon_id].get("source_ids", []):
            raise ValueError(f"{canon_id} must cite the scholarly historical-list comparison.")
        if not canon_by_id[canon_id].get("mapping_note"):
            raise ValueError(f"{canon_id} needs an explicit, attributed mapping limitation.")
    for number in range(28, 36):
        canon_id = f"eotc-nt-{number:02d}"
        if "SRC-073" not in canon_by_id[canon_id].get("source_ids", []):
            raise ValueError(f"{canon_id} must cite the dissertation used for its title crosswalk context.")
        if not canon_by_id[canon_id].get("mapping_note"):
            raise ValueError(f"{canon_id} needs an explicit title/identity limitation.")
    if any(set(book.get("source_ids", [])) - source_ids for book in canon_books):
        raise ValueError("A canon registry entry refers to an unknown source.")
    for book in canon_books:
        has_bundled_reader = str(book.get("reader_status", "")).startswith("Bundled:")
        reader_id = book.get("reader_id")
        if has_bundled_reader and reader_id not in readers_by_id:
            raise ValueError(f"Bundled canon entry {book['canon_id']} has no matching reader record.")
        if reader_id and reader_id not in readers_by_id:
            raise ValueError(f"Canon entry {book['canon_id']} refers to an unknown reader.")
        if reader_id and readers_by_id[reader_id].get("canon_id") != book["canon_id"]:
            raise ValueError(f"Reader {reader_id} is not explicitly linked back to canon entry {book['canon_id']}.")
        if not has_bundled_reader and reader_id:
            raise ValueError(f"Canon entry {book['canon_id']} links a reader while marked as unbundled.")
    for reader in readers:
        canon_id = reader.get("canon_id")
        if canon_id and canon_id not in canon_ids:
            raise ValueError(f"Reader {reader['reader_id']} refers to an unknown canon entry.")
    registry_sources = set(canon_registry.get("source_id", [])) if isinstance(canon_registry.get("source_id"), list) else {canon_registry.get("source_id")}
    registry_sources.update(canon_registry.get("context_source_ids", []))
    if not registry_sources.issubset(source_ids):
        raise ValueError("The canon registry refers to an unknown source.")
    # This is a count of reader records present in the embedded build, not the
    # number of catalogue labels that claim text is bundled.
    canon_registry["reader_count"] = sum(
        1 for book in canon_books
        if any(reader.get("canon_id") == book["canon_id"] and
               (not book.get("reader_id") or reader.get("reader_id") == book["reader_id"])
               for reader in readers)
    )

    language_records = translation_registry.get("languages", [])
    if (translation_registry.get("schema_version") != 2
            or not isinstance(language_records, list)
            or not isinstance(translation_registry.get("translation_leads"), list)
            or not isinstance(translation_registry.get("corpus_leads"), list)
            or not isinstance(translation_registry.get("edition_leads"), list)
            or not translation_registry.get("coverage_statement")):
        raise ValueError("The version 2 translation registry needs language, translation, corpus, and source-edition lists plus an explicit coverage statement.")
    identifier_audit = json.loads((ROOT / "language-script-code-audit.json").read_text(encoding="utf-8"))
    language_audit = identifier_audit.get("language_subtags", {})
    script_audit = identifier_audit.get("script_codes", {})
    audited_language_tags = set(language_audit.get("codes", []))
    audited_script_codes = set(script_audit.get("iso_15924_codes", [])) | set(script_audit.get("iana_special_codes", []))
    iana_special_script_codes = set(script_audit.get("iana_special_codes", []))
    if (language_audit.get("source_id") not in source_ids
            or script_audit.get("iso_15924_source_id") not in source_ids
            or script_audit.get("iana_special_source_id") not in source_ids
            or not audited_language_tags or not audited_script_codes):
        raise ValueError("Language and script identifier audits must cite valid authority sources and contain codes.")
    expected_coverage = build_coverage_statement(translation_registry, canon_registry)
    if translation_registry["coverage_statement"] != expected_coverage:
        raise ValueError("The translation coverage statement is stale; regenerate it from current registry records.")
    language_tags = require_unique(language_records, "language_tag", "language registry entry")
    basis_language_tags = require_unique(translation_registry.get("basis_languages", []), "language_tag", "basis language entry")
    known_language_tags = language_tags | basis_language_tags | {"und"}
    if not known_language_tags.issubset(audited_language_tags):
        raise ValueError(f"Language registry contains subtags absent from its cited IANA audit: {sorted(known_language_tags - audited_language_tags)}")
    for basis in translation_registry.get("basis_languages", []):
        if set(basis.get("source_ids", [])) - source_ids:
            raise ValueError(f"Basis language {basis['language_tag']} refers to an unknown evidence source.")
    for language in language_records:
        scripts = set(language.get("script_codes", [])) | {language.get("script_code")}
        if not scripts.issubset(audited_script_codes):
            raise ValueError(f"Language {language['language_tag']} uses script codes absent from its cited ISO/IANA audit: {sorted(scripts - audited_script_codes)}")
    language_tag_pattern = re.compile(r"^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*$")
    script_code_pattern = re.compile(r"^[A-Z][a-z]{3}$")
    for lead in translation_registry.get("translation_leads", []):
        validate_rights_classification(lead, f"Translation lead {lead.get('canon_id')}")
        if lead.get("canon_id") not in canon_ids or lead.get("language_tag") not in language_tags:
            raise ValueError("A translation lead refers to an unknown canon item or language.")
        path = lead.get("translation_path")
        if path is not None and (not isinstance(path, list) or len(path) < 2 or path[-1] != lead.get("language_tag") or any(tag not in known_language_tags for tag in path)):
            raise ValueError("A translation lead's ordered path must use known language tags and end in its output language.")
        if set(lead.get("source_ids", [])) - source_ids:
            raise ValueError("A translation lead has an unknown source record.")
        if lead.get("text_bundled") is not False or not lead.get("review_status") or not lead.get("rights_status"):
            raise ValueError("Unbundled translation leads must state their review and rights boundaries.")
    corpus_leads = translation_registry.get("corpus_leads", [])
    require_unique(corpus_leads, "corpus_id", "corpus translation lead")
    languages_by_tag = {language["language_tag"]: language for language in language_records}
    for lead in corpus_leads:
        validate_rights_classification(lead, f"Corpus lead {lead.get('corpus_id')}")
        if not language_tag_pattern.fullmatch(str(lead.get("language_tag", ""))) or not lead.get("language_name") or not lead.get("scope_description"):
            raise ValueError("A corpus lead needs valid language and explicit scope metadata.")
        language = languages_by_tag.get(lead["language_tag"])
        if not language or lead.get("language_name") != language.get("language_name"):
            raise ValueError(f"Corpus lead {lead.get('corpus_id')} must match a registered language name.")
        if not language_tag_pattern.fullmatch(str(lead.get("basis_language_tag", ""))) or not lead.get("basis_description"):
            raise ValueError("A corpus lead needs an explicit basis-language tag and description; use 'und' if unknown.")
        path = lead.get("translation_path")
        if path is not None and (not isinstance(path, list) or len(path) < 2 or path[0] != lead.get("basis_language_tag") or path[-1] != lead.get("language_tag") or any(tag not in known_language_tags for tag in path)):
            raise ValueError(f"Corpus lead {lead.get('corpus_id')} has an invalid source-to-output language path.")
        lead_script = str(lead.get("script_code", ""))
        language_scripts = set(language.get("script_codes", [])) or {language.get("script_code")}
        if not script_code_pattern.fullmatch(lead_script):
            raise ValueError("A corpus lead needs an ISO 15924 script code.")
        if lead_script != "Zzzz" and lead_script not in language_scripts:
            raise ValueError(f"Corpus lead {lead.get('corpus_id')} uses a script absent from its language profile.")
        if lead.get("script_status", "identified") not in {"identified", "unidentified", "provisional"}:
            raise ValueError(f"Corpus lead {lead.get('corpus_id')} has an invalid script review state.")
        if set(lead.get("source_ids", [])) - source_ids:
            raise ValueError("A corpus lead refers to an unknown source record.")
        if lead.get("text_bundled") is not False or not lead.get("rights_status") or not lead.get("review_status"):
            raise ValueError("Unbundled corpus leads must state review and rights boundaries.")
    edition_leads = translation_registry.get("edition_leads", [])
    require_unique(edition_leads, "edition_id", "source-edition lead")
    languages_by_tag = {language["language_tag"]: language for language in language_records}
    valid_mapping_states = {"asserted_by_source", "reviewed_match", "related_work", "uncertain", "not_mapped"}
    for lead in edition_leads:
        label = f"Source-edition lead {lead.get('edition_id')}"
        validate_rights_classification(lead, label)
        if lead.get("candidate_canon_id") not in canon_ids:
            raise ValueError(f"{label} needs a valid candidate Church-list entry.")
        if lead.get("mapping_state") not in valid_mapping_states:
            raise ValueError(f"{label} has an invalid or missing mapping state.")
        if lead.get("witness_type") not in {"manuscript", "printed_edition", "critical_edition", "digital_edition", "transcription", "composite", "unknown"}:
            raise ValueError(f"{label} has an invalid or missing witness type.")
        lead_language_tag = lead.get("language_tag")
        language_tags = lead.get("language_tags", [])
        if lead_language_tag == "mul":
            if (lead.get("language_name") != "Multiple languages"
                    or not isinstance(language_tags, list)
                    or len(language_tags) < 2
                    or len(language_tags) != len(set(language_tags))
                    or any(tag not in languages_by_tag for tag in language_tags)):
                raise ValueError(f"{label} must list at least two registered component languages for mul.")
            language_profiles = [languages_by_tag[tag] for tag in language_tags]
            language_scripts = set.intersection(*[
                set(item.get("script_codes", [])) or {item.get("script_code")}
                for item in language_profiles
            ])
        else:
            language = languages_by_tag.get(lead_language_tag)
            if not language or lead.get("language_name") != language.get("language_name"):
                raise ValueError(f"{label} must match a registered language profile.")
            if language_tags:
                raise ValueError(f"{label} may list component language_tags only when language_tag is mul.")
            language_scripts = set(language.get("script_codes", [])) or {language.get("script_code")}
        lead_script = lead.get("script_code")
        if not script_code_pattern.fullmatch(str(lead_script or "")) or lead_script not in language_scripts:
            if not (lead_language_tag == "mul" and lead_script == "Zzzz" and lead_script in iana_special_script_codes):
                raise ValueError(f"{label} must use a script code supported by its registered language profile(s).")
        if lead_language_tag not in audited_language_tags or lead_script not in audited_script_codes:
            raise ValueError(f"{label} uses a language or script identifier absent from the cited standards audits.")
        if any(tag not in audited_language_tags for tag in language_tags):
            raise ValueError(f"{label} has a component language tag absent from the cited IANA audit.")
        if set(lead.get("source_ids", [])) - source_ids:
            raise ValueError(f"{label} refers to an unknown source record.")
        if lead.get("text_bundled") is not False:
            raise ValueError(f"{label} is a discovery record and cannot itself assert bundled reader text.")
        if any(not isinstance(lead.get(field), str) or not lead[field].strip() for field in ("title", "edition_statement", "scope_description", "rights_status", "review_status")):
            raise ValueError(f"{label} needs title, edition, scope, rights, and review-limit statements.")
        if lead.get("rights_classification") == "open_license" and not (lead.get("license_id") and lead.get("license_url")):
            raise ValueError(f"{label} must identify the exact open license and URL.")
    valid_directions = {"ltr", "rtl", "unknown"}
    valid_writing_modes = {"horizontal-tb", "vertical-rl", "vertical-lr", "unknown"}
    valid_roles = {"source_text_transcription", "source_text_edition", "translation", "historical_companion_translation", "transliteration", "paraphrase", "draft_translation"}
    valid_statuses = {"candidate", "transcribed", "source_checked", "translated_draft", "translation_reviewed", "bundled"}
    readers_by_id = {reader["reader_id"]: reader for reader in readers}
    reader_ids = {item["reader_id"] for item in readers}
    research_by_reader = {item.get("reader_id"): item for item in translation_registry.get("research_corpora", [])}
    for language in language_records:
        if not language_tag_pattern.fullmatch(str(language.get("language_tag", ""))) or not language.get("language_name") or not script_code_pattern.fullmatch(str(language.get("script_code", ""))) or language.get("direction") not in valid_directions:
            raise ValueError(f"Language {language.get('language_tag')} needs name, script, and direction metadata.")
        if language.get("writing_mode") is not None and language.get("writing_mode") not in valid_writing_modes:
            raise ValueError(f"Language {language.get('language_tag')} has an invalid writing_mode.")
        script_codes = language.get("script_codes", [language.get("script_code")])
        if not isinstance(script_codes, list) or not script_codes or len(script_codes) != len(set(script_codes)) or any(not script_code_pattern.fullmatch(str(code)) for code in script_codes):
            raise ValueError(f"Language {language.get('language_tag')} has invalid or duplicate script codes.")
        if set(language.get("source_ids", [])) - source_ids:
            raise ValueError(f"Language {language.get('language_tag')} points to an unknown script evidence source.")
        validate_availability_survey(
            language.get("availability_survey"),
            f"Language {language['language_tag']} availability_survey",
            source_ids,
        )
        for layer in language.get("records", []):
            validate_rights_classification(layer, f"Language layer {language['language_tag']}/{layer.get('canon_id')}")
            if layer.get("canon_id") not in canon_ids:
                raise ValueError(f"Language layer in {language['language_tag']} points to an unknown canon item.")
            reader_id = layer.get("reader_id")
            if reader_id is not None and reader_id not in reader_ids:
                raise ValueError(f"Language layer in {language['language_tag']} points to an unknown reader.")
            if layer.get("status") == "bundled" and reader_id is None:
                raise ValueError(f"Bundled language layer in {language['language_tag']} needs a reader.")
            if layer.get("translation_id") and reader_id is None:
                raise ValueError(f"Translation layer in {language['language_tag']} needs a reader record.")
            translation_roles = {"translation", "historical_companion_translation", "draft_translation"}
            if layer.get("status") == "bundled" and layer.get("layer_role") == "draft_translation":
                raise ValueError(
                    f"Draft translation in {language['language_tag']} cannot be counted as bundled text."
                )
            if layer.get("status") == "bundled" and layer.get("layer_role") in translation_roles and not layer.get("translation_id"):
                raise ValueError(
                    f"Bundled translation in {language['language_tag']} must point to a distinct published translation layer."
                )
            if layer.get("translation_id") and layer.get("layer_role") not in translation_roles:
                raise ValueError(
                    f"Translation ID in {language['language_tag']} is attached to a non-translation layer."
                )
            if layer.get("basis_language_tag") not in known_language_tags:
                raise ValueError(f"Language layer in {language['language_tag']} has an unregistered basis language.")
            if set(layer.get("source_ids", [])) - source_ids:
                raise ValueError(f"Language layer in {language['language_tag']} points to an unknown source.")
            if not layer.get("basis_description") or not layer.get("rights_status") or not layer.get("status"):
                raise ValueError(f"Language layer in {language['language_tag']} needs basis, rights, and status metadata.")
            if not language_tag_pattern.fullmatch(str(layer.get("basis_language_tag", ""))) or layer.get("layer_role") not in valid_roles or layer.get("status") not in valid_statuses:
                raise ValueError(f"Language layer in {language['language_tag']} has an invalid language tag, role, or status.")
            path = layer.get("translation_path")
            if layer.get("layer_role") in translation_roles and (not isinstance(path, list) or len(path) < 2 or path[0] != layer.get("basis_language_tag") or path[-1] != language["language_tag"] or any(tag not in known_language_tags for tag in path)):
                raise ValueError(f"Translation layer in {language['language_tag']} needs an ordered source-to-output language path.")
            if path is not None and (not isinstance(path, list) or len(path) < 2 or path[0] != layer.get("basis_language_tag") or path[-1] != language["language_tag"] or any(tag not in known_language_tags for tag in path)):
                raise ValueError(f"Language path in {language['language_tag']} must start at its basis and end at its output language.")
            if layer.get("status") == "bundled" and layer.get("reader_id") not in reader_ids:
                raise ValueError(f"Bundled language layer in {language['language_tag']} has no reader.")
            if reader_id is not None:
                reader = readers_by_id[reader_id]
                reader_canon_id = reader.get("canon_id")
                research = research_by_reader.get(reader_id)
                if reader_canon_id is None and research:
                    reader_canon_id = research.get("candidate_canon_id")
                if reader_canon_id != layer.get("canon_id"):
                    raise ValueError(
                        f"Language layer in {language['language_tag']} points to reader {reader_id} "
                        f"for canon candidate {reader_canon_id!r}, not its declared entry {layer.get('canon_id')!r}."
                    )
                text_record = reader.get("parallel_translation") if layer.get("translation_id") else reader
                if layer.get("translation_id") and text_record is None and reader.get("translation_id") == layer["translation_id"]:
                    text_record = reader
                if layer.get("translation_id") and text_record.get("translation_id") != layer["translation_id"]:
                    raise ValueError(f"Language layer in {language['language_tag']} names a translation missing from its reader.")
                if layer.get("status") == "bundled" and text_record.get("language_tag") != language["language_tag"]:
                    raise ValueError(f"Bundled language tag in the registry disagrees with its reader data.")

    for record in related:
        missing = set(record.get("source_ids", [])) - source_ids
        if missing:
            raise ValueError(f"{record.get('title')} refers to missing sources: {sorted(missing)}")

    research_corpora = translation_registry.get("research_corpora", [])
    require_unique(research_corpora, "corpus_id", "separately scoped research corpus")
    for corpus in research_corpora:
        validate_rights_classification(corpus, f"Research corpus {corpus.get('corpus_id')}")
        reader = readers_by_id.get(corpus.get("reader_id"))
        if not reader or reader.get("research_corpus_id") != corpus.get("corpus_id"):
            raise ValueError(f"Research corpus {corpus.get('corpus_id')} must point to its matching reader record.")
        if reader.get("canon_id") is not None or corpus.get("canon_mapping_state") not in {"uncertain", "not_mapped"}:
            raise ValueError(f"Research corpus {corpus.get('corpus_id')} must stay outside canon-linked reader coverage.")
        candidate_canon_id = corpus.get("candidate_canon_id")
        mapping_state = corpus.get("canon_mapping_state")
        if mapping_state == "uncertain" and candidate_canon_id not in canon_ids:
            raise ValueError(f"Research corpus {corpus.get('corpus_id')} needs a valid, explicitly provisional title candidate.")
        if mapping_state == "not_mapped" and candidate_canon_id is not None:
            raise ValueError(f"Research corpus {corpus.get('corpus_id')} must not carry a canon candidate when mapping is not assigned.")
        if not corpus.get("language_description") or not corpus.get("unit_summary") or not corpus.get("review_status"):
            raise ValueError(f"Research corpus {corpus.get('corpus_id')} must describe language, observed units, and review limits.")
        if corpus.get("rights_classification") == "open_license" and not (corpus.get("license_id") and corpus.get("license_url")):
            raise ValueError(f"Research corpus {corpus.get('corpus_id')} must identify its exact open license and URL.")
        if set(corpus.get("source_ids", [])) - source_ids:
            raise ValueError(f"Research corpus {corpus.get('corpus_id')} refers to an unknown source.")
        if reader.get("unit_count") != corpus.get("unit_count"):
            raise ValueError(f"Research corpus {corpus.get('corpus_id')} unit count disagrees with its reader.")
        if corpus.get("text_origin") and corpus.get("text_origin") != reader.get("text_origin"):
            raise ValueError(f"Research corpus {corpus.get('corpus_id')} text origin disagrees with its reader.")
        if corpus.get("text_origin") == "published_translation":
            required_translation_fields = ("language_tag", "script_code", "basis_language_tag", "translation_path", "translation_id", "translator", "edition_statement")
            if any(not corpus.get(field) for field in required_translation_fields):
                raise ValueError(f"Research translation {corpus.get('corpus_id')} needs complete language and translation-basis metadata.")
            if any(corpus.get(field) != reader.get(field) for field in ("language_tag", "script_code", "basis_language_tag", "translation_path", "translation_id", "translator")):
                raise ValueError(f"Research translation {corpus.get('corpus_id')} language or translator metadata disagrees with its reader.")
            path = corpus["translation_path"]
            if (corpus["basis_language_tag"] not in known_language_tags or corpus["language_tag"] not in known_language_tags
                    or path[0] != corpus["basis_language_tag"] or path[-1] != corpus["language_tag"]
                    or any(tag not in known_language_tags for tag in path)):
                raise ValueError(f"Research translation {corpus.get('corpus_id')} has an unregistered or inconsistent translation path.")

    for reader in readers:
        required_reader_fields = (
            "title", "language", "language_tag", "edition", "edition_scope",
            "copyright_notice", "commercial_use", "rights_classification", "verification_status",
            "chapter_structure_note", "source_ids", "unit_count", "unit_label",
        )
        missing_fields = [field for field in required_reader_fields if not reader.get(field)]
        if missing_fields:
            raise ValueError(
                f"{reader.get('reader_id', 'Reader')} is missing provenance, rights, or review metadata: "
                f"{', '.join(missing_fields)}. Record unknowns explicitly."
            )
        if not reader["source_ids"]:
            raise ValueError(f"{reader['reader_id']} must cite at least one source record.")
        validate_rights_classification(reader, f"Reader {reader['reader_id']}")
        if reader.get("research_corpus_id"):
            rights_records = [
                record for record in research_corpora
                if record.get("reader_id") == reader["reader_id"]
                and record.get("corpus_id") == reader["research_corpus_id"]
            ]
        else:
            rights_records = [
                layer for language in language_records for layer in language.get("records", [])
                if layer.get("reader_id") == reader["reader_id"]
                and not layer.get("translation_id") and layer.get("status") == "bundled"
            ]
        if len(rights_records) != 1 or reader["rights_classification"] != rights_records[0].get("rights_classification"):
            raise ValueError(f"Reader {reader['reader_id']} rights classification must match exactly one bundled registry layer or research record.")
        if reader.get("language_tag") not in audited_language_tags or reader.get("script_code") not in audited_script_codes:
            raise ValueError(f"{reader['reader_id']} uses language or script codes absent from the cited identifier audit.")
        if reader.get("canon_id") is None and not reader.get("research_corpus_id"):
            raise ValueError(f"{reader['reader_id']} must be linked to a canon entry or a separately scoped research corpus.")
        allowed_research_translation = bool(reader.get("research_corpus_id")) and reader.get("text_origin") == "published_translation"
        if reader.get("text_origin") != "source_transcription" and not allowed_research_translation:
            raise ValueError(
                f"{reader['reader_id']} must identify a source transcription, or a separately scoped published research translation; "
                "machine-generated wording is not admissible as a scripture witness."
            )
        if allowed_research_translation:
            for field in ("translation_id", "translator", "basis_language_tag", "translation_path"):
                if not reader.get(field):
                    raise ValueError(f"Published research translation {reader['reader_id']} is missing {field}.")
            path = reader["translation_path"]
            if (reader["basis_language_tag"] not in known_language_tags or path[0] != reader["basis_language_tag"]
                    or path[-1] != reader["language_tag"] or any(tag not in known_language_tags for tag in path)):
                raise ValueError(f"Published research translation {reader['reader_id']} has an invalid translation path.")
        missing = set(reader.get("source_ids", [])) - source_ids
        if missing:
            raise ValueError(f"{reader.get('title')} refers to missing sources: {sorted(missing)}")
        chapters = reader.get("chapters", [])
        if not chapters or [item.get("chapter") for item in chapters] != list(range(1, len(chapters) + 1)):
            raise ValueError(f"{reader.get('title')} chapter sequence must be complete and ordered from 1.")
        if reader.get("chapter_count") != len(chapters):
            raise ValueError(f"{reader.get('title')} chapter count does not match its chapters.")
        validate_observed_unit_count(reader, "unit_count", reader.get("title", reader.get("reader_id", "Reader")))
        if reader.get("verse_marker_count", reader["unit_count"]) != reader["unit_count"]:
            raise ValueError(f"{reader.get('title')} legacy verse_marker_count disagrees with its generic unit_count.")
        for chapter in chapters:
            verses = chapter.get("units", chapter.get("verses", []))
            numbers = [verse.get("number", verse.get("unit_order")) for verse in verses]
            if not verses or any(not (isinstance(number, int) or isinstance(number, str) and number.strip()) for number in numbers):
                raise ValueError(f"{reader.get('title')} chapter {chapter.get('chapter')} has invalid source-unit order markers.")
            # Source editions may print duplicate, skipped, or nonnumeric labels.
            # Preserve their source order; only conventional integer-only readers
            # are required to have unique, increasing markers.
            if all(isinstance(number, int) for number in numbers) and numbers != sorted(set(numbers)):
                raise ValueError(f"{reader.get('title')} chapter {chapter.get('chapter')} has missing, unordered, or empty source-unit text.")
            for verse in verses:
                if verse.get("text", "").strip():
                    continue
                source_note_is_present = any(
                    note.get("verse") == verse.get("number") and (note.get("text") or note.get("source_reference"))
                    for note in chapter.get("notes", [])
                )
                if not (reader.get("research_corpus_id")
                        and verse.get("source_text_state") == "marker_only"
                        and source_note_is_present):
                    raise ValueError(f"{reader.get('title')} chapter {chapter.get('chapter')} has an empty unit without an explicit source marker and note.")
        companion = reader.get("parallel_translation")
        if companion:
            required_companion_fields = (
                "title", "language", "language_tag", "edition", "translator",
                "basis_language_tag", "translation_basis", "translation_method",
                "text_notice", "rights_classification", "verification_status", "source_ids", "unit_count", "unit_label", "verse_label_count",
            )
            missing_fields = [field for field in required_companion_fields if not companion.get(field)]
            if missing_fields:
                raise ValueError(
                    f"{companion.get('translation_id', 'Companion translation')} is missing basis, "
                    f"rights, or review metadata: {', '.join(missing_fields)}. Record unknowns explicitly."
                )
            if not companion["source_ids"]:
                raise ValueError(f"{companion['translation_id']} must cite at least one source record.")
            validate_rights_classification(companion, f"Translation {companion['translation_id']}")
            companion_rights = [
                layer for language in language_records for layer in language.get("records", [])
                if layer.get("translation_id") == companion["translation_id"]
                and layer.get("status") == "bundled"
            ]
            if len(companion_rights) != 1 or companion["rights_classification"] != companion_rights[0].get("rights_classification"):
                raise ValueError(f"Translation {companion['translation_id']} rights classification must match exactly one bundled registry layer.")
            if companion.get("language_tag") not in audited_language_tags or companion.get("basis_language_tag") not in audited_language_tags or companion.get("script_code") not in audited_script_codes:
                raise ValueError(f"{companion['translation_id']} uses language or script codes absent from the cited identifier audit.")
            if companion.get("text_origin") != "published_translation":
                raise ValueError(
                    f"{companion['translation_id']} must identify a published translation as its text origin; "
                    "machine-generated wording is not admissible as a scripture witness."
                )
            missing_companion_sources = set(companion.get("source_ids", [])) - source_ids
            if missing_companion_sources:
                raise ValueError(f"{companion.get('title')} refers to missing sources: {sorted(missing_companion_sources)}")
            english_chapters = companion.get("chapters", [])
            validate_observed_unit_count(companion, "unit_count", companion.get("title", companion.get("translation_id", "Companion")))
            if companion.get("verse_label_count", companion["unit_count"]) != companion["unit_count"]:
                raise ValueError(f"{companion.get('title')} verse_label_count disagrees with its generic unit_count.")
            if len(english_chapters) != companion.get("chapter_count") or [c.get("chapter") for c in english_chapters] != list(range(1, len(english_chapters) + 1)):
                raise ValueError(f"{companion.get('title')} chapter sequence/count is incomplete.")
            def english_sort_key(label):
                match = re.fullmatch(r"(\d+)([a-z]?)", str(label))
                if not match:
                    raise ValueError(f"Invalid English verse label: {label!r}")
                return int(match.group(1)), match.group(2)
            for chapter in english_chapters:
                verses = chapter.get("verses", [])
                labels = [str(verse.get("number", "")) for verse in verses]
                if not labels or labels != sorted(set(labels), key=english_sort_key) or any(not verse.get("text", "").strip() for verse in verses):
                    raise ValueError(f"{companion.get('title')} chapter {chapter.get('chapter')} has invalid labels or missing text.")

    for record in catalogue:
        if record.get("source_id") not in source_ids:
            raise ValueError(f"{record.get('display_name')} has no valid catalogue source.")
        missing = set(record.get("evidence_source_ids", [])) - source_ids
        if missing:
            raise ValueError(f"{record.get('display_name')} refers to missing evidence sources: {sorted(missing)}")
        for field in ("identity_status", "edition_or_translation", "chapter_count", "chapter_order_status",
                      "text_availability_status", "completeness_status", "rights_status", "reviewer_notes"):
            if not record.get(field):
                raise ValueError(f"{record.get('display_name')} is missing {field}; use an explicit unknown status.")

    html = HTML_PATH.read_text(encoding="utf-8")
    if len(EMBED_RE.findall(html)) != 1:
        raise ValueError('Expected exactly one <script id="archive-data"> placeholder.')

    payload = json.dumps(archive, ensure_ascii=False, separators=(",", ":"))
    # Prevent data from closing its containing script element.
    payload = payload.replace("<", "\\u003c")
    (ROOT / "examples" / "portable-text-layers.json").write_text(
        json.dumps({
            "manifest_version": 1,
            "schema_uri": "../schemas/text-layer.schema.json",
            "coverage_statement": (
                f"This manifest includes portable metadata for {len(portable_layer_records)} selected text layers across the bundled readers. "
                "It does not represent complete canon or language coverage."
            ),
            "records": portable_layer_records,
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    DATA_PATH.write_text(json.dumps(archive, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    HTML_PATH.write_text(EMBED_RE.sub(lambda match: match.group(1) + payload + match.group(2), html), encoding="utf-8")
    write_manifest(ROOT)
    manifest_file_count = verify_manifest(ROOT)
    print(
        f"Embedded {len(catalogue)} catalogue rows, {len(sources)} sources, "
        f"{len(related)} related records, {len(readers)} offline readers, "
        f"and {len(language_records)} language profiles into index.html; "
        f"wrote and verified checksums for {manifest_file_count} package files; "
        f"validated {offline_shell_files} local offline shell files."
    )


if __name__ == "__main__":
    main()
