import re
import unittest
from html.parser import HTMLParser

from build_malachi_reader import CAPTURE, PageParser, build


class BodyText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.inside=False
        self.parts=[]
    def handle_starttag(self,tag,attrs):
        if tag=='body':self.inside=True
    def handle_endtag(self,tag):
        if tag=='body':self.inside=False
    def handle_data(self,data):
        if self.inside:self.parts.append(data)


class MalachiExtractionTests(unittest.TestCase):
    def test_body_after_link_is_kept_and_footer_excluded(self):
        parser=PageParser()
        parser.feed('<p><a href="?search=Mal+1%3A1">1</a> ጽሑፍ ፡ <a href="?search=Mal+1%3A2">2</a> ቃል ።</p><p>Navigation</p>')
        parser.close()
        self.assertEqual(parser.rows,[(1,'1','ጽሑፍ ፡'),(1,'2','ቃል ።')])

    def test_all_55_units_have_letters_and_all_source_ethiopic_characters_are_retained(self):
        reader,_=build()
        letters=lambda s: ''.join(re.findall(r'[\u1200-\u137f]',s))
        self.assertEqual(reader['unit_count'],55)
        for chapter in reader['chapters']:
            with self.subTest(chapter=chapter['chapter']):
                source=BodyText()
                source.feed((CAPTURE/f"malachi-chapter-{chapter['chapter']}.html").read_text(encoding='ascii'))
                expected=letters(''.join(source.parts))
                actual=''.join(chapter.get('heading',[]))+''.join(v['text']+''.join(c['text'] for c in v.get('continuations',[])) for v in chapter['verses'])
                self.assertTrue(all(re.search(r'[\u1200-\u135a]',v['text']) for v in chapter['verses']))
                self.assertEqual(letters(actual),expected,'every source Ethiopic character remains in order')


if __name__=='__main__':unittest.main()
