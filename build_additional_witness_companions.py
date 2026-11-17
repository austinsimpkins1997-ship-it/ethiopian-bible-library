"""Seven separately navigated historical comparisons, without invented alignment."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import zipfile

import build_brenton_octateuch as brenton
from build_brenton_research_readers import build_records, CANDIDATE_CANON_LINKS
from build_minor_prophet_companions import serialize, BOUNDARY, AS_OF

ROOT = Path(__file__).resolve().parent
BASE = 'https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id'
SPECS = (
    ('HAB','habakkuk-geez-lofgren-ghebre-tau','brenton-lxx-hab-research',3,3,'eotc-ot-40'),
    ('MAL','malachi-geez-lofgren-ghebre-tau','brenton-lxx-mal-research',4,3,'eotc-ot-44'),
    ('SIR','sirach-geez-dillmann-hacohen-tau','sirach-brenton-lxx-1851-research',51,51,'eotc-ot-45'),
    ('1SA','samuel-i-geez-research','brenton-lxx-first-sa-research',31,31,'eotc-ot-09'),
    ('2SA','samuel-ii-geez-research','brenton-lxx-second-sa-research',24,24,'eotc-ot-09'),
    ('1KI','kings-i-geez-research','brenton-lxx-first-ki-research',23,22,'eotc-ot-10'),
    ('2KI','kings-ii-geez-research','brenton-lxx-second-ki-research',25,25,'eotc-ot-10'),
)
REASONS = {
    'HAB': 'Captured Habakkuk page 2 is titled/indexed as Habakkuk, but its twenty external verse links target Nahum. The discrepancy is retained, not repaired; no automatic verse pairing is offered.',
    'MAL': 'The Geʽez source has four chapter pages; this English edition has three chapters. No chapter or verse crosswalk has been established.',
    'SIR': 'The Geʽez and English Sirach witnesses retain their own gaps and labels; the English prologue includes lettered labels 1a–1g in chapter 1. Equal chapter totals do not establish alignment.',
    '1SA': 'TAU Regum I and Brenton Kings I / USFM 1SA are compared as a work-family candidate only. TAU page 31 includes a link to 2 Samuel 1:1; that boundary span is retained, not moved or merged. No chapter/verse alignment is established.',
    '2SA': 'TAU Regum II and Brenton Kings II / USFM 2SA are compared as a work-family candidate only. Page/verse boundaries and textual agreement have not been verified.',
    '1KI': 'TAU Regum III contains 23 source-page divisions, including 3a/3b and menu order 21 before 20, while Brenton Kings III / USFM 1KI has 22 chapters. Page positions are not an alignment.',
    '2KI': 'TAU Regum IV and Brenton Kings IV / USFM 2KI are compared as a work-family candidate only. Equal page/chapter totals do not establish alignment.',
}


def source_records() -> tuple[dict, dict]:
    from build_habakkuk_reader import build as habakkuk
    from build_malachi_reader import build as malachi
    from build_sirach_reader import build as sirach
    from build_reigns_readers import build as samuel
    from build_kings_research_readers import build as kings
    readers, layers = {}, {}
    for builder in (habakkuk, malachi, sirach):
        reader, layer = builder()
        readers[reader['reader_id']] = reader
        layers[reader['reader_id']] = layer
    for builder in (samuel, kings):
        batch, corpora, _ = builder()
        for reader in batch:
            readers[reader['reader_id']] = reader
            corpus = next(c for c in corpora if c['reader_id'] == reader['reader_id'])
            layers[reader['reader_id']] = source_layer(reader, corpus)
    return readers, layers


def source_layer(reader: dict, corpus: dict) -> dict:
    """Register research source layers without upgrading their canon status."""
    ids = reader['source_ids']
    mapping_ids = sorted(set(corpus['source_ids']) | {'SRC-384'})
    return {
        'schema_version':2,'record_id':f"{BASE}/layer/reader-{reader['reader_id']}",
        'work_id':f"{BASE}/work/reader-{reader['reader_id']}",
        'labels':[{'value':reader['title'],'language_tag':'en','label_type':'preferred'}],
        'tradition_assertions':[{'tradition_id':f'{BASE}/tradition/eotc',
            'canon_id':f"{BASE}/canon/{corpus['candidate_canon_id']}",
            'mapping_state':corpus['canon_mapping_state'],'evidence_source_ids':mapping_ids,
            'notes':corpus['canon_mapping_note']}],
        'witness':{'witness_id':f"{BASE}/witness/reader-{reader['reader_id']}",
            'witness_type':'digital_edition','title':reader['title'],
            'date_statement':reader['edition'],'repository_or_publisher':'Tel Aviv University website',
            'editorial_policy':reader['transcription_note'],'source_ids':ids},
        'layer_type':'source_text_transcription','text_origin':'source_transcription',
        'language_tag':'gez','language_name_as_recorded':reader['language'],'script_code':'Ethi',
        'basis_path':['gez'],'agents':[],
        'content_package':{'uri':f"../readers/{reader['reader_id']}.json",'media_type':'application/json',
            'sha256':'0'*64,'format_version':'1'},
        'coverage':{'extent_state':'complete_for_declared_edition','extent_basis':'source_inventory',
            'unit_count':reader['unit_count'],'structure_description':reader['chapter_structure_note'],
            'missing_or_lacunose_ranges':[],
            'numbering_policy':'Preserve every source page label, linked target and unit in source order. No cross-witness alignment is inferred.'},
        'rights':{'status':'permission_limited','statement':reader['copyright_notice'],
            'license_id':None,'rights_holder':'Ran HaCohen (TAU site notice)',
            'attribution_required':True,'territory_or_term_limits':reader['commercial_use'],
            'evidence_source_ids':ids},
        'review_dimensions':[
            {'dimension':'identity','state':'checked_with_limits',
             'scope':corpus['canon_mapping_note'],'reviewer':None,
             'review_method':'source_inspection',
             'review_process':'Preserved existing research/reigns-title-crosswalk-review.md and the recorded standard USFM identifier table for work/title aliases only',
             'reviewed_at':AS_OF,'evidence_source_ids':mapping_ids,
             'notes':'Work/title crosswalk only, carried from the existing cited review. Current edition identity, textual agreement and alignment remain unverified.'},
            {'dimension':'chapter_or_section_sequence','state':'checked_with_limits',
             'scope':reader['verification_status'],'reviewer':None,'review_method':'automated_validation',
             'review_process':'Retained TAU capture hashes, menu/page/linked-label parser audit',
             'reviewed_at':AS_OF,'evidence_source_ids':ids,'notes':'Digital source scope only; no print/manuscript collation.'},
            {'dimension':'transcription_accuracy','state':'unknown','scope':'Independent Geʽez proofreading and print/manuscript collation have not been performed.',
             'reviewer':None,'review_method':'unknown','review_process':None,'reviewed_at':None,
             'evidence_source_ids':ids,'notes':'Source-reported OCR/proofreading is not an independent review by this archive.'},
        ],
        'publication_state':'bundled','additional_notes':reader['edition_scope'],
    }


def prepare_pair(source: dict, english: dict, parsed: dict, code: str) -> dict:
    spec = next((s for s in SPECS if s[0] == code), None)
    if not spec or (source.get('reader_id'),english.get('reader_id')) != (spec[1],spec[2]):
        raise ValueError('Witness identities differ from the reviewed association.')
    if (source.get('rights_classification') != 'permission_limited' or not source.get('copyright_notice')
            or english.get('rights_classification') != 'public_domain_claimed' or not english.get('copyright_notice')):
        raise ValueError('Separate source rights and notices are required before copying.')
    if english.get('translation_path') != ['grc','en'] or english.get('basis_language_tag') != 'grc':
        raise ValueError('Do not substitute an unestablished translation basis.')
    for record, count in ((source,spec[3]),(english,spec[4]),(parsed,spec[4])):
        if record.get('chapter_count') != count or [c['chapter'] for c in record['chapters']] != list(range(1,count+1)):
            raise ValueError('Chapter/page inventory changed; reassess the association.')
    if english['chapters'] != parsed['chapters'] or any(english.get(k) != parsed.get(k) for k in ('source_package_sha256','source_member_sha256')):
        raise ValueError('English reader differs from the freshly parsed source member.')
    result = copy.deepcopy(source)
    companion = copy.deepcopy(parsed)
    companion.update(translation_id=english['translation_id'],title='English companion — '+english['title'],
        english_reader_id=english['reader_id'],comparison_policy='independent_chapters',
        comparison_note=REASONS[code],translation_basis=BOUNDARY+' '+REASONS[code],
        text_notice=english['copyright_notice'],verification_status=english['verification_status'])
    result['parallel_translation'] = companion
    # The enclosing record still describes the Geʽez source. English evidence
    # belongs to the nested companion and must not become Geʽez mapping evidence.
    result['source_ids'] = copy.deepcopy(source['source_ids'])
    result['additional_notes'] = 'Primary text remains the captured Geʽez witness. '+BOUNDARY+' '+REASONS[code]
    return result


def build() -> list[dict]:
    sources, layers = source_records()
    fresh_english = {r['reader_id']:r for r in build_records()[0]}
    manifest = json.loads(brenton.MANIFEST.read_text(encoding='utf-8'))
    registry_path = ROOT / 'translation-registry.json'
    registry = json.loads(registry_path.read_text(encoding='utf-8'))
    en = next(p for p in registry['languages'] if p['language_tag']=='en')
    pending, reports = [], []
    with zipfile.ZipFile(brenton.PACKAGE) as package:
        for code, sid, eid, scount, ecount, canon in SPECS:
            matches = [p for p in (ROOT/'readers').glob('*.json') if p.stem==eid or (code=='SIR' and p.name=='sirach-brenton-lxx-1851.json')]
            if len(matches)!=1: raise ValueError('English package path is not unique: '+eid)
            english = json.loads(matches[0].read_text(encoding='utf-8'))
            if code!='SIR' and {k:english.get(k) for k in fresh_english[eid]}!=fresh_english[eid]:
                raise ValueError('English source reader must be rebuilt first: '+eid)
            member = next(n for n in manifest['selected_members'] if f'-{code}eng-Brenton.usfm' in n)
            raw = package.read(member)
            pin = manifest['selected_members'][member]
            if len(raw)!=pin['byte_length'] or hashlib.sha256(raw).hexdigest()!=pin['sha256']:
                raise ValueError('Retained member digest/size changed: '+member)
            previous = brenton.BOOKS.get(code)
            brenton.BOOKS[code]=(code.lower(),0,english['title'].split(' — ')[0],ecount)
            try: parsed=brenton.parse_usfm(raw,code,member,manifest['archive_sha256'])
            finally:
                if previous is None: brenton.BOOKS.pop(code,None)
                else: brenton.BOOKS[code]=previous
            source=sources[sid]
            reader=prepare_pair(source,english,parsed,code)
            path=ROOT/'readers'/f'{sid}.json'
            digest=hashlib.sha256(serialize(reader)).hexdigest()
            source_meta=copy.deepcopy(layers[sid])
            source_meta['content_package']['sha256']=digest
            source_meta['additional_notes']='This record describes the Geʽez layer only; the shared package includes a separately identified English comparison. '+BOUNDARY
            source_paths=[p for p in (ROOT/'examples').glob('*-layer.json')
                          if json.loads(p.read_text(encoding='utf-8')).get('record_id')==source_meta['record_id']]
            if len(source_paths)>1: raise ValueError('Duplicate source layer IDs: '+sid)
            source_path=source_paths[0] if source_paths else ROOT/'examples'/f'{sid}-layer.json'
            companion=reader['parallel_translation']
            english_layer=brenton.make_layer(sid,english['title'],canon,companion,path.name)
            # A packaging occurrence of an existing translation is not a new translation.
            english_layer['record_id']=f"{BASE}/layer/{companion['translation_id']}-in-{sid}"
            english_layer['content_package']['sha256']=digest
            note=(CANDIDATE_CANON_LINKS[code][1] if code!='SIR' else 'The Church-list Sirach title and the Greek-basis English edition have a provisional title-family relationship; exact witness identity is not established.')
            english_layer['tradition_assertions'][0].update(mapping_state='uncertain',evidence_source_ids=['SRC-029','SRC-038','SRC-142'],notes=note)
            if code=='SIR':
                existing=json.loads((ROOT/'examples/sirach-brenton-translation-layer.json').read_text(encoding='utf-8'))
                english_layer['witness']=copy.deepcopy(existing['witness'])
                english_layer['work_id']=existing['work_id']
            for review in english_layer['review_dimensions']:
                if review.get('reviewed_at') is not None: review['reviewed_at']=AS_OF
            english_layer['coverage']['numbering_policy']='Keep both editions independent; no automatic chapter or verse pairing. '+REASONS[code]
            english_layer['additional_notes']='An additional packaging location of the existing Brenton witness, not a new translation. '+BOUNDARY+' '+REASONS[code]
            association={'canon_id':canon,'reader_id':sid,'translation_id':companion['translation_id'],
                'layer_role':'historical_companion_translation','status':'bundled',
                'translator':companion['translator'],'basis_language_tag':'grc',
                'basis_description':companion['translation_basis'],'rights_status':'public_domain_per_cited_source',
                'source_ids':['SRC-038','SRC-142'],'translation_path':['grc','en'],'rights_classification':'public_domain_claimed'}
            en['records']=[r for r in en['records'] if not(r.get('reader_id')==sid and r.get('translation_id')==companion['translation_id'])]+[association]
            reports.append({'reader_id':sid,'english_reader_id':eid,'comparison_policy':'independent_chapters',
                'source_pages':scount,'english_chapters':ecount,'source_units':source['unit_count'],
                'english_units':english['unit_count'],'reason':REASONS[code],
                'source_ids':reader['source_ids'],'english_source_ids':companion['source_ids'],
                'source_package_sha256':manifest['archive_sha256'],
                'english_member':member,'english_member_sha256':pin['sha256'],
                'source_page_labels':[c.get('source_page_label',c['chapter']) for c in source['chapters']],
                'english_chapter_labels':[c['chapter'] for c in english['chapters']],
                'alignment_status':'UNVERIFIED_NO_AUTOMATIC_PAIRING'})
            pending.extend([(path,reader),(source_path,source_meta),
                (ROOT/'examples'/f'{sid}-brenton-comparison-layer.json',english_layer)])
    pending += [(registry_path,registry),(ROOT/'research/additional-parallel-witness-review.json',{'as_of':AS_OF,'scope':BOUNDARY,'comparisons':reports})]
    for path,record in pending: path.write_bytes(serialize(record))
    print(f'Built {len(reports)} independent historical comparisons; no chapter/verse crosswalk inferred.')
    return reports


if __name__=='__main__': build()
