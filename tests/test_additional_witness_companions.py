import copy
import json
import unittest

from build_additional_witness_companions import ROOT, SPECS, source_records, prepare_pair


class AdditionalWitnessCompanionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources, cls.layers = source_records()

    def inputs(self, code):
        spec = next(s for s in SPECS if s[0] == code)
        source = self.sources[spec[1]]
        english_path = ROOT/'readers'/('sirach-brenton-lxx-1851.json' if code=='SIR' else spec[2]+'.json')
        english = json.loads(english_path.read_text(encoding='utf-8'))
        reader = json.loads((ROOT/'readers'/(spec[1]+'.json')).read_text(encoding='utf-8'))
        return source,english,reader['parallel_translation']

    def test_all_seven_preserve_source_and_english_without_inferred_crosswalks(self):
        for code,*_ in SPECS:
            with self.subTest(code=code):
                source,english,parsed = self.inputs(code)
                before = copy.deepcopy(source)
                reader = prepare_pair(source,english,parsed,code)
                self.assertEqual(source,before)
                self.assertEqual(reader['chapters'],source['chapters'])
                self.assertEqual(reader['copyright_notice'],source['copyright_notice'])
                self.assertEqual(reader['source_ids'],source['source_ids'],'English evidence cannot replace or expand Geʽez provenance')
                companion=reader['parallel_translation']
                self.assertEqual(companion['chapters'],english['chapters'])
                self.assertEqual(companion['comparison_policy'],'independent_chapters')
                self.assertEqual(companion['basis_language_tag'],'grc')
                self.assertIn('unverified',companion['translation_basis'])
                self.assertEqual(reader.get('canon_id'),source.get('canon_id'))
                self.assertEqual(reader.get('research_corpus_id'),source.get('research_corpus_id'))
                if source.get('research_corpus_id'):
                    layer=self.layers[source['reader_id']]
                    self.assertTrue(layer['record_id'].endswith('/layer/reader-'+source['reader_id']))
                    self.assertTrue(layer['witness']['witness_id'].endswith('/witness/reader-'+source['reader_id']))
                    self.assertIn('SRC-384',layer['tradition_assertions'][0]['evidence_source_ids'])
                    self.assertNotIn('SRC-384',layer['rights']['evidence_source_ids'],'a format table is not rights evidence')

    def test_malachi_and_kings_keep_every_nonmatching_chapter(self):
        for code,counts in [('MAL',(4,3)),('1KI',(23,22))]:
            source,english,parsed=self.inputs(code)
            reader=prepare_pair(source,english,parsed,code)
            self.assertEqual((len(reader['chapters']),len(reader['parallel_translation']['chapters'])),counts)
        kings=self.inputs('1KI')[0]
        self.assertEqual([c['source_page_label'] for c in kings['chapters'][2:4]],['3a','3b'])
        self.assertEqual([c['source_page_label'] for c in kings['chapters'][-3:]],['21','20','22'])

    def test_habakkuk_link_anomaly_is_not_rewritten(self):
        source,english,parsed=self.inputs('HAB')
        result=prepare_pair(source,english,parsed,'HAB')
        chapter=result['chapters'][1]
        self.assertEqual(chapter,source['chapters'][1])
        self.assertTrue(all('Nah' in str(v.get('source_link_target_book')) for v in chapter['verses']))
        self.assertIn('Nahum',result['parallel_translation']['comparison_note'])

    def test_sirach_prologue_and_continuation_are_retained(self):
        source,english,parsed=self.inputs('SIR')
        result=prepare_pair(source,english,parsed,'SIR')['parallel_translation']
        labels={v['number'] for v in result['chapters'][0]['verses']}
        self.assertTrue({f'1{x}' for x in 'abcdefg'} <= labels)
        self.assertEqual(sum(len(v.get('continuations',[])) for c in result['chapters'] for v in c['verses']),1)

    def test_missing_rights_and_changed_wording_are_held(self):
        source,english,parsed=self.inputs('MAL')
        bad=copy.deepcopy(english);bad['rights_classification']='unknown'
        with self.assertRaisesRegex(ValueError,'rights'):
            prepare_pair(source,bad,parsed,'MAL')
        bad=copy.deepcopy(english);bad['chapters'][0]['verses'][0]['text']+=' invented'
        with self.assertRaisesRegex(ValueError,'freshly parsed'):
            prepare_pair(source,bad,parsed,'MAL')

    def test_changed_chapter_inventory_is_not_silently_accepted(self):
        source,english,parsed=self.inputs('1KI')
        bad=copy.deepcopy(source);bad['chapter_count']=22
        with self.assertRaisesRegex(ValueError,'inventory changed'):
            prepare_pair(bad,english,parsed,'1KI')


if __name__=='__main__':unittest.main()
