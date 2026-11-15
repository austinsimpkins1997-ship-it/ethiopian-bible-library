const assert=require('node:assert/strict');
const fs=require('node:fs');
const archive=require('../archive.json');
const index=require('../english-reference-index.json');
const api=require('../reader-english.js');
const {createReaderPackage}=require('../reader-package.js');
const byId=new Map(archive.readers.map(r=>[r.reader_id,r]));
for(const reader of archive.readers) {
 const ref=api.referenceFor(index,archive.readers,reader.reader_id);
 if(reader.language_tag!=='en') {
  assert(ref,reader.reader_id+' must have its sourced English reference');
  assert.equal(ref.language_tag,'en');
  assert(ref.chapters.length>0);
 }
}
const base=byId.get('alaba-kabeena-1co-research');
const ref=api.referenceFor(index,archive.readers,base.reader_id);
const copy=JSON.stringify(base);
const exported=createReaderPackage(archive,base.reader_id,'reference',ref);
assert.equal(exported.schema_version,2);
assert.deepEqual(exported.text_layers.map(layer=>layer.language_tag),['alw','en']);
assert.equal(JSON.stringify(base),copy,'comparison export cannot modify the archived source');
assert.equal(exported.comparison_reference.english_reader_id,ref.reader_id);
assert.equal(exported.comparison_reference.reference_canon_mapping.state,'uncertain');
assert.deepEqual(exported.unresolved_source_ids,[]);
const englishOnly=createReaderPackage(archive,base.reader_id,'reference-en',ref);
assert.equal(englishOnly.text_layers.length,1);
assert.equal(englishOnly.text_layers[0].record.reader_id,ref.reader_id);
assert.equal(api.suggestedChapter({chapter:4,source_page_label:'3b'},ref.chapters),3);
assert.equal(api.suggestedChapter({chapter:999},ref.chapters),null,'missing English chapters must not silently select chapter one');
assert.equal(api.safeReaderPath('../archive.json'),false);
assert.equal(api.safeReaderPath('https://example.test/text.json'),false);
assert.equal(api.safeReaderPath('readers/english.json'),true);
assert.throws(()=>createReaderPackage(archive,base.reader_id,'reference',base));
fs.mkdirSync('tmp',{recursive:true});
fs.writeFileSync('tmp/english-reference-export.json',JSON.stringify(exported));
console.log('All '+archive.readers.length+' readers checked; sourced-reference exports and navigation boundaries passed.');
