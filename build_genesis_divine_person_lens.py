"""Build a bounded, reproducible lexical lens record from the retained Genesis 1 witnesses."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "research" / "genesis-1-divine-person-lens.json"
READER_ID = "genesis-geez-dillmann-hacohen"
ENGLISH_TRANSLATION_ID = "genesis-english-brenton-lxx-1851"
GEʽEZ_STRING = "እግዚአብሔር"
PERSON_TOKENS = ("i", "me", "my", "mine", "we", "us", "our", "ours")

# These boundaries are an editorial speaker-attribution layer. Each excerpt is
# copied from the named Brenton verse and is checked as an exact substring.
# They are not machine-inferred, theologically decisive, or independently peer
# reviewed. `stop_before` marks the narrative response “and it was so.” where
# that phrase follows the command in the same verse.
SPEECH_SPANS = [
    {"verse": "3", "start": "Let there be light", "end": "Let there be light"},
    {"verse": "6", "start": "Let there be a firmament", "stop_before": "and it was so."},
    {"verse": "9", "start": "Let the water", "stop_before": "and it was so."},
    {"verse": "11", "start": "Let the earth bring forth", "stop_before": "and it was so."},
    {"verse": "14", "start": "Let there be lights", "end": "years."},
    {"verse": "15", "start": "And let them be for light", "stop_before": "and it was so."},
    {"verse": "20", "start": "Let the waters bring forth reptiles", "stop_before": "and it was so."},
    {"verse": "22", "start": "Increase and multiply", "end": "earth."},
    {"verse": "24", "start": "Let the earth bring forth the living", "stop_before": "and it was so."},
    {"verse": "26", "start": "Let us make man", "end": "earth."},
    {"verse": "28", "start": "Increase and multiply", "end": "earth."},
    {"verse": "29", "start": "Behold I have given", "end": "food."},
    {"verse": "30", "start": "And to all the wild beasts", "stop_before": "and it was so."},
]

# Exact English narrator phrases in which the third-person subject pronoun
# "he" refers to God in the stored Brenton witness. This editorial antecedent
# attribution is narrower than a chapter-wide search for he/him/his: e.g. the
# object "him" in Genesis 1:27 refers to the human, not God.
NARRATOR_GOD_PRONOUN_SPANS = [
    {"verse": "5", "text": "he called Night"},
    {"verse": "10", "text": "he called Seas"},
    {"verse": "27", "text": "he made him"},
    {"verse": "27", "text": "he made them"},
    {"verse": "31", "text": "he had made"},
]


def chapter_fingerprint(chapter: dict) -> str:
    text = "".join(f"{verse['number']}: {verse['text']}\n" for verse in chapter["verses"])
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def extract_span(verse_text: str, specification: dict) -> str:
    start = specification["start"]
    begin = verse_text.find(start)
    if begin < 0:
        raise ValueError(f"Genesis 1:{specification['verse']} missing attributed speech start {start!r}.")
    if "end" in specification:
        end_text = specification["end"]
        finish = verse_text.find(end_text, begin)
        if finish < 0:
            raise ValueError(f"Genesis 1:{specification['verse']} missing attributed speech end {end_text!r}.")
        finish += len(end_text)
    elif "stop_before" in specification:
        finish = verse_text.find(specification["stop_before"], begin)
        if finish < 0:
            raise ValueError(f"Genesis 1:{specification['verse']} missing narrative boundary {specification['stop_before']!r}.")
    else:
        finish = len(verse_text)
    return verse_text[begin:finish].strip()


def build() -> dict:
    archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
    readers = {reader["reader_id"]: reader for reader in archive.get("readers", [])}
    reader = readers.get(READER_ID)
    if not reader or not reader.get("parallel_translation"):
        raise ValueError("The Genesis Geʽez reader and its English companion are required.")
    companion = reader["parallel_translation"]
    if companion.get("translation_id") != ENGLISH_TRANSLATION_ID:
        raise ValueError("The Genesis 1 English witness no longer matches this bounded lens.")
    geez_chapter = next((chapter for chapter in reader["chapters"] if chapter.get("chapter") == 1), None)
    english_chapter = next((chapter for chapter in companion["chapters"] if chapter.get("chapter") == 1), None)
    if not geez_chapter or not english_chapter:
        raise ValueError("Genesis chapter 1 is missing from a named witness.")
    if len(geez_chapter["verses"]) != 31 or len(english_chapter["verses"]) != 31:
        raise ValueError("This count is scoped to the stored 31 verse labels in each Genesis 1 witness.")

    english_by_label = {str(verse["number"]): verse for verse in english_chapter["verses"]}
    spans = []
    for spec in SPEECH_SPANS:
        verse = english_by_label.get(spec["verse"])
        if not verse:
            raise ValueError(f"Genesis 1:{spec['verse']} is absent from the English witness.")
        spans.append({"verse": spec["verse"], "text": extract_span(verse["text"], spec)})

    third_person_pronoun_spans = []
    for specification in NARRATOR_GOD_PRONOUN_SPANS:
        verse = english_by_label.get(specification["verse"])
        if not verse or specification["text"] not in verse["text"]:
            raise ValueError(
                f"Genesis 1:{specification['verse']} is missing the manually attributed "
                f"third-person God-reference {specification['text']!r}."
            )
        third_person_pronoun_spans.append(specification.copy())

    token_counts = Counter(
        token.casefold()
        for span in spans
        for token in re.findall(r"(?<![\w])(?:I|me|my|mine|we|us|our|ours)(?![\w])", span["text"], re.IGNORECASE)
    )
    second_person_by_verse = {
        span["verse"]: len(re.findall(r"\byou\b", span["text"], re.IGNORECASE))
        for span in spans
    }
    second_person_by_verse = {verse: count for verse, count in second_person_by_verse.items() if count}
    god_counts = {
        str(verse["number"]): len(re.findall(r"\bGod\b", verse["text"], re.IGNORECASE))
        for verse in english_chapter["verses"]
    }
    god_counts = {label: count for label, count in god_counts.items() if count}
    attributed_speech_god_counts = Counter()
    for span in spans:
        attributed_speech_god_counts[span["verse"]] += len(
            re.findall(r"\bGod\b", span["text"], re.IGNORECASE)
        )
    narrator_god_counts = {
        label: count - attributed_speech_god_counts.get(label, 0)
        for label, count in god_counts.items()
    }
    if any(count < 0 for count in narrator_god_counts.values()):
        raise ValueError("A speech excerpt contains more noun occurrences than its stored verse.")
    narrator_god_counts = {label: count for label, count in narrator_god_counts.items() if count}
    geez_counts = {
        str(verse["number"]): verse["text"].count(GEʽEZ_STRING)
        for verse in geez_chapter["verses"]
    }
    geez_counts = {label: count for label, count in geez_counts.items() if count}
    geez_fingerprint = chapter_fingerprint(geez_chapter)
    english_fingerprint = chapter_fingerprint(english_chapter)
    geez_sources = reader["source_ids"]
    english_sources = companion["source_ids"]
    return {
        "record_id": "genesis-1-divine-person-lens",
        "schema_version": 2,
        "status": "Counts describe these stored chapter witnesses only. Editorial speech boundaries are not independently reviewed; the Geʽez grammatical-person measurement is unassessed.",
        "scope": {
            "unit": {"unit_type": "chapter", "chapter": 1},
            "witnesses": [
                {
                    "witness_id": READER_ID,
                    "role": "source_text",
                    "language_tag": reader["language_tag"],
                    "source_ids": geez_sources,
                    "stored_verse_count": len(geez_chapter["verses"]),
                    "text_sha256": geez_fingerprint,
                },
                {
                    "witness_id": ENGLISH_TRANSLATION_ID,
                    "role": "translation_companion",
                    "language_tag": companion["language_tag"],
                    "source_ids": english_sources,
                    "stored_verse_count": len(english_chapter["verses"]),
                    "text_sha256": english_fingerprint,
                },
            ],
        },
        "measurements": [
            {
                "measurement_id": "english-first-person-forms-in-attributed-divine-speech",
                "witness_id": ENGLISH_TRANSLATION_ID,
                "language_tag": companion["language_tag"],
                "feature": "First-person pronoun tokens in manually delimited speech attributed to God",
                "state": "measured",
                "count": sum(token_counts.values()),
                "count_unit": "token",
                "operational_definition": "Exact English first-person pronoun tokens in the manually delimited speech excerpts; this is not a count of first-person verbs.",
                "evidence_source_ids": english_sources,
                "breakdowns": [{"dimension": "token", "values": [{"value": token, "count": count} for token, count in sorted(token_counts.items())]}],
                "excerpts": [{"unit_label": span["verse"], "text": span["text"]} for span in spans],
                "speaker_attribution": {
                    "statement": "Editorial segmentation of speech introduced by ‘And God said’ or ‘God blessed them, saying’; verse continuations are included only where specified.",
                    "review_state": "not_independently_reviewed",
                },
            },
            {
                "measurement_id": "english-explicit-noun-god",
                "witness_id": ENGLISH_TRANSLATION_ID,
                "language_tag": companion["language_tag"],
                "feature": "Case-insensitive whole-word occurrences of the noun God",
                "state": "measured",
                "count": sum(god_counts.values()),
                "count_unit": "occurrence",
                "operational_definition": "Case-insensitive whole-word occurrences of the noun ‘God’ in all stored English verse texts; excludes pronouns and theological inference.",
                "evidence_source_ids": english_sources,
                "breakdowns": [{"dimension": "verse", "values": [{"value": verse, "count": count} for verse, count in sorted(god_counts.items(), key=lambda item: int(item[0]))]}],
            },
            {
                "measurement_id": "english-third-person-narrator-noun-god",
                "witness_id": ENGLISH_TRANSLATION_ID,
                "language_tag": companion["language_tag"],
                "feature": "Explicit noun ‘God’ in narrative text outside editorially delimited divine-speech excerpts",
                "state": "measured",
                "count": sum(narrator_god_counts.values()),
                "count_unit": "occurrence",
                "operational_definition": "Case-insensitive whole-word occurrences of ‘God’ in the 31 stored English verse texts, minus occurrences inside the exact manually delimited speech excerpts recorded in this lens. This is a lexical proxy for narrative third-person reference, not a count of third-person pronouns or verbs.",
                "evidence_source_ids": english_sources,
                "breakdowns": [{"dimension": "verse", "values": [{"value": verse, "count": count} for verse, count in sorted(narrator_god_counts.items(), key=lambda item: int(item[0]))]}],
                "speaker_attribution": {
                    "statement": "The same editorial speech spans used for the first-person count are excluded; the boundaries are not independently reviewed.",
                    "review_state": "not_independently_reviewed",
                },
            },
            {
                "measurement_id": "english-third-person-pronoun-god-reference",
                "witness_id": ENGLISH_TRANSLATION_ID,
                "language_tag": companion["language_tag"],
                "feature": "Third-person subject pronoun ‘he’ manually attributed to God in narrator clauses",
                "state": "measured",
                "count": len(third_person_pronoun_spans),
                "count_unit": "token",
                "operational_definition": "Exact whole-word ‘he’ tokens in the listed narrator phrases, with God manually identified as antecedent. Only these five checked tokens are counted; this is not a chapter-wide count of every third-person form or a count of all references to God.",
                "evidence_source_ids": english_sources,
                "breakdowns": [{
                    "dimension": "verse",
                    "values": [
                        {"value": verse, "count": sum(1 for span in third_person_pronoun_spans if span["verse"] == verse)}
                        for verse in sorted({span["verse"] for span in third_person_pronoun_spans}, key=int)
                    ],
                }],
                "excerpts": [
                    {"unit_label": span["verse"], "text": span["text"]}
                    for span in third_person_pronoun_spans
                ],
                "speaker_attribution": {
                    "statement": "Each phrase is manually selected from Brenton's narrator text; the pronoun's antecedent attribution is editorial.",
                    "review_state": "not_independently_reviewed",
                },
            },
            {
                "measurement_id": "geez-exact-string-lexical-occurrences",
                "witness_id": READER_ID,
                "language_tag": reader["language_tag"],
                "feature": f"Exact Unicode string occurrences: {GEʽEZ_STRING}",
                "observed_value": GEʽEZ_STRING,
                "state": "measured",
                "count": sum(geez_counts.values()),
                "count_unit": "occurrence",
                "operational_definition": "Exact Unicode string occurrences in the stored Geʽez verse texts; not a grammatical-person count or a claim of translation equivalence.",
                "evidence_source_ids": geez_sources,
                "breakdowns": [{"dimension": "verse", "values": [{"value": verse, "count": count} for verse, count in sorted(geez_counts.items(), key=lambda item: int(item[0]))]}],
            },
            {
                "measurement_id": "geez-first-person-grammatical-forms",
                "witness_id": READER_ID,
                "language_tag": reader["language_tag"],
                "feature": "First-person grammatical forms in speech attributed to God",
                "state": "unassessed",
                "count": None,
                "count_unit": "grammatical_form",
                "operational_definition": "A language-specific morphological and speaker-attribution analysis covering this chapter; no Geʽez grammatical-person count is reported.",
                "evidence_source_ids": geez_sources,
                "reason_for_state": "No chapter-wide Geʽez morphology and independently reviewed speech-attribution method has been applied. Unassessed is not zero.",
            },
            {
                "measurement_id": "english-second-person-audience-reference-in-attributed-speech",
                "witness_id": ENGLISH_TRANSLATION_ID,
                "language_tag": companion["language_tag"],
                "feature": "Second-person audience-reference tokens in the same attributed speech excerpts",
                "state": "measured",
                "count": sum(second_person_by_verse.values()),
                "count_unit": "token",
                "operational_definition": "Exact whole-word ‘you’ in the manually delimited speech excerpts; these are audience references, not self-reference by God.",
                "evidence_source_ids": english_sources,
                "breakdowns": [{"dimension": "verse", "values": [{"value": verse, "count": count} for verse, count in sorted(second_person_by_verse.items(), key=lambda item: int(item[0]))]}],
                "speaker_attribution": {
                    "statement": "Uses the same editorial speech spans as the first-person count.",
                    "review_state": "not_independently_reviewed",
                },
            },
        ],
        "interpretive_limits": [
            "Brenton is a historical English translation from the Greek Septuagint, not a direct translation from this Geʽez witness.",
            "Matching lexical counts do not establish word-for-word correspondence or translation equivalence.",
            "The English speaker spans are editorial; the count makes no theological claim about the plural in ‘us’ or ‘our’.",
            "The English third-person pronoun count includes only the five listed ‘he’ tokens manually attributed to God; other pronouns and all Geʽez grammatical forms remain outside that measurement.",
            "A Geʽez first-person grammatical count remains unassessed, not zero, pending a Genesis-covering morphology and independently reviewed speech-attribution method.",
        ],
    }


def write() -> dict:
    record = build()
    OUTPUT.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return record


if __name__ == "__main__":
    record = write()
    measurements = {item["measurement_id"]: item for item in record["measurements"]}
    print(
        "Built Genesis 1 lens record: "
        f"{measurements['english-first-person-forms-in-attributed-divine-speech']['count']} manually attributed English first-person forms, "
        f"{measurements['english-explicit-noun-god']['count']} English noun occurrences, and "
        f"{measurements['geez-exact-string-lexical-occurrences']['count']} exact Ge'ez string occurrences."
    )
